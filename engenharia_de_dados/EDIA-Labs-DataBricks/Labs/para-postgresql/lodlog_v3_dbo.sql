
CREATE TABLE IF NOT EXISTS lodlog_op.cliente (
  cliente_id    BIGSERIAL    NOT NULL PRIMARY KEY,
  cnpj          TEXT         NOT NULL,  -- UNIQUE: não duplicar CNPJ
  razao_social  TEXT         NOT NULL,
  nome_fantasia TEXT,
  segmento      TEXT         NOT NULL,  -- Valores: 'Varejista','Industrial','Atacadista','Outro'
  email         TEXT,
  telefone      TEXT,
  data_cadastro DATE         NOT NULL,
  ativo         BOOLEAN      NOT NULL
);
COMMENT ON TABLE lodlog_op.cliente IS 'Cadastro de clientes ativos da LODLog';

-- Separar endereço evita dependência transitiva (3FN):
-- bairro/municipio/uf dependem do CEP, não do cliente_id
CREATE TABLE IF NOT EXISTS lodlog_op.endereco_cliente (
  endereco_id BIGSERIAL    NOT NULL PRIMARY KEY,
  cliente_id  BIGINT       NOT NULL,  -- FK → lodlog_op.cliente.cliente_id
  logradouro  TEXT         NOT NULL,
  numero      TEXT,
  complemento TEXT,
  bairro      TEXT         NOT NULL,
  municipio   TEXT         NOT NULL,
  uf          TEXT         NOT NULL,
  cep         TEXT         NOT NULL,
  latitude    DECIMAL(9,6),
  longitude   DECIMAL(9,6),
  tipo        TEXT         NOT NULL,  -- Valores: 'Entregas','Cobrança','Principal'
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id)
);

CREATE TABLE IF NOT EXISTS lodlog_op.contrato (
  contrato_id          BIGSERIAL     NOT NULL PRIMARY KEY,
  cliente_id           BIGINT        NOT NULL,  -- FK → cliente
  numero_contrato      TEXT          NOT NULL,
  data_inicio          DATE          NOT NULL,
  data_fim             DATE,
  sla_pontualidade_pct DECIMAL(5,2)  NOT NULL,  -- 0-100
  multa_atraso_pct     DECIMAL(5,2)  NOT NULL,  -- >= 0
  status               TEXT          NOT NULL,  -- Valores: 'Ativo','Encerrado','Suspenso'
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id)
);


-- ================================================================
-- CÉLULA 3 — Domínio FROTA
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.veiculo (
  veiculo_id     BIGSERIAL     NOT NULL PRIMARY KEY,
  placa          TEXT          NOT NULL,  -- UNIQUE
  modelo         TEXT          NOT NULL,
  fabricante     TEXT,
  ano_fabricacao SMALLINT      NOT NULL,  -- >= 1990
  tipo           TEXT          NOT NULL,  -- Valores: 'Leve','Médio','Pesado'
  capacidade_kg  DECIMAL(10,2) NOT NULL,  -- > 0
  hodometro_km   DECIMAL(10,0) NOT NULL,  -- >= 0
  data_aquisicao DATE,
  status         TEXT          NOT NULL   -- Valores: 'Disponível','Em Rota','Manutenção','Inativo'
);

CREATE TABLE IF NOT EXISTS lodlog_op.motorista (
  motorista_id     BIGSERIAL    NOT NULL PRIMARY KEY,
  cpf              TEXT         NOT NULL,  -- UNIQUE
  nome_completo    TEXT         NOT NULL,
  cnh              TEXT         NOT NULL,  -- UNIQUE
  categoria_cnh    TEXT         NOT NULL,  -- Valores: 'A','B','C','D','E','AB','AC','AD','AE'
  validade_cnh     DATE         NOT NULL,
  data_admissao    DATE         NOT NULL,
  score_seguranca  DECIMAL(5,2),           -- NULL ou 0-100
  status           TEXT         NOT NULL   -- Valores: 'Ativo','Afastado','Desligado'
);

CREATE TABLE IF NOT EXISTS lodlog_op.manutencao (
  manutencao_id   BIGSERIAL     NOT NULL PRIMARY KEY,
  veiculo_id      BIGINT        NOT NULL,  -- FK → veiculo
  tipo            TEXT          NOT NULL,  -- Valores: 'Preventiva','Corretiva','Preditiva'
  data_abertura   TIMESTAMP     NOT NULL,
  data_conclusao  TIMESTAMP,
  km_no_momento   DECIMAL(10,0) NOT NULL,  -- >= 0
  custo_total     DECIMAL(12,2),           -- NULL ou >= 0
  descricao       TEXT,
  status          TEXT          NOT NULL,  -- Valores: 'Aberta','Em Execução','Concluída'
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id)
);

-- Alta frequência: ~864k eventos/dia — particionar por data para eficiência
CREATE TABLE IF NOT EXISTS lodlog_op.telemetria (
  telemetria_id         BIGSERIAL     NOT NULL PRIMARY KEY,
  veiculo_id            BIGINT        NOT NULL,  -- FK → veiculo
  timestamp_evento      TIMESTAMP     NOT NULL,
  data_evento           DATE          NOT NULL,  -- Coluna de partição
  latitude              DECIMAL(9,6)  NOT NULL,
  longitude             DECIMAL(9,6)  NOT NULL,
  velocidade_kmh        DECIMAL(6,2)  NOT NULL,  -- 0-200
  rpm_motor             INT,                      -- NULL ou 0-8000
  temperatura_motor_c   DECIMAL(6,2),             -- NULL ou -50 a 200
  nivel_combustivel_pct DECIMAL(5,2),             -- NULL ou 0-100
  peso_carga_kg         DECIMAL(10,2),            -- NULL ou >= 0
  hodometro_km          DECIMAL(10,0),
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id)
);
COMMENT ON TABLE lodlog_op.telemetria IS 'Eventos IoT da frota (~864k/dia). Particionamento por data recomendado em produção.';


-- ================================================================
-- CÉLULA 4 — Domínio ESTOQUE
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.centro_distribuicao (
  cd_id         BIGSERIAL     NOT NULL PRIMARY KEY,
  codigo        TEXT          NOT NULL,  -- UNIQUE: ex. 'CD-CAMPINAS'
  nome          TEXT          NOT NULL,
  municipio     TEXT          NOT NULL,
  uf            TEXT          NOT NULL,
  cep           TEXT          NOT NULL,
  latitude      DECIMAL(9,6)  NOT NULL,
  longitude     DECIMAL(9,6)  NOT NULL,
  capacidade_m3 DECIMAL(10,2) NOT NULL,  -- > 0
  ativo         BOOLEAN       NOT NULL
);

CREATE TABLE IF NOT EXISTS lodlog_op.produto (
  produto_id         BIGSERIAL     NOT NULL PRIMARY KEY,
  sku                TEXT          NOT NULL,  -- UNIQUE
  nome               TEXT          NOT NULL,
  categoria          TEXT          NOT NULL,
  peso_unitario_kg   DECIMAL(10,3) NOT NULL,  -- > 0
  volume_unitario_m3 DECIMAL(10,4),            -- NULL ou > 0
  ativo              BOOLEAN       NOT NULL
);

-- Posição atual do estoque por combinação (cd_id, produto_id)
CREATE TABLE IF NOT EXISTS lodlog_op.estoque (
  estoque_id            BIGSERIAL  NOT NULL PRIMARY KEY,
  cd_id                 BIGINT     NOT NULL,  -- FK → centro_distribuicao
  produto_id            BIGINT     NOT NULL,  -- FK → produto
  quantidade_disponivel INT        NOT NULL,  -- >= 0
  quantidade_reservada  INT        NOT NULL,  -- >= 0
  posicao_galpao        TEXT,
  ultima_atualizacao    TIMESTAMP  NOT NULL,
  FOREIGN KEY (cd_id) REFERENCES lodlog_op.centro_distribuicao(cd_id),
  FOREIGN KEY (produto_id) REFERENCES lodlog_op.produto(produto_id)
);

-- Log de cada movimentação — estoque atual é derivado desse histórico
CREATE TABLE IF NOT EXISTS lodlog_op.movimentacao_estoque (
  movimentacao_id BIGSERIAL  NOT NULL PRIMARY KEY,
  estoque_id      BIGINT     NOT NULL,  -- FK → estoque
  tipo_mov        TEXT       NOT NULL,  -- Valores: 'Entrada','Saída','Reserva','Liberação','Ajuste'
  quantidade      INT        NOT NULL,
  timestamp_mov   TIMESTAMP  NOT NULL,
  referencia      TEXT,                 -- pedido_id, NF, etc.
  observacao      TEXT,
  FOREIGN KEY (estoque_id) REFERENCES lodlog_op.estoque(estoque_id)
);


-- ================================================================
-- CÉLULA 5 — Domínio OPERAÇÃO (Pedido / Entregas)
-- ================================================================

CREATE TABLE IF NOT EXISTS lodlog_op.pedido (
  pedido_id           BIGSERIAL  NOT NULL PRIMARY KEY,
  numero_pedido       TEXT       NOT NULL,  -- UNIQUE
  cliente_id          BIGINT     NOT NULL,  -- FK → cliente
  contrato_id         BIGINT,               -- FK → contrato (opcional)
  cd_origem_id        BIGINT     NOT NULL,  -- FK → centro_distribuicao
  endereco_destino_id BIGINT     NOT NULL,  -- FK → endereco_cliente
  data_pedido         TIMESTAMP  NOT NULL,
  prazo_entrega       TIMESTAMP  NOT NULL,  -- > data_pedido
  prioridade          TEXT       NOT NULL,  -- Valores: 'Baixa','Normal','Alta','Urgente'
  status_pedido       TEXT       NOT NULL,  -- Valores: 'Aberto','Em Separação','Despachado','Entregue','Cancelado'
  FOREIGN KEY (cliente_id) REFERENCES lodlog_op.cliente(cliente_id),
  FOREIGN KEY (contrato_id) REFERENCES lodlog_op.contrato(contrato_id),
  FOREIGN KEY (cd_origem_id) REFERENCES lodlog_op.centro_distribuicao(cd_id),
  FOREIGN KEY (endereco_destino_id) REFERENCES lodlog_op.endereco_cliente(endereco_id)
);

-- Tabela de associação Pedido ↔ Produto (N:M) com atributos próprios
CREATE TABLE IF NOT EXISTS lodlog_op.item_pedido (
  item_id       BIGSERIAL     NOT NULL PRIMARY KEY,
  pedido_id     BIGINT        NOT NULL,  -- FK → pedido
  produto_id    BIGINT        NOT NULL,  -- FK → produto
  quantidade    INT           NOT NULL,  -- > 0
  peso_total_kg DECIMAL(10,2) NOT NULL,  -- > 0
  FOREIGN KEY (pedido_id) REFERENCES lodlog_op.pedido(pedido_id),
  FOREIGN KEY (produto_id) REFERENCES lodlog_op.produto(produto_id)
);

-- ════════════════════════════════════════════════════════════════
-- TABELA ENTREGA — 3FN
-- ════════════════════════════════════════════════════════════════
-- Dados de cliente, veículo, motorista e CD NÃO são repetidos
-- aqui: ficam nas próprias tabelas e são acessados pelas FKs.
-- Cliente e CD de origem vêm do pedido (entrega → pedido).
-- ════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS lodlog_op.entrega (
  entrega_id            BIGSERIAL     NOT NULL PRIMARY KEY,
  pedido_id             BIGINT        NOT NULL,  -- FK → pedido
  veiculo_id            BIGINT        NOT NULL,  -- FK → veiculo
  motorista_id          BIGINT        NOT NULL,  -- FK → motorista

  -- Datas e medidas
  data_saida            TIMESTAMP     NOT NULL,
  data_entrega_prevista TIMESTAMP     NOT NULL,
  data_entrega_real     TIMESTAMP,
  distancia_km          DECIMAL(10,2) NOT NULL,  -- > 0
  custo_combustivel     DECIMAL(12,2),            -- NULL ou >= 0
  custo_pedagio         DECIMAL(12,2),            -- NULL ou >= 0
  valor_frete           DECIMAL(12,2) NOT NULL,  -- > 0
  multa_atraso          DECIMAL(12,2),            -- NULL ou >= 0
  status_entrega        TEXT          NOT NULL,  -- Valores: 'Pendente','Em Rota','Entregue','Ocorrência','Devolvido'

  -- ⭐ NOVO ATRIBUTO v2 — KPI de pontualidade
  -- Derivado de minutos_atraso (calculado na aplicação/ETL).
  -- Valores: 'Adiantado' | 'No Prazo' | 'Atraso Leve' | 'Atraso Moderado' | 'Atraso Crítico'
  kpi_cat_atraso        TEXT          NOT NULL,
  FOREIGN KEY (pedido_id) REFERENCES lodlog_op.pedido(pedido_id),
  FOREIGN KEY (veiculo_id) REFERENCES lodlog_op.veiculo(veiculo_id),
  FOREIGN KEY (motorista_id) REFERENCES lodlog_op.motorista(motorista_id)
);
COMMENT ON TABLE lodlog_op.entrega IS 'Tabela ENTREGA em 3FN. Inclui kpi_cat_atraso (NOVO v2).';
