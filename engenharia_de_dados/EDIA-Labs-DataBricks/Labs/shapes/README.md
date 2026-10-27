# Malha municipal do Brasil (IBGE 2025, simplificada)

`BR_Municipios_2025_simplificado.zip` é o shapefile **BR_Municipios_2025** da [Malha Municipal Digital do IBGE](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html), com as geometrias simplificadas para caber no repositório.

| | Original IBGE | Este arquivo |
| --- | --- | --- |
| Tamanho do zip | ~237 MB | ~26 MB |
| Vértices | ~20 milhões | ~1,9 milhão |
| Municípios | 5.573 | 5.573 |
| Atributos | `CD_MUN`, `NM_MUN`, `SIGLA_UF`, `NM_REGIAO`, `AREA_KM2` etc. | iguais |
| CRS | SIRGAS 2000 (EPSG:4674), graus | igual |

**Simplificação:** tolerância de 0,0005° (~55 m), com `simplify(preserve_topology=True)` do shapely. As fronteiras entre municípios vizinhos podem ficar com pequenas sobreposições ou frestas dessa ordem. Num teste com 22 mil pontos aleatórios, 0,13% caíram em município diferente do original. Para geolocalizar posts no nível de município isso é suficiente. Para uso cartográfico ou oficial, use o arquivo original do IBGE.

**Regerar:** veja `gerar_simplificado.py`.

**Uso:** notebook `Labs/LAB4-X-API.ipynb` (Passo 8), que carrega o shapefile como a tabela `lodlog_lake.municipios_br`.

Antes de usar os dados, leia a nota metodológica do IBGE citada no `LEIA-ME.txt` dentro do zip.
