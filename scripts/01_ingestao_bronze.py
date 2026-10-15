import os
import shutil
import hashlib
import json
from datetime import datetime

SOURCE_DIR = "datasets_miniprojeto_versionado"
BRONZE_DIR = os.path.join("lakehouse", "bronze")

def calculate_checksum(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def ingest_to_bronze():
    print(f"[{datetime.now().isoformat()}] Iniciando Ingestão para a Camada Bronze...")
    os.makedirs(BRONZE_DIR, exist_ok=True)
    
    manifest = {
        "camada": "Bronze",
        "data_ingestao": datetime.now().isoformat(),
        "descricao": "Arquivos originais preservados sem modificação, mantendo integridade e fidelidade aos dados de origem.",
        "arquivos": []
    }
    
    # List of relevant raw dataset files
    dataset_files = [
        "clientes_corrigido.csv",
        "produtos_corrigido.csv",
        "vendas_corrigido.csv",
        "avaliacoes_corrigido.csv",
        "avaliacoes_texto_corrigido.txt",
        "atendimento_corrigido_final.txt",
        "eventos_web_app_corrigido_final.json",
        "LEIA-ME_CORRECOES_DATASETS.txt"
    ]
    
    for filename in dataset_files:
        src_path = os.path.join(SOURCE_DIR, filename)
        if not os.path.exists(src_path):
            print(f"Aviso: Arquivo {src_path} não encontrado!")
            continue
            
        dest_path = os.path.join(BRONZE_DIR, filename)
        # Copy raw file directly
        shutil.copy2(src_path, dest_path)
        
        file_size = os.path.getsize(dest_path)
        checksum = calculate_checksum(dest_path)
        
        file_meta = {
            "nome_arquivo": filename,
            "caminho_bronze": dest_path.replace("\\", "/"),
            "tamanho_bytes": file_size,
            "tamanho_mb": round(file_size / (1024 * 1024), 2),
            "sha256": checksum,
            "formato": filename.split(".")[-1].lower(),
            "data_copia": datetime.now().isoformat()
        }
        manifest["arquivos"].append(file_meta)
        print(f" -> Arquivo ingerido: {filename} ({file_meta['tamanho_mb']} MB, SHA256: {checksum[:12]}...)")
        
    manifest_path = os.path.join(BRONZE_DIR, "_ingestion_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"[{datetime.now().isoformat()}] Ingestão da camada Bronze concluída com sucesso! Manifesto gerado em {manifest_path}")

if __name__ == "__main__":
    ingest_to_bronze()
