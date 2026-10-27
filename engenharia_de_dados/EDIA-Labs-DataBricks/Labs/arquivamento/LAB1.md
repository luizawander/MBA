LAB 1 — Mapeamento do Ecossistema de Dados e Fundamentos

# LAB 1 — Mapeamento do Ecossistema de Dados e Fundamentos

**Disciplina** Engenharia de Dados para IA

**Aula** 1 — Fundamentos

**Duração do Lab** ~1h30 (em aula)

**Entrega** Documento + Diagrama

## Objetivos de Aprendizagem

1. Mapear o ecossistema de dados de uma organização real ou fictícia.
2. Distinguir sistemas transacionais de sistemas analíticos.
3. Classificar dados segundo os 5 Vs do Big Data.
4. Identificar oportunidades de uso de IA a partir de dados existentes.
5. Posicionar serviços de nuvem nos modelos IaaS, PaaS e SaaS.

## Parte 0 — Formação dos Grupos (10 min)

* Formar grupos de 5 a 6 integrantes.
* Escolher um **"Data Product Owner"** do grupo (quem representará o grupo nas discussões).
* Acessar o ECLASS e confirmar a formação.

## Parte 1 — Linha do Tempo da Engenharia de Dados (20 min)

### Atividade 1.1: Cartão-Resposta Histórico, 10 min

Para cada marco histórico abaixo, responda em uma frase: **"Por que isso mudou a forma como organizamos dados?"**

|  |  |
| --- | --- |
| Marco | Sua Resposta |
| Cartões perfurados (Hollerith, 1911) |  |
| Fitas magnéticas (1951) |  |
| Discos rígidos e acesso randômico (anos 70) |  |
| Modelo relacional de Codd (1970) |  |
| Primeiro SGBD comercial (Oracle, 1977) |  |
| Data Warehouse (Inmon/Kimball, anos 90) |  |
| Google File System / Big Data (1998/1997) |  |
| Hypervisor e computação em nuvem (2000+) |  |
| Transformers / IA Generativa (2017/2022) |  |

### Atividade 1.2: Discussão em Grupo, 10 min

Discuta no grupo: **"Qual desses marcos foi mais importante para a Inteligência Artificial aplicada a negócios? Por que?"**

Registre a conclusão do grupo em 3 a 5 linhas.

## Parte 2 — Transacional vs. Analítico (20 min)

### Atividade 2.1: Classifique os Sistemas, 10 min

Classifique cada sistema da LODLog como **Transacional (T)** ou **Analítico (A)**. Justifique em uma frase.

|  |  |  |
| --- | --- | --- |
| Sistema | T ou A? | Justificativa |
| ERP que registra o pagamento de um pedido |  |  |
| Dashboard de SLA de entregas do mês |  |  |
| WMS que baixa o estoque no momento da expedição |  |  |
| Modelo de ML que prediz atraso de entrega |  |  |
| TMS que aloca um veículo a um pedido |  |  |
| Relatório de ranking de CDs por eficiência |  |  |
| API de IoT que recebe evento do sensor da frota |  |  |
| Planilha Excel usada pelo supervisor para escalar motoristas |  |  |

### Atividade 2.2: Mapeamento LODLog, 10 min

No cenário da LODLog, liste:

1. **3 sistemas transacionais** que a empresa provavelmente já possui.
2. **2 sistemas analíticos** que ela deveria ter.
3. **1 sistema que começa como transacional e vira analítico** (ex: dados de IoT).

## Parte 3 — Os 5 Vs na LODLog (25 min)

### Atividade 3.1: Preencha a Matriz dos 5 Vs grupo, 15 min

Para cada fonte de dados da LODLog, discuta e preencha o seu perfil nos 5 Vs e como ela se conecta com as necessidades de Ciência de Dados e IA (exemplos de uso prático):

|  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| Fonte | Valor (insights) | Veracidade (desafios) | Variedade (formato) | Velocidade | Volume/  dia | Conexão com CD (ML/IA) |
| Sensores IoT da frota |  |  |  |  |  |  |
| Pedidos do TMS |  |  |  |  |  |  |
| Estoque do WMS |  |  |  |  |  |  |
| APIs externas (clima, tráfego) |  |  |  |  |  |  |
| Planilhas Excel do supervisor |  | NA | NA |  | NA |  |

### Atividade 3.2: Priorização, 10 min

Dado o problema de negócio da LODLog (*"estamos perdendo dinheiro, mas não sabemos onde"*), ordene as fontes acima por **prioridade de ingestão** (1 = mais urgente). Justifique a escolha do top 3.

## Parte 4 — Nuvem e Modelos de Serviço (20 min)

### Atividade 4.1: Classifique os Serviços individual, 10 min

Classifique cada serviço/tecnologia como **IaaS**, **PaaS**, **SaaS** ou **On-Premise**:

|  |  |
| --- | --- |
| Serviço/Tecnologia | IaaS / PaaS / SaaS / On-Prem? |
| Servidor físico no datacenter da empresa |  |
| Amazon EC2 (maquina virtual) |  |
| Amazon RDS (banco gerenciado) |  |
| Power BI Online |  |
| Databricks Community Edition |  |
| PostgreSQL instalado em um EC2 |  |
| Snowflake |  |
| Excel instalado no computador do usuário |  |

### ----linha de base---

## Material de Apoio

* Slide 21 da Aula 1: "Informação transacional vs informação analítica"
* Slide 26: "Big Data: os 5 Vs"
* Slide 36: "Modelo de serviço em nuvem (IaaS/PaaS/SaaS)"

**Dica do Professor:** Não se preocupe em "acertar" a arquitetura agora. O objetivo do LAB 1 é **diagnosticar** o que o grupo já sabe e **alinhá-lo** com os conceitos da aula. A arquitetura evoluirá nos próximos labs.