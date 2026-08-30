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
