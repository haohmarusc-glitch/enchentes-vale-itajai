#!/usr/bin/env python3
"""A consulta `Tags_data` que o próprio mapa da Defesa Civil de SC usa — a única que a API aceita hoje.

O QUE MUDOU (descoberto em 20/11/2026): entre 17/11/2026 10h31 e 20/11, a API GraphQL de
monitoramento.defesacivil.sc.gov.br passou a recusar TODA consulta `Tags_data` que não seja o texto
de uma lista fechada:

    HTTP 400 {"errors":[{"message":"Consulta não permitida. Use exatamente o texto das consultas
    do guia da API (docs/guia-da-api.md).","extensions":{"code":"QUERY_NOT_ALLOWED"}}]}

As três consultas do `coleta_nivel_sc.py`, a da chuva e a do `gaspar_estadual.py` caíram juntas. O
`ultimo_nivel_sc.json` ficou parado em 17/11 10h31, e Brusque, Ascurra e Rio dos Cedros (que só têm
leitura pela rede estadual) ficaram cinza no site, como manda a regra para leitura antiga.

O "guia da API" citado na mensagem não está publicado em lugar que tenhamos achado. A consulta que o
mapa público deles faz ao abrir — no arquivo JavaScript que o próprio site serve — é aceita, e o
`Historic` (série) continua aceito do jeito que já pedíamos. O servidor ignora diferença de espaços;
o que conta são os campos.

POR QUE ISTO É LEGÍTIMO: é a própria API dizendo qual texto usar, e usamos exatamente o texto que o
site deles manda, com o User-Agent do projeto e o mesmo ritmo de sempre. Nada aqui contorna bloqueio:
não pedimos campo que a lista recusa. Em particular, `rio_alarmes` (a faixa estadual) NÃO está nesta
consulta — enquanto só ela for aceita, a classificação estadual sai `indisponivel`, com o motivo.

O texto fica num arquivo próprio, copiado sem mudança (`consultas_dcsc/tags_data_do_site.graphql`).
Se a DCSC trocar o site e a consulta, a recusa volta a aparecer no log e no `consulta.motivo`; aí se
copia o texto novo do arquivo JavaScript atual — nunca se monta à mão.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ARQUIVO = Path(__file__).resolve().parent / "consultas_dcsc" / "tags_data_do_site.graphql"

#: Onde o texto foi copiado, e quando. O nome do arquivo JavaScript muda a cada versão do site.
ORIGEM = "https://monitoramento.defesacivil.sc.gov.br/assets/U7pWP52Ug3.js"
COPIADA_EM = "2026-11-20"

TAGS_DATA_DO_SITE: str = ARQUIVO.read_text(encoding="utf-8")


#: Hora de Brasília (sem horário de verão desde 2019).
FUSO_BRASILIA = timezone(timedelta(hours=-3))


def instante(carimbo: Any) -> datetime | None:
    """O `timestamp` da DCSC como instante com fuso.

    Até 17/11/2026 a API mandava UTC com offset (`…+00:00`). Desde a lista fechada, a consulta do site
    devolve o carimbo SEM fuso (`2026-11-20T19:55:00.000`), e ele é hora de BRASÍLIA: conferido em
    20/11/2026 às 22h57 UTC pelo cabeçalho `Date` do próprio servidor, com 170 estações marcando 19h55.
    Ler o sem-fuso como UTC deixaria toda leitura três horas mais velha, e leitura velha não pinta.
    Com offset, o offset manda; sem offset, Brasília.
    """
    if not carimbo:
        return None
    try:
        t = datetime.fromisoformat(str(carimbo).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=FUSO_BRASILIA)


def hora_de_brasilia(carimbo: Any) -> str | None:
    """O carimbo da DCSC no formato do projeto: hora de Brasília sem fuso, em segundos."""
    t = instante(carimbo)
    return t.astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds") if t else None


class Recusada(RuntimeError):
    """A API devolveu `errors`. `args[0]` é a lista crua de erros, para o motivo sair como a API disse."""


def mensagem(e: Exception) -> str:
    """O que a API disse, como ela disse: `errors[].message` do GraphQL, ou o erro HTTP."""
    arg = e.args[0] if e.args else None
    if isinstance(arg, list):
        textos = [x.get("message") for x in arg if isinstance(x, dict) and x.get("message")]
        if textos:
            return "; ".join(str(t) for t in textos)
    return str(e)


def corpo(resposta: Any) -> dict:
    """O JSON de uma resposta do `requests`. A recusa do GraphQL vem em HTTP 400 COM `errors`: devolve o
    corpo, para a mensagem da API chegar ao motivo (o `raise_for_status` só diria "400 Client Error")."""
    if getattr(resposta, "status_code", None) == 400:
        try:
            j = resposta.json()
        except ValueError:
            j = None
        if isinstance(j, dict) and j.get("errors"):
            return j
    resposta.raise_for_status()
    return resposta.json()


def estacoes(j: dict) -> list[dict]:
    if j.get("errors"):
        raise Recusada(j["errors"])
    return (((j.get("data") or {}).get("tags_data") or {}).get("qualle_meteorologia") or [])


def tags_data(pedir: Callable[[str], dict], propria: str) -> tuple[list[dict], dict[str, Any]]:
    """Tenta a consulta `propria` (menor); se a API recusar, a do site. Devolve (estações, consulta).

    `pedir(query) -> corpo JSON` faz o POST (e levanta em erro HTTP). `consulta` diz qual texto
    respondeu e, quando foi o do site, a recusa real da própria — para o log não esconder a mudança.
    """
    try:
        return estacoes(pedir(propria)), {"degrau": "propria", "motivo": None}
    except Exception as e:  # noqa: BLE001 — a recusa é dado: vai para o motivo
        recusa = mensagem(e)
    try:
        lista = estacoes(pedir(TAGS_DATA_DO_SITE))
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"consulta recusada: própria ({recusa}); do site ({mensagem(e)})") from e
    return lista, {"degrau": "site", "motivo": f"consulta própria recusada: {recusa}"}
