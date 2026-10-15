import os
import json
import re
from datetime import datetime
import pandas as pd
from deltalake import write_deltalake

BRONZE_DIR = os.path.join("lakehouse", "bronze")
SILVER_DIR = os.path.join("lakehouse", "silver")

def clean_and_process_clientes():
    print("Processando silver_clientes...")
    path = os.path.join(BRONZE_DIR, "clientes_corrigido.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    
    # Clean UF and standardize
    df["uf"] = df["uf"].fillna("ND").astype(str).str.strip().str.upper()
    df["nome"] = df["nome"].astype(str).str.strip()
    df["canal_preferencial"] = df["canal_preferencial"].astype(str).str.strip()
    df["segmento"] = df["segmento"].astype(str).str.strip()
    df["data_cadastro"] = pd.to_datetime(df["data_cadastro"]).dt.strftime("%Y-%m-%d")
    df["ingestion_timestamp"] = datetime.now().isoformat()
    
    dest_path = os.path.join(SILVER_DIR, "silver_clientes")
    write_deltalake(dest_path, df, mode="overwrite")
    print(f" -> silver_clientes salva: {len(df)} registros em {dest_path}")
    return len(df)

def clean_and_process_produtos():
    print("Processando silver_produtos...")
    path = os.path.join(BRONZE_DIR, "produtos_corrigido.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    
    # Standardize category: 'Eletronicos' -> 'Eletrônicos'
    df["categoria"] = df["categoria"].replace({"Eletronicos": "Eletrônicos"}).str.strip()
    df["marca"] = df["marca"].astype(str).str.strip()
    df["produto_nome"] = df["produto_nome"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip()
    df["is_ativo"] = df["status"] == "Ativo"
    df["preco_lista"] = df["preco_lista"].astype(float).round(2)
    df["ingestion_timestamp"] = datetime.now().isoformat()
    
    dest_path = os.path.join(SILVER_DIR, "silver_produtos")
    write_deltalake(dest_path, df, mode="overwrite")
    print(f" -> silver_produtos salva: {len(df)} registros em {dest_path}")
    return len(df)

def clean_and_process_vendas():
    print("Processando silver_vendas...")
    path = os.path.join(BRONZE_DIR, "vendas_corrigido.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    df["data"] = df["data_venda"].dt.strftime("%Y-%m-%d")
    df["ano_mes"] = df["data_venda"].dt.strftime("%Y-%m")
    df["data_venda"] = df["data_venda"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Recalculate/validate valor_total
    calculated_total = (df["quantidade"] * df["valor_unitario"] * (1 - df["desconto_pct"])).round(2)
    df["valor_total"] = calculated_total
    
    df["canal"] = df["canal"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip()
    df["ingestion_timestamp"] = datetime.now().isoformat()
    
    dest_path = os.path.join(SILVER_DIR, "silver_vendas")
    write_deltalake(dest_path, df, mode="overwrite")
    print(f" -> silver_vendas salva: {len(df)} registros em {dest_path}")
    return len(df)

def clean_and_process_avaliacoes():
    print("Processando silver_avaliacoes...")
    path_csv = os.path.join(BRONZE_DIR, "avaliacoes_corrigido.csv")
    path_txt = os.path.join(BRONZE_DIR, "avaliacoes_texto_corrigido.txt")
    
    df_csv = pd.read_csv(path_csv, encoding="utf-8-sig")
    df_txt = pd.read_csv(path_txt, sep="\t", encoding="utf-8-sig")
    
    # Join structured evaluations with unstructured review text
    df = pd.merge(df_csv, df_txt, on="avaliacao_id", how="left")
    
    # Fix nota out-of-scale (e.g. nota = 6 clipped to 5)
    df["nota"] = df["nota"].clip(lower=1, upper=5).astype(int)
    
    # Classify sentiment by star rating
    def map_sentiment(n):
        if n <= 2:
            return "Negativo"
        elif n == 3:
            return "Neutro"
        return "Positivo"
    
    df["sentimento_avaliacao"] = df["nota"].apply(map_sentiment)
    df["tema_principal"] = df["tema_principal"].fillna("outros").astype(str).str.strip().str.lower()
    df["canal"] = df["canal"].astype(str).str.strip()
    df["texto_avaliacao"] = df["texto_avaliacao"].fillna("").astype(str).str.strip()
    
    # Clean datetime
    df["data_avaliacao"] = pd.to_datetime(df["data_avaliacao"], format="mixed").dt.strftime("%Y-%m-%d")
    df["ingestion_timestamp"] = datetime.now().isoformat()
    
    dest_path = os.path.join(SILVER_DIR, "silver_avaliacoes")
    write_deltalake(dest_path, df, mode="overwrite")
    print(f" -> silver_avaliacoes salva: {len(df)} registros em {dest_path}")
    return len(df)

def clean_and_process_eventos_web():
    print("Processando silver_eventos_web...")
    path = os.path.join(BRONZE_DIR, "eventos_web_app_corrigido_final.json")
    
    records = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
                
    df = pd.DataFrame(records)
    
    # Parse epoch timestamp in milliseconds to datetime
    df["data_hora_evento"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["data"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
    
    # Fill nulls appropriately
    df["search_term"] = df["search_term"].fillna("")
    df["venda_id"] = df["venda_id"].fillna("")
    df["user_id"] = df["user_id"].fillna("")
    df["product_id"] = df["product_id"].fillna("")
    df["amount"] = df["amount"].fillna(0.0).astype(float)
    df["duration_ms"] = df["duration_ms"].fillna(0).astype(int)
    df["ingestion_timestamp"] = datetime.now().isoformat()
    
    dest_path = os.path.join(SILVER_DIR, "silver_eventos_web")
    write_deltalake(dest_path, df, mode="overwrite")
    print(f" -> silver_eventos_web salva: {len(df)} registros em {dest_path}")
    return len(df)

def clean_and_process_atendimento():
    print("Processando silver_atendimento (parsing semi/não estruturado com Regex)...")
    path = os.path.join(BRONZE_DIR, "atendimento_corrigido_final.txt")
    
    pat = re.compile(
        r'\[(?P<data_hora>.*?)\]\s+PROTOCOLO\s+(?P<protocolo>\d+)\s+\|\s+CLIENTE\s+(?P<cliente_id>\w+)\s+\|\s+PRODUTO\s+(?P<produto_id>\w+)\s+\|\s+ATENDENTE\s+(?P<atendente>[\w\s]+?)\s+\|\s+(?P<texto>.*)'
    )
    
    parsed_rows = []
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pat.match(line)
            if m:
                txt = m.group("texto")
                
                # Extract reason/motivo
                m_motivo = re.search(r'sobre\s+([^.]+?)\.', txt)
                motivo = m_motivo.group(1).strip() if m_motivo else "não especificado"
                
                # Extract sentiment
                m_sent = re.search(r'demonstra\s+estar\s+([^;]+?);', txt)
                sentimento = m_sent.group(1).strip() if m_sent else "neutro"
                
                # Extract resolution/encaminhamento
                m_enc = re.search(r'Encaminhamento:\s+([^.]*)', txt)
                encaminhamento = m_enc.group(1).strip() if m_enc else "em aberto"
                
                parsed_rows.append({
                    "protocolo": m.group("protocolo"),
                    "data_hora": m.group("data_hora"),
                    "data": m.group("data_hora").split(" ")[0] if " " in m.group("data_hora") else m.group("data_hora"),
                    "cliente_id": m.group("cliente_id"),
                    "produto_id": m.group("produto_id"),
                    "atendente": m.group("atendente").strip(),
                    "motivo_contato": motivo,
                    "sentimento_cliente": sentimento,
                    "encaminhamento": encaminhamento,
                    "texto_completo": txt,
                    "ingestion_timestamp": datetime.now().isoformat()
                })
                
    df = pd.DataFrame(parsed_rows)
    dest_path = os.path.join(SILVER_DIR, "silver_atendimento")
    write_deltalake(dest_path, df, mode="overwrite")
    print(f" -> silver_atendimento salva: {len(df)} registros em {dest_path}")
    return len(df)

def run_silver_pipeline():
    os.makedirs(SILVER_DIR, exist_ok=True)
    print(f"[{datetime.now().isoformat()}] Iniciando Pipeline da Camada Silver...")
    c1 = clean_and_process_clientes()
    c2 = clean_and_process_produtos()
    c3 = clean_and_process_vendas()
    c4 = clean_and_process_avaliacoes()
    c5 = clean_and_process_eventos_web()
    c6 = clean_and_process_atendimento()
    print(f"[{datetime.now().isoformat()}] Camada Silver concluída com sucesso! Total de 6 tabelas Delta criadas.")

if __name__ == "__main__":
    run_silver_pipeline()
