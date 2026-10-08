#!/usr/bin/env python3
"""
Coleta a régua do CENTRO de Ituporanga (Boletim Diário da Prefeitura) pelo GitHub Actions.

POR QUE EXISTE (08/10/2026). A Prefeitura de Ituporanga recusa a VPS: `robots.txt` responde **403** ao IP dela
(Hetzner, Helsinque), e o projeto não pede página sem ler o robots. Na sessão de código e no runner do GitHub a
página abre e o robots diz `Allow: /`. Mesmo caminho da estação 21 de Gaspar (`gaspar_actions.py`, decisão de
04/10/2026): o runner lê, publica num branch próprio só quando a leitura muda, e a VPS lê o arquivo publicado.

    runner  --só quando a leitura muda-->  branch `coleta-ituporanga` (ituporanga-centro.json + o HTML bruto)
    VPS     --coleta_ituporanga.py --publicar, 15 min-->  tenta a página; bloqueada, lê o publicado pelo Actions
                                                        e grava data/tempo-real/ultimo_ituporanga_centro.json

O QUE NÃO MUDA. A régua do Centro continua sem cor, fora de `leituras`, em arquivo próprio (docs/ITUPORANGA-CENTRO.md).
`medido_em` segue Brasília sem fuso; `pagina_lida_em` é UTC com fuso — a hora em que o runner leu a página.

Uso no runner:
    python3 scripts/ituporanga_actions.py --anterior anterior/ituporanga-centro.json --saida saida
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
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import coleta_ituporanga as ci  # noqa: E402
from comum import USER_AGENT, baixar, espera_turno, nivel_plausivel  # noqa: E402
from importar_cotas_rio_do_sul import robots_permite  # noqa: E402

URL = ci.URL
ROBOTS = ci.URL_ROBOTS
BRANCH = "coleta-ituporanga"
ARQUIVO_LEITURA = "ituporanga-centro.json"
ARQUIVO_BRUTO = "ituporanga-nivel-rio.html"
COLETOR = "github-actions"

#: Onde a VPS lê o que o Actions publicou. O repositório é público, e é por este host que o site busca o `tempo-real`.
URL_PUBLICADO = ("https://raw.githubusercontent.com/haohmarusc-glitch/"
                 f"enchentes-vale-itajai/{BRANCH}/{ARQUIVO_LEITURA}")

#: (conectar, ler), em segundos.
TIMEOUT_S = (10, 30)

#: Página lida há mais que isto não serve à VPS: o Actions roda a cada 30 min; se parou, a leitura pode já ter
#: mudado na Prefeitura sem ninguém ver. É teto da CONSULTA; a idade da LEITURA (18 h) é conta do coletor.
TETO_PAGINA_LIDA_H = 3.0

#: Medição no futuro além disto é relógio ou fuso errado, não leitura.
TOLERANCIA_FUTURO = timedelta(minutes=15)


class Falha(Exception):
    """A rodada não produziu leitura. `codigo` é estável; `bruto`, o que chegou."""

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
    """Sai calado se o robots.txt libera /nivel-rio; senão levanta `Falha`."""
    status, corpo = pedir(ROBOTS)
    if status == 404:
        return  # sem robots.txt: sem regras (RFC 9309)
    if status != 200:
        # 403 é o que a Prefeitura responde à VPS: na dúvida, a página não é pedida.
        raise Falha("robots", f"robots.txt da Prefeitura de Ituporanga respondeu HTTP {status}; "
                              "na dúvida, a página não foi pedida")
    caminho = urlparse(URL).path
    if not robots_permite(corpo.decode("utf-8", errors="replace"), caminho):
        raise Falha("robots", f"bloqueado por robots.txt: {ROBOTS} recusa {caminho}; a página não foi pedida")


# --- coleta -----------------------------------------------------------------

def medicao_utc(medido_em: str) -> datetime:
    """`medido_em` (Brasília, sem fuso) como instante UTC."""
    return datetime.fromisoformat(medido_em).replace(tzinfo=ZoneInfo("America/Sao_Paulo")).astimezone(timezone.utc)


def mesma_leitura(a: dict | None, b: dict | None) -> bool:
    """Mesmo horário de medição e mesmo nível."""
    if not a or not b:
        return False
    return all(a.get(k) == b.get(k) for k in ("medido_em", "nivel_m"))


def ler_anterior(caminho: Path | None) -> dict | None:
    if caminho is None:
        return None
    try:
        corpo = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return corpo if isinstance(corpo, dict) else None


def coletar(anterior: dict | None, agora: datetime | None = None, pedir=pedir_http) -> dict:
    """
    Uma rodada. Devolve `{"estado", "mudou", "corpo", "bruto", "idade_h", "avisos", "dados"}`.

    `estado` é "nova" (leitura diferente da anterior, para publicar) ou "sem_mudanca". O que impede ter leitura
    levanta `Falha`, com o bruto quando ele chegou.
    """
    agora = agora or datetime.now(timezone.utc)
    robots_libera(pedir)
    status, bruto = pedir(URL)
    if status != 200:
        raise Falha("http", f"a página do Boletim respondeu HTTP {status}", bruto)
    try:
        dados = ci.extrair(bruto.decode("utf-8", errors="replace"))
    except Exception as erro:  # noqa: BLE001 — qualquer recusa do extrator é falha registrada, não silêncio
        raise Falha("sem_leitura", f"a página não trouxe a leitura do Centro: {erro}", bruto) from erro

    idade = agora - medicao_utc(dados["medido_em"])
    if idade < -TOLERANCIA_FUTURO:
        raise Falha("futuro", f"medição de {dados['medido_em']} (Brasília) está no futuro: relógio ou fuso errado",
                    bruto)
    idade_h = idade.total_seconds() / 3600

    avisos = []
    if idade_h * 60 > ci.FRESCA_MIN:
        avisos.append(f"leitura velha: a medição de {dados['medido_em']} (Brasília) tem {idade_h:.1f} h, acima das "
                      f"{ci.FRESCA_MIN // 60} h — o Boletim parou de atualizar, não a coleta. A tela a mostra como antiga.")

    if mesma_leitura((anterior or {}).get("dados"), dados):
        return {"estado": "sem_mudanca", "mudou": False, "corpo": None, "bruto": None,
                "idade_h": idade_h, "avisos": avisos, "dados": dados}

    corpo = {
        "fonte": ci.FONTE,
        "fonte_url": URL,
        "coletor": COLETOR,
        # UTC com offset: a hora em que ESTA leitura foi vista pela primeira vez pelo runner.
        "pagina_lida_em": agora.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "dados": dados,
        "bruto": {"arquivo": ARQUIVO_BRUTO, "sha256": hashlib.sha256(bruto).hexdigest(),
                  "bytes": len(bruto), "http": status},
        "user_agent": USER_AGENT,
        "nota": ("medido_em é horário de Brasília sem fuso, como a página publica; pagina_lida_em é UTC. "
                 "O arquivo só é regravado quando a leitura muda. A régua do Centro não tem cor no site."),
    }
    return {"estado": "nova", "mudou": True, "corpo": corpo, "bruto": bruto,
            "idade_h": idade_h, "avisos": avisos, "dados": dados}


# --- leitura na VPS ---------------------------------------------------------

def validar(corpo, agora: datetime | None = None) -> dict | None:
    """
    Os `dados` publicados pelo Actions, se forem deste coletor, tiverem a forma do extrator e a página tiver
    sido lida há no máximo `TETO_PAGINA_LIDA_H`. Devolve `{"dados", "pagina_lida_em"}` ou None.
    """
    agora = agora or datetime.now(timezone.utc)
    if not isinstance(corpo, dict) or corpo.get("coletor") != COLETOR:
        return None
    dados = corpo.get("dados")
    lida = corpo.get("pagina_lida_em")
    if not isinstance(dados, dict) or not isinstance(lida, str):
        return None
    try:
        lida_em = datetime.fromisoformat(lida)
    except ValueError:
        return None
    if lida_em.tzinfo is None:
        return None
    idade_h = (agora - lida_em).total_seconds() / 3600
    if not (-TOLERANCIA_FUTURO.total_seconds() / 3600 <= idade_h <= TETO_PAGINA_LIDA_H):
        return None
    if not (isinstance(dados.get("medido_em"), str) and isinstance(dados.get("nivel_m"), (int, float))):
        return None
    try:
        medido = datetime.fromisoformat(dados["medido_em"])
    except ValueError:
        return None
    if medido.tzinfo is not None:
        return None  # o contrato é Brasília SEM fuso (CLAUDE.md); com fuso, alguém converteu e a idade sairia errada
    if not nivel_plausivel(dados["nivel_m"]):
        return None
    return {"dados": dados, "pagina_lida_em": lida}


def ler_publicado(buscar=None, agora: datetime | None = None) -> dict | None:
    """O que o Actions publicou, validado. Qualquer falha devolve None, dita no log: é um caminho a mais."""
    buscar = buscar or (lambda url: baixar(url, tentativas=1))
    try:
        return validar(json.loads(buscar(URL_PUBLICADO)), agora)
    except Exception as erro:  # noqa: BLE001 — rede, JSON quebrado, branch ainda inexistente
        print(f"aviso: leitura do Centro de Ituporanga pelo Actions indisponível ({erro}).", file=sys.stderr)
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
    ap.add_argument("--anterior", type=Path, help=f"{ARQUIVO_LEITURA} publicado na rodada anterior (pode não existir)")
    ap.add_argument("--saida", type=Path, required=True, help="pasta onde gravar o JSON e o bruto, só se a leitura mudou")
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
        print(f"::error title=Coleta de Ituporanga ({falha.codigo})::{_uma_linha(falha.motivo)}")
        _saidas_do_passo(mudou="false", estado=falha.codigo, motivo=falha.motivo)
        _resumo(f"**Falhou** ({falha.codigo}): {falha.motivo}")
        return 1

    dados = r["dados"]
    for aviso in r["avisos"]:
        print(f"::warning title=Ituporanga: leitura velha::{_uma_linha(aviso)}")
    estado = "leitura_velha" if r["avisos"] else r["estado"]
    linha = (f"{dados['nivel_m']:.2f} m no Centro, medido em {dados['medido_em']} (Brasília), "
             f"{r['idade_h']:.1f} h atrás, criticidade na fonte: {dados.get('criticidade_na_fonte') or '—'}")
    if r["mudou"]:
        (args.saida / ARQUIVO_BRUTO).write_bytes(r["bruto"])
        (args.saida / ARQUIVO_LEITURA).write_text(
            json.dumps(r["corpo"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"leitura nova: {linha} — gravada em {args.saida / ARQUIVO_LEITURA}")
    else:
        print(f"sem mudança: {linha} — nada regravado")
    _saidas_do_passo(mudou="true" if r["mudou"] else "false", estado=estado, motivo="; ".join(r["avisos"]) or linha)
    _resumo(f"Ituporanga, Centro: {linha} · {'publicada' if r['mudou'] else 'sem mudança'}"
            + "".join(f"\n\n> {a}" for a in r["avisos"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
