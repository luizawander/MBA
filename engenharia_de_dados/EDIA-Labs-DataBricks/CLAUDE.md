# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Educational course repository for **EDIA** (Engenharia de Dados para Inteligência Artificial), a graduate-level Data Engineering program. All labs use a fictional logistics company — **LODLog Transportes e Distribuição S.A.** — as the running business case.

This is **not a production codebase**. There are no build pipelines, package managers, or test suites. All lab work executes directly in **Databricks Community Edition** via the web UI.

## Repository Structure

```
Labs/
├── LAB1.md / LAB1.html    # Data Ecosystem Mapping (no code)
├── LAB2.md / LAB2.html    # ER & Star Schema modeling (no code)
├── LAB3.md / LAB3.html    # Advanced SQL + data prep in Databricks
├── LAB4.md / LAB4.html    # MLOps & Medallion architecture (no code)
├── lodlog_modelo_dados.sql # Complete schema: operational ER + Star Schema
└── lodlog_lab3_seed.py     # Synthetic data generator for Databricks
Suporte LODLog.ipynb        # Cleanup/support notebook
```

## How to Run Lab 3 (Only Executable Lab)

1. Import `lodlog_lab3_seed.py` as a notebook into Databricks Community Edition
2. Run all cells — creates `lodlog` database with seed data
3. Students write SQL/Python queries in their own notebook against `lodlog.fato_entregas` and related tables

No CLI execution; Databricks Community Edition is the only runtime.

## Data Architecture

### Two-Layer Schema Design

**`lodlog_op`** — Operational layer (3NF, transactional):
- Domains: `cliente/endereco_cliente/contrato`, `veiculo/motorista/manutencao/telemetria`, `centro_distribuicao/produto/estoque/movimentacao_estoque`, `pedido/item_pedido/entrega`
- `telemetria` is partitioned by `data_evento` (high-frequency IoT data)

**`lodlog_dw`** — Analytical layer (Star Schema for BI/ML):
- Fact: `fato_entregas` (~50k rows, binary ML target `indicador_atraso`)
- Dims: `dim_tempo` (SK = YYYYMMDD integer), `dim_cliente`, `dim_veiculo`, `dim_motorista` (SCD Type 2), `dim_centro_distribuicao` (SCD Type 1)

All tables use `USING DELTA`. High-cardinality columns use `ZORDER BY`.

### Hard rules
- Always update the `lodlog_dw` in a connected and coherent manner to the `lodlog_op`, if necessary, make the changes in the `lodlog_op` first.

### SCD Type 2 Pattern
`dim_cliente`, `dim_veiculo`, `dim_motorista` track history via `data_inicio_vigencia`, `data_fim_vigencia`, `flag_registro_atual`.

### Seed Data — Intentional Anomalies in `fato_entregas`
`lodlog_lab3_seed.py` injects 230 anomalous rows into 49,770 clean rows, for Lab 3 data quality exercises:
- 100 duplicate `pedido_id` rows
- 50 rows with negative `distancia_km`, `peso_kg`, or `custo_combustivel`
- 30 statistical outliers (impossible delays/advances)
- 50 rows with orphaned FKs (`sk_cliente` 201–300, which have no matching dim row)

## Databricks SQL Patterns Used

- Spark SQL dialect throughout (not standard PostgreSQL/MySQL)
- Window functions: `OVER (PARTITION BY ... ORDER BY ...)`, `ROWS BETWEEN`
- `CREATE VIEW vw_features_ml` pattern for ML feature engineering
- Rolling aggregates for ML features (e.g., `historico_atrasos_7d`)
- Data quality detection via `GROUP BY ... HAVING COUNT(*) > 1`, `LEFT JOIN ... WHERE IS NULL`, percentile/Z-score outlier queries

## Lab Content Summary

| Lab | Topic | Executable |
|-----|-------|-----------|
| LAB1 | Data ecosystem mapping, 5Vs, IaaS/PaaS/SaaS | No |
| LAB2 | ER modeling (3NF), Star Schema design, DDL | No |
| LAB3 | Window functions, feature engineering, data quality SQL | Yes (Databricks) |
| LAB4 | Medallion architecture, MLOps pipeline, LGPD compliance | No |

## Language

All course content, SQL identifiers, and documentation are in **Brazilian Portuguese**.
