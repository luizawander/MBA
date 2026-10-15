import os
from datetime import datetime
import duckdb
import pandas as pd
from deltalake import write_deltalake, DeltaTable

SILVER_DIR = os.path.join("lakehouse", "silver")
GOLD_DIR = os.path.join("lakehouse", "gold")

def run_gold_pipeline():
    print(f"[{datetime.now().isoformat()}] Iniciando Pipeline da Camada Gold com DuckDB e Delta Lake...")
    os.makedirs(GOLD_DIR, exist_ok=True)
    
    con = duckdb.connect()
    
    # Load Silver Delta tables as pyarrow tables into DuckDB
    print("Carregando tabelas Silver no DuckDB...")
    t_clientes = DeltaTable(os.path.join(SILVER_DIR, "silver_clientes")).to_pyarrow_table()
    t_produtos = DeltaTable(os.path.join(SILVER_DIR, "silver_produtos")).to_pyarrow_table()
    t_vendas = DeltaTable(os.path.join(SILVER_DIR, "silver_vendas")).to_pyarrow_table()
    t_avaliacoes = DeltaTable(os.path.join(SILVER_DIR, "silver_avaliacoes")).to_pyarrow_table()
    t_eventos = DeltaTable(os.path.join(SILVER_DIR, "silver_eventos_web")).to_pyarrow_table()
    t_atendimento = DeltaTable(os.path.join(SILVER_DIR, "silver_atendimento")).to_pyarrow_table()
    
    con.register("silver_clientes", t_clientes)
    con.register("silver_produtos", t_produtos)
    con.register("silver_vendas", t_vendas)
    con.register("silver_avaliacoes", t_avaliacoes)
    con.register("silver_eventos_web", t_eventos)
    con.register("silver_atendimento", t_atendimento)
    
    # -------------------------------------------------------------
    # 1. Gold: Desempenho de Produtos e Categorias
    # Integra: Vendas (estruturado) + Produtos (estruturado) + Avaliações (misto) + Atendimento (não estruturado)
    # Responde: Perguntas 1, 2, 3 e 5
    # -------------------------------------------------------------
    print("Gerando gold_desempenho_produtos_categorias...")
    query_desempenho = """
    WITH vendas_agregadas AS (
        SELECT 
            produto_id,
            COUNT(DISTINCT venda_id) AS total_pedidos,
            SUM(CASE WHEN status = 'Concluída' THEN quantidade ELSE 0 END) AS unidades_vendidas_concluidas,
            SUM(CASE WHEN status = 'Concluída' THEN valor_unitario * quantidade ELSE 0 END) AS faturamento_bruto,
            SUM(CASE WHEN status = 'Concluída' THEN (valor_unitario * quantidade) * desconto_pct ELSE 0 END) AS total_descontos,
            SUM(CASE WHEN status = 'Concluída' THEN valor_total ELSE 0 END) AS faturamento_liquido,
            COUNT(DISTINCT CASE WHEN status = 'Cancelada' THEN venda_id END) AS pedidos_cancelados,
            COUNT(DISTINCT CASE WHEN status = 'Devolvida' THEN venda_id END) AS pedidos_devolvidos
        FROM silver_vendas
        GROUP BY produto_id
    ),
    avaliacoes_agregadas AS (
        SELECT 
            produto_id,
            COUNT(avaliacao_id) AS total_avaliacoes,
            ROUND(AVG(nota), 2) AS nota_media,
            COUNT(CASE WHEN nota <= 2 THEN 1 END) AS avaliacoes_negativas,
            COUNT(CASE WHEN nota >= 4 THEN 1 END) AS avaliacoes_positivas
        FROM silver_avaliacoes
        GROUP BY produto_id
    ),
    atendimento_agregado AS (
        SELECT 
            produto_id,
            COUNT(protocolo) AS total_chamados_suporte,
            COUNT(CASE WHEN sentimento_cliente = 'irritado' THEN 1 END) AS chamados_cliente_irritado,
            COUNT(CASE WHEN motivo_contato LIKE '%defeito%' THEN 1 END) AS chamados_por_defeito
        FROM silver_atendimento
        GROUP BY produto_id
    )
    SELECT 
        p.produto_id,
        p.produto_nome,
        p.categoria,
        p.marca,
        p.preco_lista,
        p.status AS status_produto,
        COALESCE(v.total_pedidos, 0) AS total_pedidos,
        COALESCE(v.unidades_vendidas_concluidas, 0) AS unidades_vendidas,
        ROUND(COALESCE(v.faturamento_bruto, 0.0), 2) AS faturamento_bruto,
        ROUND(COALESCE(v.total_descontos, 0.0), 2) AS total_descontos,
        ROUND(COALESCE(v.faturamento_liquido, 0.0), 2) AS faturamento_liquido,
        COALESCE(v.pedidos_cancelados, 0) AS pedidos_cancelados,
        COALESCE(v.pedidos_devolvidos, 0) AS pedidos_devolvidos,
        ROUND(CASE WHEN COALESCE(v.total_pedidos, 0) > 0 
                   THEN (COALESCE(v.pedidos_cancelados, 0)::FLOAT / v.total_pedidos) * 100 
                   ELSE 0.0 END, 2) AS taxa_cancelamento_pct,
        ROUND(CASE WHEN COALESCE(v.total_pedidos, 0) > 0 
                   THEN (COALESCE(v.pedidos_devolvidos, 0)::FLOAT / v.total_pedidos) * 100 
                   ELSE 0.0 END, 2) AS taxa_devolucao_pct,
        COALESCE(a.total_avaliacoes, 0) AS total_avaliacoes,
        COALESCE(a.nota_media, 0.0) AS nota_media_avaliacao,
        COALESCE(a.avaliacoes_negativas, 0) AS avaliacoes_negativas,
        COALESCE(a.avaliacoes_positivas, 0) AS avaliacoes_positivas,
        ROUND(CASE WHEN COALESCE(a.total_avaliacoes, 0) > 0 
                   THEN (COALESCE(a.avaliacoes_negativas, 0)::FLOAT / a.total_avaliacoes) * 100 
                   ELSE 0.0 END, 2) AS prop_avaliacoes_negativas_pct,
        COALESCE(atend.total_chamados_suporte, 0) AS total_chamados_suporte,
        COALESCE(atend.chamados_cliente_irritado, 0) AS chamados_cliente_irritado,
        COALESCE(atend.chamados_por_defeito, 0) AS chamados_por_defeito,
        CURRENT_TIMESTAMP AS data_carga_gold
    FROM silver_produtos p
    LEFT JOIN vendas_agregadas v ON p.produto_id = v.produto_id
    LEFT JOIN avaliacoes_agregadas a ON p.produto_id = a.produto_id
    LEFT JOIN atendimento_agregado atend ON p.produto_id = atend.produto_id
    """
    df_desempenho = con.execute(query_desempenho).df()
    dest_desempenho = os.path.join(GOLD_DIR, "gold_desempenho_produtos_categorias")
    write_deltalake(dest_desempenho, df_desempenho, mode="overwrite")
    print(f" -> gold_desempenho_produtos_categorias salva: {len(df_desempenho)} linhas")
    
    # -------------------------------------------------------------
    # 2. Gold: Jornada Digital e Conversão
    # Integra: Eventos Web/App (semiestruturado) + Vendas (estruturado)
    # Responde: Pergunta 4 (comportamento digital que antecede compras)
    # -------------------------------------------------------------
    print("Gerando gold_jornada_digital_conversao...")
    query_jornada = """
    WITH sessao_metricas AS (
        SELECT 
            session_id,
            MAX(user_id) AS user_id,
            MAX(device) AS device,
            MAX(source) AS canal_aquisicao,
            MIN(data_hora_evento) AS inicio_sessao,
            MAX(data_hora_evento) AS fim_sessao,
            COUNT(event_id) AS total_eventos,
            SUM(duration_ms) / 1000.0 AS duracao_sessao_segundos,
            COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) AS qtd_page_views,
            COUNT(CASE WHEN event_type = 'search' THEN 1 END) AS qtd_buscas,
            COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) AS qtd_vistas_produto,
            COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) AS qtd_adicoes_carrinho,
            COUNT(CASE WHEN event_type = 'remove_from_cart' THEN 1 END) AS qtd_remocoes_carrinho,
            COUNT(CASE WHEN event_type = 'checkout_start' THEN 1 END) AS qtd_inicios_checkout,
            COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS converteu_compra,
            MAX(venda_id) AS venda_id,
            MAX(CASE WHEN event_type = 'purchase' THEN product_id END) AS produto_comprado,
            MAX(CASE WHEN event_type = 'purchase' THEN amount END) AS valor_compra_evento,
            MAX(CASE WHEN search_term != '' THEN search_term END) AS principal_termo_busca
        FROM silver_eventos_web
        GROUP BY session_id
    )
    SELECT 
        s.session_id,
        s.user_id,
        s.device,
        s.canal_aquisicao,
        s.inicio_sessao,
        s.fim_sessao,
        s.total_eventos,
        ROUND(s.duracao_sessao_segundos, 1) AS duracao_sessao_segundos,
        s.qtd_page_views,
        s.qtd_buscas,
        s.qtd_vistas_produto,
        s.qtd_adicoes_carrinho,
        s.qtd_remocoes_carrinho,
        s.qtd_inicios_checkout,
        (s.converteu_compra > 0) AS converteu_compra,
        s.venda_id,
        s.produto_comprado,
        COALESCE(s.valor_compra_evento, v.valor_total, 0.0) AS valor_venda_final,
        s.principal_termo_busca,
        (s.total_eventos - s.converteu_compra) AS acoes_precedentes_a_compra,
        CURRENT_TIMESTAMP AS data_carga_gold
    FROM sessao_metricas s
    LEFT JOIN silver_vendas v ON s.venda_id = v.venda_id
    """
    df_jornada = con.execute(query_jornada).df()
    dest_jornada = os.path.join(GOLD_DIR, "gold_jornada_digital_conversao")
    write_deltalake(dest_jornada, df_jornada, mode="overwrite")
    print(f" -> gold_jornada_digital_conversao salva: {len(df_jornada)} linhas")
    
    # -------------------------------------------------------------
    # 3. Gold: Satisfação, Atendimento e Qualidade
    # Integra: Atendimento (não estruturado) + Avaliações (misto) + Produtos (estruturado)
    # Responde: Perguntas 5 e 6
    # -------------------------------------------------------------
    print("Gerando gold_satisfacao_atendimento_qualidade...")
    query_satisfacao = """
    SELECT 
        p.categoria,
        atend.motivo_contato AS tema_reclamacao,
        COUNT(atend.protocolo) AS total_chamados_suporte,
        COUNT(CASE WHEN atend.sentimento_cliente = 'irritado' THEN 1 END) AS clientes_irritados,
        COUNT(CASE WHEN atend.sentimento_cliente = 'insatisfeito' THEN 1 END) AS clientes_insatisfeitos,
        COUNT(CASE WHEN atend.sentimento_cliente = 'preocupado' THEN 1 END) AS clientes_preocupados,
        COUNT(CASE WHEN atend.encaminhamento LIKE '%troca%' THEN 1 END) AS encaminhamentos_troca,
        COUNT(CASE WHEN atend.encaminhamento LIKE '%reembolso%' THEN 1 END) AS encaminhamentos_reembolso,
        CURRENT_TIMESTAMP AS data_carga_gold
    FROM silver_atendimento atend
    JOIN silver_produtos p ON atend.produto_id = p.produto_id
    GROUP BY p.categoria, atend.motivo_contato
    ORDER BY total_chamados_suporte DESC
    """
    df_satisfacao = con.execute(query_satisfacao).df()
    dest_satisfacao = os.path.join(GOLD_DIR, "gold_satisfacao_atendimento_qualidade")
    write_deltalake(dest_satisfacao, df_satisfacao, mode="overwrite")
    print(f" -> gold_satisfacao_atendimento_qualidade salva: {len(df_satisfacao)} linhas")
    
    # -------------------------------------------------------------
    # 4. Gold: Visão 360 do Cliente (Omnichannel)
    # Integra: Clientes + Vendas + Avaliações + Atendimento + Eventos
    # -------------------------------------------------------------
    print("Gerando gold_visao_360_cliente...")
    query_cliente360 = """
    WITH compras_cliente AS (
        SELECT 
            cliente_id,
            COUNT(DISTINCT venda_id) AS total_pedidos,
            SUM(CASE WHEN status = 'Concluída' THEN valor_total ELSE 0 END) AS total_gasto,
            ROUND(AVG(CASE WHEN status = 'Concluída' THEN valor_total END), 2) AS ticket_medio,
            COUNT(DISTINCT canal) AS canais_utilizados_compras
        FROM silver_vendas
        GROUP BY cliente_id
    ),
    avaliacoes_cliente AS (
        SELECT 
            cliente_id,
            COUNT(avaliacao_id) AS total_avaliacoes,
            ROUND(AVG(nota), 2) AS media_avaliacoes_feitas
        FROM silver_avaliacoes
        GROUP BY cliente_id
    ),
    atendimentos_cliente AS (
        SELECT 
            cliente_id,
            COUNT(protocolo) AS total_chamados,
            COUNT(CASE WHEN sentimento_cliente = 'irritado' THEN 1 END) AS chamados_irritado
        FROM silver_atendimento
        GROUP BY cliente_id
    ),
    eventos_cliente AS (
        SELECT 
            user_id AS cliente_id,
            COUNT(DISTINCT session_id) AS total_sessoes_web,
            COUNT(event_id) AS total_eventos_web
        FROM silver_eventos_web
        WHERE user_id != ''
        GROUP BY user_id
    )
    SELECT 
        c.cliente_id,
        c.nome,
        c.idade,
        c.uf,
        c.canal_preferencial,
        c.segmento,
        c.data_cadastro,
        COALESCE(cmp.total_pedidos, 0) AS total_pedidos,
        ROUND(COALESCE(cmp.total_gasto, 0.0), 2) AS total_gasto,
        COALESCE(cmp.ticket_medio, 0.0) AS ticket_medio,
        COALESCE(cmp.canais_utilizados_compras, 0) AS canais_utilizados_compras,
        COALESCE(av.total_avaliacoes, 0) AS total_avaliacoes,
        COALESCE(av.media_avaliacoes_feitas, 0.0) AS media_avaliacoes_feitas,
        COALESCE(atend.total_chamados, 0) AS total_chamados_suporte,
        COALESCE(atend.chamados_irritado, 0) AS chamados_irritado,
        COALESCE(ev.total_sessoes_web, 0) AS total_sessoes_web,
        COALESCE(ev.total_eventos_web, 0) AS total_eventos_web,
        CURRENT_TIMESTAMP AS data_carga_gold
    FROM silver_clientes c
    LEFT JOIN compras_cliente cmp ON c.cliente_id = cmp.cliente_id
    LEFT JOIN avaliacoes_cliente av ON c.cliente_id = av.cliente_id
    LEFT JOIN atendimentos_cliente atend ON c.cliente_id = atend.cliente_id
    LEFT JOIN eventos_cliente ev ON c.cliente_id = ev.cliente_id
    """
    df_cliente360 = con.execute(query_cliente360).df()
    dest_cliente360 = os.path.join(GOLD_DIR, "gold_visao_360_cliente")
    write_deltalake(dest_cliente360, df_cliente360, mode="overwrite")
    print(f" -> gold_visao_360_cliente salva: {len(df_cliente360)} linhas")
    
    print(f"[{datetime.now().isoformat()}] Pipeline Gold concluído com sucesso!")

if __name__ == "__main__":
    run_gold_pipeline()
