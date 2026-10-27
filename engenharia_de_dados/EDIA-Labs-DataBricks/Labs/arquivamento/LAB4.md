**LAB 4 — Arquiteturas Analíticas Modernas e MLOps**

**Disciplina** Engenharia de Dados para Inteligência Artificial e Analytics (MBA)

**Aula**4 — Arquiteturas modernas para dados em escala (Cloud, Data Mesh e MLOps)

**Duração do Lab**~1h30min

# Considerar apenas item 1.2

**Objetivos de Aprendizagem**

Ao final deste laboratório, o grupo será capaz de:

1. Diferenciar as características, vantagens e limitações de **Data Warehouse**, **Data Lake**, **Data Lakehouse** e **Data Mesh**.
2. Avaliar um cenário de negócio de logística e posicioná-lo na arquitetura analítica mais adequada ao seu momento de crescimento.
3. Projetar um pipeline de dados distribuído utilizando a **Arquitetura Medallion** (Bronze, Silver e Gold), mapeando o fluxo de processamento Batch e Streaming.
4. Estruturar o papel da Engenharia de Dados no ciclo de vida de modelos preditivos (\*\*MLOps\*\*), especificando a integração com Feature Stores e mecanismos de data drift.
5. Elaborar um \*\*Roadmap de Evolução Arquitetural\*\* e um checklist de conformidade com a **LGPD**.

**Parte 0 — Contexto (5 min)**

Nos laboratórios anteriores (LABs 1 a 3), vocês realizaram a modelagem lógica e física do banco analítico da LODLog e construíram views para preparação de modelos de ML no Databricks. Agora, o desafio é expandir esse projeto para uma visão integrada de arquitetura de dados moderna. Vocês deverão desenhar a solução técnica corporativa da LODLog que suporte:

* **Big Data:** Crescimento exponencial do volume de entregas e dados de sensores IoT.
* **Variedade de Fontes:** Arquivos JSON de e-commerce, bancos relacionais ERP, APIs de clima e logs de telemetria da frota.
* **Modelos de ML em Produção (MLOps):** Suporte estável para os modelos de *Predição de Atrasos* e *Manutenção Preditiva*.
* **Governança de Dados:** Controle de acesso, auditoria e conformidade regulatória (LGPD).

**Parte 1 — Arquiteturas Analíticas: O Quadrante de Decisão (20 min)**

**Atividade 1.1: Complete o Quadrante**

Preencha os espaços em branco na tabela comparativa de arquiteturas analíticas modernas. Use esta tabela como base conceitual para o relatório de entrega.

| **Arquitetura** | **Tipo de Dados Suportados** | **Estratégia de Schema** | **Caso Ideal de Uso (Melhor para)** | **Limitações (Evitar quando)** |
| --- | --- | --- | --- | --- |
| **Data Warehouse** | Estruturado apenas (tabelas relacionais) | Schema-on-write (validação rígida na escrita) | Business Intelligence tradicional, relatórios de auditoria e dashboards executivos estáveis. | Dados semiestruturados de alta frequência (IoT), mídias não estruturadas e ML exploratório. |
| **Data Lake** | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | Armazenamento em escala de dados brutos, Big Data e exploração de Data Science. | Usuários finais de negócio necessitam de consultas rápidas e diretas (risco de *Data Swamp*). |
| **Data Lakehouse** | Estruturado, semiestruturado e não estruturado | Híbrido (Metadados abertos com ACID) | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | Projetos muito pequenos com equipes sem maturidade ou sem demandas de IA. |
| **Data Mesh** | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | Descentralizado (por domínio de negócio) | Grandes organizações com múltiplos domínios de negócio autônomos. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |

**Atividade 1.2: Posicionamento Estratégico da LodLog**

Discutam o seguinte cenário de crescimento e tomem uma decisão de arquitetura para a LODLog:

* **Momento Atual:** 450 veículos na frota, 5 centros de distribuição ativos, volume de ~50k entregas por mês.
* **Projeção para Daqui a 3 Anos:** 1.500 veículos na frota, 30 centros de distribuição ativos, volume projetado de ~250k entregas por mês, integração em tempo real de dados de telemetria (IoT) e operação em 3 países da América Latina (iniciando fusões e aquisições).

**Questão:** *"Qual arquitetura analítica vocês recomendam para a LODLog hoje? Qual a evolução proposta para os próximos 3 anos? Justifiquem a escolha em 6 a 10 linhas no relatório final."*

**Parte 2 — Camadas Medallion na Prática (30 min)**

**Atividade 2.1: Mapeamento da Arquitetura**

Para o cenário da LODLog, a empresa utiliza quatro fontes principais de dados. Preencham a tabela definindo quais transformações, limpezas e filtros os dados sofrerão ao longo das três camadas da Arquitetura Medallion:

| **Fonte Original** | **Zonas de Ingestão / Camada Bronze** | **Camada Silver (Limpeza e Conformidade)** | **Camada Gold (Consumo e KPIs)** |
| --- | --- | --- | --- |
| **Telemetria IoT (GPS e Sensores da Frota)** | Dados em JSON bruto salvos em diretórios particionados por data. | Schema aplicado, validação de coordenadas geográficas e filtragem de duplicatas de sensores. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |
| **Pedidos do TMS (Banco Relacional)** | Tabelas operacionais replicadas na Bronze sem transformações. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | Métricas agregadas de frete por CD, taxa de sinistros e custos operacionais. |
| **Estoque do WMS (Arquivos CSV)** | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | Limpeza de registros nulos e uniformização de SKUs com o cadastro de produtos. | Nível de giro de estoque por CD e alertas de ruptura. |
| **APIs Externas de Clima (JSON)** | Retorno da API armazenado com timestamp de coleta. | Conversão de temperaturas e padronização das condições de chuva/sol. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |

**Atividade 2.2: Latência de Processamento**

Definam a latência de processamento adequada (**Batch**, **Real-Time/Streaming** ou **Híbrido**) para os seguintes fluxos de dados, justificando a decisão com base nas necessidades reais da operação da LODLog:

| **Fluxo de Dados** | **Latência Proposta** | **Justificativa de Negócio / Decisão Operacional** | |
| --- | --- | --- | --- |
| **Ingestão IoT da Frota → Bronze** | Streaming (Kinesis/Kafka) | | Necessário para saber a localização dos motoristas em tempo real e monitorar a integridade das cargas críticas. |
| **Carga do ERP → Camada Silver** | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | |
| **Cálculo do SLA de Entregas → Dashboard Executivo** | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | |
| **Detecção de Falha Mecânica IoT → Alerta no TMS** | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | |

**Atividade 2.3: Desenho Técnico do Pipeline (Exemplo de arquitetura de ingestão e armazenamento)**

Esbocem ou diagramem o pipeline completo da LODLog, desde as origens até os consumidores finais (Dashboards de BI e Modelos de ML). Tomem como base um **exemplo de arquitetura de ingestão e armazenamento** em nuvem. É preciso indicar explicitamente tecnologias sugeridas que englobem conceitos além da AWS, integrando obrigatoriamente os **conceitos do Databricks Lakehouse**, tais como:

* Armazenamento resiliente e escalável no Data Lake usando cloud object storage (ex: AWS S3, Azure ADLS ou GCP Cloud Storage).
* Adoção da camada de **Delta Lake** sobre o storage para conferir confiabilidade de DW (transações ACID, versionamento).
* Ingestão e processamento de dados massivos e unificados (batch e streaming) com **Apache Spark** (computação).
* Organização do ciclo de vida dos dados usando a arquitetura **Medallion** (camadas Bronze, Silver e Gold).

**Parte 3 — MLOps e Engenharia de Dados (25 min)**

**Atividade 3.1: O Ciclo de Vida do Dado no MLOps (10 min, individual)**

Analise o diagrama do pipeline de Machine Learning abaixo e responda:

[Dados Brutos] --(1)--> [Bronze] --(2)--> [Silver] --(3)--> [Gold / Feature Store] --(4)--> [Treinamento ML] --(5)--> [Inferência em Prod]

**Perguntas:**

1. Qual a responsabilidade técnica do **Engenheiro de Dados** nos passos (1), (2) e (3)? E qual a responsabilidade do **Cientista de Dados** no passo (4)?
2. Em produção, o modelo consome dados novos na etapa (5). Por que o pipeline de dados que gera as features para a inferência em tempo real deve ser **idêntico** ao pipeline que gerou os dados de treinamento no passo (3)?

**Atividade 3.2: Desenho do Pipeline de MLOps (15 min, em grupo)**

Escolha **um dos dois modelos preditivos** da LODLog:

* **Modelo A: Predição de Atraso de Entregas** (Classificação - prevê se a viagem atrasará).
* **Modelo B: Manutenção Preditiva dos Veículos** (Séries Temporais - prevê falha de componentes mecânicos baseados em telemetria IoT).

Para o modelo escolhido, descreva o pipeline de MLOps respondendo de forma objetiva aos seguintes tópicos:

1. **Origem de Treinamento:** De qual tabela ou view da camada Gold o modelo lerá os dados de treinamento?
2. **Frequência de Atualização:** Com qual frequência os dados da Feature Store devem ser atualizados e o que dispara o retreinamento do modelo?
3. **Inferência:** A predição em produção deve rodar em Batch (ex: rodar toda noite para as viagens do dia seguinte) ou Real-Time (ex: atualizar a probabilidade a cada nova coordenada de GPS)? Justifiquem a escolha.
4. **Monitoramento de Data Drift:** Como a engenharia de dados pode monitorar se a distribuição dos dados em produção está mudando (ex: novos motoristas contratados com perfil diferente) e como acionar alertas de degradação do modelo?

**Parte 4 — Governança de Dados, LGPD e Roadmap (20 min)**

**Atividade 4.1: Checklist de Conformidade com a LGPD (10 min, em grupo)**

Preencham o checklist descrevendo como o pipeline de dados da LODLog garantirá a conformidade com a LGPD nos pontos críticos de engenharia:

| **Exigência da LGPD** | **Impacto no Pipeline da LODLog** | **Como Implementar Tecnicamente no Data Lakehouse?** |
| --- | --- | --- |
| **Anonimização de Dados Pessoais** | Dados de motoristas (CNH, CPF) e clientes (Nome, Endereço de entrega). | Mascaramento dinâmico de colunas na camada Silver ou criação de views anonimizadas na Gold utilizando hashes/criptografia. |
| **Direito de Exclusão (Esquecimento)** | O cliente solicita a remoção completa do seu histórico pessoal do banco de dados. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |
| **Minimização e Retenção de Dados** | Armazenamento de logs IoT indefinidamente gera altos custos e riscos legais. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |
| **Controle de Acesso e Auditoria** | Prevenir que analistas de BI visualizem dados salariais de motoristas. | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |

**Atividade 4.2: Roadmap de Implementação**

Estruturem um plano realista de implementação de 18 meses para a LODLog, dividindo o roadmap técnico nas três fases clássicas de evolução de dados:

| **Fase de Evolução** | **Período** | **Objetivo Principal de Negócio** | **Arquitetura Alvo** | **Principais Tecnologias do Bloco** |
| --- | --- | --- | --- | --- |
| **Fase 1 (MVP e Fundações)** | Meses 1 a 3 | Unificar as fontes operacionais do WMS, TMS e ERP em repositório central. | Data Lake / DW inicial | Databricks SQL, S3, Delta Lake. |
| **Fase 2 (Escala e Qualidade)** | Meses 4 a 9 | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | Data Lakehouse completo | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |
| **Fase 3 (IA Nativa e MLOps)** | Meses 10 a 18 | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |

**Dica do Professor:** Arquitetura de dados não é uma escolha dogmática ou apenas sobre seguir o \*hype\* do mercado. O papel do gestor de tecnologia é encontrar a melhor solução custo-benefício para o momento de maturidade da empresa. Justifiquem cada tecnologia sugerida com base no valor de negócio que ela desbloqueia e na complexidade que a equipe consegue operar. Bom trabalho!