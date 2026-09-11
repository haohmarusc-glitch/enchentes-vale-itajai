#!/usr/bin/env python3
"""Importa o cadastro XLSX do Cemaden; não importa medições nem ativa estações.

Uso: python scripts/importar_rede_cemaden.py caminho/arquivo.xlsx
Somente biblioteca padrão. Preserva a origem por hash, aba e linha.
"""

import argparse
import hashlib
import json
import math
import posixpath
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ABA = "Rede Cemaden SC"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
DESTINO = Path(__file__).resolve().parents[1] / "data/cemaden-rede-observacional-sc.json"


def importar(arquivo: Path) -> dict:
    with ZipFile(arquivo) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(e.itertext()) for e in
                       ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        sheets = ET.fromstring(z.read("xl/workbook.xml")).findall("s:sheets/s:sheet", NS)
        sheet = next(s for s in sheets if s.attrib["name"] == ABA)
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.attrib["Target"] for r in rels if r.attrib["Id"] == sheet.attrib[REL])
        target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
        registros, codigos = [], set()
        for row in ET.fromstring(z.read(target)).findall("s:sheetData/s:row", NS):
            linha = int(row.attrib["r"])
            valores = {}
            for c in row.findall("s:c", NS):
                coluna = "".join(ch for ch in c.attrib["r"] if ch.isalpha())
                v = c.find("s:v", NS)
                valor = v.text if v is not None else ""
                if c.attrib.get("t") == "s":
                    valor = strings[int(valor)]
                elif c.attrib.get("t") == "inlineStr":
                    valor = "".join(c.find("s:is", NS).itertext())
                valores[coluna] = valor
            campos = [valores.get(c, "") for c in "ABCDEFG"]
            if not any(campos):
                continue
            if linha == 1:
                if campos != ["Codigo PCD", "Tipo rede", "UF", "Município", "lat", "long", "status"]:
                    raise ValueError("Cabeçalho diferente do cadastro esperado")
                continue
            codigo, tipo, uf, municipio, lat, lon, status = campos
            if not all(campos) or codigo in codigos:
                raise ValueError(f"Linha {linha}: campos ausentes ou código duplicado")
            if tipo not in {"Pluviométrica", "Hidrológica"} or status not in {"Operacional", "Inativa"} or uf != "SC":
                raise ValueError(f"Linha {linha}: tipo, UF ou status inesperado")
            lat, lon = float(lat), float(lon)
            if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"Linha {linha}: coordenadas inválidas")
            codigos.add(codigo)
            registros.append(dict(codigo=codigo, tipo_rede=tipo, uf=uf, municipio=municipio,
                                  lat=lat, lon=lon, status_cadastro=status, linha_origem=linha))
    if not registros:
        raise ValueError("Cadastro vazio")
    return {"_meta": {"arquivo_origem": arquivo.name, "aba": ABA,
                      "sha256": hashlib.sha256(arquivo.read_bytes()).hexdigest(),
                      "data_referencia_status": None,
                      "nota": "Cadastro fornecido pelo usuário. Status não comprova transmissão atual. "
                              "Sem medições, cotas, datum ou data de atualização por estação."},
            "estacoes": registros}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arquivo", type=Path)
    ap.add_argument("--destino", type=Path, default=DESTINO)
    args = ap.parse_args()
    dados = importar(args.arquivo)
    args.destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(dados['estacoes'])} estações importadas")
