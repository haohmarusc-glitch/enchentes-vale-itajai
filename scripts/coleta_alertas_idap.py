#!/usr/bin/env python3
"""Alertas que as Defesas Civis mandaram à população de SC, pelo feed CAP nacional da IDAP.

POR QUE EXISTE (08/11/2026). O site `www.defesacivil.sc.gov.br` recusa conexão de fora do Brasil: a VPS
(Helsinque), o runner do GitHub e a sessão de código não conectam; do Brasil abre. A IDAP — Interface de
Divulgação de Alertas Públicos, da Defesa Civil Nacional (MIDR/SEDEC) — publica num feed Atom/CAP 1.2 os alertas
que as Defesas Civis cadastram para a população (canal Google Alertas Públicos), e a VPS alcança o feed: robots.txt
inexistente (404, sem regras) e 200 em 07/11/2026. Na leitura de 08/11, 02:12 UTC: 284 alertas das ~12 h
anteriores, 15 de SC — Defesa Civil Estadual ("ATENÇÃO – INUNDAÇÃO GRADUAL … para o município de Gaspar") e
AlertaBlu ("previsão … 8,20 m à 01h do dia 08/11/26, sendo este o pico estimado").

O QUE ELE DIZ E O QUE NÃO DIZ. Cada alerta traz o município pelo código IBGE (ou "SANTA CATARINA/SC" como área,
`area_declarada: "estado"` — e aí o TEXTO pode nomear só alguns municípios), quem emitiu, quando, até quando vale e o texto mandado à população. Nada daqui pinta faixa, dispara aviso
de cota, entra em `leituras` ou vira número de nível: é o aviso oficial, repassado com fonte, emissor e hora.
`cidades_do_projeto` só casa o NOME do município do alerta com o nome da cidade em `estacoes.json`.

LIMITES. O feed é grande (≈38 MB com os polígonos, ≈85 s para baixar da VPS) e guarda só ~12 h; por isso este
coletor roda em linha própria do cron, fora do corte de 60 s da publicação, e guarda os alertas ainda vigentes que
já saíram do feed. `publicar_tempo_real.sh` só leva o arquivo ao ar se foi gerado há no máximo 45 min.
O endereço do feed é citado por terceiros; não achamos documentação oficial do MIDR para ele.

Fuso: `enviado_em` e `expira_em` saem em horário de Brasília SEM fuso (contrato do projeto, `CLAUDE.md`);
`*_original` guarda o carimbo do feed com o offset. `gerado_em` é UTC, como `coletado_em`.

Uso:
    python3 scripts/coleta_alertas_idap.py                 # imprime os alertas de SC
    python3 scripts/coleta_alertas_idap.py --gravar        # grava data/tempo-real/ultimo_alertas_idap.json
    python3 scripts/coleta_alertas_idap.py --arquivo cap.xml   # lê um feed já baixado, sem rede

Cron na VPS (linha própria; conferir o diretório com `crontab -l`):
    4,19,34,49 * * * * cd /opt/enchentes-vale-itajai && flock -n /tmp/alertas-idap.lock \
        timeout 300 python3 scripts/coleta_alertas_idap.py --gravar >> /var/log/alertas-idap.log 2>&1
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import DADOS, USER_AGENT, cidades, espera_turno, grava_json  # noqa: E402
from importar_cotas_rio_do_sul import robots_permite  # noqa: E402

URL = "https://idapfile.mdr.gov.br/idap/api/rss/cap"
ROBOTS = "https://idapfile.mdr.gov.br/robots.txt"
ARQUIVO_PUBLICAVEL = "tempo-real/ultimo_alertas_idap.json"
FUSO_BRASILIA = timezone(timedelta(hours=-3))
ATOM = "{http://www.w3.org/2005/Atom}"
CAP = "{urn:oasis:names:tc:emergency:cap:1.2}"
#: Código IBGE de município de SC começa por 42 (código da UF).
PREFIXO_IBGE_SC = "42"
TEXTO_MAX = 600
#: Alerta que saiu do feed continua no arquivo enquanto vale, e mais estas horas depois de vencer.
GUARDA_APOS_EXPIRAR_H = 6
MAX_ALERTAS = 100
#: (conectar, ler entre pedaços), em segundos. O total é cortado pelo `timeout 300` do cron.
TIMEOUT_S = (15, 60)
#: Idade máxima que a publicação aceita (o mesmo número está em publicar_tempo_real.sh).
IDADE_MAX_PUBLICACAO_S = 2700


class Falha(Exception):
    pass


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower().strip()


def _limpo(texto: str | None) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def _cortado(texto: str) -> str:
    return texto[:TEXTO_MAX] + ("…" if len(texto) > TEXTO_MAX else "")


def _quando(carimbo: str | None) -> tuple[str | None, datetime | None]:
    """Carimbo CAP com offset → (Brasília sem fuso, datetime com fuso). Sem offset não é aceito."""
    try:
        t = datetime.fromisoformat((carimbo or "").strip())
    except ValueError:
        return None, None
    if t.tzinfo is None:
        return None, None
    return t.astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds"), t


def nomes_das_cidades() -> dict[str, str]:
    """Nome sem acento → slug, das cidades de `estacoes.json` (Itajaí aparece nos dois rios: um slug só)."""
    return {_sem_acento(c["nome"]): c["id"] for c in cidades() if c.get("nome") and c.get("id")}


def municipios_de(area_desc: str, geocodigos: list[str]) -> list[dict]:
    """"Anita Garibaldi/SC, Abdon Batista/SC" + códigos IBGE → [{nome, uf, ibge}].

    O feed põe os nomes no `areaDesc` e os códigos em `geocode`, na mesma ordem nos alertas lidos. Se as contagens
    não batem, o nome fica sem código (nunca se adivinha o par).
    """
    nomes = [p.strip() for p in (area_desc or "").split(",") if p.strip()]
    pares = len(nomes) == len(geocodigos)
    saida = []
    for i, bruto in enumerate(nomes):
        nome, _, uf = bruto.rpartition("/")
        if not nome:
            nome, uf = bruto, ""
        saida.append({"nome": nome.strip(), "uf": uf.strip().upper() or None,
                      "ibge": geocodigos[i] if pares else None})
    return saida


def converter(alerta: ET.Element, cidades_por_nome: dict[str, str]) -> dict | None:
    """Um `<alert>` CAP → alerta do projeto, ou None se não é de SC."""
    info = alerta.find(CAP + "info")
    if info is None:
        return None
    areas = info.findall(CAP + "area")
    area_desc = ", ".join(_limpo(a.findtext(CAP + "areaDesc")) for a in areas if a.findtext(CAP + "areaDesc"))
    geocodigos = [_limpo(g.findtext(CAP + "value")) for a in areas for g in a.findall(CAP + "geocode")
                  if _limpo(g.findtext(CAP + "valueName")).upper() == "IBGE"]
    municipios = municipios_de(area_desc, geocodigos)
    estado_inteiro = _sem_acento(area_desc) == "santa catarina/sc"
    de_sc = (estado_inteiro or any(g.startswith(PREFIXO_IBGE_SC) for g in geocodigos)
             or any(m["uf"] == "SC" for m in municipios))
    if not de_sc:
        return None
    if estado_inteiro:
        municipios = []
    enviado, enviado_dt = _quando(alerta.findtext(CAP + "sent"))
    expira, expira_dt = _quando(info.findtext(CAP + "expires"))
    if enviado_dt is None:
        return None
    titulo = _limpo(info.findtext(CAP + "headline"))
    titulo = re.sub(r"^Defesa Civil:\s*", "", titulo)
    descricao = _limpo(info.findtext(CAP + "description"))
    do_projeto = []
    for m in municipios:
        slug = cidades_por_nome.get(_sem_acento(m["nome"])) if m["uf"] in ("SC", None) else None
        if slug and slug not in do_projeto:
            do_projeto.append(slug)
    return {
        "identificador": _limpo(alerta.findtext(CAP + "identifier")),
        "tipo_mensagem": _limpo(alerta.findtext(CAP + "msgType")) or None,
        "referencias": _limpo(alerta.findtext(CAP + "references")) or None,
        "emissor": _limpo(info.findtext(CAP + "senderName")) or None,
        "evento": _limpo(info.findtext(CAP + "event")) or None,
        "severidade": _limpo(info.findtext(CAP + "severity")) or None,
        "urgencia": _limpo(info.findtext(CAP + "urgency")) or None,
        "certeza": _limpo(info.findtext(CAP + "certainty")) or None,
        "enviado_em": enviado,
        "enviado_em_original": _limpo(alerta.findtext(CAP + "sent")),
        "expira_em": expira,
        "expira_em_original": _limpo(info.findtext(CAP + "expires")) or None,
        "titulo": titulo or _cortado(descricao),
        "descricao": _cortado(descricao),
        "instrucao": _cortado(_limpo(info.findtext(CAP + "instruction"))) or None,
        "area": area_desc,
        "area_declarada": "estado" if estado_inteiro else "municipios",
        "municipios": municipios,
        "cidades_do_projeto": do_projeto,
    }


def ler_feed(fluxo, cidades_por_nome: dict[str, str] | None = None) -> tuple[str | None, list[dict], int]:
    """Lê o feed em fluxo (o arquivo tem dezenas de MB de polígonos). → (updated do feed, alertas de SC, total)."""
    cidades_por_nome = nomes_das_cidades() if cidades_por_nome is None else cidades_por_nome
    atualizado, alertas, total = None, [], 0
    for _, el in ET.iterparse(fluxo, events=("end",)):
        if el.tag == ATOM + "updated" and atualizado is None:
            atualizado = _limpo(el.text)
        elif el.tag == ATOM + "entry":
            total += 1
            alerta = el.find(f"{ATOM}content/{CAP}alert")
            if alerta is not None:
                a = converter(alerta, cidades_por_nome)
                if a and a["identificador"]:
                    alertas.append(a)
            el.clear()
    if total == 0:
        raise Falha("o feed não trouxe nenhuma entrada; formato mudou ou resposta não é o feed")
    return atualizado, alertas, total


def _vale_ainda(alerta: dict, agora: datetime) -> bool:
    _, expira = _quando(alerta.get("expira_em_original"))
    if expira is None:
        _, enviado = _quando(alerta.get("enviado_em_original"))
        return enviado is not None and agora - enviado <= timedelta(hours=24)
    return agora - expira <= timedelta(hours=GUARDA_APOS_EXPIRAR_H)


def juntar(novos: list[dict], anterior: dict | None, agora: datetime) -> list[dict]:
    """Os do feed (marcados `no_feed`) + os do arquivo anterior que saíram do feed e ainda valem."""
    vistos_antes = {a["identificador"]: a for a in ((anterior or {}).get("alertas") or [])
                    if isinstance(a, dict) and a.get("identificador")}
    agora_txt = agora.astimezone(timezone.utc).isoformat(timespec="seconds")
    saida = {}
    for a in novos:
        antes = vistos_antes.get(a["identificador"])
        saida[a["identificador"]] = {**a, "no_feed": True,
                                     "visto_primeiro_em": (antes or {}).get("visto_primeiro_em") or agora_txt}
    for ident, a in vistos_antes.items():
        if ident not in saida and _vale_ainda(a, agora):
            saida[ident] = {**a, "no_feed": False}
    # Cancelamento CAP: a mensagem `Cancel` aponta o alerta cancelado em `references` (sender,identifier,sent).
    cancelados = {ref.split(",")[1] for a in saida.values() if a.get("tipo_mensagem") == "Cancel"
                  for ref in (a.get("referencias") or "").split() if ref.count(",") >= 2}
    for ident in cancelados:
        if ident in saida:
            saida[ident]["cancelado"] = True
    ordem = sorted(saida.values(), key=lambda a: _quando(a.get("enviado_em_original"))[1]
                   or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return ordem[:MAX_ALERTAS]


def montar(alertas: list[dict], gerado_em: str, feed_atualizado_em: str | None, total_no_feed: int) -> dict:
    return {
        "versao": 1,
        "fonte": "Defesa Civil Nacional — IDAP (Interface de Divulgação de Alertas Públicos), feed CAP 1.2",
        "fonte_url": URL,
        "gerado_em": gerado_em,
        "feed_atualizado_em": feed_atualizado_em,
        "alertas_no_feed": total_no_feed,
        "aviso": ("Alertas que as Defesas Civis mandaram à população de SC pela IDAP, como publicados, com emissor e "
                  "hora. Não são faixa de rio, não disparam aviso de cota e não substituem o 199. O feed guarda só "
                  "~12 h; alerta que saiu dele fica aqui enquanto vale (`no_feed: false`). `cidades_do_projeto` só "
                  "casa o nome do município do alerta com o de estacoes.json."),
        "alertas": alertas,
    }


def validar(corpo: dict, agora: datetime) -> bool:
    """O que a publicação aceita: versão 1, lista de alertas bem formados, gerado há no máximo 45 min."""
    try:
        gerado = datetime.fromisoformat(corpo["gerado_em"])
    except (KeyError, TypeError, ValueError):
        return False
    if gerado.tzinfo is None or not (0 <= (agora - gerado).total_seconds() <= IDADE_MAX_PUBLICACAO_S):
        return False
    if corpo.get("versao") != 1 or not isinstance(corpo.get("alertas"), list):
        return False
    for a in corpo["alertas"]:
        if not isinstance(a, dict) or not a.get("identificador") or not a.get("enviado_em"):
            return False
        try:
            if datetime.fromisoformat(a["enviado_em"]).tzinfo is not None:
                return False  # enviado_em é Brasília SEM fuso
        except (TypeError, ValueError):
            return False
    return True


# --- rede ---------------------------------------------------------------------

def _get(url: str):
    import requests

    espera_turno()
    try:
        return requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
    except requests.RequestException as erro:
        raise Falha(f"falha ao pedir {url}: {type(erro).__name__}: {erro}") from erro


def robots_libera(pedir=None) -> None:
    """Sai calado se o robots.txt libera o caminho do feed; senão levanta `Falha` (na dúvida, nada é pedido)."""
    r = (pedir or _get)(ROBOTS)
    if r.status_code == 404:
        return  # sem robots.txt: sem regras (RFC 9309)
    if r.status_code != 200:
        raise Falha(f"robots.txt da IDAP respondeu HTTP {r.status_code}; nada foi pedido")
    caminho = urlparse(URL).path
    if not robots_permite(r.text, caminho):
        raise Falha(f"robots.txt da IDAP recusa {caminho}; nada foi pedido")


def baixar_feed(pedir=None) -> bytes:
    robots_libera(pedir)
    r = (pedir or _get)(URL)
    if r.status_code != 200:
        raise Falha(f"feed da IDAP respondeu HTTP {r.status_code}")
    return r.content


def gravar(baixador=baixar_feed, agora: datetime | None = None) -> int:
    """`--gravar`: baixa, filtra SC, junta com o anterior e grava. Falha NÃO apaga o anterior: ele envelhece e a
    publicação deixa de levá-lo depois de 45 min, sem que um alerta ainda vigente suma por um soluço de rede."""
    agora = agora or datetime.now(tz=timezone.utc)
    destino = DADOS / ARQUIVO_PUBLICAVEL
    try:
        atualizado, novos, total = ler_feed(io.BytesIO(baixador()))
    except Exception as e:  # noqa: BLE001 — alerta da IDAP nunca segura nada do resto
        print(f"aviso: alertas da IDAP não coletados ({e})", file=sys.stderr)
        return 1
    try:
        anterior = json.loads(destino.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        anterior = None
    alertas = juntar(novos, anterior if isinstance(anterior, dict) else None, agora)
    grava_json(ARQUIVO_PUBLICAVEL, montar(alertas, agora.isoformat(timespec="seconds"), atualizado, total))
    projeto = sum(1 for a in alertas if a["cidades_do_projeto"])
    print(f"{agora:%Y-%m-%dT%H:%M}Z {total} alerta(s) no feed, {len(novos)} de SC, {len(alertas)} no arquivo, "
          f"{projeto} com cidade do projeto -> data/{ARQUIVO_PUBLICAVEL}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--arquivo", type=Path, help="feed já baixado, para rodar sem rede")
    ap.add_argument("--gravar", action="store_true", help=f"grava data/{ARQUIVO_PUBLICAVEL}")
    a = ap.parse_args(argv)
    if a.gravar:
        return gravar((lambda: a.arquivo.read_bytes()) if a.arquivo else baixar_feed)
    with (a.arquivo.open("rb") if a.arquivo else io.BytesIO(baixar_feed())) as fluxo:
        atualizado, alertas, total = ler_feed(fluxo)
    print(f"feed atualizado em {atualizado}: {total} alerta(s), {len(alertas)} de SC")
    for al in sorted(alertas, key=lambda x: x["enviado_em"], reverse=True):
        marca = ",".join(al["cidades_do_projeto"]) or ("área: SC" if al["area_declarada"] == "estado" else "")
        print(f"{al['enviado_em']}  {al['evento'] or '':32.32s} {marca:16.16s} {al['emissor'] or '':42.42s} "
              f"{al['titulo'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
