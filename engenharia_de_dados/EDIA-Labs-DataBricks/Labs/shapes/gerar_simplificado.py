"""Gera BR_Municipios_2025_simplificado.zip a partir da malha municipal do IBGE.

O shapefile original (BR_Municipios_2025.zip, ~237 MB) passa do limite de 100 MB
por arquivo do GitHub. As geometrias são simplificadas com tolerância de 0,0005°
(~55 m), mantendo atributos, CRS (SIRGAS 2000, EPSG:4674) e nomes dos arquivos.

Uso:
    pip install geopandas
    curl -LO https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip
    python gerar_simplificado.py BR_Municipios_2025.zip
"""
import os
import sys
import tempfile
import zipfile

import geopandas as gpd

TOLERANCIA_GRAUS = 0.0005
SAIDA = "BR_Municipios_2025_simplificado.zip"

origem = sys.argv[1]
mun = gpd.read_file(origem)
mun["geometry"] = mun.geometry.simplify(TOLERANCIA_GRAUS, preserve_topology=True)
assert mun.is_valid.all() and not mun.is_empty.any()

with tempfile.TemporaryDirectory() as tmp:
    mun.to_file(os.path.join(tmp, "BR_Municipios_2025.shp"), engine="pyogrio")
    with zipfile.ZipFile(SAIDA, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome in sorted(os.listdir(tmp)):
            zf.write(os.path.join(tmp, nome), nome)
        with zipfile.ZipFile(origem) as zorig:
            zf.writestr("LEIA-ME.txt", zorig.read("LEIA-ME.txt"))
print(f"{len(mun)} municípios gravados em {SAIDA} ({os.path.getsize(SAIDA) / 1e6:.1f} MB)")
