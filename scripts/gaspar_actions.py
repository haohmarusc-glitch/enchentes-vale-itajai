#!/usr/bin/env python3
"""
Gaspar pelo GitHub Actions: a coleta (no runner) e a leitura (na VPS).

POR QUE EXISTE (decisão do Jefferson, 04/10/2026)
-------------------------------------------------
O portal da Defesa Civil de Gaspar dá timeout na VPS (Hetzner, Helsinque) desde
31/08/2026 e responde ao runner do GitHub: a captura de 28/09 trouxe a tabela e a
estação 21 com HTTP 200 e o robots.txt permitindo (docs/CAPTURA-FONTES-2026-09-28.md).
A ponte pelo PC (`enviar_gaspar_pc.py`) depende de um computador ligado em casa.
Este módulo põe a coleta no Actions, de 15 em 15 min
(`.github/workflows/coletar-gaspar.yml`), e a VPS lê o resultado pelo
raw.githubusercontent.com, do mesmo jeito que o site lê o `tempo-real`.

O CAMINHO DO DADO
-----------------
    runner  --robots.txt + estação 21-->  portal de Gaspar
    runner  --só quando a leitura muda-->  branch `coleta-gaspar`
                                           (gaspar.json + o HTML bruto)
    VPS     --coleta_niveis.py, 15 min-->  raw.githubusercontent.com/.../coleta-gaspar/gaspar.json
    VPS     --publicar_tempo_real.sh--->  branch `tempo-real` (ultimo.json), como sempre

Branch próprio, e não o `tempo-real`, porque a VPS reescreve o `tempo-real`
inteiro a cada 15 min com um commit órfão: um arquivo posto lá pelo Actions
sumiria na publicação seguinte, e os dois escritores disputariam o mesmo ref.

AS REGRAS DO COLETOR, cada uma por um motivo
--------------------------------------------
1. **robots.txt antes de tudo.** Caminho recusado não é pedido; vira falha com
   o motivo. robots.txt com 4xx conta como sem regras (RFC 9309); com 5xx ou
   sem resposta, conta como recusa — na dúvida, não se pede.
2. **User-Agent do projeto** (`comum.USER_AGENT`), intervalo mínimo entre
   pedidos (`comum.espera_turno`) e **um pedido por rodada, sem insistir**: a
   rodada seguinte, 15 min depois, é a nova tentativa. Dois pedidos a cada
   15 min (robots.txt + a página) é toda a carga sobre o servidor do município.
3. **Timeout curto** (10 s para conectar, 30 s para ler) e falha visível:
   o job sai com erro, o log diz o motivo e o fluxo abre ou atualiza a issue
   "Coleta de Gaspar pelo Actions falhando".
4. **Não regrava o que não mudou.** Mesma régua, mesmo nível, mesmo horário de
   medição: nada é escrito e nada é publicado. Sem isto seriam 96 commits por
   dia no branch, todos iguais.
5. **Leitura velha é detectada, não escondida nem renovada.** A estação 21
   publica com atraso por conta própria (5 h na captura de 28/09; 25 h parada
   em 16–17/09). Acima de 3 h o job avisa (anotação `warning`), mas não falha:
   quem parou foi a estação, não a coleta. A VPS recusa a leitura pelo mesmo
   teto de 3 h (`gaspar_pc.TETO_MEDICAO_S`) e Gaspar volta ao cinza.
6. **Guarda o bruto.** O HTML de onde a leitura saiu vai junto no branch, com o
   sha256 dentro do `gaspar.json`. Em falha, o que chegou fica no artefato do run.

Fuso: `medido_em` é horário de Brasília sem fuso (regra do CLAUDE.md), como a
página publica; `coletado_em` é UTC com offset.

Uso (no runner; o fluxo faz isto):
    python3 scripts/gaspar_actions.py --anterior anterior/gaspar.json --saida saida/
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

import coleta_gaspar as cg
import gaspar_pc
from comum import USER_AGENT, baixar, espera_turno
from importar_cotas_rio_do_sul import robots_permite

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

URL = cg.URL_ESTACAO
ROBOTS = cg.ROBOTS
BRANCH = "coleta-gaspar"
ARQUIVO_LEITURA = "gaspar.json"
ARQUIVO_BRUTO = "gaspar-estacao-21.html"
COLETOR = "github-actions"

#: Onde a VPS lê o que o Actions publicou. O repositório é público, e é por
#: este mesmo host que o site busca o `tempo-real`.
URL_PUBLICADO = ("https://raw.githubusercontent.com/haohmarusc-glitch/"
                 f"enchentes-vale-itajai/{BRANCH}/{ARQUIVO_LEITURA}")

#: (conectar, ler), em segundos. O município responde ao runner em menos de 1 s;
#: o que passa disto é host fora do ar, e a próxima rodada tenta de novo.
TIMEOUT_S = (10, 30)

#: Medição mais velha que isto é "leitura velha": o teto do monitor e da VPS.
TETO_IDADE_H = gaspar_pc.TETO_MEDICAO_S / 3600

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
    """Um GET com o User-Agent do projeto e timeout, sem insistir.

    Timeout vira `Falha("timeout")`; outro erro de transporte, `Falha("transporte")`.
    """
    import requests

    espera_turno()
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
    except requests.Timeout as erro:
        raise Falha("timeout", f"timeout ao pedir {url} ({erro})") from erro
    except requests.RequestException as erro:
        raise Falha("transporte", f"falha de rede ao pedir {url}: "
                                  f"{type(erro).__name__}: {erro}") from erro
    return r.status_code, r.content


def robots_libera(pedir=pedir_http) -> None:
    """Sai calado se o robots.txt libera a estação 21; senão levanta `Falha`."""
    status, corpo = pedir(ROBOTS)
    if 400 <= status < 500:
        return  # sem robots.txt: sem regras (RFC 9309)
    if status != 200:
        raise Falha("robots", f"robots.txt de Gaspar respondeu HTTP {status}; "
                              "na dúvida, a estação 21 não foi pedida")
    caminho = urlparse(URL).path
    if not robots_permite(corpo.decode("utf-8", errors="replace"), caminho):
        raise Falha("robots", f"bloqueado por robots.txt: {ROBOTS} recusa {caminho}; "
                              "a página não foi pedida")


# --- coleta -----------------------------------------------------------------

def medicao_utc(medido_em: str) -> datetime:
    """`medido_em` (Brasília, sem fuso) como instante UTC."""
    return datetime.fromisoformat(medido_em).replace(tzinfo=FUSO_BRASILIA).astimezone(timezone.utc)


def mesma_leitura(a: dict | None, b: dict | None) -> bool:
    """Mesma régua, mesmo nível e mesmo horário de medição."""
    if not a or not b:
        return False
    return all(a.get(k) == b.get(k) for k in ("estacao", "nivel_m", "medido_em"))


def ler_anterior(caminho: Path | None) -> dict | None:
    """O `gaspar.json` publicado na rodada anterior, ou None se não há ou não se lê."""
    if caminho is None:
        return None
    try:
        corpo = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return corpo if isinstance(corpo, dict) else None


def coletar(anterior: dict | None, agora: datetime | None = None,
            pedir=pedir_http) -> dict:
    """
    Uma rodada. Devolve `{"estado", "mudou", "corpo", "bruto", "idade_h", "avisos"}`.

    `estado` é "nova" (leitura diferente da anterior, para publicar) ou
    "sem_mudanca" (nada a gravar). Qualquer coisa que impeça ter leitura levanta
    `Falha`, com o bruto quando ele chegou.
    """
    agora = agora or datetime.now(timezone.utc)
    robots_libera(pedir)
    status, bruto = pedir(URL)
    if status != 200:
        raise Falha("http", f"a estação 21 respondeu HTTP {status}", bruto)

    from enviar_gaspar_pc import porque_recusou

    leitura = cg.leitura_da_cidade(cg.analisar_estacao(bruto.decode("utf-8", errors="replace")))
    if leitura is None:
        raise Falha("sem_leitura", porque_recusou(None), bruto)

    idade = agora - medicao_utc(leitura["medido_em"])
    if idade < -TOLERANCIA_FUTURO:
        raise Falha("futuro", porque_recusou(leitura, agora), bruto)
    idade_h = idade.total_seconds() / 3600

    avisos = []
    if idade_h > TETO_IDADE_H:
        avisos.append(
            f"leitura velha: a medição de {leitura['medido_em']} (Brasília) tem "
            f"{idade_h:.1f} h, acima do teto de {TETO_IDADE_H:.0f} h — a estação do "
            f"município parou de atualizar, não a coleta. A VPS a recusa pela idade.")

    if mesma_leitura((anterior or {}).get("leitura"), leitura):
        return {"estado": "sem_mudanca", "mudou": False, "corpo": None, "bruto": None,
                "idade_h": idade_h, "avisos": avisos, "leitura": leitura}

    corpo = {
        "fonte": gaspar_pc.FONTE,
        "coletor": COLETOR,
        # UTC com offset: a hora em que ESTA leitura foi vista pela primeira vez.
        "coletado_em": agora.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "leitura": leitura,
        "bruto": {"arquivo": ARQUIVO_BRUTO, "sha256": hashlib.sha256(bruto).hexdigest(),
                  "bytes": len(bruto), "http": status},
        "user_agent": USER_AGENT,
        "nota": ("medido_em é horário de Brasília sem fuso, como a página publica; "
                 "coletado_em é UTC. O arquivo só é regravado quando a leitura muda."),
    }
    return {"estado": "nova", "mudou": True, "corpo": corpo, "bruto": bruto,
            "idade_h": idade_h, "avisos": avisos, "leitura": leitura}


# --- leitura na VPS ---------------------------------------------------------

def validar(corpo, agora: datetime | None = None) -> dict | None:
    """A leitura publicada pelo Actions, se for da estação 21 e tiver até 3 h.

    Mesma validação da ponte do PC (identidade, número, formato, medição até
    3 h), sem o teto de 30 min da consulta: aqui o arquivo só muda quando a
    leitura muda, e a idade que importa é a da medição.
    """
    if not isinstance(corpo, dict) or corpo.get("coletor") != COLETOR:
        return None
    return gaspar_pc.validar(corpo, agora, teto_consulta_s=None)


def ler_publicado(buscar=None, agora: datetime | None = None) -> dict | None:
    """O que o Actions publicou, validado. Qualquer falha devolve None, calada no
    retorno e dita no log: é uma fonte a mais, não pode derrubar a coleta."""
    buscar = buscar or (lambda url: baixar(url, tentativas=1))
    try:
        return validar(json.loads(buscar(URL_PUBLICADO)), agora)
    except Exception as erro:  # rede, JSON quebrado, branch ainda inexistente
        print(f"aviso: leitura de Gaspar pelo Actions indisponível ({erro}).", file=sys.stderr)
        return None


# --- linha de comando (no runner) --------------------------------------------

def _uma_linha(texto: str) -> str:
    return " ".join(str(texto).split())[:500]


def _saidas_do_passo(**valores: str) -> None:
    """Escreve em $GITHUB_OUTPUT, quando existe (no runner)."""
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


def main(argv: list[str] | None = None, agora: datetime | None = None,
         pedir=pedir_http) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anterior", type=Path,
                    help="gaspar.json publicado na rodada anterior (pode não existir)")
    ap.add_argument("--saida", type=Path, required=True,
                    help="pasta onde gravar gaspar.json e o bruto, só se a leitura mudou")
    args = ap.parse_args(argv)
    args.saida.mkdir(parents=True, exist_ok=True)

    try:
        r = coletar(ler_anterior(args.anterior), agora, pedir)
    except Falha as falha:
        # Diagnóstico para o artefato do run: o motivo e, se chegou, o corpo.
        (args.saida / "falha.json").write_text(json.dumps({
            "codigo": falha.codigo, "motivo": falha.motivo, "url": URL,
            "quando_utc": (agora or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if falha.bruto:
            (args.saida / f"falha-{ARQUIVO_BRUTO}").write_bytes(falha.bruto)
        print(f"::error title=Coleta de Gaspar ({falha.codigo})::{_uma_linha(falha.motivo)}")
        _saidas_do_passo(mudou="false", estado=falha.codigo, motivo=falha.motivo)
        _resumo(f"**Falhou** ({falha.codigo}): {falha.motivo}")
        return 1

    leitura = r["leitura"]
    for aviso in r["avisos"]:
        print(f"::warning title=Gaspar: leitura velha::{_uma_linha(aviso)}")
    estado = "leitura_velha" if r["avisos"] else r["estado"]
    linha = (f"{leitura['nivel_m']:.2f} m, medido em {leitura['medido_em']} (Brasília), "
             f"{r['idade_h']:.1f} h atrás")
    if r["mudou"]:
        (args.saida / ARQUIVO_BRUTO).write_bytes(r["bruto"])
        (args.saida / ARQUIVO_LEITURA).write_text(
            json.dumps(r["corpo"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"leitura nova: {linha} — gravada em {args.saida / ARQUIVO_LEITURA}")
    else:
        print(f"sem mudança: {linha} — nada regravado")
    _saidas_do_passo(mudou="true" if r["mudou"] else "false", estado=estado,
                     motivo="; ".join(r["avisos"]) or linha)
    _resumo(f"Gaspar, estação 21: {linha} · {'publicada' if r['mudou'] else 'sem mudança'}"
            + ("".join(f"\n\n> {a}" for a in r["avisos"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
