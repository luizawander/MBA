import os
import shutil
from datetime import datetime
import pandas as pd
from deltalake import write_deltalake, DeltaTable

DEMO_TABLE_DIR = os.path.join("lakehouse", "demo_gerenciamento_tabela")

def demonstrate_table_management():
    print("=" * 70)
    print("DEMONSTRAÇÃO DE CAPACIDADES DE GERENCIAMENTO DE TABELA LAKEHOUSE")
    print("=" * 70)
    
    if os.path.exists(DEMO_TABLE_DIR):
        shutil.rmtree(DEMO_TABLE_DIR)
        
    # -------------------------------------------------------------------------
    # PASSO 1: Criação da Tabela Inicial (Versão 0)
    # -------------------------------------------------------------------------
    print("\n[1] Criando Tabela Delta Inicial (Versão 0)...")
    dados_v0 = pd.DataFrame([
        {"produto_id": "P00001", "nome": "Smartphone Vitta 0001", "preco": 178.53, "status": "Ativo"},
        {"produto_id": "P00002", "nome": "Perfume Vitta 0002", "preco": 159.52, "status": "Ativo"},
        {"produto_id": "P00003", "nome": "Webcam CasaMais", "preco": 263.26, "status": "Ativo"}
    ])
    
    write_deltalake(DEMO_TABLE_DIR, dados_v0, mode="error")
    dt = DeltaTable(DEMO_TABLE_DIR)
    print(f" -> Tabela criada com sucesso!")
    print(f" -> Versão atual: {dt.version()}")
    print(" -> Esquema V0:", [f.name for f in dt.schema().fields])
    print(" -> Registros V0:\n", dt.to_pandas())
    
    # -------------------------------------------------------------------------
    # PASSO 2: Demonstração de Evolução de Esquema (Schema Evolution) -> Versão 1
    # -------------------------------------------------------------------------
    print("\n[2] Demonstrando SCHEMA EVOLUTION (Adicionando nova coluna 'categoria' e 'margem_pct')...")
    dados_v1_novos = pd.DataFrame([
        {"produto_id": "P00004", "nome": "Smartwatch Tech", "preco": 320.00, "status": "Ativo", "categoria": "Eletrônicos", "margem_pct": 0.25}
    ])
    
    # Escrevendo com schema_mode="merge" permite que novas colunas sejam incorporadas
    write_deltalake(DEMO_TABLE_DIR, dados_v1_novos, mode="append", schema_mode="merge")
    dt = DeltaTable(DEMO_TABLE_DIR)
    print(f" -> Schema Evolution aplicado com sucesso! Nova Versão: {dt.version()}")
    print(" -> Novo Esquema pós-evolução:", [f.name for f in dt.schema().fields])
    print(" -> Registros pós-evolução:\n", dt.to_pandas())
    
    # -------------------------------------------------------------------------
    # PASSO 3: Demonstração de Time Travel (Viagem no Tempo)
    # -------------------------------------------------------------------------
    print("\n[3] Demonstrando TIME TRAVEL (Consultando Versão 0 vs Versão 1)...")
    dt_v0 = DeltaTable(DEMO_TABLE_DIR, version=0)
    print(f" -> Lendo snapshot histórico na Versão 0 (3 registros, esquema antigo sem 'categoria'):")
    print(dt_v0.to_pandas())
    
    dt_v1 = DeltaTable(DEMO_TABLE_DIR, version=1)
    print(f"\n -> Lendo snapshot atual na Versão 1 (4 registros, com 'categoria' e 'margem_pct'):")
    print(dt_v1.to_pandas())
    
    # -------------------------------------------------------------------------
    # PASSO 4: Demonstração de Operação ACID e Log de Transações (_delta_log)
    # -------------------------------------------------------------------------
    print("\n[4] Inspecionando o Log de Transações ACID (_delta_log)...")
    history = dt.history()
    print(f" -> Total de commits registrados no histórico: {len(history)}")
    for commit in history:
        print(f"    - Versão {commit['version']}: Operação={commit['operation']}, Timestamp={commit['timestamp']}, Adicionados={commit.get('operationMetrics', {}).get('num_added_files', 'N/A')} arquivos")
        
    print("\n" + "=" * 70)
    print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    demonstrate_table_management()
