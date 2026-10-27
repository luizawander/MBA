**LAB 2 — Modelagem de Dados para Analytics**

**Disciplina:** Engenharia de Dados para Inteligência Artificial e Analytics
**Aula:** 2 — Modelagem: Estruturas de dados para suporte a IA e analytics
**Duração do lab:** ~1h30
**Entrega:** Diagrama ER + Normalização até 3FN + Star Schema + DDL SQL + justificativas + KPI
**Scripts de apoio:** lodlog\_modelo\_dados\_v3.sql e lodlog\_lab3\_seed\_v3.py

1. A tabela lodlog\_op.entrega é entregue **propositalmente em 2FN** — com colunas redundantes de cliente, veículo, motorista e CD (dependências transitivas). Os alunos devem **normalizar para 3FN**.
2. Adição de KPI: kpi\_categoria\_atraso na entrega (operacional) e na fato (DW). Categoria derivada de minutos\_atraso.
3. Mini-dimensão lodlog\_dw.dim\_categoria\_atraso (Kimball, SCD Tipo 1, 5 linhas). Surrogate key sk\_categoria\_atraso replicada na fato.

**Objetivos de Aprendizagem**

1. Validar e corrigir um modelo entidade-relacionamento para um cenário de negócio
2. Identificar dependências transitivas em uma tabela em 2FN e **normalizar até a 3FN**
3. Validar um Star Schema para analytics e ML
4. Adicionar um atributo de KPI em uma dimensão do Star Schema (minidimensão)
5. Justificar o uso de surrogate keys vs natural keys
6. Identificar quando desnormalizar para ganho de performance

**Parte 0 — Contexto (5 min)**

Na Aula 1, o grupo mapeou o ecossistema de dados da LODLog. Agora é hora de **estruturar** esses dados.

***Problema do dia:****A LODLog tem dados espalhados em ERP, WMS, TMS e sensores IoT. Cada sistema usa suas próprias chaves e formatos. Não há uma visão unificada do cliente, do veículo ou do produto. Relatórios demoram porque precisam fazer JOINs complexos entre sistemas.*

**Missão do LAB 2:** Receber o modelo com a tabela entrega em **2FN** (proposital), normalizar até **3FN**, projetar o **Star Schema** com a **nova mini-dimensão** dim\_categoria\_atraso, e implementar o DDL correspondente.

**Antes de começar:** rode o script lodlog\_modelo\_dados\_v2.sql no Databricks. Ele cria as tabelas. Você pode inspecionar as tabelas no menu “Catalog” antes de começar o lab.

**Parte 1 — Modelo Entidade-Relacionamento (25 min)**

**Atividade 1.1: Identifique as Entidades**

A partir do cenário LODLog e das tabelas geradas em lodlog\_op, liste pelo menos **8 entidades** com seus atributos principais. Use como referência o script lodlog\_modelo\_dados\_v2.sql.

**Atividade 1.2: Relacionamentos e Cardinalidade**

|  |  |  |  |
| --- | --- | --- | --- |
| **Entidade A** | **Entidade B** | **Cardinalidade** | **Descrição do Relacionamento** |
| VEICULO | MOTORISTA |  |  |
| PEDIDO | CLIENTE |  |  |
| PEDIDO | VEICULO |  |  |
| PRODUTO | CENTRO\_DISTRIBUICAO |  |  |
| MOTORISTA | MANUTENCAO |  |  |

--- linha de base ---

Daqui para baixo é desejável/opcional.

**Parte 2 — Normalização até 3FN (25 min)**

**ATENÇÃO —**a tabela lodlog\_op.entrega está **propositalmente em 2FN**. Ela tem **dependências transitivas** (dados redundantes de outras entidades). Sua missão é normalizar até a **3FN**.

**Atividade 2.1: Identifique as Anomalias e Dependências Transitivas (individual, 10 min)**

Inspecione a tabela lodlog\_op.entrega no Databricks. Ela tem a PK entrega\_id (simples), portanto está em 1FN e 2FN (sem dependências parciais), mas tem **4 grupos de dependências transitivas**:

ENTREGA(entrega\_id, pedido\_id, veiculo\_id, motorista\_id,

-- Dados redundantes do CLIENTE (dependência transitiva 1)

cliente\_id, cliente\_cnpj, cliente\_razao\_social, cliente\_segmento,

-- Dados redundantes do VEÍCULO (dependência transitiva 2)

veiculo\_placa, veiculo\_modelo, veiculo\_fabricante, veiculo\_capacidade\_kg,

-- Dados redundantes do MOTORISTA (dependência transitiva 3)

motorista\_nome, motorista\_cnh, motorista\_categoria,

-- Dados redundantes do CD (dependência transitiva 4)

cd\_origem\_id, cd\_origem\_codigo, cd\_origem\_nome, cd\_origem\_uf,

data\_saida, data\_entrega\_prevista, data\_entrega\_real,

distancia\_km, custo\_combustivel, custo\_pedagio, valor\_frete,

multa\_atraso, status\_entrega,

kpi\_categoria\_atraso)

**Responda (escreva no caderno ou no chat):**

1. **Quantas anomalias** essa tabela tem se um cliente trocar de razão social? (anomalia de \_\_\_\_\_\_\_\_\_\_\_\_)
2. **Quantos registros** precisam ser atualizados se o veículo 42 mudar de placa?
3. Se uma entrega for cancelada, **o que acontece com os dados do cliente** nessa entrega?
4. Liste as **4 dependências funcionais transitivas** no formato X → Y → Z (ex: cliente\_id → cliente\_cnpj → cliente\_razao\_social).

**Atividade 2.2: Normalize até a 3FN (grupo, 15 min)**

Decomponha a tabela ENTREGA (que está em 2FN) até a **Terceira Forma Normal (3FN)**.

**Sua entrega deve conter:**

1. Lista de **tabelas finais** após a normalização (mínimo: cliente, veiculo, motorista, centro\_distribuicao, entrega).
2. Para cada tabela: PK e FKs.
3. Atualize o script SQL (lodlog\_modelo\_dados\_v2.sql) para que a tabela ENTREGA fique na 3FN.

**Parte 3 — Star Schema para Analytics (30 min)**

**Atividade 3.1: Diferença ER vs Star Schema (individual, 5 min)**

|  |  |  |
| --- | --- | --- |
| **Característica** | **Modelo ER (Transacional)** | **Star Schema (Analítico)** |
| Objetivo principal |  |  |
| Número de tabelas |  |  |
| Tipo de JOIN |  |  |
| Granularidade |  |  |
| Uso de surrogate keys |  |  |
| Otimizado para |  |  |

**Atividade 3.2: Compreenda o Star Schema da LODLog (grupo, 15 min)**

A partir do ER normalizado (Parte 2), compreenda o **Star Schema** para responder as perguntas de negócio abaixo. Use o lodlog\_modelo\_dados\_v2.sql como referência das tabelas DW existentes.

Para as perguntas de negócio abaixo, indique quais tabelas do DW poderiam trazer a resposta. Não precisa rodar consulta ou obter resultado.

1. Qual a taxa de pontualidade por centro de distribuição e por mês?
2. Qual o custo médio de frete por região e por tipo de veículo?
3. Quantos pedidos foram entregues com atraso por cliente no último trimestre?
4. Qual a distribuição de atrasos por categoria (Adiantado / No Prazo / Atraso Leve / Moderado / Crítico) por mês?
5. Qual a correlação entre a categoria de atraso e o score de segurança do motorista?

**Requisitos:** tabela fato bem definida, pelo menos **5 dimensões** (4 originais + a nova dim\_categoria\_atraso), granularidade clara.

**Atividade 3.3: Surrogate Keys (individual, 5 min)**

|  |  |  |
| --- | --- | --- |
| **Tabela** | **Usa surrogate key?** | **Por que?** |
| Fato entregas |  |  |
| Dimensão Tempo |  |  |
| Dimensão Cliente |  |  |
| Dimensão Veículo |  |  |  | |
| Dimensão Localidade |  |  |  |
| Dimensão Categoria Atraso |  |  |  |

**Atividade 3.4 — Minidimensão do KPI (grupo, 5 min)**

O script de seed v2 já criou a mini-dimensão lodlog\_dw.dim\_cat\_atraso com 5 registros. Responda:

1. **Por que** a categoria de atraso foi para uma **mini-dimensão** (e não para a dim\_tempo ou dim\_motorista)?
2. A coluna kpi\_cat\_atraso aparece **duas vezes** no modelo: na entrega (operacional) e na fato\_entregas (DW). Isso é **redundância** aceitável? Justifique.
3. A coluna sla\_violado na mini-dimensão é uma **flag booleana**. Ela poderia virar uma **dimensão separada** (SCD Tipo 1)?

**Conceito-chave — Mini-dimensão (Kimball):** atributos de **baixa cardinalidade** que são **estáveis** (mudam raramente) e usados em filtros/agrupamentos de BI devem ser isolados em uma **mini-dimensão**, em vez de serem replicados como string na fato. Isso permite:

* Performance: a fato é menor (INT em vez de STRING)
* Flexibilidade: trocar a descrição da categoria sem alterar a fato
* Conformidade: o valor da categoria passa a ser controlado pela dimensão

**Parte 4 — SQL DDL (20 min)**

**Atividade 4.1: Crie a Nova Tabela Operacional (individual, 10 min) v2**

Você já normalizou a tabela entrega na Atividade 2.2. Agora **aplique a normalização no script SQL**:

1. Abra o script lodlog\_modelo\_dados\_v2.sql no Databricks.
2. Localize o CREATE TABLE lodlog\_op.entrega (que está em 2FN).
3. **Substitua-o** pela sua versão normalizada em 3FN — apenas com FKs e medidas (sem colunas redundantes).

**Atividade 4.2: Valide a Mini-Dimensão no DW (individual, 5 min) (opcional)**

A mini-dimensão dim\_categoria\_atraso já foi criada. Mas vocês precisam garantir a **integridade**:

1. Faça uma query que conte quantas entregas tem cada categoria:

Join de fato e cat\_atraso

1. Faça uma query que mostre a taxa de pontualidade por região (usando dim\_centro\_distribuicao):

Join de fato com dim\_centro\_distribuicao

Usar:

SELECT c.regiao,

SUM(CASE WHEN f.indicador\_atraso = 0 THEN 1 ELSE 0 END) \* 1.0 / COUNT(\*) AS taxa\_pontualidade

**Atividade 4.3: Justifique suas Escolhas (grupo, 5 min)**

1. Por que escolheu essa granularidade para a tabela fato?
2. Qual dimensão vai crescer mais? Como lidaria com isso?
3. Se o negócio pedir uma nova categoria "Atraso Severíssimo" (> 24h), o que muda no modelo?

***Dica do Professor:****O Star Schema não é "melhor" que o ER — são modelos para propósitos diferentes. O ER serve para operar (transações); o Star Schema serve para analisar (agregações). Um pipeline de dados bem projetado começa no ER dos sistemas transacionais (em 3FN) e termina no Star Schema do DW — com mini-dimensões para KPIs de baixa cardinalidade.*