CREATE TABLE IF NOT EXISTS lodlog_dw.dim_tempo (
  sk_tempo          INT      NOT NULL PRIMARY KEY,  -- ex. 20250714 (YYYYMMDD)
  data_completa     DATE     NOT NULL,
  dia               SMALLINT NOT NULL,  -- 1-31
  mes               SMALLINT NOT NULL,  -- 1-12
  ano               SMALLINT NOT NULL,
  trimestre         SMALLINT NOT NULL,  -- 1-4
  semana_do_ano     SMALLINT NOT NULL,  -- 1-53
  dia_da_semana     SMALLINT NOT NULL,  -- 1=Seg ... 7=Dom
  nome_dia_semana   TEXT     NOT NULL,
  nome_mes          TEXT     NOT NULL,
  flag_feriado      BOOLEAN  NOT NULL,
  flag_fim_semana   BOOLEAN  NOT NULL,
  descricao_feriado TEXT
);
COMMENT ON TABLE lodlog_dw.dim_tempo IS 'Dimensão tempo — carga feita via script Python (1 linha/dia)';

-- DIM_CLIENTE — SCD Tipo 2 (histórico de mudanças de segmento/SLA)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_cliente (
  sk_cliente                 BIGSERIAL    NOT NULL PRIMARY KEY,
  cliente_id                 BIGINT       NOT NULL,  -- chave natural (OLTP)
  cnpj                       TEXT         NOT NULL,
  razao_social               TEXT         NOT NULL,
  segmento                   TEXT         NOT NULL,
  municipio                  TEXT         NOT NULL,
  uf                         TEXT         NOT NULL,
  regiao                     TEXT         NOT NULL,  -- Valores: 'Norte','Nordeste','Centro-Oeste','Sudeste','Sul'
  tempo_relacionamento_meses INT          NOT NULL,  -- >= 0
  sla_contratual_pct         DECIMAL(5,2),
  -- campos SCD Tipo 2: rastreiam versões históricas do registro
  data_inicio_vigencia       DATE         NOT NULL,
  data_fim_vigencia          DATE,                   -- NULL = registro atual
  flag_registro_atual        BOOLEAN      NOT NULL,
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id)
);

-- DIM_VEICULO — SCD Tipo 2 (hodômetro e status mudam)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_veiculo (
  sk_veiculo           BIGSERIAL     NOT NULL PRIMARY KEY,
  veiculo_id           BIGINT        NOT NULL,
  placa                TEXT          NOT NULL,
  modelo               TEXT          NOT NULL,
  fabricante           TEXT,
  ano_fabricacao       SMALLINT      NOT NULL,
  tipo                 TEXT          NOT NULL,
  capacidade_kg        DECIMAL(10,2) NOT NULL,
  faixa_capacidade     TEXT          NOT NULL,  -- Valores: 'Até 1t','1-5t','5-15t','Acima 15t'
  data_inicio_vigencia DATE          NOT NULL,
  data_fim_vigencia    DATE,
  flag_registro_atual  BOOLEAN       NOT NULL,
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id)
);

-- DIM_MOTORISTA — SCD Tipo 2 (score e experiência evoluem)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_motorista (
  sk_motorista         BIGSERIAL    NOT NULL PRIMARY KEY,
  motorista_id         BIGINT       NOT NULL,
  nome_completo        TEXT         NOT NULL,
  categoria_cnh        TEXT         NOT NULL,
  tempo_empresa_meses  INT          NOT NULL,  -- >= 0
  faixa_experiencia    TEXT         NOT NULL,  -- Valores: 'Júnior','Pleno','Sênior'
  score_seguranca      DECIMAL(5,2),            -- NULL ou 0-100
  data_inicio_vigencia DATE         NOT NULL,
  data_fim_vigencia    DATE,
  flag_registro_atual  BOOLEAN      NOT NULL,
  FOREIGN KEY (motorista_id) REFERENCES lodlog_op.motorista(motorista_id)
);

-- DIM_CENTRO_DISTRIBUICAO — SCD Tipo 1 (atualiza no lugar, sem histórico)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_centro_distribuicao (
  sk_cd         BIGSERIAL     NOT NULL PRIMARY KEY,
  cd_id         BIGINT        NOT NULL,  -- chave natural (OLTP)
  codigo        TEXT          NOT NULL,
  nome          TEXT          NOT NULL,
  municipio     TEXT          NOT NULL,
  uf            TEXT          NOT NULL,
  regiao        TEXT          NOT NULL,  -- Valores: 'Norte','Nordeste','Centro-Oeste','Sudeste','Sul'
  capacidade_m3 DECIMAL(10,2) NOT NULL,
  latitude      DECIMAL(9,6),
  longitude     DECIMAL(9,6),
  FOREIGN KEY (cd_id) REFERENCES lodlog_op.centro_distribuicao(cd_id)
);

-- ⭐ NOVA DIMENSÃO v2 — DIM_CATEGORIA_ATRASO (minidimensão Kimball)
-- Categoria derivada de minutos_atraso.
-- Minidimensão = boa prática para atributos de baixa cardinalidade
-- usados em filtros/agrupamentos de BI. SCD Tipo 1 (estável).
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_cat_atraso (
  sk_cat_atraso        INT      NOT NULL PRIMARY KEY,
  categoria            TEXT     NOT NULL,  -- 'Adiantado' | 'No Prazo' | 'Atraso Leve' | 'Atraso Moderado' | 'Atraso Crítico'
  descricao            TEXT     NOT NULL,  -- texto explicativo
  limite_inferior_min  INT      NOT NULL,  -- ex. -9999, 0, 1, 61, 241
  limite_superior_min  INT,                -- ex. 0, 0, 60, 240, NULL (=infinito)
  sla_violado          BOOLEAN  NOT NULL,  -- TRUE se a categoria viola SLA contratual
  ordem                SMALLINT NOT NULL   -- 1..5 para ordenar gráficos
);
COMMENT ON TABLE lodlog_dw.dim_cat_atraso IS 'Minidimensão (Kimball) para a categoria de atraso. SCD Tipo 1 (valores estáveis).';

-- FATO_ENTREGAS — tabela central do Star Schema
-- 1 linha por entrega realizada
-- PK: entrega_id (dimensão degenerada — grain: 1 entrega por linha)
-- indicador_atraso = variável-alvo (target) do modelo de classificação
CREATE TABLE IF NOT EXISTS lodlog_dw.fato_entregas (
  sk_entrega              BIGSERIAL     NOT NULL,  -- surrogate key (não é a PK)
  -- Surrogate keys das dimensões
  sk_data                 INT           NOT NULL,  -- FK → dim_tempo
  sk_cliente              BIGINT        NOT NULL,  -- FK → dim_cliente
  sk_cd_origem            BIGINT        NOT NULL,  -- FK → dim_centro_distribuicao
  sk_veiculo              BIGINT        NOT NULL,  -- FK → dim_veiculo
  sk_motorista            BIGINT        NOT NULL,  -- FK → dim_motorista
  sk_cat_atraso           INT           NOT NULL,  -- FK → dim_cat_atraso  ⭐ NOVO v2
  -- Chaves naturais degeneradas (sem dimensão própria, para rastreabilidade)
  entrega_id              BIGINT        NOT NULL PRIMARY KEY,  -- PK: grain = 1 entrega
  pedido_id               BIGINT        NOT NULL,
  -- Atributos de data/hora
  data_entrega            DATE,                    -- data da entrega (conveniência)
  hora_saida              TIMESTAMP,               -- timestamp completo de saída
  -- Métricas aditivas (somáveis em qualquer combinação de dimensões)
  quantidade_volumes      INT           NOT NULL,  -- >= 0
  peso_total_kg           DECIMAL(10,2) NOT NULL,  -- > 0
  distancia_km            DECIMAL(10,2) NOT NULL,  -- > 0
  tempo_estimado_min      INT           NOT NULL,  -- > 0
  tempo_real_min          INT,
  custo_combustivel       DECIMAL(12,2) NOT NULL,
  custo_pedagio           DECIMAL(12,2) NOT NULL,
  valor_frete             DECIMAL(12,2) NOT NULL,  -- > 0
  multa_atraso            DECIMAL(12,2) NOT NULL,
  -- Métricas derivadas
  minutos_atraso          INT           NOT NULL,  -- 0 = no prazo | >0 = quantos min atrasou
  indicador_atraso        SMALLINT      NOT NULL,  -- 0 = pontual | 1 = atrasado  ← TARGET ML
  temperatura_media_motor DECIMAL(6,2),            -- temperatura média do motor (°C)
  -- ⭐ NOVO v2 — KPI replicado do operacional
  kpi_cat_atraso          TEXT          NOT NULL,  -- 'Adiantado' | 'No Prazo' | 'Atraso Leve' | 'Atraso Moderado' | 'Atraso Crítico'
  FOREIGN KEY (sk_data)      REFERENCES lodlog_dw.dim_tempo(sk_tempo),
  FOREIGN KEY (sk_cliente)   REFERENCES lodlog_dw.dim_cliente(sk_cliente),
  FOREIGN KEY (sk_cd_origem) REFERENCES lodlog_dw.dim_centro_distribuicao(sk_cd),
  FOREIGN KEY (sk_veiculo)   REFERENCES lodlog_dw.dim_veiculo(sk_veiculo),
  FOREIGN KEY (sk_motorista) REFERENCES lodlog_dw.dim_motorista(sk_motorista),
  FOREIGN KEY (sk_cat_atraso) REFERENCES lodlog_dw.dim_cat_atraso(sk_cat_atraso)
);
COMMENT ON TABLE lodlog_dw.fato_entregas IS 'Fato entregas — granularidade: 1 linha por entrega. indicador_atraso é o target do modelo de predição. v2 inclui sk_cat_atraso (FK) e kpi_cat_atraso (atributo replicado do op).';
