"""Régua municipal dos fundos da Celesc; nunca converter DCSC-00006.

ROBOTS.TXT É OBRIGATÓRIO AQUI (decisão do Jefferson, 04/10/2026)
----------------------------------------------------------------
O documento da Defesa Civil de Indaial está no Google Docs, e o texto sai pelo
caminho de exportação (`/document/d/<id>/export?format=txt`). A captura de
28/09/2026 consultou o robots.txt de `docs.google.com`, viu que ele recusa esse
caminho e não pediu (docs/CAPTURA-FONTES-2026-09-28.md). Este coletor pedia
mesmo assim. Agora ele consulta o robots.txt antes de cada coleta e, se o
caminho for proibido, **não baixa**: avisa o motivo no log e devolve lista
vazia, sem derrubar as outras cidades da rodada.

Sem contorno: não troca de User-Agent, não usa outro endereço que entregue o
mesmo documento (`/pub`, `/gviz`, `mobilebasic`…) e não trata o documento como
exceção. A leitura de Indaial volta por captura manual autorizada ou por outra
fonte pública que o robots.txt libere.

Na dúvida, não se pede: robots.txt que não responde (5xx, rede, 429) conta
como recusa. Só 4xx conta como "sem regras", que é o que a RFC 9309 diz. O
caminho é proibido se QUALQUER uma de três leituras o proibir: a do projeto
(`robots_permite`, a mesma da captura), a da biblioteca padrão
(`urllib.robotparser`) e uma que entende os curingas `*` e `$` da RFC 9309,
que as outras duas não entendem.
"""
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

from comum import USER_AGENT, baixar
from importar_cotas_rio_do_sul import robots_permite

FONTE = "https://docs.google.com/document/d/1EN1iEU3lDUfRnOtPx6IjeSpoO7DMGd-iD4i2AdHiFvk/edit"
URL = FONTE.removesuffix("/edit") + "/export?format=txt"
ROBOTS = "https://docs.google.com/robots.txt"

#: O que sai no log quando o robots.txt recusa. Frase fixa, para o log de 15 em
#: 15 min responder sozinho por que Indaial não veio.
MOTIVO_ROBOTS = ("bloqueado por robots.txt ({robots} recusa {caminho}); "
                 "usar captura manual autorizada ou outra fonte pública")


def caminho_com_consulta(url: str) -> str:
    u = urlparse(url)
    return (u.path or "/") + (f"?{u.query}" if u.query else "")


def _proibido_com_curinga(texto: str, caminho: str) -> bool:
    """`Disallow` do grupo `*` com `*` (qualquer coisa) e `$` (fim), sem `Allow`.

    Ignorar o `Allow` é deliberado: só pode tornar a resposta mais restritiva.
    """
    no_grupo, proibido = False, False
    for linha in texto.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if ":" not in linha:
            continue
        chave, valor = (p.strip() for p in linha.split(":", 1))
        chave = chave.lower()
        if chave == "user-agent":
            no_grupo = valor == "*"
        elif chave == "disallow" and no_grupo and valor:
            padrao = re.escape(valor).replace(r"\*", ".*")
            if padrao.endswith(r"\$"):
                padrao = padrao[:-2] + "$"
            if re.match(padrao, caminho):
                proibido = True
    return proibido


def robots_proibe(texto: str, url: str = URL) -> bool:
    """O robots.txt proíbe esta URL? Basta uma das três leituras dizer que sim."""
    caminho = caminho_com_consulta(url)
    if not robots_permite(texto, caminho) or _proibido_com_curinga(texto, caminho):
        return True
    leitor = RobotFileParser()
    leitor.parse(texto.splitlines())
    return not leitor.can_fetch(USER_AGENT, url)


def motivo_para_nao_baixar(buscar=None) -> str | None:
    """None se o robots.txt libera o documento; senão, o motivo em uma frase."""
    buscar = buscar or baixar
    try:
        texto = buscar(ROBOTS)
    except Exception as exc:
        if re.search(r"\b4(?!29)\d\d Client Error", str(exc)):
            return None  # robots.txt inexistente: sem regras (RFC 9309)
        return (f"robots.txt de docs.google.com sem resposta ({exc}); "
                "na dúvida, o documento não foi pedido")
    if robots_proibe(texto, URL):
        return MOTIVO_ROBOTS.format(robots=ROBOTS, caminho=caminho_com_consulta(URL))
    return None


def interpretar(texto, agora=None):
    agora = agora or datetime.now(ZoneInfo("America/Sao_Paulo"))
    agora = agora.astimezone(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
    if "Régua instalada fundos Celesc" not in texto:
        raise ValueError("Referência municipal não encontrada")
    data = None
    valores = {}
    for linha in texto.splitlines():
        linha = linha.strip().lstrip("﻿")
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
    return {
        "estacao": "Indaial — fundos da Celesc (Defesa Civil)",
        "cidade": "indaial", "rio": "itajai-acu", "nivel_m": valores[instante],
        "medido_em": instante.isoformat(), "fonte": FONTE}


def coletar(buscar=None):
    """A leitura municipal de Indaial, ou [] — nunca uma exceção.

    `buscar` entra por parâmetro para o teste; sem ele, `comum.baixar`, lido na
    hora da chamada.
    """
    buscar = buscar or baixar
    motivo = motivo_para_nao_baixar(buscar)
    if motivo:
        print(f"aviso: régua municipal de Indaial não coletada — {motivo}.", file=sys.stderr)
        return []
    try:
        return [interpretar(buscar(URL))]
    except Exception as exc:
        print(f"aviso: régua municipal de Indaial indisponível: {exc}", file=sys.stderr)
        return []


if __name__ == "__main__":
    import json
    print(json.dumps(coletar(), ensure_ascii=False, indent=2))
