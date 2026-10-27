# Databricks notebook source
# Importar este arquivo no Databricks como notebook Python e executar UMA VEZ antes do LAB 2.
# File: lodlog_lab3_seed_v3.py
# Uso: Workspace > Import > selecione este arquivo (.py) > Run All
#
# ════════════════════════════════════════════════════════════════
# O QUE MUDA NA v3 (junho/2026) — em relação ao seed v2
# ════════════════════════════════════════════════════════════════
# 1) ETL do DW migrado de geração Python para SQL INSERT INTO…SELECT
#    a partir de lodlog_op — reflete pipelines de dados reais.
#
# 2) dim_tempo e dim_cat_atraso continuam em Python (não têm fonte
#    em lodlog_op: calendário e lookup estático).
#
# 3) Anomalias propositais mantidas em fato_entregas; agora inseridas
#    via INSERT INTO após o ETL SQL base (modo append).
#
# 4) PK de fato_entregas atualizada para entrega_id (dimensão
#    degenerada — grain: 1 linha por entrega realizada).

# COMMAND ----------

# MAGIC %md
# MAGIC # LODLog — Geração de Dados Sintéticos & ETL · LAB 2 (v3)
# MAGIC
# MAGIC Execute este notebook **uma única vez** antes do LAB 2.
# MAGIC
# MAGIC **v3:** ETL do DW feito via `INSERT INTO … SELECT` a partir de `lodlog_op`.
# MAGIC
# MAGIC **Tabelas populadas:**
# MAGIC
# MAGIC ### lodlog_op (Operacional):
# MAGIC | Tabela | Linhas | Descrição |
# MAGIC |--------|--------|-----------|
# MAGIC | `cliente` | 200 | Clientes LODLog |
# MAGIC | `endereco_cliente` | 200 | Endereços dos clientes |
# MAGIC | `contrato` | 200 | Contratos ativos |
# MAGIC | `veiculo` | 50 | Frota de veículos |
# MAGIC | `motorista` | 100 | Motoristas |
# MAGIC | `manutencao` | ~220 | Histórico de manutenção |
# MAGIC | `telemetria` | ~50K | Eventos IoT (simplificado) |
# MAGIC | `centro_distribuicao` | 5 | Centros de distribuição |
# MAGIC | `produto` | 50 | Catálogo de produtos |
# MAGIC | `estoque` | 250 | Posições de estoque |
# MAGIC | `movimentacao_estoque` | ~10K | Movimentações |
# MAGIC | `pedido` | ~50K | Pedidos de entrega |
# MAGIC | `item_pedido` | ~150K | Itens dos pedidos |
# MAGIC | `entrega` | ~50K | **Entregas em 2FN (proposital)** com kpi_cat_atraso |
# MAGIC
# MAGIC ### lodlog_dw (Data Warehouse - Star Schema):
# MAGIC | Tabela | Fonte | Descrição |
# MAGIC |--------|-------|-----------|
# MAGIC | `dim_tempo` | Python (calendário) | 2024–2026 |
# MAGIC | `dim_cat_atraso` | Python (lookup estático) | 5 categorias |
# MAGIC | `dim_centro_distribuicao` | SQL ← lodlog_op.centro_distribuicao | SCD Tipo 1 |
# MAGIC | `dim_cliente` | SQL ← lodlog_op.cliente + endereco + contrato | SCD Tipo 2 |
# MAGIC | `dim_veiculo` | SQL ← lodlog_op.veiculo | SCD Tipo 2 |
# MAGIC | `dim_motorista` | SQL ← lodlog_op.motorista | SCD Tipo 2 |
# MAGIC | `fato_entregas` | SQL ← entrega + pedido + item_pedido | ~50K + anomalias |
# MAGIC
# MAGIC > **Anomalias propositais** em fato_entregas (para Parte 4 do LAB):
# MAGIC > duplicatas · valores negativos · outliers · FK quebrada

# COMMAND ----------

import random
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

print("Gerando dados LODLog para o LAB 2 (v3)...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 1: Dados Mestre (Dimensionais Operacionais)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# CENTRO_DISTRIBUICAO — 5 centros
# ─────────────────────────────────────────────────────────────

_centros_codigos = ["CD-CAMPINAS", "CD-SAO-PAULO", "CD-BELO-HORIZONTE",
                    "CD-CURITIBA", "CD-PORTO-ALEGRE"]
_centros_nomes = ["CD Campinas", "CD São Paulo Norte", "CD Belo Horizonte",
                  "CD Curitiba", "CD Porto Alegre"]
_cidades_centros = ["Campinas", "São Paulo", "Belo Horizonte", "Curitiba", "Porto Alegre"]
_ufs = ["SP", "SP", "MG", "PR", "RS"]
_regioes = ["Sudeste", "Sudeste", "Sudeste", "Sul", "Sul"]
_capacidades = [15000.00, 8000.00, 6000.00, 5500.00, 4000.00]
_lats = [-22.9068, -23.4500, -19.9167, -25.4290, -30.0346]
_lons = [-47.0626, -46.6233, -43.9345, -49.2710, -51.2177]
_ceps = ["13010000", "02000000", "30130000", "80010000", "90010000"]

centros_op = []
for i in range(5):
    centros_op.append({
        "cd_id": i+1,
        "codigo": _centros_codigos[i],
        "nome": _centros_nomes[i],
        "municipio": _cidades_centros[i],
        "uf": _ufs[i],
        "cep": _ceps[i],
        "latitude": _lats[i],
        "longitude": _lons[i],
        "capacidade_m3": _capacidades[i],
        "ativo": True,
    })

df_centro_distribuicao_op = pd.DataFrame(centros_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# CLIENTE — 200 clientes
# ─────────────────────────────────────────────────────────────

_bases = ["Supermercados Beta", "Atacadão Sul", "Distribuidora Norte",
          "Logex Comércio", "GrupoAlpha Varejo", "Fast Shop", "Mag Retail",
          "Americanas Filial", "BIG Hipermercado", "Cencosud Brasil",
          "Leroy Merlin", "C&A Modas", "Renner", "Shopee BR", "Amazon BR",
          "Raia Drogasil", "Nissei", "GNDI Saúde", "Carrefour", "Assaí"]

_cidades = [("São Paulo", "SP")] * 6 + [("Campinas", "SP")] * 3 + \
           [("Santos", "SP")] * 2 + [("Rio de Janeiro", "RJ")] * 4 + \
           [("Belo Horizonte", "MG")] * 2 + [("Curitiba", "PR")] * 2 + \
           [("Porto Alegre", "RS"), ("Goiânia", "GO"), ("Salvador", "BA"),
            ("Fortaleza", "CE"), ("Brasília", "DF")]

_segmentos = ["Varejo", "Atacado", "Indústria", "E-commerce", "Alimentício"]
_dominios_email = ["gmail.com", "yahoo.com.br", "outlook.com", "empresas.com.br"]

clientes_op = []
for i in range(1, 201):
    cidade, uf = random.choice(_cidades)
    base = random.choice(_bases)
    cnpj = f"{random.randint(1,99999999):08d}0001{random.randint(1,99):02d}"
    data_cadastro = date(2020, 1, 1) + timedelta(days=random.randint(0, 1825))
    clientes_op.append({
        "cliente_id": i,
        "cnpj": cnpj,
        "razao_social": f"{base} {i:03d} LTDA",
        "nome_fantasia": f"{base} {i:03d}",
        "segmento": random.choice(_segmentos),
        "email": f"contato_{i:03d}@{random.choice(_dominios_email)}".lower(),
        "telefone": f"({random.randint(11,99)}) {random.randint(9000,9999)}-{random.randint(1000,9999)}",
        "data_cadastro": data_cadastro.isoformat(),
        "ativo": True,
    })

df_cliente_op = pd.DataFrame(clientes_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# ENDERECO_CLIENTE — 1 endereço principal por cliente
# ─────────────────────────────────────────────────────────────

_bairros_sp = ["Bela Vista", "Consolação", "Pinheiros", "Itaim Bibi", "Jardins",
               "Vila Mariana", "Santana", "Lapa", "Barra Funda"]
_bairros_rj = ["Copacabana", "Ipanema", "Leblon", "Tijuca", "Botafogo",
               "Centro", "Barra da Tijuca"]
_bairros_outros = ["Centro", "Industrial", "Residencial", "Comercial", "Jardim"]

enderecos_op = []
for i, cliente in df_cliente_op.iterrows():
    cidade = cliente["municipio"] if "municipio" in cliente else random.choice(_cidades)[0]
    uf = cliente["uf"] if "uf" in cliente else random.choice(_cidades)[1]
    if cidade == "São Paulo":
        bairro = random.choice(_bairros_sp)
    elif cidade == "Rio de Janeiro":
        bairro = random.choice(_bairros_rj)
    else:
        bairro = random.choice(_bairros_outros)
    cep_base = {"SP": "01310", "RJ": "20040", "MG": "30130", "PR": "80010",
                "RS": "90010", "GO": "74010", "BA": "40010", "CE": "60010", "DF": "70010"}
    cep = f"{cep_base.get(uf, '01310')}{random.randint(0, 9999):04d}"
    lat_lon_map = {
        ("São Paulo", "SP"): (-23.5630, -46.6544),
        ("Campinas", "SP"): (-22.9068, -47.0626),
        ("Rio de Janeiro", "RJ"): (-22.9068, -43.1729),
        ("Belo Horizonte", "MG"): (-19.9167, -43.9345),
        ("Curitiba", "PR"): (-25.4290, -49.2710),
        ("Porto Alegre", "RS"): (-30.0346, -51.2177),
        ("Goiânia", "GO"): (-16.6869, -49.2648),
        ("Salvador", "BA"): (-12.9714, -38.5014),
        ("Fortaleza", "CE"): (-3.7172, -38.5434),
        ("Brasília", "DF"): (-15.8267, -47.9218),
    }
    lat, lon = lat_lon_map.get((cidade, uf), (-23.5630, -46.6544))
    enderecos_op.append({
        "endereco_id": i + 1,
        "cliente_id": cliente["cliente_id"],
        "logradouro": f"Rua {random.choice(['Principal', 'Comercial', 'Industrial', 'das Flores', 'Augusta'])}",
        "numero": str(random.randint(100, 5000)),
        "complemento": random.choice([None, f"Bloco {random.choice('ABCDE')}", "Sala 1", ""]),
        "bairro": bairro,
        "municipio": cidade,
        "uf": uf,
        "cep": cep,
        "latitude": round(lat + random.uniform(-0.01, 0.01), 6),
        "longitude": round(lon + random.uniform(-0.01, 0.01), 6),
        "tipo": "Principal",
    })

df_endereco_cliente_op = pd.DataFrame(enderecos_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# CONTRATO — 1 contrato por cliente
# ─────────────────────────────────────────────────────────────

contratos_op = []
for i, cliente in df_cliente_op.iterrows():
    data_inicio = date.fromisoformat(cliente["data_cadastro"]) + timedelta(days=random.randint(30, 180))
    data_fim = data_inicio + timedelta(days=random.randint(365, 1095))
    contratos_op.append({
        "contrato_id": i + 1,
        "cliente_id": cliente["cliente_id"],
        "numero_contrato": f"CTR-{cliente['cliente_id']:05d}-{random.randint(1, 999):03d}",
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "sla_pontualidade_pct": round(random.uniform(85.0, 99.5), 2),
        "multa_atraso_pct": round(random.uniform(0.5, 5.0), 2),
        "status": "Ativo",
    })

df_contrato_op = pd.DataFrame(contratos_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# VEICULO — 50 veículos
# ─────────────────────────────────────────────────────────────

_modelos = ["VW Delivery 9.170", "Mercedes-Benz Atego 2430",
            "Iveco Daily 35S14", "Ford Cargo 1723", "Scania R450",
            "MAN TGX 28.440", "Volvo FH 460", "Renault Master 2.3"]
_fabricantes = ["Volkswagen", "Mercedes-Benz", "Iveco", "Ford",
               "Scania", "MAN", "Volvo", "Renault"]
_letras = "ABCDEFGHJKLMNPQRSTUVWXYZ"

veiculos_op = []
for i in range(1, 51):
    fabricante_idx = random.randint(0, len(_fabricantes) - 1)
    veiculos_op.append({
        "veiculo_id": i,
        "placa": (f"{''.join(random.choices(_letras, k=3))}"
                  f"{random.randint(0,9)}{random.choice(_letras)}{random.randint(10,99)}"),
        "modelo": _modelos[fabricante_idx],
        "fabricante": _fabricantes[fabricante_idx],
        "ano_fabricacao": random.randint(2015, 2023),
        "tipo": random.choice(["Leve", "Médio", "Pesado"]),
        "capacidade_kg": random.choice([3500, 5000, 8000, 15000, 25000]),
        "hodometro_km": random.randint(10000, 200000),
        "data_aquisicao": (date(2020, 1, 1) + timedelta(days=random.randint(0, 1460))).isoformat(),
        "status": random.choice(["Disponível", "Em Rota", "Manutenção"]),
    })

df_veiculo_op = pd.DataFrame(veiculos_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# MOTORISTA — 100 motoristas
# ─────────────────────────────────────────────────────────────

_primeiros_nomes = ["João", "Maria", "Carlos", "Ana", "Pedro", "Julia", "Rafael", "Fernanda",
                    "Daniel", "Marcia", "Bruno", "Renata", "Eder", "Simone", "Marcelo", "Paula",
                    "Diego", "Barbara", "Rodrigo", "Patrícia", "Anderson", "Priscila", "Luiz",
                    "Vanessa", "Fabio", "Rita", "José", "Teresa", "Antonio", "Cida"]
_sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Pereira",
               "Lima", "Gomes", "Ribeiro", "Martins", "Almeida", "Barbosa", "Araujo", "Dias",
               "Nunes", "Moraes", "Costa", "Leite", "Teixeira", "Queiroz", "Nascimento"]
_categorias_cnh = ["A", "B", "C", "D", "E", "AB", "AC", "AD", "AE"]

motoristas_op = []
for i in range(1, 101):
    nome_completo = f"{random.choice(_primeiros_nomes)} {random.choice(_sobrenomes)}"
    cpf = f"{random.randint(100000000, 999999999):09d}{random.randint(0, 99):02d}"
    cnh = f"CNH{random.randint(1000000, 9999999):07d}"
    data_admissao = date(2015, 1, 1) + timedelta(days=random.randint(0, 3285))
    tempo_empresa_meses = (date(2024, 6, 1) - data_admissao).days // 30
    validade_cnh = data_admissao + timedelta(days=1825)
    if tempo_empresa_meses < 24:
        faixa = "Júnior"
    elif tempo_empresa_meses < 96:
        faixa = "Pleno"
    else:
        faixa = "Sênior"
    if faixa == "Sênior":
        score = round(random.uniform(60, 100), 2)
    elif faixa == "Pleno":
        score = round(random.uniform(40, 85), 2)
    else:
        score = round(random.uniform(30, 70), 2)
    motoristas_op.append({
        "motorista_id": i,
        "cpf": cpf,
        "nome_completo": nome_completo,
        "cnh": cnh,
        "categoria_cnh": random.choice(_categorias_cnh),
        "validade_cnh": validade_cnh.isoformat(),
        "data_admissao": data_admissao.isoformat(),
        "score_seguranca": score,
        "status": "Ativo",
    })

df_motorista_op = pd.DataFrame(motoristas_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# MANUTENCAO — ~220 registros
# ─────────────────────────────────────────────────────────────

_dt0 = date(2023, 1, 1)
_dt1 = date(2026, 5, 1)
_span = (_dt1 - _dt0).days

manutencoes_op = []
manut_id = 1
for vid in range(1, 51):
    for dt in sorted(random.choices(
            [_dt0 + timedelta(days=d) for d in range(_span)],
            k=random.randint(2, 7))):
        data_abertura = datetime(dt.year, dt.month, dt.day,
                                  random.randint(0, 23), random.randint(0, 59), 0)
        data_conclusao = data_abertura + timedelta(hours=random.randint(2, 72))
        manutencoes_op.append({
            "manutencao_id": manut_id,
            "veiculo_id": vid,
            "tipo": random.choice(["Preventiva", "Corretiva", "Revisão geral", "Troca de óleo"]),
            "data_abertura": data_abertura.isoformat(),
            "data_conclusao": data_conclusao.isoformat(),
            "km_no_momento": random.randint(10000, 250000),
            "custo_total": round(random.uniform(200, 15000), 2),
            "descricao": f"Manutenção {random.choice(['rotineira', 'urgente', 'programada'])} no veículo {vid}",
            "status": "Concluída",
        })
        manut_id += 1

df_manutencao_op = pd.DataFrame(manutencoes_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# PRODUTO — 50 produtos
# ─────────────────────────────────────────────────────────────

_categorias_produto = ["Eletrônicos", "Alimentos", "Farmacêutico", "Industrial",
                       "Limpeza", "Bebidas", "Automotivo", "Construção"]

produtos_op = []
for i in range(1, 51):
    categoria = random.choice(_categorias_produto)
    cat_prefix = {"Eletrônicos": "ELE", "Alimentos": "ALI", "Farmacêutico": "FAR",
                  "Industrial": "IND", "Limpeza": "LIM", "Bebidas": "BEB",
                  "Automotivo": "AUT", "Construção": "CON"}
    sku = f"{cat_prefix[categoria]}-{i:04d}"
    if categoria == "Eletrônicos":
        peso = round(random.uniform(0.5, 20.0), 3)
        volume = round(random.uniform(0.001, 0.5), 4)
    elif categoria == "Alimentos":
        peso = round(random.uniform(0.5, 10.0), 3)
        volume = round(random.uniform(0.001, 0.1), 4)
    elif categoria == "Farmacêutico":
        peso = round(random.uniform(0.01, 2.0), 3)
        volume = round(random.uniform(0.0001, 0.01), 4)
    elif categoria == "Industrial":
        peso = round(random.uniform(5.0, 100.0), 3)
        volume = round(random.uniform(0.01, 0.5), 4)
    else:
        peso = round(random.uniform(1.0, 15.0), 3)
        volume = round(random.uniform(0.01, 0.2), 4)
    produtos_op.append({
        "produto_id": i,
        "sku": sku,
        "nome": f"Produto {categoria} {i:03d}",
        "categoria": categoria,
        "peso_unitario_kg": peso,
        "volume_unitario_m3": volume,
        "ativo": True,
    })

df_produto_op = pd.DataFrame(produtos_op)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# ESTOQUE & MOVIMENTACAO_ESTOQUE
# ─────────────────────────────────────────────────────────────

estoques_op = []
estoque_id = 1
for cd in range(1, 6):
    for prod in range(1, 51):
        estoques_op.append({
            "estoque_id": estoque_id,
            "cd_id": cd,
            "produto_id": prod,
            "quantidade_disponivel": random.randint(0, 1000),
            "quantidade_reservada": random.randint(0, 200),
            "posicao_galpao": f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(1, 20):02d}-{random.randint(1, 10)}",
            "ultima_atualizacao": (date(2024, 1, 1) + timedelta(days=random.randint(0, 547))).isoformat() + " 10:00:00",
        })
        estoque_id += 1

df_estoque_op = pd.DataFrame(estoques_op)

movimentacoes_op = []
for estoque in df_estoque_op.itertuples():
    estoque_row = estoque._asdict()
    n_movs = random.randint(100, 250)
    for m in range(n_movs):
        dt_mov = date(2024, 1, 1) + timedelta(days=random.randint(0, 547))
        hora = random.randint(0, 23)
        minuto = random.randint(0, 59)
        tipo_mov = random.choice(["Entrada", "Saída", "Reserva", "Liberação", "Ajuste"])
        if tipo_mov == "Entrada":
            qtd = random.randint(1, 50)
        elif tipo_mov == "Saída":
            qtd = -random.randint(1, 50)
        elif tipo_mov == "Reserva":
            qtd = -random.randint(1, 20)
        elif tipo_mov == "Liberação":
            qtd = random.randint(1, 20)
        else:
            qtd = random.choice([-1, 1]) * random.randint(1, 5)
        movimentacoes_op.append({
            "movimentacao_id": len(movimentacoes_op) + 1,
            "estoque_id": estoque_row["estoque_id"],
            "tipo_mov": tipo_mov,
            "quantidade": qtd,
            "timestamp_mov": f"{dt_mov.isoformat()} {hora:02d}:{minuto:02d}:00",
            "referencia": f"REF-{random.randint(10000, 99999)}",
            "observacao": random.choice([None, "Movimentação automática", "Ajuste de inventário"]),
        })

df_movimentacao_estoque_op = pd.DataFrame(movimentacoes_op)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 2: Dados Transacionais (Pedidos e Entregas)

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# TEMPO — 2024-01-01 a 2026-09-30
# ─────────────────────────────────────────────────────────────

_feriados = {
    "2024-01-01","2024-02-12","2024-02-13","2024-03-29","2024-04-21",
    "2024-05-01","2024-05-30","2024-09-07","2024-10-12","2024-11-02",
    "2024-11-15","2024-11-20","2024-12-25",
    "2025-01-01","2025-03-03","2025-03-04","2025-04-18","2025-04-21",
    "2025-05-01","2025-06-19","2025-09-07","2025-10-12","2025-11-02",
    "2025-11-15","2025-11-20","2025-12-25",
    "2026-01-01","2026-02-16","2026-02-17","2026-04-03","2026-04-21",
    "2026-05-01","2026-06-04","2026-09-07",
}
_mes_nomes = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
              "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
_dia_nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]

tempo_dw_rows = []
dt = date(2024, 1, 1)
while dt <= date(2026, 9, 30):
    ds = dt.isoformat()
    tempo_dw_rows.append({
        "sk_tempo": int(dt.strftime("%Y%m%d")),
        "data_completa": ds,
        "dia": dt.day,
        "mes": dt.month,
        "ano": dt.year,
        "trimestre": (dt.month - 1) // 3 + 1,
        "semana_do_ano": dt.isocalendar()[1],
        "dia_da_semana": dt.weekday() + 1,
        "nome_dia_semana": _dia_nomes[dt.weekday()],
        "nome_mes": _mes_nomes[dt.month],
        "flag_feriado": 1 if ds in _feriados else 0,
        "flag_fim_semana": 1 if dt.weekday() >= 5 else 0,
        "descricao_feriado": None,
    })
    dt += timedelta(days=1)

df_dim_tempo_dw = pd.DataFrame(tempo_dw_rows)

_data_por_sk_tempo = dict(zip(df_dim_tempo_dw["sk_tempo"], df_dim_tempo_dw["data_completa"]))
_dias_uteis_sk = df_dim_tempo_dw[
    (df_dim_tempo_dw["flag_fim_semana"] == 0) &
    (df_dim_tempo_dw["flag_feriado"] == 0)
]["sk_tempo"].values

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# PEDIDO, ITEM_PEDIDO, ENTREGA — ~50.000 entregas
# ─────────────────────────────────────────────────────────────

N_ENTREGAS = 49_770
_cd_pesos = [0.20, 0.25, 0.15, 0.25, 0.15]

sk_datas     = rng.choice(_dias_uteis_sk, size=N_ENTREGAS, replace=True)
sk_clientes  = rng.integers(1, 201, size=N_ENTREGAS)
sk_veiculos  = rng.integers(1, 51,  size=N_ENTREGAS)
sk_motoristas = rng.integers(1, 101, size=N_ENTREGAS)
sk_cd_origens = rng.choice([1, 2, 3, 4, 5], size=N_ENTREGAS, p=_cd_pesos)

distancias         = np.clip(np.round(np.exp(rng.normal(4.87, 0.65, N_ENTREGAS)), 1), 15.0, 1500.0)
pesos              = np.clip(np.round(rng.normal(2500, 1100, N_ENTREGAS)), 50, 25000).astype(float)
quantidade_volumes = np.clip(np.round(rng.normal(10, 5, N_ENTREGAS)), 1, 50).astype(int)
hh = rng.integers(6, 18, N_ENTREGAS)
mm = rng.integers(0, 60, N_ENTREGAS)

_tipo  = rng.choice(["adi", "ok", "lat", "mla"], N_ENTREGAS, p=[0.40, 0.42, 0.14, 0.04])
atraso = np.zeros(N_ENTREGAS, dtype=int)
atraso[_tipo == "adi"] = -rng.integers(5, 61,   (_tipo == "adi").sum())
atraso[_tipo == "lat"] =  rng.integers(1, 121,  (_tipo == "lat").sum())
atraso[_tipo == "mla"] =  rng.integers(121, 481,(_tipo == "mla").sum())

tempo_estimado_min = np.round(distancias * 1.2, 0).astype(int)
tempo_real_min     = np.clip(tempo_estimado_min + rng.normal(0, 15, N_ENTREGAS).astype(int), 1, None)

valor_frete  = np.round(distancias * 2.5 + pesos * 0.5 + rng.uniform(-100, 500, N_ENTREGAS), 2)
custo_comb   = np.clip(np.round(distancias * 0.75 * rng.normal(1.0, 0.12, N_ENTREGAS), 2), 15.0, 3500.0)
custo_pedagio = np.round(distancias * rng.uniform(0.30, 0.70, N_ENTREGAS), 2)
multa_atraso  = np.zeros(N_ENTREGAS)
multa_atraso[atraso > 0] = np.round(valor_frete[atraso > 0] * 0.10, 2)

indicador_atraso = (atraso > 0).astype(int)

datas_str = [_data_por_sk_tempo[s] for s in sk_datas]
datas_dt  = [datetime.strptime(d, "%Y-%m-%d") for d in datas_str]
horas_str = [f"{d.year:04d}-{d.month:02d}-{d.day:02d} {h:02d}:{m:02d}:00"
             for d, h, m in zip(datas_dt, hh, mm)]

pedidos_op    = []
entregas_op   = []
item_pedido_op = []

pedido_id  = 1
entrega_id = 1
item_id    = 1

for i in range(N_ENTREGAS):
    sk_data     = sk_datas[i]
    sk_cliente  = sk_clientes[i]
    sk_cd       = sk_cd_origens[i]
    sk_veiculo  = sk_veiculos[i]
    sk_motorista = sk_motoristas[i]

    data_pedido_dt       = datas_dt[i] - timedelta(days=random.randint(1, 3))
    prazo_entrega_dt     = datas_dt[i] + timedelta(hours=random.randint(12, 48))
    data_saida_dt        = datetime.strptime(horas_str[i], "%Y-%m-%d %H:%M:%S")
    data_entrega_real_dt = data_saida_dt + timedelta(minutes=int(tempo_real_min[i]))

    if atraso[i] > 300:
        status_pedido  = "Entregue"
        status_entrega = "Ocorrência"
    else:
        status_pedido  = "Entregue"
        status_entrega = "Entregue"

    if distancias[i] > 1000:
        prioridade = "Alta"
    elif distancias[i] > 500:
        prioridade = "Normal"
    else:
        prioridade = random.choice(["Normal", "Baixa"])

    _min_atraso = int(atraso[i])
    if _min_atraso < 0:
        _kpi_cat = "Adiantado"
    elif _min_atraso == 0:
        _kpi_cat = "No Prazo"
    elif _min_atraso <= 60:
        _kpi_cat = "Atraso Leve"
    elif _min_atraso <= 240:
        _kpi_cat = "Atraso Moderado"
    else:
        _kpi_cat = "Atraso Crítico"

    _cli = df_cliente_op.iloc[sk_cliente - 1]
    _vei = df_veiculo_op.iloc[sk_veiculo - 1]
    _mot = df_motorista_op.iloc[sk_motorista - 1]
    _cd  = df_centro_distribuicao_op.iloc[sk_cd - 1]

    pedidos_op.append({
        "pedido_id": pedido_id,
        "numero_pedido": f"PED-{datas_str[i][:4]}-{pedido_id:06d}",
        "cliente_id": sk_cliente,
        "contrato_id": random.choice([None, sk_cliente]),
        "cd_origem_id": sk_cd,
        "endereco_destino_id": sk_cliente,
        "data_pedido": f"{data_pedido_dt.strftime('%Y-%m-%d')} {random.randint(8, 17):02d}:00:00",
        "prazo_entrega": f"{prazo_entrega_dt.strftime('%Y-%m-%d %H:%M:%S')}",
        "prioridade": prioridade,
        "status_pedido": status_pedido,
    })

    entregas_op.append({
        "entrega_id": entrega_id,
        "pedido_id": pedido_id,
        "veiculo_id": sk_veiculo,
        "motorista_id": sk_motorista,
        "cliente_id":            int(sk_cliente),
        "cliente_cnpj":          _cli["cnpj"],
        "cliente_razao_social":  _cli["razao_social"],
        "cliente_segmento":      _cli["segmento"],
        "veiculo_placa":         _vei["placa"],
        "veiculo_modelo":        _vei["modelo"],
        "veiculo_fabricante":    _vei["fabricante"],
        "veiculo_capacidade_kg": float(_vei["capacidade_kg"]),
        "motorista_nome":        _mot["nome_completo"],
        "motorista_cnh":         _mot["cnh"],
        "motorista_categoria":   _mot["categoria_cnh"],
        "cd_origem_id":          int(sk_cd),
        "cd_origem_codigo":      _cd["codigo"],
        "cd_origem_nome":        _cd["nome"],
        "cd_origem_uf":          _cd["uf"],
        "data_saida": horas_str[i],
        "data_entrega_prevista": f"{prazo_entrega_dt.strftime('%Y-%m-%d %H:%M:%S')}",
        "data_entrega_real": data_entrega_real_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "distancia_km": round(float(distancias[i]), 2),
        "custo_combustivel": round(float(custo_comb[i]), 2),
        "custo_pedagio": round(float(custo_pedagio[i]), 2),
        "valor_frete": round(float(valor_frete[i]), 2),
        "multa_atraso": round(float(multa_atraso[i]), 2),
        "status_entrega": status_entrega,
        "kpi_cat_atraso": _kpi_cat,
    })

    n_itens = random.randint(1, 5)
    peso_total_item = pesos[i]
    for j in range(n_itens):
        produto_id = random.randint(1, 50)
        peso_item  = round(peso_total_item * (0.5 + random.random()), 2)
        qtd        = random.randint(1, 10)
        item_pedido_op.append({
            "item_id": item_id,
            "pedido_id": pedido_id,
            "produto_id": produto_id,
            "quantidade": qtd,
            "peso_total_kg": round(qtd * peso_item, 2),
        })
        item_id += 1

    pedido_id  += 1
    entrega_id += 1

df_pedido_op      = pd.DataFrame(pedidos_op)
df_entrega_op     = pd.DataFrame(entregas_op)
df_item_pedido_op = pd.DataFrame(item_pedido_op)

print(f"Pedidos gerados:       {len(df_pedido_op):,}")
print(f"Entregas geradas:      {len(df_entrega_op):,}")
print(f"Itens de pedido gerados: {len(df_item_pedido_op):,}")

# COMMAND ----------

# ─────────────────────────────────────────────────────────────
# TELEMETRIA — simplificada (1 registro por entrega)
# ─────────────────────────────────────────────────────────────

telemetrias_op = []
for i, entrega in df_entrega_op.iterrows():
    data_evento_dt = datetime.strptime(entrega["data_saida"], "%Y-%m-%d %H:%M:%S")
    telemetrias_op.append({
        "telemetria_id": i + 1,
        "veiculo_id": entrega["veiculo_id"],
        "timestamp_evento": entrega["data_saida"],
        "data_evento": data_evento_dt.strftime("%Y-%m-%d"),
        "latitude": round(random.uniform(-30, -15), 6),
        "longitude": round(random.uniform(-55, -35), 6),
        "velocidade_kmh": round(random.uniform(0, 110), 2),
        "rpm_motor": random.randint(800, 3000),
        "temperatura_motor_c": round(random.uniform(80, 110), 2),
        "nivel_combustivel_pct": round(random.uniform(10, 100), 2),
        "peso_carga_kg": round(random.uniform(100, 25000), 2),
        "hodometro_km": random.randint(50000, 300000),
    })

df_telemetria_op = pd.DataFrame(telemetrias_op)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 3: SALVAR DADOS OPERACIONAIS (lodlog_op)

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, TimestampType, IntegerType, DoubleType, DecimalType

spark.sql("CREATE DATABASE IF NOT EXISTS lodlog_op")
spark.sql("USE lodlog_op")

def _save_op(df_pd, nome, tipo_cast=None):
    spark.sql(f"DROP TABLE IF EXISTS lodlog_op.{nome}")
    df_sp = spark.createDataFrame(df_pd)
    if tipo_cast:
        for col, t in tipo_cast.items():
            df_sp = df_sp.withColumn(col, F.col(col).cast(t))
    (df_sp.write.format("delta")
         .mode("overwrite")
         .option("overwriteSchema", "true")
         .saveAsTable(f"lodlog_op.{nome}"))
    n = spark.table(f"lodlog_op.{nome}").count()
    print(f"  ✓ lodlog_op.{nome}: {n:,} linhas")

print("Salvando tabelas operacionais (lodlog_op)...")

_save_op(df_cliente_op, "cliente", {
    "data_cadastro": DateType(),
    "ativo": "boolean"
})
_save_op(df_endereco_cliente_op, "endereco_cliente", {
    "latitude": DecimalType(9, 6),
    "longitude": DecimalType(9, 6)
})
_save_op(df_contrato_op, "contrato", {
    "data_inicio": DateType(),
    "data_fim": DateType()
})
_save_op(df_centro_distribuicao_op, "centro_distribuicao", {
    "capacidade_m3": DecimalType(10, 2),
    "latitude": DecimalType(9, 6),
    "longitude": DecimalType(9, 6),
    "ativo": "boolean"
})
_save_op(df_veiculo_op, "veiculo", {
    "capacidade_kg": DecimalType(10, 2),
    "hodometro_km": DecimalType(10, 0),
    "data_aquisicao": DateType()
})
_save_op(df_motorista_op, "motorista", {
    "score_seguranca": DecimalType(5, 2),
    "data_admissao": DateType(),
    "validade_cnh": DateType()
})
_save_op(df_manutencao_op, "manutencao", {
    "data_abertura": TimestampType(),
    "data_conclusao": TimestampType(),
    "km_no_momento": DecimalType(10, 0),
    "custo_total": DecimalType(12, 2)
})
_save_op(df_produto_op, "produto", {
    "peso_unitario_kg": DecimalType(10, 3),
    "volume_unitario_m3": DecimalType(10, 4),
    "ativo": "boolean"
})
_save_op(df_estoque_op, "estoque", {
    "ultima_atualizacao": TimestampType()
})
_save_op(df_movimentacao_estoque_op, "movimentacao_estoque", {
    "timestamp_mov": TimestampType()
})
_save_op(df_pedido_op, "pedido", {
    "data_pedido": TimestampType(),
    "prazo_entrega": TimestampType()
})
_save_op(df_entrega_op, "entrega", {
    "data_saida": TimestampType(),
    "data_entrega_prevista": TimestampType(),
    "data_entrega_real": TimestampType(),
    "distancia_km": DecimalType(10, 2),
    "custo_combustivel": DecimalType(12, 2),
    "custo_pedagio": DecimalType(12, 2),
    "valor_frete": DecimalType(12, 2),
    "multa_atraso": DecimalType(12, 2),
    "veiculo_capacidade_kg": DecimalType(10, 2)
})
_save_op(df_item_pedido_op, "item_pedido", {
    "peso_total_kg": DecimalType(10, 2)
})
_save_op(df_telemetria_op, "telemetria", {
    "timestamp_evento": TimestampType(),
    "data_evento": DateType(),
    "latitude": DecimalType(9, 6),
    "longitude": DecimalType(9, 6),
    "velocidade_kmh": DecimalType(6, 2),
    "temperatura_motor_c": DecimalType(6, 2),
    "nivel_combustivel_pct": DecimalType(5, 2),
    "peso_carga_kg": DecimalType(10, 2),
    "hodometro_km": DecimalType(10, 0)
})

print("\nTabelas operacionais salvas com sucesso!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 4: ETL — Dimensões Estáticas
# MAGIC
# MAGIC `dim_cat_atraso` e `dim_tempo` não têm tabela-fonte em `lodlog_op`
# MAGIC (lookup estático e calendário), por isso continuam sendo geradas em Python.

# COMMAND ----------

print("\nProcessando ETL para lodlog_dw...")
spark.sql("CREATE DATABASE IF NOT EXISTS lodlog_dw")
spark.sql("USE lodlog_dw")

def _save_dw(df_pd, nome, tipo_cast=None):
    spark.sql(f"DROP TABLE IF EXISTS lodlog_dw.{nome}")
    df_sp = spark.createDataFrame(df_pd)
    if tipo_cast:
        for col, t in tipo_cast.items():
            df_sp = df_sp.withColumn(col, F.col(col).cast(t))
    (df_sp.write.format("delta")
         .mode("overwrite")
         .option("overwriteSchema", "true")
         .saveAsTable(f"lodlog_dw.{nome}"))
    n = spark.table(f"lodlog_dw.{nome}").count()
    print(f"  ✓ lodlog_dw.{nome}: {n:,} linhas")

# ── dim_cat_atraso (minidimensão Kimball, SCD Tipo 1) ───────────
dim_cat_atraso_dw = [
    {"sk_cat_atraso": 1, "categoria": "Adiantado",
     "descricao": "Entregas concluída antes do prazo previsto",
     "limite_inferior_min": -99999, "limite_superior_min": -1,
     "sla_violado": False, "ordem": 1},
    {"sk_cat_atraso": 2, "categoria": "No Prazo",
     "descricao": "Entregas concluída exatamente no prazo previsto",
     "limite_inferior_min": 0, "limite_superior_min": 0,
     "sla_violado": False, "ordem": 2},
    {"sk_cat_atraso": 3, "categoria": "Atraso Leve",
     "descricao": "Atraso de até 60 minutos — dentro de margem tolerável",
     "limite_inferior_min": 1, "limite_superior_min": 60,
     "sla_violado": True, "ordem": 3},
    {"sk_cat_atraso": 4, "categoria": "Atraso Moderado",
     "descricao": "Atraso entre 61 e 240 minutos — impacta SLA contratual",
     "limite_inferior_min": 61, "limite_superior_min": 240,
     "sla_violado": True, "ordem": 4},
    {"sk_cat_atraso": 5, "categoria": "Atraso Crítico",
     "descricao": "Atraso acima de 240 minutos — pode gerar multa e perda de cliente",
     "limite_inferior_min": 241, "limite_superior_min": None,
     "sla_violado": True, "ordem": 5},
]
_save_dw(pd.DataFrame(dim_cat_atraso_dw), "dim_cat_atraso", {
    "sk_cat_atraso": IntegerType(),
    "limite_inferior_min": IntegerType(),
    "limite_superior_min": IntegerType(),
    "sla_violado": "boolean",
    "ordem": IntegerType(),
})

# ── dim_tempo (calendário 2024-01-01 a 2026-09-30) ──────────────
_save_dw(df_dim_tempo_dw, "dim_tempo", {
    "sk_tempo": IntegerType(),
    "data_completa": DateType(),
    "flag_feriado": "boolean",
    "flag_fim_semana": "boolean"
})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 5: ETL — Dimensões a partir de `lodlog_op`
# MAGIC
# MAGIC Cada dimensão é reconstruída com `CREATE TABLE … AS SELECT` (CTAS)
# MAGIC diretamente das tabelas operacionais — sem geração de dados em Python.

# COMMAND ----------

# Expressão SQL reutilizável para mapear UF → Região geográfica
_REGIAO_CASE = """
  CASE uf
    WHEN 'SP' THEN 'Sudeste' WHEN 'MG' THEN 'Sudeste'
    WHEN 'RJ' THEN 'Sudeste' WHEN 'ES' THEN 'Sudeste'
    WHEN 'PR' THEN 'Sul'     WHEN 'RS' THEN 'Sul'     WHEN 'SC' THEN 'Sul'
    WHEN 'GO' THEN 'Centro-Oeste' WHEN 'DF' THEN 'Centro-Oeste'
    WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste'
    WHEN 'BA' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
    WHEN 'CE' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste'
    WHEN 'MA' THEN 'Nordeste' WHEN 'PI' THEN 'Nordeste'
    WHEN 'SE' THEN 'Nordeste' WHEN 'AL' THEN 'Nordeste' WHEN 'PB' THEN 'Nordeste'
    WHEN 'PA' THEN 'Norte'   WHEN 'AM' THEN 'Norte'
    WHEN 'AC' THEN 'Norte'   WHEN 'RO' THEN 'Norte'
    WHEN 'RR' THEN 'Norte'   WHEN 'AP' THEN 'Norte'   WHEN 'TO' THEN 'Norte'
    ELSE 'Sudeste'
  END
"""

# COMMAND ----------

# ── dim_centro_distribuicao (SCD Tipo 1) ────────────────────────
print("  ETL: dim_centro_distribuicao")
spark.sql("DROP TABLE IF EXISTS lodlog_dw.dim_centro_distribuicao")
spark.sql(f"""
CREATE TABLE lodlog_dw.dim_centro_distribuicao
USING DELTA AS
SELECT
  cd_id                       AS sk_cd,
  cd_id,
  codigo,
  nome,
  municipio,
  uf,
  {_REGIAO_CASE}              AS regiao,
  capacidade_m3,
  latitude,
  longitude
FROM lodlog_op.centro_distribuicao
""")
n = spark.table("lodlog_dw.dim_centro_distribuicao").count()
print(f"  ✓ lodlog_dw.dim_centro_distribuicao: {n:,} linhas")

# COMMAND ----------

# ── dim_cliente (SCD Tipo 2 — carga inicial, 1 versão por cliente) ──
# Joins: cliente + endereco_cliente (1:1) + contrato (1:1 neste dataset)
print("  ETL: dim_cliente")
spark.sql("DROP TABLE IF EXISTS lodlog_dw.dim_cliente")
spark.sql(f"""
CREATE TABLE lodlog_dw.dim_cliente
USING DELTA AS
SELECT
  c.cliente_id                                                    AS sk_cliente,
  c.cliente_id,
  c.cnpj,
  c.razao_social,
  c.segmento,
  e.municipio,
  e.uf,
  {_REGIAO_CASE.replace('uf', 'e.uf')}                           AS regiao,
  CAST(DATEDIFF(DATE('2024-06-01'), c.data_cadastro) / 30 AS INT) AS tempo_relacionamento_meses,
  co.sla_pontualidade_pct                                         AS sla_contratual_pct,
  c.data_cadastro                                                 AS data_inicio_vigencia,
  CAST(NULL AS DATE)                                              AS data_fim_vigencia,
  TRUE                                                            AS flag_registro_atual
FROM      lodlog_op.cliente          c
JOIN      lodlog_op.endereco_cliente e  ON e.cliente_id  = c.cliente_id
LEFT JOIN lodlog_op.contrato         co ON co.cliente_id = c.cliente_id
""")
n = spark.table("lodlog_dw.dim_cliente").count()
print(f"  ✓ lodlog_dw.dim_cliente: {n:,} linhas")

# COMMAND ----------

# ── dim_veiculo (SCD Tipo 2 — carga inicial) ────────────────────
print("  ETL: dim_veiculo")
spark.sql("DROP TABLE IF EXISTS lodlog_dw.dim_veiculo")
spark.sql("""
CREATE TABLE lodlog_dw.dim_veiculo
USING DELTA AS
SELECT
  veiculo_id  AS sk_veiculo,
  veiculo_id,
  placa,
  modelo,
  fabricante,
  ano_fabricacao,
  tipo,
  capacidade_kg,
  CASE
    WHEN capacidade_kg <= 1000  THEN 'Até 1t'
    WHEN capacidade_kg <= 5000  THEN '1-5t'
    WHEN capacidade_kg <= 15000 THEN '5-15t'
    ELSE                             'Acima 15t'
  END          AS faixa_capacidade,
  data_aquisicao   AS data_inicio_vigencia,
  CAST(NULL AS DATE) AS data_fim_vigencia,
  TRUE             AS flag_registro_atual
FROM lodlog_op.veiculo
""")
n = spark.table("lodlog_dw.dim_veiculo").count()
print(f"  ✓ lodlog_dw.dim_veiculo: {n:,} linhas")

# COMMAND ----------

# ── dim_motorista (SCD Tipo 2 — carga inicial) ──────────────────
print("  ETL: dim_motorista")
spark.sql("DROP TABLE IF EXISTS lodlog_dw.dim_motorista")
spark.sql("""
CREATE TABLE lodlog_dw.dim_motorista
USING DELTA AS
SELECT
  motorista_id  AS sk_motorista,
  motorista_id,
  nome_completo,
  categoria_cnh,
  CAST(DATEDIFF(DATE('2024-06-01'), data_admissao) / 30 AS INT) AS tempo_empresa_meses,
  CASE
    WHEN DATEDIFF(DATE('2024-06-01'), data_admissao) / 30 < 24  THEN 'Júnior'
    WHEN DATEDIFF(DATE('2024-06-01'), data_admissao) / 30 < 96  THEN 'Pleno'
    ELSE                                                              'Sênior'
  END           AS faixa_experiencia,
  score_seguranca,
  data_admissao AS data_inicio_vigencia,
  CAST(NULL AS DATE) AS data_fim_vigencia,
  TRUE          AS flag_registro_atual
FROM lodlog_op.motorista
""")
n = spark.table("lodlog_dw.dim_motorista").count()
print(f"  ✓ lodlog_dw.dim_motorista: {n:,} linhas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 6: ETL — `fato_entregas`
# MAGIC
# MAGIC **Base limpa:** `INSERT INTO … SELECT` a partir de `lodlog_op` (entrega + pedido + item_pedido).
# MAGIC
# MAGIC **Anomalias propositais** inseridas em seguida via `INSERT INTO` (modo append):
# MAGIC - 100 linhas duplicadas (mesmo `entrega_id`, `custo_combustivel` levemente alterado)
# MAGIC - 50 linhas com valores negativos (`distancia_km`, `peso_total_kg` ou `custo_combustivel`)
# MAGIC - 30 linhas com outliers em `minutos_atraso` (> 1000 min ou adiantamento impossível)
# MAGIC - 50 linhas com FK quebrada (`sk_cliente` 201–300, inexistente em `dim_cliente`)

# COMMAND ----------

# ── fato_entregas — base limpa via SQL ──────────────────────────
# minutos_atraso = tempo_real (seg→min) − tempo_estimado (distancia * 1.2)
# sk_data         = data de entrega real (ou prevista) no formato YYYYMMDD
# temperatura_media_motor gerada com RAND() — dado sintético sem fonte op
print("  ETL: fato_entregas (base)")
spark.sql("DROP TABLE IF EXISTS lodlog_dw.fato_entregas")
spark.sql("""
CREATE TABLE lodlog_dw.fato_entregas
USING DELTA AS
WITH base AS (
  SELECT
    e.entrega_id,
    e.pedido_id,
    e.veiculo_id,
    e.motorista_id,
    e.data_saida,
    e.data_entrega_real,
    e.distancia_km,
    e.custo_combustivel,
    e.custo_pedagio,
    e.valor_frete,
    e.multa_atraso,
    p.cliente_id,
    p.cd_origem_id,
    CAST(DATE_FORMAT(
      COALESCE(e.data_entrega_real, e.data_entrega_prevista),
      'yyyyMMdd'
    ) AS INT)                                                   AS sk_data,
    DATE(COALESCE(e.data_entrega_real, e.data_entrega_prevista)) AS data_entrega,
    CAST(e.distancia_km * 1.2 AS INT)                           AS tempo_estimado_min,
    GREATEST(
      CAST((UNIX_TIMESTAMP(e.data_entrega_real)
            - UNIX_TIMESTAMP(e.data_saida)) / 60 AS INT),
      1
    )                                                           AS tempo_real_min,
    CAST((UNIX_TIMESTAMP(e.data_entrega_real)
          - UNIX_TIMESTAMP(e.data_saida)) / 60 AS INT)
      - CAST(e.distancia_km * 1.2 AS INT)                       AS minutos_atraso
  FROM lodlog_op.entrega e
  JOIN lodlog_op.pedido p ON p.pedido_id = e.pedido_id
),
itens AS (
  SELECT
    pedido_id,
    COUNT(*)           AS quantidade_volumes,
    SUM(peso_total_kg) AS peso_total_kg
  FROM lodlog_op.item_pedido
  GROUP BY pedido_id
)
SELECT
  b.entrega_id                                                   AS sk_entrega,
  b.sk_data,
  b.cliente_id                                                   AS sk_cliente,
  b.cd_origem_id                                                 AS sk_cd_origem,
  b.veiculo_id                                                   AS sk_veiculo,
  b.motorista_id                                                 AS sk_motorista,
  CASE
    WHEN b.minutos_atraso < 0   THEN 1
    WHEN b.minutos_atraso = 0   THEN 2
    WHEN b.minutos_atraso <= 60  THEN 3
    WHEN b.minutos_atraso <= 240 THEN 4
    ELSE 5
  END                                                            AS sk_cat_atraso,
  b.entrega_id,
  CAST(b.pedido_id AS STRING)                                    AS pedido_id,
  b.data_entrega,
  b.data_saida                                                   AS hora_saida,
  COALESCE(i.quantidade_volumes, 0)                              AS quantidade_volumes,
  COALESCE(CAST(i.peso_total_kg AS DECIMAL(10,2)), CAST(0 AS DECIMAL(10,2))) AS peso_total_kg,
  b.distancia_km,
  b.tempo_estimado_min,
  b.tempo_real_min,
  b.custo_combustivel,
  b.custo_pedagio,
  b.valor_frete,
  b.multa_atraso,
  b.minutos_atraso,
  CAST(CASE WHEN b.minutos_atraso > 0 THEN 1 ELSE 0 END AS INT) AS indicador_atraso,
  ROUND(85 + RAND() * 20, 2)                                    AS temperatura_media_motor,
  CASE
    WHEN b.minutos_atraso < 0   THEN 'Adiantado'
    WHEN b.minutos_atraso = 0   THEN 'No Prazo'
    WHEN b.minutos_atraso <= 60  THEN 'Atraso Leve'
    WHEN b.minutos_atraso <= 240 THEN 'Atraso Moderado'
    ELSE 'Atraso Crítico'
  END                                                            AS kpi_cat_atraso
FROM base b
LEFT JOIN itens i ON i.pedido_id = b.pedido_id
""")
n_base = spark.table("lodlog_dw.fato_entregas").count()
print(f"  ✓ lodlog_dw.fato_entregas (base): {n_base:,} linhas")

# COMMAND ----------

# ── Anomalias propositais — leitura da base + append ────────────
# Lemos o fato limpo de volta para Python para gerar as anomalias
# via sampling, depois inserimos via INSERT INTO (modo append).

df_fato_clean = spark.table("lodlog_dw.fato_entregas").toPandas()
# Colunas DECIMAL voltam como Python Decimal (dtype object) após toPandas().
# Cast para float evita PySparkTypeError na conversão Arrow ao fazer o append.
_decimal_cols = [
    "peso_total_kg", "distancia_km", "custo_combustivel",
    "custo_pedagio", "valor_frete", "multa_atraso", "temperatura_media_motor",
]
for _c in _decimal_cols:
    if _c in df_fato_clean.columns:
        df_fato_clean[_c] = df_fato_clean[_c].astype(float)

# Colunas INT (não BIGINT) voltam como int64 no pandas, que o Spark infere
# como LongType. Delta recusa mergeSchema INT ↔ Long com DELTA_FAILED_TO_MERGE_FIELDS.
# Cast para int32 restaura o mapeamento correto pandas int32 → Spark IntegerType.
# NOTA: quantidade_volumes é LONG na tabela, não INT, então não deve ser convertido.
_int32_cols = [
    "sk_data", "sk_cat_atraso", "tempo_estimado_min",
    "tempo_real_min", "minutos_atraso", "indicador_atraso",
]
for _c in _int32_cols:
    if _c in df_fato_clean.columns:
        df_fato_clean[_c] = df_fato_clean[_c].astype("int32")

sk_next = int(df_fato_clean["entrega_id"].max()) + 1

anomalias = []
_sample = lambda n: df_fato_clean.sample(n, random_state=SEED).copy()

# --- Anomalia 1 · Duplicatas (100 linhas) ---
# mesmo entrega_id (PK repetida), custo_combustivel levemente diferente
for _, row in _sample(100).iterrows():
    row = row.copy()
    row["sk_entrega"] = sk_next
    row["custo_combustivel"] = round(float(row["custo_combustivel"]) * random.uniform(0.98, 1.02), 2)
    anomalias.append(row.to_dict())
    sk_next += 1

# --- Anomalia 2 · Valores negativos (50 linhas) ---
for _, row in _sample(50).iterrows():
    row = row.copy()
    row["sk_entrega"] = sk_next
    row["pedido_id"] = f"PED-NEG-{sk_next:06d}"
    campo = random.choice(["distancia_km", "peso_total_kg", "custo_combustivel"])
    row[campo] = -abs(float(row[campo]))
    anomalias.append(row.to_dict())
    sk_next += 1

# --- Anomalia 3 · Outliers em minutos_atraso (30 linhas) ---
for _, row in _sample(30).iterrows():
    row = row.copy()
    row["sk_entrega"] = sk_next
    row["pedido_id"] = f"PED-OUT-{sk_next:06d}"
    row["minutos_atraso"] = random.choice([
        random.randint(1_001, 5_760),   # até 4 dias de atraso
        random.randint(-1_440, -481),   # adiantamento impossível
    ])
    anomalias.append(row.to_dict())
    sk_next += 1

# --- Anomalia 4 · FK quebrada — sk_cliente inexistente (50 linhas) ---
for _, row in _sample(50).iterrows():
    row = row.copy()
    row["sk_entrega"] = sk_next
    row["pedido_id"] = f"PED-FKB-{sk_next:06d}"
    row["sk_cliente"] = random.randint(201, 300)
    anomalias.append(row.to_dict())
    sk_next += 1

df_anomalias = pd.DataFrame(anomalias)
df_anomalias["pedido_id"] = df_anomalias["pedido_id"].astype(str)

# Criar DataFrame Spark e garantir tipos exatos compatíveis com a tabela
from pyspark.sql.types import IntegerType, DecimalType, DoubleType

df_spark_anomalias = spark.createDataFrame(df_anomalias)

# Cast explícito para IntegerType nas colunas INT (não LONG)
for col_name in ["sk_data", "sk_cat_atraso", "tempo_estimado_min",
                 "tempo_real_min", "minutos_atraso", "indicador_atraso"]:
    df_spark_anomalias = df_spark_anomalias.withColumn(col_name, F.col(col_name).cast(IntegerType()))

# Cast explícito para DecimalType com precisão correta
df_spark_anomalias = (df_spark_anomalias
    .withColumn("peso_total_kg", F.col("peso_total_kg").cast(DecimalType(10, 2)))
    .withColumn("distancia_km", F.col("distancia_km").cast(DecimalType(10, 2)))
    .withColumn("custo_combustivel", F.col("custo_combustivel").cast(DecimalType(12, 2)))
    .withColumn("custo_pedagio", F.col("custo_pedagio").cast(DecimalType(12, 2)))
    .withColumn("valor_frete", F.col("valor_frete").cast(DecimalType(12, 2)))
    .withColumn("multa_atraso", F.col("multa_atraso").cast(DecimalType(12, 2)))
    .withColumn("temperatura_media_motor", F.col("temperatura_media_motor").cast(DoubleType()))
)

# Append das anomalias ao fato (Delta não força PK — duplicatas ficam visíveis)
(df_spark_anomalias
     .write.format("delta")
     .mode("append")
     .saveAsTable("lodlog_dw.fato_entregas"))

n_final = spark.table("lodlog_dw.fato_entregas").count()
print(f"  ✓ lodlog_dw.fato_entregas (final): {n_final:,} linhas ({len(df_anomalias)} anômalas)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parte 7: OPTIMIZE e Validação

# COMMAND ----------

print("\nOtimizando tabelas...")
spark.sql("OPTIMIZE lodlog_dw.fato_entregas ZORDER BY (sk_data, sk_cd_origem, indicador_atraso, sk_cat_atraso)")
spark.sql("OPTIMIZE lodlog_dw.dim_tempo ZORDER BY (sk_tempo)")
spark.sql("OPTIMIZE lodlog_dw.dim_cat_atraso ZORDER BY (sk_cat_atraso)")
spark.sql("OPTIMIZE lodlog_op.entrega ZORDER BY (status_entrega, data_saida)")
spark.sql("OPTIMIZE lodlog_op.pedido ZORDER BY (cliente_id, status_pedido)")
print("Otimização concluída.")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Contagens em lodlog_op
# MAGIC SELECT 'lodlog_op' AS schema, 'cliente'              AS tabela, COUNT(*) AS linhas FROM lodlog_op.cliente             UNION ALL
# MAGIC SELECT 'lodlog_op',           'veiculo',                        COUNT(*) FROM lodlog_op.veiculo              UNION ALL
# MAGIC SELECT 'lodlog_op',           'motorista',                      COUNT(*) FROM lodlog_op.motorista             UNION ALL
# MAGIC SELECT 'lodlog_op',           'centro_distribuicao',            COUNT(*) FROM lodlog_op.centro_distribuicao   UNION ALL
# MAGIC SELECT 'lodlog_op',           'pedido',                         COUNT(*) FROM lodlog_op.pedido                UNION ALL
# MAGIC SELECT 'lodlog_op',           'entrega',                        COUNT(*) FROM lodlog_op.entrega;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Contagens em lodlog_dw
# MAGIC SELECT 'lodlog_dw' AS schema, 'dim_tempo'               AS tabela, COUNT(*) AS linhas FROM lodlog_dw.dim_tempo                UNION ALL
# MAGIC SELECT 'lodlog_dw',           'dim_cat_atraso',                    COUNT(*) FROM lodlog_dw.dim_cat_atraso           UNION ALL
# MAGIC SELECT 'lodlog_dw',           'dim_cliente',                       COUNT(*) FROM lodlog_dw.dim_cliente              UNION ALL
# MAGIC SELECT 'lodlog_dw',           'dim_veiculo',                       COUNT(*) FROM lodlog_dw.dim_veiculo              UNION ALL
# MAGIC SELECT 'lodlog_dw',           'dim_motorista',                     COUNT(*) FROM lodlog_dw.dim_motorista            UNION ALL
# MAGIC SELECT 'lodlog_dw',           'dim_centro_distribuicao',           COUNT(*) FROM lodlog_dw.dim_centro_distribuicao  UNION ALL
# MAGIC SELECT 'lodlog_dw',           'fato_entregas',                     COUNT(*) FROM lodlog_dw.fato_entregas;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Validar grain e anomalias do fato
# MAGIC SELECT
# MAGIC   COUNT(*)                        AS total_linhas,
# MAGIC   COUNT(DISTINCT entrega_id)      AS entrega_id_unicos,
# MAGIC   COUNT(*) - COUNT(DISTINCT entrega_id) AS duplicatas_entrega_id,
# MAGIC   SUM(CASE WHEN distancia_km    < 0 THEN 1 ELSE 0 END) AS neg_distancia,
# MAGIC   SUM(CASE WHEN peso_total_kg   < 0 THEN 1 ELSE 0 END) AS neg_peso,
# MAGIC   SUM(CASE WHEN custo_combustivel < 0 THEN 1 ELSE 0 END) AS neg_custo,
# MAGIC   SUM(CASE WHEN minutos_atraso > 1000 OR minutos_atraso < -480 THEN 1 ELSE 0 END) AS outliers_atraso,
# MAGIC   SUM(CASE WHEN sk_cliente > 200 THEN 1 ELSE 0 END) AS fk_quebrada_cliente
# MAGIC FROM lodlog_dw.fato_entregas;

# COMMAND ----------

# MAGIC %md
# MAGIC ### Setup Concluído!
# MAGIC
# MAGIC **Anomalias propositais em `fato_entregas` (para Parte 4 do LAB):**
# MAGIC - ~100 linhas duplicadas por `entrega_id` (mesmo pedido, custo levemente diferente)
# MAGIC - ~50 linhas com valores negativos (`distancia_km`, `peso_total_kg` ou `custo_combustivel`)
# MAGIC - ~30 linhas com outliers em `minutos_atraso` (> 1.000 min ou adiantamento < −480 min)
# MAGIC - ~50 linhas com FK quebrada (`sk_cliente` 201–300 não existem em `dim_cliente`)
