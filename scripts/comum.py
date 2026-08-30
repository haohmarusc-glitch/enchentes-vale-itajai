"""Utilidades compartilhadas pelos scripts de coleta e análise.

Regras que valem para todos os scripts (CLAUDE.md):

* idempotência: rodar duas vezes não duplica nem apaga registro;
* nada de credencial em código — chaves vêm do `.env`, que está no `.gitignore`;
* todo request se identifica no `User-Agent` e respeita intervalo entre chamadas.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"

USER_AGENT = (
    "enchentes-vale-itajai/0.1 (projeto aberto de dados de enchentes; "
    "contato via repositório GitHub)"
)

#: Intervalo mínimo entre chamadas à mesma fonte, em segundos.
INTERVALO_S = 1.5

_ultima_chamada = 0.0


def espera_turno() -> None:
    """Segura a chamada para não sobrecarregar servidor público."""
    global _ultima_chamada
    agora = time.monotonic()
    resta = INTERVALO_S - (agora - _ultima_chamada)
    if resta > 0:
        time.sleep(resta)
    _ultima_chamada = time.monotonic()


def carrega_env(caminho: Path | None = None) -> None:
    """Lê um `.env` simples (CHAVE=valor) para o ambiente, sem sobrescrever."""
    arquivo = caminho or (RAIZ / ".env")
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


def le_json(nome: str) -> Any:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def grava_json(nome: str, conteudo: Any) -> None:
    """Grava com quebra de linha final e acentos preservados.

    Escreve num arquivo temporário e só então substitui o original: se o
    processo morrer no meio, o arquivo bom continua lá. Estes JSONs são a
    fonte de verdade do site — perder um deles é perder o projeto.
    """
    destino = DADOS / nome
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    temporario.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporario.replace(destino)


def cidades(rio: str | None = None) -> list[dict[str, Any]]:
    """Cidades de `estacoes.json`, em ordem montante -> jusante."""
    estacoes = le_json("estacoes.json")
    saida: list[dict[str, Any]] = []
    for rio_id, dados in estacoes["rios"].items():
        if rio is not None and rio_id != rio:
            continue
        for cidade in sorted(dados["cidades"], key=lambda c: c["ordem"]):
            saida.append({**cidade, "rio": rio_id})
    return saida


# --- Estações de tempo real -------------------------------------------------
#
# A ligação entre o título que a Defesa Civil publica e o par (rio, cidade)
# fica em `estacoes.json`, não aqui: é dado, não código, e quem mantém os dados
# precisa poder acrescentar estação sem mexer em Python. As expressões abaixo
# são só a rede de segurança para um título que ainda não esteja cadastrado.

import re as _re

_FALLBACK: list[tuple[str, str, str]] = [
    (r"^DC-0[12]\b", "itajai-acu", "itajai"),
    (r"^DC-11\b", "itajai-acu", "ilhota"),
    (r"^DC-0[3456]\b", "itajai-mirim", "itajai"),
    (r"^DC-10\b", "itajai-mirim", "itajai"),
    (r"^DC-07\b|^DC-09\b", "ribeirao-murta", "itajai"),
    (r"^DC-08\b", "ribeirao-canhanduba", "itajai"),
    (r"^Brusque", "itajai-mirim", "brusque"),
    (r"^Blumenau", "itajai-acu", "blumenau"),
    (r"^Rio do Sul", "itajai-acu", "rio-do-sul"),
]


def estacoes_tempo_real() -> list[dict[str, Any]]:
    return le_json("estacoes.json").get("estacoes_tempo_real", [])


def estacao_por_titulo(titulo: str) -> dict[str, Any] | None:
    """
    A estação cadastrada que corresponde a este título.

    Casa pelo título exato e, se não achar, pelo código DC-NN no começo — a
    Defesa Civil já mudou o texto depois do código mais de uma vez, e o código
    é a parte estável.
    """
    cadastradas = estacoes_tempo_real()
    for e in cadastradas:
        if e.get("titulo") == titulo:
            return e
    codigo = _re.match(r"^(DC-\d{2})\b", titulo or "")
    if codigo:
        for e in cadastradas:
            if e.get("codigo") == codigo.group(1):
                return e
    return None


def classificar_estacao(titulo: str) -> tuple[str | None, str | None]:
    """(rio, cidade) da estação, ou (None, None) quando o título é desconhecido."""
    e = estacao_por_titulo(titulo)
    if e:
        return e.get("rio"), e.get("cidade")
    for padrao, rio, cidade in _FALLBACK:
        if _re.search(padrao, titulo or ""):
            return rio, cidade
    return None, None


def cota_da_estacao(titulo: str) -> tuple[float | None, str | None]:
    """
    Cota de referência DESTA régua, quando cadastrada em `estacoes.json`.

    Existe porque a cota da cidade não serve para uma cidade com várias réguas:
    os zeros são diferentes, e aplicar a mesma a todas criaria evento onde não
    há e esconderia onde há.
    """
    e = estacao_por_titulo(titulo)
    for chave in ("atencao", "alerta", "inundacao"):
        valor = (e or {}).get("cotas_m", {}).get(chave)
        if isinstance(valor, (int, float)):
            return float(valor), chave
    return None, None


def cota_de_referencia(rio: str, cidade: str) -> tuple[float | None, str | None]:
    """
    Cota a partir da qual vale considerar que há cheia, pela CIDADE.

    Prefere 'atencao', depois 'alerta', depois 'inundacao'. Devolve (None, None)
    quando a cidade não tem cota levantada — e nesse caso quem chama deve pedir
    um limiar explícito em vez de inventar um.
    """
    estacoes = le_json("estacoes.json")
    rio_dados = estacoes["rios"].get(rio)
    if not rio_dados:
        return None, None
    for c in rio_dados["cidades"]:
        if c["id"] != cidade:
            continue
        for chave in ("atencao", "alerta", "inundacao"):
            if chave in c.get("cotas_m", {}):
                return float(c["cotas_m"][chave]), chave
    return None, None
