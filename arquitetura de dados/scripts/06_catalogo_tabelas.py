import os
import glob
from deltalake import DeltaTable

def gerar_catalogo():
    linhas_md = [
        "# Catálogo Físico e Lógico das Tabelas Delta Lake",
        "",
        "Este catálogo inventaria os metadados físicos e lógicos das tabelas Silver e Gold do Lakehouse AulaStore.",
        "",
        "---",
        ""
    ]
    
    pastas = [
        ("Camada Silver (Tabelas Canônicas)", os.path.join("lakehouse", "silver")),
        ("Camada Gold (Modelos Analíticos)", os.path.join("lakehouse", "gold"))
    ]
    
    for titulo, pasta_base in pastas:
        linhas_md.append(f"## {titulo}\n")
        if not os.path.exists(pasta_base):
            continue
            
        tabelas = sorted([d for d in os.listdir(pasta_base) if os.path.isdir(os.path.join(pasta_base, d)) and not d.startswith(".")])
        for tab_nome in tabelas:
            caminho_tab = os.path.join(pasta_base, tab_nome)
            try:
                dt = DeltaTable(caminho_tab)
                schema = dt.schema()
                versao = dt.version()
                arquivos = dt.files()
                num_arquivos = len(arquivos)
                df = dt.to_pandas()
                num_linhas = len(df)
                
                linhas_md.append(f"### Tabela: `{tab_nome}`")
                linhas_md.append(f"- **Caminho:** `{caminho_tab}`")
                linhas_md.append(f"- **Versão Atual (Delta):** {versao}")
                linhas_md.append(f"- **Total de Linhas:** {num_linhas:,}".replace(",", "."))
                linhas_md.append(f"- **Total de Arquivos Parquet Ativos:** {num_arquivos}")
                linhas_md.append("")
                linhas_md.append("| Coluna | Tipo Delta / Arrow |")
                linhas_md.append("| :--- | :--- |")
                for campo in schema.fields:
                    linhas_md.append(f"| `{campo.name}` | `{campo.type}` |")
                linhas_md.append("\n---\n")
            except Exception as e:
                linhas_md.append(f"- *Erro ao ler {tab_nome}: {e}*\n")
                
    output_path = os.path.join("lakehouse", "_catalogo_tabelas.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_md))
        
    print(f"Catálogo de tabelas gerado com sucesso em: {output_path}")

if __name__ == "__main__":
    gerar_catalogo()
