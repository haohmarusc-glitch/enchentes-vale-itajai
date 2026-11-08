#!/usr/bin/env python3
"""
Lê os avisos da Defesa Civil de SC (`wp-json`, categorias Alerta e Aviso) pelo GitHub Actions.

POR QUE EXISTE (08/11/2026). Da VPS (Hetzner, Helsinque) o site `www.defesacivil.sc.gov.br` nem aceita a conexão:
`ConnectTimeoutError` em 50 s, na rodada manual de 07/11/2026, durante a cheia. Da sessão de código a conexão cai
("connection reset"). O runner do GitHub alcança: a sondagem de 04/11/2026 recebeu 200 com JSON. É o mesmo caminho
de Gaspar (`gaspar_actions.py`) e do Centro de Ituporanga (`ituporanga_actions.py`):

    runner  --a cada 30 min-->  branch `coleta-avisos-dcsc` (avisos-dcsc.json + a resposta crua)
    VPS     --coleta_avisos_dcsc.py --publicar, 15 min-->  tenta o site; recusada, lê o publicado pelo Actions
                                                          e grava data/tempo-real/ultimo_avisos_dcsc.json

O QUE PUBLICA. Os avisos JÁ CONVERTIDOS por `coleta_avisos_dcsc.converter` — a mesma função que a VPS usa, para
os dois caminhos darem o mesmo arquivo —, a hora em que o runner leu (`pagina_lida_em`, UTC com fuso) e o
sha256 da resposta crua. Regrava quando os avisos MUDAM ou quando a publicação anterior tem mais de
`REFRESCAR_H`: a VPS recusa leitura com mais de `TETO_PAGINA_LIDA_H`, e aviso que não mudou continua valendo.

REGRAS DE SEMPRE. robots.txt antes (sem robots, 404, é sem regras; outro erro é recusa); User-Agent do projeto;
um pedido por rodada; nunca trocar o User-Agent nem pular o robots para passar (CLAUDE.md, Ituporanga).

Uso no runner:
    python3 scripts/avisos_dcsc_actions.py --anterior anterior/avisos-dcsc.json --saida saida
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import coleta_avisos_dcsc as ca  # noqa: E402
from comum import USER_AGENT, baixar, espera_turno  # noqa: E402
from importar_cotas_rio_do_sul import robots_permite  # noqa: E402

URL = ca.URL
ROBOTS = "https://www.defesacivil.sc.gov.br/robots.txt"
BRANCH = "coleta-avisos-dcsc"
ARQUIVO = "avisos-dcsc.json"
ARQUIVO_BRUTO = "avisos-dcsc-wp-json.json"
COLETOR = "github-actions"

#: Onde a VPS lê o que o Actions publicou (repositório público; o site busca o `tempo-real` pelo mesmo host).
URL_PUBLICADO = f"https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/{BRANCH}/{ARQUIVO}"

#: (conectar, ler), em segundos — no runner.
TIMEOUT_S = (10, 40)
#: (conectar, ler) da VPS lendo o publicado: soma com o site (`coleta_avisos_dcsc.TIMEOUT_S`) dentro dos 60 s.
TIMEOUT_PUBLICADO_S = (5, 8)

#: A VPS não usa leitura do runner mais velha que isto: o Actions roda a cada 30 min; parado, um aviso novo
#: pode ter saído sem ninguém ver.
TETO_PAGINA_LIDA_H = 3.0
#: Sem mudança nos avisos, o runner regrava mesmo assim depois disto, para a leitura não passar do teto.
REFRESCAR_H = 2.0
TOLERANCIA_FUTURO = timedelta(minutes=15)

CAMPOS_DO_AVISO = ("id", "categoria", "titulo", "publicado_em", "link", "regioes", "estado_inteiro", "inclui_bacia")


class Falha(Exception):
    """A rodada não produziu avisos. `codigo` é estável; `bruto`, o que chegou."""

    def __init__(self, codigo: str, motivo: str, bruto: bytes | None = None):
        super().__init__(motivo)
        self.codigo = codigo
        self.motivo = motivo
        self.bruto = bruto


# --- rede -------------------------------------------------------------------

def pedir_http(url: str) -> tuple[int, bytes]:
    """Um GET com o User-Agent do projeto e timeout, sem insistir."""
    import requests

    espera_turno()
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
    except requests.Timeout as erro:
        raise Falha("timeout", f"timeout ao pedir {url} ({erro})") from erro
    except requests.RequestException as erro:
        raise Falha("transporte", f"falha de rede ao pedir {url}: {type(erro).__name__}: {erro}") from erro
    return r.status_code, r.content


def robots_libera(pedir=pedir_http) -> None:
    """Sai calado se o robots.txt libera o caminho do `wp-json`; senão levanta `Falha`."""
    status, corpo = pedir(ROBOTS)
    if status == 404:
        return  # sem robots.txt: sem regras (RFC 9309)
    if status != 200:
        raise Falha("robots", f"robots.txt da Defesa Civil de SC respondeu HTTP {status}; na dúvida, nada foi pedido")
    caminho = urlparse(URL).path
    if not robots_permite(corpo.decode("utf-8", errors="replace"), caminho):
        raise Falha("robots", f"bloqueado por robots.txt: {ROBOTS} recusa {caminho}; nada foi pedido")


# --- coleta -----------------------------------------------------------------

def ler_anterior(caminho: Path | None) -> dict | None:
    if caminho is None:
        return None
    try:
        corpo = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return corpo if isinstance(corpo, dict) else None


def _assinatura(avisos: list[dict]) -> str:
    """O que conta como "mudou": id, título e regiões de cada aviso (o trecho pode ser reformatado sem mudar nada)."""
    chave = [(a.get("id"), a.get("titulo"), tuple(a.get("regioes") or ())) for a in avisos]
    return hashlib.sha256(json.dumps(chave, ensure_ascii=False).encode("utf-8")).hexdigest()


def _lida_em(corpo: dict | None) -> datetime | None:
    try:
        d = datetime.fromisoformat(str((corpo or {}).get("pagina_lida_em")))
    except ValueError:
        return None
    return d if d.tzinfo is not None else None


def coletar(anterior: dict | None, agora: datetime | None = None, pedir=pedir_http) -> dict:
    """
    Uma rodada. Devolve `{"estado", "mudou", "corpo", "bruto", "avisos"}`; `estado` é "nova", "refresco" ou
    "sem_mudanca". O que impede ter avisos levanta `Falha`, com o bruto quando ele chegou.
    """
    agora = agora or datetime.now(timezone.utc)
    robots_libera(pedir)
    status, bruto = pedir(URL)
    if status != 200:
        raise Falha("http", f"o wp-json da Defesa Civil de SC respondeu HTTP {status}", bruto)
    try:
        posts = json.loads(bruto.decode("utf-8", errors="replace"))
        if not isinstance(posts, list):
            raise ValueError(f"resposta não é lista de posts: {str(posts)[:120]}")
        avisos = ca.converter(posts)
    except Exception as erro:  # noqa: BLE001 — resposta que não vira aviso é falha registrada, não silêncio
        raise Falha("formato", f"a resposta não trouxe avisos: {erro}", bruto) from erro

    assinatura = _assinatura(avisos)
    lida_antes = _lida_em(anterior)
    igual = bool(anterior) and anterior.get("assinatura") == assinatura
    if igual and lida_antes and agora - lida_antes < timedelta(hours=REFRESCAR_H):
        return {"estado": "sem_mudanca", "mudou": False, "corpo": None, "bruto": None, "avisos": avisos}
    corpo = {
        "versao": 1,
        "fonte": "Defesa Civil de Santa Catarina — www.defesacivil.sc.gov.br (categorias Alerta e Aviso)",
        "fonte_url": URL,
        "coletor": COLETOR,
        # UTC com offset: a hora em que o runner leu o site (o `gerado_em` do arquivo do site é o da VPS).
        "pagina_lida_em": agora.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "assinatura": assinatura,
        "avisos": avisos,
        "bruto": {"arquivo": ARQUIVO_BRUTO, "sha256": hashlib.sha256(bruto).hexdigest(), "bytes": len(bruto),
                  "http": status},
        "user_agent": USER_AGENT,
        "nota": ("Avisos convertidos por coleta_avisos_dcsc.converter, a mesma função da VPS. publicado_em é "
                 "Brasília sem fuso; pagina_lida_em é UTC. Regravado quando os avisos mudam ou a cada "
                 f"{REFRESCAR_H:g} h."),
    }
    return {"estado": "refresco" if igual else "nova", "mudou": True, "corpo": corpo, "bruto": bruto,
            "avisos": avisos}


# --- leitura na VPS ---------------------------------------------------------

def validar(corpo, agora: datetime | None = None) -> dict | None:
    """Os avisos publicados pelo Actions, se forem deste coletor, com a forma certa e lidos há ≤ TETO. Ou None."""
    agora = agora or datetime.now(timezone.utc)
    if not isinstance(corpo, dict) or corpo.get("coletor") != COLETOR or corpo.get("versao") != 1:
        return None
    lida = _lida_em(corpo)
    if lida is None:
        return None
    idade = agora - lida
    if idade < -TOLERANCIA_FUTURO or idade > timedelta(hours=TETO_PAGINA_LIDA_H):
        return None
    avisos = corpo.get("avisos")
    if not isinstance(avisos, list) or not all(isinstance(a, dict) and all(k in a for k in CAMPOS_DO_AVISO)
                                               for a in avisos):
        return None
    for a in avisos:
        try:
            if datetime.fromisoformat(str(a["publicado_em"])).tzinfo is not None:
                return None  # o contrato é Brasília SEM fuso (CLAUDE.md)
        except ValueError:
            return None
    return {"avisos": avisos, "pagina_lida_em": corpo["pagina_lida_em"]}


def ler_publicado(buscar=None, agora: datetime | None = None) -> dict | None:
    """O que o Actions publicou, validado. Qualquer falha devolve None, dita no log: é um caminho a mais."""
    buscar = buscar or (lambda url: baixar(url, tentativas=1, timeout=TIMEOUT_PUBLICADO_S))
    try:
        return validar(json.loads(buscar(URL_PUBLICADO)), agora)
    except Exception as erro:  # noqa: BLE001 — rede, JSON quebrado, branch ainda inexistente
        print(f"aviso: avisos da Defesa Civil de SC pelo Actions indisponíveis ({erro}).", file=sys.stderr)
        return None


# --- linha de comando (no runner) --------------------------------------------

def _uma_linha(texto: str) -> str:
    return " ".join(str(texto).split())[:500]


def _saidas_do_passo(**valores: str) -> None:
    destino = os.environ.get("GITHUB_OUTPUT")
    if not destino:
        return
    with open(destino, "a", encoding="utf-8") as f:
        for chave, valor in valores.items():
            f.write(f"{chave}={_uma_linha(valor)}\n")


def _resumo(texto: str) -> None:
    destino = os.environ.get("GITHUB_STEP_SUMMARY")
    if destino:
        with open(destino, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def main(argv: list[str] | None = None, agora: datetime | None = None, pedir=pedir_http) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anterior", type=Path, help=f"{ARQUIVO} publicado na rodada anterior (pode não existir)")
    ap.add_argument("--saida", type=Path, required=True, help="pasta onde gravar o JSON e o bruto, se for publicar")
    args = ap.parse_args(argv)
    args.saida.mkdir(parents=True, exist_ok=True)

    try:
        r = coletar(ler_anterior(args.anterior), agora, pedir)
    except Falha as falha:
        (args.saida / "falha.json").write_text(json.dumps({
            "codigo": falha.codigo, "motivo": falha.motivo, "url": URL,
            "quando_utc": (agora or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if falha.bruto:
            (args.saida / f"falha-{ARQUIVO_BRUTO}").write_bytes(falha.bruto)
        print(f"::error title=Avisos da Defesa Civil de SC ({falha.codigo})::{_uma_linha(falha.motivo)}")
        _saidas_do_passo(mudou="false", estado=falha.codigo, motivo=falha.motivo)
        _resumo(f"**Falhou** ({falha.codigo}): {falha.motivo}")
        return 1

    bacia = sum(1 for a in r["avisos"] if a.get("inclui_bacia"))
    linha = f"{len(r['avisos'])} aviso(s), {bacia} citando a bacia do Itajaí"
    if r["mudou"]:
        (args.saida / ARQUIVO_BRUTO).write_bytes(r["bruto"])
        (args.saida / ARQUIVO).write_text(json.dumps(r["corpo"], ensure_ascii=False, indent=1) + "\n",
                                          encoding="utf-8")
        print(f"{r['estado']}: {linha} — gravado em {args.saida / ARQUIVO}")
    else:
        print(f"sem mudança: {linha} — nada regravado")
    _saidas_do_passo(mudou="true" if r["mudou"] else "false", estado=r["estado"], motivo=linha)
    _resumo(f"Avisos da Defesa Civil de SC: {linha} · {r['estado']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
