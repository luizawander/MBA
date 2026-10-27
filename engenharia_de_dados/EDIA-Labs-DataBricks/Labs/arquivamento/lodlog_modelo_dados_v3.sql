-- ================================================================
-- LODLog Transportes e Distribuição S.A.
-- Modelo de Dados Completo — LAB 2 (Scaffold / Gabarito) — VERSÃO 2
-- Databricks SQL · Delta Lake · Community Edition compatible
-- ================================================================
-- COMO USAR:
--   1. Abra um notebook SQL no Databricks (Language: SQL)
--   2. Cole este script inteiro em uma célula  OU
--      divida cada bloco em células separadas (recomendado)
--   3. Execute de cima para baixo
--
-- ════════════════════════════════════════════════════════════════
-- O QUE MUDA NA v2 (junho/2026)
-- ════════════════════════════════════════════════════════════════
-- 1) A tabela `lodlog_op.entrega` está propositalmente em 2FN.
--    Ela carrega colunas redundantes (dados de cliente, veículo,
--    motorista, CD) que são DEPENDÊNCIAS TRANSITIVAS — ou seja,
--    a tabela NÃO está em 3FN. Os alunos devem normalizar para
--    3FN como exercício do LAB 2 (Atividade 2.2).
--
-- 2) Nova coluna `kpi_cat_atraso` na tabela `entrega`
--    (operacional) e na `fato_entregas` (DW). Esse atributo é
--    uma classificação derivada de `minutos_atraso`:
--      'Adiantado'       (< 0)
--      'No Prazo'        (== 0)
--      'Atraso Leve'     (1 a 60)
--      'Atraso Moderado' (61 a 240)
--      'Atraso Crítico'  (> 240)
--
-- 3) Nova mini-dimensão `lodlog_dw.dim_cat_atraso` no DW.
--    É a "casa" do KPI no Star Schema — boa prática de modelagem
--    dimensional (Kimball: minidimension para atributos de baixa
--    cardinalidade usados em filtros de BI).
--
-- Diferenças vs PostgreSQL:
--   · SCHEMA → DATABASE  (Databricks Community usa Hive Metastore)
--   · SERIAL/BIGSERIAL → BIGINT  (IDs explícitos nos INSERTs)
--   · REFERENCES → comentários informativos (Delta não força FKs)
--   · CREATE INDEX → OPTIMIZE ... ZORDER BY
--   · VARCHAR/CHAR → STRING
--   · x::INT → CAST(x AS INT)
--   · CHECK constraints → REMOVED (not supported in this Databricks version)
--   · NOT NULL é ENFORCED pelo Delta Lake
-- ================================================================


-- ================================================================
-- CÉLULA 1 — Criar databases (equivalente a schemas)
-- ================================================================

CREATE DATABASE IF NOT EXISTS lodlog_op
  COMMENT 'LODLog — modelo operacional (ER 3FN)';

CREATE DATABASE IF NOT EXISTS lodlog_dw
  COMMENT 'LODLog — modelo analítico (Star Schema DW/ML)';


-- ================================================================
-- CÉLULA 2 — SCHEMA OPERACIONAL (lodlog_op)
-- Domínio CLIENTE
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.cliente (
  cliente_id    BIGINT    NOT NULL PRIMARY KEY,  -- PK (gerado na aplicação) PRIMARY KEY
  cnpj          STRING    NOT NULL,  -- UNIQUE: não duplicar CNPJ
  razao_social  STRING    NOT NULL,
  nome_fantasia STRING,
  segmento      STRING    NOT NULL,  -- Valores: 'Varejista','Industrial','Atacadista','Outro'
  email         STRING,
  telefone      STRING,
  data_cadastro DATE      NOT NULL,
  ativo         BOOLEAN   NOT NULL
)
USING DELTA
COMMENT 'Cadastro de clientes ativos da LODLog';

-- Separar endereço evita dependência transitiva (3FN):
-- bairro/municipio/uf dependem do CEP, não do cliente_id
CREATE TABLE IF NOT EXISTS lodlog_op.endereco_cliente (
  endereco_id BIGINT  NOT NULL PRIMARY KEY,
  cliente_id  BIGINT  NOT NULL,  -- FK → lodlog_op.cliente.cliente_id
  logradouro  STRING  NOT NULL,
  numero      STRING,
  complemento STRING,
  bairro      STRING  NOT NULL,
  municipio   STRING  NOT NULL,
  uf          STRING  NOT NULL,
  cep         STRING  NOT NULL,
  latitude    DECIMAL(9,6),
  longitude   DECIMAL(9,6),
  tipo        STRING  NOT NULL,  -- Valores: 'Entregas','Cobrança','Principal'
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS lodlog_op.contrato (
  contrato_id          BIGINT      NOT NULL PRIMARY KEY,
  cliente_id           BIGINT      NOT NULL,  -- FK → cliente
  numero_contrato      STRING      NOT NULL,
  data_inicio          DATE        NOT NULL,
  data_fim             DATE,
  sla_pontualidade_pct DECIMAL(5,2) NOT NULL,  -- 0-100
  multa_atraso_pct     DECIMAL(5,2) NOT NULL,  -- >= 0
  status               STRING      NOT NULL,    -- Valores: 'Ativo','Encerrado','Suspenso'
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id)
)
USING DELTA;


-- ================================================================
-- CÉLULA 3 — Domínio FROTA
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.veiculo (
  veiculo_id     BIGINT      NOT NULL PRIMARY KEY,
  placa          STRING      NOT NULL,  -- UNIQUE
  modelo         STRING      NOT NULL,
  fabricante     STRING,
  ano_fabricacao SMALLINT    NOT NULL,  -- >= 1990
  tipo           STRING      NOT NULL,  -- Valores: 'Leve','Médio','Pesado'
  capacidade_kg  DECIMAL(10,2) NOT NULL,  -- > 0
  hodometro_km   DECIMAL(10,0) NOT NULL,  -- >= 0
  data_aquisicao DATE,
  status         STRING      NOT NULL  -- Valores: 'Disponível','Em Rota','Manutenção','Inativo'
)
USING DELTA;

CREATE TABLE IF NOT EXISTS lodlog_op.motorista (
  motorista_id     BIGINT   NOT NULL PRIMARY KEY,
  cpf              STRING   NOT NULL,  -- UNIQUE
  nome_completo    STRING   NOT NULL,
  cnh              STRING   NOT NULL,  -- UNIQUE
  categoria_cnh    STRING   NOT NULL,  -- Valores: 'A','B','C','D','E','AB','AC','AD','AE'
  validade_cnh     DATE     NOT NULL,
  data_admissao    DATE     NOT NULL,
  score_seguranca  DECIMAL(5,2),  -- NULL ou 0-100
  status           STRING   NOT NULL  -- Valores: 'Ativo','Afastado','Desligado'
)
USING DELTA;

CREATE TABLE IF NOT EXISTS lodlog_op.manutencao (
  manutencao_id   BIGINT        NOT NULL PRIMARY KEY,
  veiculo_id      BIGINT        NOT NULL,  -- FK → veiculo
  tipo            STRING        NOT NULL,  -- Valores: 'Preventiva','Corretiva','Preditiva'
  data_abertura   TIMESTAMP     NOT NULL,
  data_conclusao  TIMESTAMP,
  km_no_momento   DECIMAL(10,0) NOT NULL,  -- >= 0
  custo_total     DECIMAL(12,2),  -- NULL ou >= 0
  descricao       STRING,
  status          STRING        NOT NULL,  -- Valores: 'Aberta','Em Execução','Concluída'
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id)
)
USING DELTA;

-- Alta frequência: ~864k eventos/dia — particionada por data para eficiência
CREATE TABLE IF NOT EXISTS lodlog_op.telemetria (
  telemetria_id         BIGINT        NOT NULL PRIMARY KEY,
  veiculo_id            BIGINT        NOT NULL,  -- FK → veiculo
  timestamp_evento      TIMESTAMP     NOT NULL,
  data_evento           DATE          NOT NULL,  -- Coluna de partição (DATE extraído de timestamp_evento)
  latitude              DECIMAL(9,6)  NOT NULL,
  longitude             DECIMAL(9,6)  NOT NULL,
  velocidade_kmh        DECIMAL(6,2)  NOT NULL,  -- 0-200
  rpm_motor             INT,  -- NULL ou 0-8000
  temperatura_motor_c   DECIMAL(6,2),  -- NULL ou -50 a 200
  nivel_combustivel_pct DECIMAL(5,2),  -- NULL ou 0-100
  peso_carga_kg         DECIMAL(10,2),  -- NULL ou >= 0
  hodometro_km          DECIMAL(10,0),
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id)
)
USING DELTA
CLUSTER BY (data_evento, veiculo_id)
COMMENT 'Eventos IoT da frota (~864k/dia). Particionar por data é obrigatório em produção.';


-- ================================================================
-- CÉLULA 4 — Domínio ESTOQUE
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.centro_distribuicao (
  cd_id         BIGINT        NOT NULL PRIMARY KEY,
  codigo        STRING        NOT NULL,  -- UNIQUE: ex. 'CD-CAMPINAS'
  nome          STRING        NOT NULL,
  municipio     STRING        NOT NULL,
  uf            STRING        NOT NULL,
  cep           STRING        NOT NULL,
  latitude      DECIMAL(9,6)  NOT NULL,
  longitude     DECIMAL(9,6)  NOT NULL,
  capacidade_m3 DECIMAL(10,2) NOT NULL,  -- > 0
  ativo         BOOLEAN       NOT NULL
)
USING DELTA;

CREATE TABLE IF NOT EXISTS lodlog_op.produto (
  produto_id         BIGINT        NOT NULL PRIMARY KEY,
  sku                STRING        NOT NULL,  -- UNIQUE
  nome               STRING        NOT NULL,
  categoria          STRING        NOT NULL,
  peso_unitario_kg   DECIMAL(10,3) NOT NULL,  -- > 0
  volume_unitario_m3 DECIMAL(10,4),  -- NULL ou > 0
  ativo              BOOLEAN       NOT NULL
)
USING DELTA;

-- Posição atual do estoque por combinação (cd_id, produto_id)
CREATE TABLE IF NOT EXISTS lodlog_op.estoque (
  estoque_id            BIGINT NOT NULL PRIMARY KEY,
  cd_id                 BIGINT NOT NULL,  -- FK → centro_distribuicao
  produto_id            BIGINT NOT NULL,  -- FK → produto
  quantidade_disponivel INT    NOT NULL,  -- >= 0
  quantidade_reservada  INT    NOT NULL,  -- >= 0
  posicao_galpao        STRING,
  ultima_atualizacao    TIMESTAMP NOT NULL,
  FOREIGN KEY (cd_id) REFERENCES lodlog_op.centro_distribuicao(cd_id),
  FOREIGN KEY (produto_id) REFERENCES lodlog_op.produto(produto_id)
)
USING DELTA;

-- Log de cada movimentação — estoque atual é derivado desse histórico
CREATE TABLE IF NOT EXISTS lodlog_op.movimentacao_estoque (
  movimentacao_id BIGINT    NOT NULL PRIMARY KEY,
  estoque_id      BIGINT    NOT NULL,  -- FK → estoque
  tipo_mov        STRING    NOT NULL,  -- Valores: 'Entrada','Saída','Reserva','Liberação','Ajuste'
  quantidade      INT       NOT NULL,
  timestamp_mov   TIMESTAMP NOT NULL,
  referencia      STRING,              -- pedido_id, NF, etc.
  observacao      STRING,
  FOREIGN KEY (estoque_id) REFERENCES lodlog_op.estoque(estoque_id)
)
USING DELTA;


-- ================================================================
-- CÉLULA 5 — Domínio OPERAÇÃO (Pedido / Entregas)
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.pedido (
  pedido_id           BIGINT    NOT NULL PRIMARY KEY,
  numero_pedido       STRING    NOT NULL,  -- UNIQUE
  cliente_id          BIGINT    NOT NULL,  -- FK → cliente
  contrato_id         BIGINT,             -- FK → contrato (opcional)
  cd_origem_id        BIGINT    NOT NULL,  -- FK → centro_distribuicao
  endereco_destino_id BIGINT    NOT NULL,  -- FK → endereco_cliente
  data_pedido         TIMESTAMP NOT NULL,
  prazo_entrega       TIMESTAMP NOT NULL,  -- > data_pedido
  prioridade          STRING    NOT NULL,  -- Valores: 'Baixa','Normal','Alta','Urgente'
  status_pedido       STRING    NOT NULL,  -- Valores: 'Aberto','Em Separação','Despachado','Entregue','Cancelado'
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id),
  FOREIGN KEY (contrato_id) REFERENCES lodlog_op.contrato(contrato_id),
  FOREIGN KEY (cd_origem_id) REFERENCES lodlog_op.centro_distribuicao(cd_id),
  FOREIGN KEY (endereco_destino_id) REFERENCES lodlog_op.endereco_cliente(endereco_id)
)
USING DELTA;

-- Tabela de associação Pedido ↔ Produto (N:M) com atributos próprios
CREATE TABLE IF NOT EXISTS lodlog_op.item_pedido (
  item_id       BIGINT        NOT NULL PRIMARY KEY,
  pedido_id     BIGINT        NOT NULL,  -- FK → pedido
  produto_id    BIGINT        NOT NULL,  -- FK → produto
  quantidade    INT           NOT NULL,  -- > 0
  peso_total_kg DECIMAL(10,2) NOT NULL,  -- > 0
  FOREIGN KEY (pedido_id) REFERENCES lodlog_op.pedido(pedido_id),
  FOREIGN KEY (produto_id) REFERENCES lodlog_op.produto(produto_id)
)
USING DELTA;

-- ════════════════════════════════════════════════════════════════
-- TABELA ENTREGA — PROPOSITALMENTE EM 2FN
-- ════════════════════════════════════════════════════════════════
-- Esta tabela carrega DEPENDÊNCIAS TRANSITIVAS: dados de
-- cliente, veículo, motorista e CD estão duplicados aqui.
-- A PK é simples (entrega_id) — então está em 2FN
-- (1FN + sem dependências parciais), mas tem dependências
-- transitivas (X → Y → Z) que violam a 3FN.
--
-- Exercício LAB 2 — Atividade 2.2: decompor até 3FN.
-- ════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS lodlog_op.entrega (
  -- PK + chaves estrangeiras (originais)
  entrega_id            BIGINT        NOT NULL PRIMARY KEY,  -- PK
  pedido_id             BIGINT        NOT NULL,  -- FK → pedido
  veiculo_id            BIGINT        NOT NULL,  -- FK → veiculo
  motorista_id          BIGINT        NOT NULL,  -- FK → motorista

  -- ▓▓▓ DADOS REDUNDANTES DO CLIENTE (dependência transitiva) ▓▓▓
  -- cliente_id determina estes campos. Devem ser removidos na 3FN.
  cliente_id            BIGINT        NOT NULL,  -- FK → cliente
  cliente_cnpj          STRING        NOT NULL,  -- redundante
  cliente_razao_social  STRING        NOT NULL,  -- redundante
  cliente_segmento      STRING        NOT NULL,  -- redundante

  -- ▓▓▓ DADOS REDUNDANTES DO VEÍCULO (dependência transitiva) ▓▓▓
  veiculo_placa         STRING        NOT NULL,  -- redundante
  veiculo_modelo        STRING        NOT NULL,  -- redundante
  veiculo_fabricante    STRING,                  -- redundante
  veiculo_capacidade_kg DECIMAL(10,2) NOT NULL,  -- redundante

  -- ▓▓▓ DADOS REDUNDANTES DO MOTORISTA (dependência transitiva) ▓▓▓
  motorista_nome        STRING        NOT NULL,  -- redundante
  motorista_cnh         STRING        NOT NULL,  -- redundante
  motorista_categoria   STRING        NOT NULL,  -- redundante

  -- ▓▓▓ DADOS REDUNDANTES DO CD DE ORIGEM (dependência transitiva) ▓▓▓
  cd_origem_id          BIGINT        NOT NULL,  -- FK → centro_distribuicao
  cd_origem_codigo      STRING        NOT NULL,  -- redundante
  cd_origem_nome        STRING        NOT NULL,  -- redundante
  cd_origem_uf          STRING        NOT NULL,  -- redundante

  -- Datas e medidas (corretas, sem redundância)
  data_saida            TIMESTAMP     NOT NULL,
  data_entrega_prevista TIMESTAMP     NOT NULL,
  data_entrega_real     TIMESTAMP,
  distancia_km          DECIMAL(10,2) NOT NULL,  -- > 0
  custo_combustivel     DECIMAL(12,2),           -- NULL ou >= 0
  custo_pedagio         DECIMAL(12,2),           -- NULL ou >= 0
  valor_frete           DECIMAL(12,2) NOT NULL,  -- > 0
  multa_atraso          DECIMAL(12,2),           -- NULL ou >= 0
  status_entrega        STRING        NOT NULL,  -- Valores: 'Pendente','Em Rota','Entregue','Ocorrência','Devolvido'

  -- ⭐ NOVO ATRIBUTO v2 — KPI de pontualidade
  -- Derivado de minutos_atraso (calculado na aplicação/ETL).
  -- Valores: 'Adiantado' | 'No Prazo' | 'Atraso Leve' | 'Atraso Moderado' | 'Atraso Crítico'
  kpi_cat_atraso  STRING        NOT NULL,
  FOREIGN KEY (pedido_id) REFERENCES lodlog_op.pedido(pedido_id),
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id),
  FOREIGN KEY (motorista_id) REFERENCES lodlog_op.motorista(motorista_id),
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id),
  FOREIGN KEY (cd_origem_id) REFERENCES lodlog_op.centro_distribuicao(cd_id)
)
USING DELTA
COMMENT 'Tabela ENTREGA em 2FN (proposital). Tem dependências transitivas — alunos devem normalizar para 3FN. Inclui kpi_cat_atraso (NOVO v2).';


-- ================================================================
-- CÉLULA 6 — SCHEMA ANALÍTICO (lodlog_dw) — Star Schema
-- Granularidade da fato: 1 linha por entrega realizada
-- ================================================================

-- DIM_TEMPO — SK no formato YYYYMMDD (INT), sem IDENTITY
-- Motivo: o valor da SK é também o identificador de negócio (a data)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_tempo (
  sk_tempo         INT     NOT NULL PRIMARY KEY,  -- PK: ex. 20250714 (YYYYMMDD)
  data_completa    DATE    NOT NULL,
  dia              SMALLINT NOT NULL,  -- 1-31
  mes              SMALLINT NOT NULL,  -- 1-12
  ano              SMALLINT NOT NULL,
  trimestre        SMALLINT NOT NULL,  -- 1-4
  semana_do_ano    SMALLINT NOT NULL,  -- 1-53
  dia_da_semana    SMALLINT NOT NULL,  -- 1=Seg ... 7=Dom
  nome_dia_semana  STRING  NOT NULL,
  nome_mes         STRING  NOT NULL,
  flag_feriado     BOOLEAN NOT NULL,
  flag_fim_semana  BOOLEAN NOT NULL,
  descricao_feriado STRING
)
USING DELTA
COMMENT 'Dimensão tempo — carga feita via script Python (1 linha/dia)';

-- DIM_CLIENTE — SCD Tipo 2 (histórico de mudanças de segmento/SLA)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_cliente (
  sk_cliente                 BIGINT  NOT NULL PRIMARY KEY,  -- PK surrogate
  cliente_id                 BIGINT  NOT NULL,  -- chave natural (OLTP)
  cnpj                       STRING  NOT NULL,
  razao_social               STRING  NOT NULL,
  segmento                   STRING  NOT NULL,
  municipio                  STRING  NOT NULL,
  uf                         STRING  NOT NULL,
  regiao                     STRING  NOT NULL,  -- Valores: 'Norte','Nordeste','Centro-Oeste','Sudeste','Sul'
  tempo_relacionamento_meses INT     NOT NULL,  -- >= 0
  sla_contratual_pct         DECIMAL(5,2),
  -- campos SCD Tipo 2: rastreiam versões históricas do registro
  data_inicio_vigencia       DATE    NOT NULL,
  data_fim_vigencia          DATE,                -- NULL = registro atual
  flag_registro_atual        BOOLEAN NOT NULL,
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id)
)
USING DELTA;

-- DIM_VEICULO — SCD Tipo 2 (hodômetro e status mudam)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_veiculo (
  sk_veiculo           BIGINT      NOT NULL PRIMARY KEY,
  veiculo_id           BIGINT      NOT NULL,
  placa                STRING      NOT NULL,
  modelo               STRING      NOT NULL,
  fabricante           STRING,
  ano_fabricacao       SMALLINT    NOT NULL,
  tipo                 STRING      NOT NULL,
  capacidade_kg        DECIMAL(10,2) NOT NULL,
  faixa_capacidade     STRING      NOT NULL,  -- Valores: 'Até 1t','1-5t','5-15t','Acima 15t'
  data_inicio_vigencia DATE        NOT NULL,
  data_fim_vigencia    DATE,
  flag_registro_atual  BOOLEAN     NOT NULL,
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id)
)
USING DELTA;

-- DIM_MOTORISTA — SCD Tipo 2 (score e experiência evoluem)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_motorista (
  sk_motorista         BIGINT   NOT NULL PRIMARY KEY,
  motorista_id         BIGINT   NOT NULL,
  nome_completo        STRING   NOT NULL,
  categoria_cnh        STRING   NOT NULL,
  tempo_empresa_meses  INT      NOT NULL,  -- >= 0
  faixa_experiencia    STRING   NOT NULL,  -- Valores: 'Júnior','Pleno','Sênior'
  score_seguranca      DECIMAL(5,2),  -- NULL ou 0-100
  data_inicio_vigencia DATE     NOT NULL,
  data_fim_vigencia    DATE,
  flag_registro_atual  BOOLEAN  NOT NULL,
  FOREIGN KEY (motorista_id) REFERENCES lodlog_op.motorista(motorista_id)
)
USING DELTA;

-- DIM_CENTRO_DISTRIBUICAO — SCD Tipo 1 (atualiza no lugar, sem histórico)
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_centro_distribuicao (
  sk_cd         BIGINT        NOT NULL PRIMARY KEY,
  cd_id         BIGINT        NOT NULL,  -- chave natural (OLTP)
  codigo        STRING        NOT NULL,
  nome          STRING        NOT NULL,
  municipio     STRING        NOT NULL,
  uf            STRING        NOT NULL,
  regiao        STRING        NOT NULL,  -- Valores: 'Norte','Nordeste','Centro-Oeste','Sudeste','Sul'
  capacidade_m3 DECIMAL(10,2) NOT NULL,
  latitude      DECIMAL(9,6),
  longitude     DECIMAL(9,6),
  FOREIGN KEY (cd_id) REFERENCES lodlog_op.centro_distribuicao(cd_id)
)
USING DELTA;

-- ⭐ NOVA DIMENSÃO v2 — DIM_CATEGORIA_ATRASO (minidimensão Kimball)
-- Categoria derivada de minutos_atraso.
-- Minidimensão = boa prática para atributos de baixa cardinalidade
-- usados em filtros/agrupamentos de BI. SCD Tipo 1 (estável).
CREATE TABLE IF NOT EXISTS lodlog_dw.dim_cat_atraso (
  sk_cat_atraso  INT     NOT NULL PRIMARY KEY,  -- PK surrogate
  categoria            STRING  NOT NULL,  -- 'Adiantado' | 'No Prazo' | 'Atraso Leve' | 'Atraso Moderado' | 'Atraso Crítico'
  descricao            STRING  NOT NULL,  -- texto explicativo
  limite_inferior_min  INT     NOT NULL,  -- ex. -9999, 0, 1, 61, 241
  limite_superior_min  INT,              -- ex. 0, 0, 60, 240, NULL (=infinito)
  sla_violado          BOOLEAN NOT NULL,  -- TRUE se a categoria viola SLA contratual
  ordem                SMALLINT NOT NULL  -- 1..5 para ordenar gráficos
)
USING DELTA
COMMENT 'Minidimensão (Kimball) para a categoria de atraso. SCD Tipo 1 (valores estáveis).';

-- FATO_ENTREGAS — tabela central do Star Schema
-- 1 linha por entrega realizada
-- indicador_atraso = variável-alvo (target) do modelo de classificação
CREATE TABLE IF NOT EXISTS lodlog_dw.fato_entregas (
  sk_entrega           BIGINT  NOT NULL,  -- surrogate key (PK migrada para pedido_id + hora_saida)
  -- Surrogate keys das dimensões
  sk_data              INT     NOT NULL,  -- FK → dim_tempo
  sk_cliente           BIGINT  NOT NULL,  -- FK → dim_cliente
  sk_cd_origem         BIGINT  NOT NULL,  -- FK → dim_centro_distribuicao
  sk_veiculo           BIGINT  NOT NULL,  -- FK → dim_veiculo
  sk_motorista         BIGINT  NOT NULL,  -- FK → dim_motorista
  sk_cat_atraso  INT     NOT NULL,  -- FK → dim_cat_atraso  ⭐ NOVO v2
  -- Chaves naturais degeneradas (sem dimensão própria, para rastreabilidade)
  entrega_id           BIGINT  NOT NULL PRIMARY KEY,  -- PK (dimensão degenerada — grain: 1 linha por entrega)
  pedido_id            BIGINT  NOT NULL,
  -- Atributos de data/hora
  data_entrega         DATE,               -- data da entrega (conveniência)
  hora_saida           TIMESTAMP,           -- timestamp completo de saída
-- Métricas aditivas (somáveis em qualquer combinação de dimensões)
  quantidade_volumes   INT           NOT NULL,  -- >= 0
  peso_total_kg        DECIMAL(10,2) NOT NULL,  -- > 0
  distancia_km         DECIMAL(10,2) NOT NULL,  -- > 0
  tempo_estimado_min   INT           NOT NULL,  -- > 0
  tempo_real_min       INT,
  custo_combustivel    DECIMAL(12,2) NOT NULL,
  custo_pedagio        DECIMAL(12,2) NOT NULL,
  valor_frete          DECIMAL(12,2) NOT NULL,  -- > 0
  multa_atraso         DECIMAL(12,2) NOT NULL,
-- Métricas derivadas
  minutos_atraso       INT     NOT NULL,  -- 0 = no prazo | >0 = quantos min atrasou
  indicador_atraso     SMALLINT NOT NULL,  -- 0 = pontual | 1 = atrasado  ← TARGET ML (valores: 0 ou 1)
  temperatura_media_motor DECIMAL(6,2),   -- temperatura média do motor (°C)
  -- ⭐ NOVO v2 — KPI replicado do operacional
  kpi_cat_atraso STRING  NOT NULL,  -- 'Adiantado' | 'No Prazo' | 'Atraso Leve' | 'Atraso Moderado' | 'Atraso Crítico'
  FOREIGN KEY (sk_data) REFERENCES lodlog_dw.dim_tempo(sk_tempo),
  FOREIGN KEY (sk_cliente) REFERENCES lodlog_dw.dim_cliente(sk_cliente),
  FOREIGN KEY (sk_cd_origem) REFERENCES lodlog_dw.dim_centro_distribuicao(sk_cd),
  FOREIGN KEY (sk_veiculo) REFERENCES lodlog_dw.dim_veiculo(sk_veiculo),
  FOREIGN KEY (sk_motorista) REFERENCES lodlog_dw.dim_motorista(sk_motorista),
  FOREIGN KEY (sk_cat_atraso) REFERENCES lodlog_dw.dim_cat_atraso(sk_cat_atraso)
)
USING DELTA
COMMENT 'Fato entregas — granularidade: 1 linha por entrega. indicador_atraso é o target do modelo de predição. v2 inclui sk_cat_atraso (FK) e kpi_cat_atraso (atributo replicado do op).';


-- ================================================================
-- CÉLULA 7 — ZORDER (otimização pós-carga)
-- ================================================================
-- NOTA: OPTIMIZE/ZORDER devem ser executados DEPOIS da carga.
-- O script de seed Python faz isso automaticamente.
-- ================================================================


-- ================================================================
-- CÉLULA 8 — Verificação final (execute após carga e ETL)
-- ================================================================

-- SHOW TABLES IN lodlog_op;
-- SHOW TABLES IN lodlog_dw;

-- SELECT 'lodlog_op.entrega' AS tabela, COUNT(*) AS linhas
-- FROM lodlog_op.entrega
-- WHERE kpi_cat_atraso IS NOT NULL;
-- -- Deve retornar ~50.000

-- SELECT 'lodlog_dw.dim_cat_atraso' AS tabela, COUNT(*) AS linhas
-- FROM lodlog_dw.dim_cat_atraso;
-- -- Deve retornar 5
