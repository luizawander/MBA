import os
import pandas as pd
from deltalake import DeltaTable

TABELA_PRODUTOS = os.path.join("lakehouse", "silver", "silver_produtos")

def executar_gerenciamento_upsert_restore():
    print("=" * 75)
    print("SCRIPT 07: GERENCIAMENTO AVANÇADO (MERGE, HISTÓRICO E RESTORE)")
    print("=" * 75)
    
    if not os.path.exists(TABELA_PRODUTOS):
        print(f"Erro: Tabela não encontrada em {TABELA_PRODUTOS}")
        return

    dt = DeltaTable(TABELA_PRODUTOS)
    versao_inicial = dt.version()
    linhas_iniciais = len(dt.to_pandas())
    
    print("\n[1] ESTADO INICIAL DA TABELA (silver_produtos):")
    print(f" -> Versão atual: {versao_inicial}")
    print(f" -> Total de registros: {linhas_iniciais}")
    
    df_atual = dt.to_pandas()
    p0 = df_atual.iloc[0].to_dict()
    preco_original = p0["preco_lista"]
    p0["preco_lista"] = round(preco_original * 1.10, 2)
    
    p_novo = {
        "produto_id": "P09999",
        "produto_nome": "Smartphone Delta Ultra 5G",
        "categoria": "Eletrônicos",
        "marca": "NovaTech",
        "preco_lista": 3899.90,
        "status": "Ativo",
        "is_ativo": True,
        "ingestion_timestamp": "2026-10-18T14:40:00"
    }
    
    lote = pd.DataFrame([p0, p_novo])
    
    print("\n[2] EXECUTANDO OPERAÇÃO MERGE (UPSERT ATÔMICO):")
    print(f" -> Registro a atualizar (produto_id={p0['produto_id']}): preco_lista {preco_original} -> {p0['preco_lista']}")
    print(f" -> Registro novo a inserir (produto_id={p_novo['produto_id']}): {p_novo['produto_nome']}")
    
    merge_result = dt.merge(
        source=lote,
        predicate="t.produto_id = s.produto_id",
        source_alias="s",
        target_alias="t"
    ).when_matched_update_all() \
     .when_not_matched_insert_all() \
     .execute()
     
    print("\n -> Métricas retornadas pela transação MERGE:")
    for k, v in merge_result.items():
        print(f"    - {k}: {v}")
        
    dt = DeltaTable(TABELA_PRODUTOS)
    print(f"\n -> Nova versão após MERGE: {dt.version()}")
    print(f" -> Total de registros após MERGE: {len(dt.to_pandas())}")
    
    print("\n[3] TRILHA DE AUDITORIA E HISTÓRICO DE TRANSAÇÕES (_delta_log):")
    for h in dt.history()[:5]:
        op_metrics = h.get("operationMetrics", {})
        ins = op_metrics.get("num_target_rows_inserted", "-")
        upd = op_metrics.get("num_target_rows_updated", "-")
        print(f" -> Versão {h['version']} | Operação: {h['operation']} | Inseridos: {ins} | Atualizados: {upd}")
        
    print("\n[4] SIMULANDO ROLLBACK VIA TIME TRAVEL E RESTORE:")
    print(f" -> Restaurando tabela para a Versão {versao_inicial}...")
    dt.restore(versao_inicial)
    
    dt = DeltaTable(TABELA_PRODUTOS)
    print(f" -> Versão gerada pelo RESTORE: {dt.version()}")
    print(f" -> Total de registros após Rollback: {len(dt.to_pandas())}")
    
    df_restaurado = dt.to_pandas()
    preco_restaurado = df_restaurado[df_restaurado["produto_id"] == p0["produto_id"]]["preco_lista"].values[0]
    print(f" -> Verificação de integridade: Preço do produto {p0['produto_id']} voltou para {preco_restaurado}")
    print(f" -> Produto {p_novo['produto_id']} presente na base ativa? {p_novo['produto_id'] in df_restaurado['produto_id'].values}")
    
    print("\n" + "=" * 75)
    print("SCRIPT CONCLUÍDO COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    executar_gerenciamento_upsert_restore()
