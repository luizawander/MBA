**LAB 3 — SQL Avançado e Preparação de Dados para Modelos de IA**

**Disciplina** Engenharia de Dados para Inteligência Artificial e Analytics (MBA)

**Aula**3 — SQL analítico e pipeline de Feature Engineering

**Duração do Lab**~1h30min

**Ambiente** Databricks Community Edition

**Objetivos de Aprendizagem**

Ao final deste laboratório, você será capaz de:

1. Escrever consultas analíticas avançadas em Spark SQL (JOINs de múltiplas tabelas, agregações e filtragens pós-agrupamento).
2. Aplicar **Window Functions** no Databricks para gerar métricas de ranking, percentil e médias móveis (análise de séries temporais).
3. Construir um pipeline de **Feature Engineering** gerando uma View de Feature Store consolidada para alimentar modelos de IA.
4. Escrever queries de auditoria para detectar e diagnosticar anomalias de **Qualidade de Dados** (duplicatas, valores negativos, outliers e quebra de integridade referencial).

**Importante:** Este laboratório utiliza exclusivamente o ambiente corporativo da **Databricks Community Edition**. O banco de dados mestre da LODLog já foi reestruturado na **Versão 3 (v3)**, separando a base operacional transacional (lodlog\_op) e o modelo multidimensional analítico (lodlog\_dw).

**Parte 0 — Setup do Ambiente no Databricks (10 min)**

Para inicializar os dados da LODLog no seu ambiente gratuito do Databricks, siga os passos abaixo:

1. Acesse [community.cloud.databricks.com](https://community.cloud.databricks.com/) e faça login.
2. No painel lateral esquerdo, selecione **Workspace**, clique em “Create Git Folder”.

![](data:image/png;base64...)

Já fizemos no LAB2, mas se ainda não fez, adicione o endereço <https://github.com/Escola-de-Matematica-Aplicada/EDIA-Labs-DataBricks.git>

1. Na pasta “EDIA-Labs-DataBricks” abra “Labs” e execute apenas Labs/lodlog\_lab3\_seed\_v3, considerando que você já rodou na última aula “Labs/lodlog\_modelo\_dados\_v3.sql”.
2. Com o notebook aberto, clique em **Run All** (ou *Executar tudo*) no canto superior direito. Certifique-se de a opção “Serverless” estar selecionada.

![](data:image/png;base64...)

Esse script irá demorar cerca de 2 minutos para rodar. Ele irá carregar dados aleatórios no banco de dados operacional lodlog\_op, e no analítico lodlog\_dw (Star Schema) e popular a tabela fato com 50.000 entregas fictícias.

1. Após a execução do seed terminar com sucesso, abra o notebook “Labs/LAB3\_apoio” para desenvolver as atividades do LAB.
2. Na primeira célula do seu novo notebook, execute o comando de seleção de banco:

%sql

USE lodlog\_dw;

SHOW TABLES;

**Parte 1 — Análise Exploratória com SQL (25 min)**

**Atividade 1.1: Conhecendo os Dados do DW (10 min, individual)**

As tabelas do modelo dimensional analítico estão salvas sob o schema lodlog\_dw. Execute e interprete as três queries analíticas abaixo. Em seu notebook, escreva uma frase curta de interpretação sobre o que o resultado revela para a gestão da LODLog.

-- Query 1: Volume de entregas e atrasos por mês

SELECT DATE\_TRUNC('month', data\_entrega) AS mes,

COUNT(\*) AS total\_entregas,

SUM(CASE WHEN minutos\_atraso > 0 THEN 1 ELSE 0 END) AS entregas\_atrasadas

FROM fato\_entregas

GROUP BY 1

ORDER BY 1;

**Sua Interpretação:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

-- Query 2: Ranking de Centros de Distribuição (CD) por eficiência operacional

SELECT cd.codigo AS cd\_origem,

ROUND(AVG(fe.minutos\_atraso), 2) AS atraso\_medio\_min,

ROUND(SUM(fe.custo\_combustivel + fe.custo\_pedagio), 2) AS custo\_total\_operacional,

COUNT(DISTINCT fe.sk\_veiculo) AS frota\_alocada

FROM fato\_entregas fe

INNER JOIN dim\_centro\_distribuicao cd ON fe.sk\_cd\_origem = cd.sk\_cd

WHERE fe.data\_entrega >= CURRENT\_DATE - INTERVAL '90 days'

GROUP BY cd.codigo

ORDER BY atraso\_medio\_min ASC;

**Sua Interpretação:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

-- Query 3: Correlação estatística simples entre a distância percorrida e o custo de combustível

SELECT corr(distancia\_km, custo\_combustivel) AS correlacao\_distancia\_custo

FROM fato\_entregas

WHERE data\_entrega >= CURRENT\_DATE - INTERVAL '30 days';

**Sua Interpretação:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Atividade 1.2: Sua Primeira Query Analítica (15 min, individual)**

Escreva uma consulta SQL para responder à seguinte pergunta da diretoria comercial:

**"Qual o percentual de entregas no prazo por cliente nos últimos 90 dias, considerando apenas clientes com mais de 10 entregas realizadas no período?"**

**Dicas de implementação:**

* Faça um INNER JOIN entre a fato fato\_entregas e a dimensão dim\_cliente (utilizando as surrogate keys).
* Filtre a data de entrega usando a cláusula WHERE fe.data\_entrega >= CURRENT\_DATE - INTERVAL '90 days'.
* Use GROUP BY na coluna razao\_social do cliente.
* Filtre o total de grupos utilizando HAVING COUNT(\*) > 10.
* Calcule o percentual de pontualidade: considere uma entrega "no prazo" se a coluna minutos\_atraso = 0 (ou utilize o indicador\_atraso = 0). Divida o volume pontual pelo total de entregas e multiplique por 100 (arredonde com ROUND(..., 2)).
* Ordene do menor percentual de pontualidade (piores clientes) para o maior.

-- Escreva sua query de pontualidade aqui e execute no Databricks

**Parte 2 — Window Functions e Séries Temporais (25 min)**

**Atividade 2.1: Média Móvel de Atrasos por CD (10 min, individual)**

Métricas de tempo de atraso diário são ruidosas. Para suavizar as tendências em relatórios de BI, a gerência pediu para calcular a **média móvel de 7 dias** de atrasos das entregas agrupadas por centro de distribuição.

Escreva a query que retorne o CD (código), a data da entrega, o atraso individual da linha e a média móvel das últimas 7 linhas daquele mesmo CD (ordenadas por data).

**Dica Spark SQL:** Use a estrutura AVG(minutos\_atraso) OVER (PARTITION BY sk\_cd\_origem ORDER BY data\_entrega ROWS BETWEEN 6 PRECEDING AND CURRENT ROW). Se quiser exibir o código amigável do CD, realize o JOIN com dim\_centro\_distribuicao.

-- Escreva sua query de média móvel aqui

**Atividade 2.2: Ranking de Eficiência da Frota (10 min, individual)**

Escreva uma consulta que analise o custo de combustível por quilômetro rodado de cada motorista (tabela `dim\_motorista`) nos últimos 30 dias. A query deve classificar os motoristas em **quartis (1 a 4)** utilizando a window function de segmentação NTILE e calcular o **percentil exato** de eficiência utilizando a função PERCENT\_RANK().

**Dica de estrutura:** Crie uma CTE temporária agrupando as entregas por sk\_motorista para obter o custo de combustível por km (SUM(custo\_combustivel) / NULLIF(SUM(distancia\_km), 0)). Em seguida, na consulta principal externa, faça um JOIN com dim\_motorista e aplique NTILE(4) OVER (ORDER BY custo\_por\_km ASC) e PERCENT\_RANK() OVER (ORDER BY custo\_por\_km ASC).

-- Escreva sua query de ranking de motoristas aqui

**Atividade 2.3: Discussão Analítica (5 min, em grupo)**

Debata com seu grupo: do ponto de vista de arquitetura de banco de dados e plano de execução, por que as **Window Functions** são computacionalmente mais eficientes no Spark SQL do que implementar a mesma lógica utilizando subqueries correlacionadas clássicas?

**Parte 3 — Feature Engineering em SQL (30 min)**

**Atividade 3.1: Crie a View de Feature Store vw\_features\_ml (20 min, em grupo)**

Os cientistas de dados precisam treinar um modelo preditivo de probabilidade de atraso. O modelo exige que cada linha represente uma entrega com um conjunto unificado de 9 variáveis explicativas (features) e a variável resposta (target).

Crie a view analítica vw\_features\_ml sob o banco de dados lodlog\_dw estruturando as seguintes variáveis a partir do esquema multidimensional:

| **Nome da Feature** | **Tipo/Origem** | **Fórmula / Lógica de Extração em SQL** |
| --- | --- | --- |
| sk\_entrega | Identificador | Chave surrogate da entrega (já existe em fato\_entregas) |
| distancia\_km | Numérica (Fato) | distancia\_km (da fato) |
| peso\_total\_kg | Numérica (Fato) | peso\_total\_kg (da fato) |
| hora\_saida | Numérica (Derivada) | hour(hora\_saida) ou EXTRACT(HOUR FROM hora\_saida) |
| dia\_semana | Numérica (Derivada) | dayofweek(data\_entrega) (1 = Domingo, 7 = Sábado) |
| eh\_feriado | Booleana (Dimensão) | Coluna flag\_feriado da dim\_tempo (requer JOIN) |
| temperatura\_media\_motor | Numérica (IoT) | Coluna temperatura\_media\_motor (já presente na fato) |
| historico\_atrasos\_7d | Janela (Móvel) | Média móvel de atraso (minutos) do mesmo cliente nos últimos 7 dias via Window Function |
| dias\_ultima\_manutencao | Diferença (Histórica) | Diferença em dias entre data\_entrega e a data de conclusão da última manutenção do veículo (requer JOIN com lodlog\_op.manutencao filtrando por status = 'Concluída') |
| target\_atraso | Variável Resposta | indicador\_atraso da tabela fato (0 = no prazo, 1 = atrasado) |

-- Desenvolva a View Feature Store abaixo e crie-a no Databricks

CREATE OR REPLACE VIEW lodlog\_dw.vw\_features\_ml AS

WITH hist\_cliente AS (

SELECT sk\_cliente, data\_entrega,

AVG(minutos\_atraso) OVER (

PARTITION BY sk\_cliente

ORDER BY data\_entrega

ROWS BETWEEN 6 PRECEDING AND CURRENT ROW

) AS hist\_7d

FROM fato\_entregas

),

manut\_veiculo AS (

-- Dica: Encontre a data de conclusão da última manutenção de cada veículo

SELECT veiculo\_id,

data\_conclusao,

ROW\_NUMBER() OVER (PARTITION BY veiculo\_id ORDER BY data\_conclusao DESC) as rn

FROM lodlog\_op.manutencao

WHERE status = 'Concluída'

)

SELECT

fe.sk\_entrega,

fe.distancia\_km,

fe.peso\_total\_kg,

hour(fe.hora\_saida) AS hora\_saida,

dayofweek(fe.data\_entrega) AS dia\_semana,

dt.flag\_feriado AS eh\_feriado,

fe.temperatura\_media\_motor,

ROUND(h.hist\_7d, 2) AS historico\_atrasos\_7d,

DATEDIFF(fe.data\_entrega, mv.data\_conclusao) AS dias\_ultima\_manutencao,

fe.indicador\_atraso AS target\_atraso

FROM fato\_entregas fe

INNER JOIN dim\_tempo dt ON fe.sk\_data = dt.sk\_tempo

LEFT JOIN hist\_cliente h ON fe.sk\_cliente = h.sk\_cliente AND fe.data\_entrega = h.data\_entrega

LEFT JOIN manut\_veiculo mv ON fe.sk\_veiculo = mv.veiculo\_id AND mv.rn = 1 AND mv.data\_conclusao <= fe.data\_entrega;

**-- linha de base --- a partir daqui é opcional**

**Atividade 3.2: Valide a Feature Store (10 min, individual)**

Execute as queries de validação de metadados na view recém-criada e documente os resultados:

1. **Completude:** Há registros com dados de manutenção nulos? O que isso indica?

SELECT COUNT(\*) FROM vw\_features\_ml WHERE dias\_ultima\_manutencao IS NULL;

1. **Distribuição do Target:** O dataset está balanceado em termos de atrasos?

SELECT target\_atraso, COUNT(\*) AS volume, ROUND(100.0 \* COUNT(\*) / SUM(COUNT(\*)) OVER(), 2) AS pct

FROM vw\_features\_ml

GROUP BY 1;

Montar um dashboard para controle ver o percentual de atrasos.

Dashboards -> Create dashboard -> Data -> Add data

![](data:image/png;base64...)

Escolher a view recém criada.

Você habilitou essa fonte de dados para ser usada no dashboard.

Vá na aba dashboard, adicione um gráfico com essa fonte, conforme a seguir:

![](data:image/png;base64...)

O objetivo é visualizar quantidade de atrasos por dia da semana.

![](data:image/png;base64...)

1. **Correlação com a Variável Alvo:** A quilometragem rodada está correlacionada com o atraso?

SELECT corr(distancia\_km, target\_atraso) AS correlacao\_dist\_target FROM vw\_features\_ml;

**Parte 4 — Qualidade de Dados via SQL (15 min)**

**Atividade 4.1: Auditoria Automática de Dados (10 min, individual)**

O notebook de seed introduziu anomalias operacionais na tabela fato para simular problemas de pipelines em produção. Escreva consultas SQL específicas que detectem as seguintes inconsistências em lodlog\_dw.fato\_entregas:

1. **Registros Duplicados:** Encontre registros que tenham o mesmo entrega\_id (deveria ser único por grain).

-- Escreva sua query para encontrar entrega\_id duplicados

1. **Valores Inválidos / Negativos:** Detecte registros com campos físicos negativos que violam a lógica de negócio (distância, peso ou custos).

-- Escreva sua query para valores negativos

1. **Outliers de Tempo:** Identifique registros com tempos de atraso absurdamente altos (ex: atrasos maiores que 24 horas/1440 min) ou adiantamentos fisicamente impossíveis (adiantados mais de 8 horas / -480 min).

-- Escreva sua query para outliers de atraso/adiantamento

1. **Inconsistência de Integridade (Orfãos):** Utilize uma query do tipo **Anti-Join** (LEFT JOIN ... IS NULL) para identificar registros de entregas na fato que apontam para clientes (sk\_cliente) inexistentes no cadastro de clientes (dim\_cliente).

-- Escreva sua query de auditoria referencial (Anti-Join)

**Atividade 4.2: Conexão com o Trabalho em Grupo (5 min, em grupo)**

Para cada tipo de anomalia identificado no banco multidimensional:

* Qual a causa provável desse erro na ingestão ou nos sistemas de origem?
* Como você implementaria a limpeza e conformidade dessa variável nas camadas **Bronze e Silver** do seu pipeline multi-cloud?