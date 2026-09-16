"""Régua municipal dos fundos da Celesc; nunca converter DCSC-00006."""
import re
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from comum import baixar

FONTE = "https://docs.google.com/document/d/1EN1iEU3lDUfRnOtPx6IjeSpoO7DMGd-iD4i2AdHiFvk/edit"
URL = FONTE.removesuffix("/edit") + "/export?format=txt"


def interpretar(texto, agora=None):
    agora = agora or datetime.now(ZoneInfo("America/Sao_Paulo"))
    agora = agora.astimezone(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
    if "Régua instalada fundos Celesc" not in texto:
        raise ValueError("Referência municipal não encontrada")
    data = None
    valores = {}
    for linha in texto.splitlines():
        linha = linha.strip().lstrip("\ufeff")
        dia = re.fullmatch(r"(\d{2})/?(\d{2})/(\d{4})", linha)
        if dia:
            # Documento publica o dia mais recente no topo. Não misturar
            # o arquivo histórico (que contém erros de digitação) ao vivo.
            if data is not None:
                break
            data = datetime(int(dia[3]), int(dia[2]), int(dia[1]))
            continue
        # Não carregar a data anterior através de cabeçalho malformado.
        if re.match(r"\d.*?/.*?\d{4}", linha):
            raise ValueError("Cabeçalho de data ambíguo")
        leitura = re.fullmatch(r"(\d{1,2})h(?:(\d{2}))?\s*-\s*(\d{1,2}[,.]\d{1,2})\s*m", linha)
        if not leitura or data is None:
            continue
        instante = data.replace(hour=int(leitura[1]), minute=int(leitura[2] or 0))
        valor = float(leitura[3].replace(",", "."))
        if instante > agora + timedelta(minutes=15):
            raise ValueError("Medição no futuro")
        if instante in valores and valores[instante] != valor:
            raise ValueError("Valores conflitantes para o mesmo horário")
        valores[instante] = valor
    if not valores:
        raise ValueError("Nenhuma medição municipal válida")
    instante = max(valores)
    return {"estacao": "Indaial — fundos da Celesc (Defesa Civil)",
            "cidade": "indaial", "rio": "itajai-acu", "nivel_m": valores[instante],
            "medido_em": instante.isoformat(), "fonte": FONTE}


def coletar():
    try:
        return [interpretar(baixar(URL))]
    except Exception as exc:
        print(f"aviso: régua municipal de Indaial indisponível: {exc}", file=sys.stderr)
        return []


if __name__ == "__main__":
    import json
    print(json.dumps(coletar(), ensure_ascii=False, indent=2))
