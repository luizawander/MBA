import os
import duckdb
from deltalake import DeltaTable

GOLD_DIR = os.path.join("lakehouse", "gold")

def run_analytical_queries():
    con = duckdb.connect()
    
    t_desempenho = DeltaTable(os.path.join(GOLD_DIR, "gold_desempenho_produtos_categorias")).to_pyarrow_table()
    t_jornada = DeltaTable(os.path.join(GOLD_DIR, "gold_jornada_digital_conversao")).to_pyarrow_table()
    t_satisfacao = DeltaTable(os.path.join(GOLD_DIR, "gold_satisfacao_atendimento_qualidade")).to_pyarrow_table()
    t_cliente360 = DeltaTable(os.path.join(GOLD_DIR, "gold_visao_360_cliente")).to_pyarrow_table()
    
    con.register("gold_desempenho", t_desempenho)
    con.register("gold_jornada", t_jornada)
    con.register("gold_satisfacao", t_satisfacao)
    con.register("gold_cliente360", t_cliente360)
    
    print("=" * 80)
    print("RESPOSTAS ÀS PERGUNTAS ANALÍTICAS DO MINIPROJETO")
    print("=" * 80)
    
    # -------------------------------------------------------------
    # Pergunta 1: Categorias com maior faturamento (bruto, líquido)
    # -------------------------------------------------------------
    print("\n[PERGUNTA 1] Faturamento Bruto e Líquido por Categoria:")
    q1 = """
    SELECT 
        categoria,
        COUNT(produto_id) AS total_produtos,
        SUM(unidades_vendidas) AS unidades_vendidas,
        ROUND(SUM(faturamento_bruto), 2) AS faturamento_bruto,
        ROUND(SUM(total_descontos), 2) AS total_descontos,
        ROUND(SUM(faturamento_liquido), 2) AS faturamento_liquido,
        ROUND((SUM(total_descontos) / NULLIF(SUM(faturamento_bruto), 0)) * 100, 2) AS desconto_medio_pct
    FROM gold_desempenho
    GROUP BY categoria
    ORDER BY faturamento_liquido DESC
    """
    df_q1 = con.execute(q1).df()
    print(df_q1.to_string(index=False))
    
    # -------------------------------------------------------------
    # Pergunta 2: Produtos com maior volume e melhor avaliação
    # -------------------------------------------------------------
    print("\n[PERGUNTA 2] Top 5 Produtos com Maior Volume e Melhor Avaliação (min 20 avaliações):")
    q2 = """
    SELECT 
        produto_id,
        produto_nome,
        categoria,
        marca,
        unidades_vendidas,
        total_pedidos,
        nota_media_avaliacao,
        total_avaliacoes,
        ROUND(faturamento_liquido, 2) AS faturamento_liquido
    FROM gold_desempenho
    WHERE total_avaliacoes >= 20
    ORDER BY unidades_vendidas DESC, nota_media_avaliacao DESC
    LIMIT 5
    """
    df_q2 = con.execute(q2).df()
    print(df_q2.to_string(index=False))
    
    # -------------------------------------------------------------
    # Pergunta 3: Relação entre Avaliação Média e Volume de Vendas
    # -------------------------------------------------------------
    print("\n[PERGUNTA 3] Relação entre Faixa de Avaliação e Volume Médio de Vendas:")
    q3 = """
    SELECT 
        CASE 
            WHEN nota_media_avaliacao >= 4.5 THEN '4.5 a 5.0 (Excelente)'
            WHEN nota_media_avaliacao >= 4.0 THEN '4.0 a 4.4 (Bom)'
            WHEN nota_media_avaliacao >= 3.5 THEN '3.5 a 3.9 (Regular)'
            WHEN nota_media_avaliacao >= 3.0 THEN '3.0 a 3.4 (Baixo)'
            ELSE 'Menor que 3.0 (Crítico)'
        END AS faixa_avaliacao,
        COUNT(produto_id) AS qtd_produtos,
        ROUND(AVG(unidades_vendidas), 1) AS media_unidades_por_produto,
        ROUND(AVG(faturamento_liquido), 2) AS faturamento_medio_por_produto,
        ROUND(AVG(taxa_cancelamento_pct), 2) AS taxa_cancelamento_media_pct,
        ROUND(AVG(taxa_devolucao_pct), 2) AS taxa_devolucao_media_pct
    FROM gold_desempenho
    WHERE total_pedidos > 0
    GROUP BY 1
    ORDER BY MIN(nota_media_avaliacao) DESC
    """
    df_q3 = con.execute(q3).df()
    print(df_q3.to_string(index=False))
    
    # -------------------------------------------------------------
    # Pergunta 4: Comportamentos digitais que antecedem uma compra
    # -------------------------------------------------------------
    print("\n[PERGUNTA 4] Comportamento Digital: Sessões com Compra vs Sessões sem Compra:")
    q4 = """
    SELECT 
        converteu_compra,
        COUNT(session_id) AS total_sessoes,
        ROUND(AVG(duracao_sessao_segundos), 1) AS duracao_media_segundos,
        ROUND(AVG(total_eventos), 1) AS media_eventos_sessao,
        ROUND(AVG(qtd_page_views), 1) AS media_page_views,
        ROUND(AVG(qtd_buscas), 1) AS media_buscas,
        ROUND(AVG(qtd_vistas_produto), 1) AS media_vistas_produto,
        ROUND(AVG(qtd_adicoes_carrinho), 1) AS media_adicoes_carrinho,
        ROUND(AVG(qtd_inicios_checkout), 1) AS media_inicios_checkout,
        ROUND(AVG(acoes_precedentes_a_compra), 1) AS media_passos_pre_compra
    FROM gold_jornada
    GROUP BY converteu_compra
    """
    df_q4 = con.execute(q4).df()
    print(df_q4.to_string(index=False))
    
    # -------------------------------------------------------------
    # Pergunta 5: Categorias com maior proporção de avaliações negativas
    # -------------------------------------------------------------
    print("\n[PERGUNTA 5] Proporção de Avaliações Negativas por Categoria:")
    q5 = """
    SELECT 
        categoria,
        SUM(total_avaliacoes) AS total_avaliacoes,
        SUM(avaliacoes_negativas) AS total_avaliacoes_negativas,
        ROUND((SUM(avaliacoes_negativas)::FLOAT / NULLIF(SUM(total_avaliacoes), 0)) * 100, 2) AS prop_avaliacoes_negativas_pct,
        ROUND(AVG(nota_media_avaliacao), 2) AS nota_media_categoria,
        SUM(total_chamados_suporte) AS total_chamados_suporte
    FROM gold_desempenho
    GROUP BY categoria
    ORDER BY prop_avaliacoes_negativas_pct DESC
    """
    df_q5 = con.execute(q5).df()
    print(df_q5.to_string(index=False))
    
    # -------------------------------------------------------------
    # Pergunta 6: Temas mais frequentes nas reclamações de suporte
    # -------------------------------------------------------------
    print("\n[PERGUNTA 6] Top Temas de Reclamações no Suporte:")
    q6 = """
    SELECT 
        tema_reclamacao,
        SUM(total_chamados_suporte) AS total_chamados,
        ROUND((SUM(total_chamados_suporte)::FLOAT / (SELECT SUM(total_chamados_suporte) FROM gold_satisfacao)) * 100, 2) AS pct_do_total,
        SUM(clientes_irritados) AS clientes_irritados,
        SUM(clientes_insatisfeitos) AS clientes_insatisfeitos,
        SUM(encaminhamentos_troca) AS trocas,
        SUM(encaminhamentos_reembolso) AS reembolsos
    FROM gold_satisfacao
    GROUP BY tema_reclamacao
    ORDER BY total_chamados DESC
    LIMIT 10
    """
    df_q6 = con.execute(q6).df()
    print(df_q6.to_string(index=False))
    print("=" * 80)

if __name__ == "__main__":
    run_analytical_queries()
