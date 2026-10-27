# LAB 4 — Arquiteturas Analiticas Modernas e MLOps

> **Disciplina:** Engenharia de Dados para Inteligencia Artificial e Analytics  
> **Aula:** 4 — Arquiteturas: Solucoes modernas para dados em escala (Cloud, Data Mesh, MLOps)  
> **Duracao do lab:** ~1h30  
> **Entrega:** Arquitetura proposta + justificativa tecnica + roadmap MLOps  

---

## Objetivos de Aprendizagem

Ao final deste lab, o aluno sera capaz de:

1. Diferenciar Data Warehouse, Data Lake, Data Lakehouse e Data Mesh
2. Posicionar um cenario de negocio na arquitetura mais adequada
3. Desenhar um pipeline completo de dados (Bronze/Silver/Gold)
4. Entender o papel da engenharia de dados no MLOps
5. Propor um roadmap de evolucao arquitetural

---

## Parte 0 — Contexto (5 min)

Nos Labs 1-3, o grupo:
- Mapeou o ecossistema (LAB 1)
- Modelou dados transacionais e analiticos (LAB 2)
- Construiu SQL de features e qualidade (LAB 3)

Agora e hora de **integrar tudo** em uma arquitetura moderna que suporte:
- Crescimento de volume (Big Data)
- Diversidade de fontes (JSON, CSV, APIs, IoT)
- Modelos de ML em producao (MLOps)
- Governanca e compliance (LGPD)

---

## Parte 1 — Arquiteturas Analiticas: O Quadrante (20 min)

### Atividade 1.1: Complete o Quadrante (individual, 10 min)

Para cada arquitetura abaixo, preencha:

| Arquitetura | Tipo de Dados | Schema | Caso Ideal | Nao Serve Para |
|-------------|--------------|--------|-----------|---------------|
| Data Warehouse | Estruturado apenas | Schema-on-write | Relatorios gerenciais, BI tradicional | Dados brutos de IoT, imagens |
| Data Lake | | | | |
| Data Lakehouse | | | | |
| Data Mesh | | | | |

### Atividade 1.2: Posicione a LODLog (grupo, 10 min)

Discuta no grupo: **"Qual arquitetura (ou combinacao) e mais adequada para a LODLog hoje? E daqui a 3 anos?"**

Considere:
- Hoje: 450 veiculos, 12 CDs, 18k entregas/mes
- Daqui a 3 anos: projecao de 1.200 veiculos, 35 CDs, 60k entregas/mes, operacao em 2 paises

Justifique em 5-8 linhas.

---

## Parte 2 — Camadas Medallion na Pratica (30 min)

### Atividade 2.1: Mapeamento Bronze/Silver/Gold (grupo, 15 min)

Para cada fonte de dados da LODLog, defina:
- Como chega na **Bronze** (formato, particionamento, retencao)
- O que acontece na **Silver** (limpeza, deduplicacao, enriquecimento)
- O que e produzido na **Gold** (tabelas, views, features)

| Fonte | Bronze (como chega) | Silver (o que limpa/enriquece) | Gold (o que entrega) |
|-------|--------------------|-------------------------------|---------------------|
| IoT sensores da frota | | | |
| Pedidos do TMS | | | |
| Estoque do WMS | | | |
| APIs externas (clima) | | | |

### Atividade 2.2: Batch vs Streaming (grupo, 10 min)

Para cada caminho acima, classifique como **Batch**, **Streaming** ou **Hibrido**:

| Fluxo de Dados | Batch / Streaming / Hibrido? | Justificativa de Negocio |
|---------------|------------------------------|-------------------------|
| IoT -> Bronze | | |
| Bronze -> Silver | | |
| Silver -> Gold (KPIs) | | |
| Gold -> ML modelo | | |
| Gold -> Dashboard | | |

### Atividade 2.3: Desenhe o Pipeline (grupo, 5 min)

Desenhe o pipeline completo da LODLog:
- Da fonte ate o consumo
- Indicando Batch vs Streaming em cada seta
- Indicando as tecnologias sugeridas (pode ser agnostico ou citar AWS/Azure/GCP/Databricks)

---

## Parte 3 — MLOps e Engenharia de Dados (25 min)

### Atividade 3.1: O Papel do Engenheiro de Dados no MLOps (individual, 10 min)

Leia o fluxo abaixo e complete: **"Onde o engenheiro de dados atua em cada etapa?"**

```
[ Dados Brutos ] -> [ ? ] -> [ Feature Store ] -> [ ? ] -> [ Modelo Treinado ]
                       ^                              ^
                  Eng. Dados                    Eng. Dados?
```

Complete tambem para as etapas:
- Monitoramento de data drift
- Retreinamento automatizado
- Versionamento de dados (vs versionamento de modelo)
- Pipeline de inferencia em producao

### Atividade 3.2: Proponha um Pipeline MLOps para a LODLog (grupo, 15 min)

Escolha **um dos modelos** abaixo e desenhe o pipeline MLOps:

A. **Predicao de Atraso** (classificacao)
B. **Manutencao Preditiva** (classificacao + serie temporal)

Para o modelo escolhido, defina:
1. De onde vêm os dados de treinamento (qual camada Gold?)
2. Como os dados de treinamento sao atualizados (frequencia, trigger)
3. Como o modelo recebe dados para inferencia (batch ou real-time?)
4. Como detectar se os dados mudaram (data drift) e quando retreinar
5. Quem e responsavel por cada etapa: Engenheiro de Dados, Cientista de Dados, ou MLOps Engineer?

---

## Parte 4 — Governanca e Roadmap (20 min)

### Atividade 4.1: Checklist LGPD para o Pipeline (grupo, 10 min)

Avalie o pipeline da LODLog segundo os requisitos da LGPD:

| Requisito LGPD | Aplica-se a LODLog? | Como implementar no pipeline? |
|----------------|--------------------|------------------------------|
| Consentimento do titular | | |
| Finalidade determinada | | |
| Necessidade/adequacao | | |
| Anonimizacao de dados sensiveis | | |
| Direito de acesso | | |
| Direito de exclusao | | |
| Retencao minima | | |
| Seguranca da informacao | | |

### Atividade 4.2: Roadmap de Evolucao (grupo, 10 min)

Crie um roadmap em 3 fases para a arquitetura de dados da LODLog:

| Fase | Periodo | Objetivo | Arquitetura | Tecnologias Sugeridas |
|------|---------|----------|-------------|----------------------|
| 1 (MVP) | Meses 1-3 | | | |
| 2 (Escala) | Meses 4-9 | | | |
| 3 (IA nativa) | Meses 10-18 | | | |

---

## Parte 5 — Entrega do Grupo (10 min)

### Produto do LAB 4

Entregue um documento contendo:

1. **Arquitetura escolhida** para a LODLog (Lakehouse recomendada) com justificativa
2. **Diagrama Bronze/Silver/Gold** com pelo menos 3 fontes mapeadas
3. **Pipeline MLOps** para um dos modelos (A ou B)
4. **Checklist LGPD** preenchido
5. **Roadmap** de 3 fases

### Rubrica de Avaliacao do LAB 4 (compoe 15% da nota do projeto em grupo)

| Criterio | Peso | Excelente | Satisfatorio | Insatisfatorio |
|----------|------|-----------|--------------|----------------|
| Escolha arquitetural | 20% | Justificativa solida, considera crescimento | Escolha razoavel, justificativa generica | Escolha inadequada ou sem justificativa |
| Camadas Medallion | 20% | 3+ fontes mapeadas com clareza em cada camada | 2 fontes mapeadas, alguma confusao | < 2 fontes ou camadas mal definidas |
| MLOps | 25% | Pipeline completo, papéis claros, drift monitorado | Pipeline basico, falta monitoramento | Sem pipeline ou sem compreensao de MLOps |
| Governanca/LGPD | 20% | Checklist completo, implementacoes concretas | Checklist parcial, implementacoes vagas | Checklist incompleto ou incorreto |
| Roadmap | 15% | 3 fases realistas, tecnologias adequadas, evolucao clara | 3 fases, mas tecnologias genericas | < 3 fases ou sem evolucao |

---

## Material de Apoio

- Aula 4 — Slides de Arquiteturas Modernas e MLOps
- Documento base: `Projeto-Eng-Dados-IA-para-Negocio.md` (Secoes 10, 11, 12)
- Artigo: "Data Lakehouse: A New Generation of Open Platforms" (Databricks)
- Artigo: "Data Mesh" de Zhamak Dehghani (Thoughtworks)

---

> **Dica do Professor:** Nao existe arquitetura perfeita — existe arquitetura adequada ao momento da empresa. Uma startup pode comecar com um Data Lake simples em S3 + Athena. Uma empresa em crescimento precisa de um Lakehouse com Delta Lake. Uma multinacional com multiplos dominios precisa considerar Data Mesh. O importante e justificar sua escolha com base no cenario de negocio, nao no hype tecnologico.
