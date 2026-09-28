#!/usr/bin/env python3
"""
Captura o CORPO BRUTO das fontes de tempo real das cidades, para conferência.

POR QUE EXISTE
--------------
O ambiente das sessões de código recebe 403 do proxy para todas as fontes
municipais (portal de Itajaí, Taió, Rio do Sul/Asthon, Gaspar, Ituporanga,
AlertaBlu, o documento de Indaial). Conferir uma fonte exige o corpo como o
servidor o entrega, e até 27/09/2026 ele só chegava salvo à mão. Este script
roda no GitHub Actions (`.github/workflows/capturar-portal-itajai.yml`), grava
cada corpo em disco e imprime no log um resumo e o corpo em gzip+base64
fatiado, com o sha256. `--remontar` faz o caminho de volta numa sessão sem
acesso ao host: junta as fatias e só grava o que bater com o sha256.

AS REGRAS, cada uma por um motivo
---------------------------------
1. **robots.txt antes de tudo, em cada host.** É a regra que o coletor de
   Gaspar já seguia. Caminho recusado não é pedido; fica no manifesto como
   `recusado_robots`. robots.txt que não responde 200 conta como sem regras,
   que é o que a norma diz.
2. **User-Agent do projeto** (`comum.USER_AGENT`), sem disfarce de navegador,
   e intervalo mínimo entre pedidos ao mesmo host (`comum.espera_turno`).
3. **TLS verificado sempre.** O AlertaBlu serve a cadeia incompleta; o
   intermediário vai junto (`certs/sectigo-dv-r36.pem`), como no coletor
   dele. Nunca `verify=False`.
4. **Não interpreta.** Captura é evidência: o corpo sai byte a byte. Quem lê
   nível, cota ou carimbo são os coletores, com os testes deles.
5. **Um pedido por alvo, sem insistir.** Falha vira linha no manifesto com o
   motivo; a captura das outras fontes segue.

Uso:
    python3 scripts/capturar_fontes.py --saida captura/            # no runner
    python3 scripts/capturar_fontes.py --remontar log.txt destino/  # na sessão
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from comum import USER_AGENT, espera_turno
from importar_cotas_rio_do_sul import robots_permite

CERT_ALERTABLU = Path(__file__).resolve().parent / "certs" / "sectigo-dv-r36.pem"

#: Largura das fatias de base64 no log. Linhas muito longas são cortadas por
#: alguns leitores de log; 3500 cabem com folga.
LARGURA_FATIA = 3500


@dataclass(frozen=True)
class Alvo:
    arquivo: str
    cidade: str
    url: str
    #: Cadeia de certificados extra, para servidor que não manda o intermediário.
    ca_extra: Path | None = None


PORTAL_ITAJAI = "https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios"

#: As fontes que os coletores leem, uma linha por pedido. A lista sai dos
#: próprios coletores (URL, URL_CARDS, URL_PAINEL…), não de busca por nome.
ALVOS: tuple[Alvo, ...] = (
    Alvo("itajai-portal-rios-municipio-1-itajai.html", "itajai", PORTAL_ITAJAI),
    Alvo("itajai-portal-rios-municipio-2-brusque.html", "brusque", PORTAL_ITAJAI + "?municipio_id=2"),
    Alvo("itajai-portal-rios-municipio-3-blumenau.html", "blumenau", PORTAL_ITAJAI + "?municipio_id=3"),
    Alvo("itajai-portal-rios-municipio-4-rio-do-sul.html", "rio-do-sul", PORTAL_ITAJAI + "?municipio_id=4"),
    Alvo("taio-uniparking-cards.json", "taio",
         "https://api-scr.uniparking.com.br/v1/defesa-civil-taio/dados/cards?v=1"),
    Alvo("taio-uniparking-historico.json", "taio",
         "https://api-scr.uniparking.com.br/v1/defesa-civil-taio/dados/historico?v=1"),
    Alvo("rio-do-sul-asthon-panel.json", "rio-do-sul",
         "https://public.asthon.com.br/public/panel?city_id=4214805"),
    Alvo("rio-do-sul-asthon-dams.json", "rio-do-sul",
         "https://public.asthon.com.br/public/dams?city_id=4214805"),
    Alvo("gaspar-monitoramento-tabela.html", "gaspar",
         "https://defesacivil.gaspar.sc.gov.br/monitoramento/tabela"),
    Alvo("gaspar-estacao-21.html", "gaspar",
         "https://defesacivil.gaspar.sc.gov.br/estacao/ver/21"),
    Alvo("ituporanga-nivel-rio.html", "ituporanga",
         "https://www.ituporanga.sc.gov.br/nivel-rio"),
    Alvo("blumenau-alertablu-nivel-oficial.json", "blumenau",
         "https://defesacivil.blumenau.sc.gov.br/static/data/nivel_oficial.json",
         ca_extra=CERT_ALERTABLU),
    Alvo("indaial-documento-defesa-civil.txt", "indaial",
         "https://docs.google.com/document/d/1EN1iEU3lDUfRnOtPx6IjeSpoO7DMGd-iD4i2AdHiFvk/export?format=txt"),
)


# --- robots.txt -------------------------------------------------------------

def caminho_com_consulta(url: str) -> str:
    u = urlparse(url)
    return (u.path or "/") + (f"?{u.query}" if u.query else "")


def robots_de(host_url: str, pedir) -> str:
    """O texto do robots.txt do host, ou "" quando não há (norma: sem regras)."""
    u = urlparse(host_url)
    status, corpo, _tipo = pedir(f"{u.scheme}://{u.netloc}/robots.txt", None)
    if status != 200:
        return ""
    return corpo.decode("utf-8", errors="replace")


# --- rede -------------------------------------------------------------------

def pedir_http(url: str, ca_extra: Path | None) -> tuple[int, bytes, str]:
    """Um GET, sem insistir. Devolve (status, corpo, content-type).

    Falha de transporte vira status 0 com a mensagem no corpo — a captura das
    outras fontes não pode parar por causa de um host fora do ar.
    """
    import requests

    espera_turno()
    verificar: bool | str = True
    if ca_extra is not None:
        # Bundle padrão + o intermediário que o servidor esquece de mandar.
        bundle = Path("/tmp/ca-com-intermediario.pem")
        bundle.write_bytes(Path(requests.certs.where()).read_bytes()
                           + b"\n" + ca_extra.read_bytes())
        verificar = str(bundle)
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45,
                         verify=verificar)
    except requests.RequestException as erro:
        return 0, f"{type(erro).__name__}: {erro}".encode(), ""
    return r.status_code, r.content, r.headers.get("Content-Type", "")


# --- captura ----------------------------------------------------------------

def capturar(alvos, saida: Path, pedir=pedir_http) -> list[dict]:
    saida.mkdir(parents=True, exist_ok=True)
    robots: dict[str, str] = {}
    linhas = []
    for alvo in alvos:
        host = urlparse(alvo.url).netloc
        if host not in robots:
            robots[host] = robots_de(alvo.url, lambda u, _ca: pedir(u, alvo.ca_extra))
        item = {"arquivo": alvo.arquivo, "cidade": alvo.cidade, "url": alvo.url}
        if not robots_permite(robots[host], caminho_com_consulta(alvo.url)):
            item.update(estado="recusado_robots", http=None, bytes=0, sha256=None)
            linhas.append(item)
            continue
        status, corpo, tipo = pedir(alvo.url, alvo.ca_extra)
        if status == 0:
            item.update(estado="falha_transporte", http=None, bytes=0, sha256=None,
                        motivo=corpo.decode(errors="replace")[:300])
            linhas.append(item)
            continue
        (saida / alvo.arquivo).write_bytes(corpo)
        item.update(estado="ok" if status == 200 else "http_nao_200", http=status,
                    bytes=len(corpo), sha256=hashlib.sha256(corpo).hexdigest(),
                    content_type=tipo)
        linhas.append(item)
    return linhas


def fatias(nome: str, corpo: bytes, largura: int = LARGURA_FATIA) -> list[str]:
    """O corpo em gzip+base64, fatiado, uma linha por fatia, com o sha256."""
    sha = hashlib.sha256(corpo).hexdigest()
    b64 = base64.b64encode(gzip.compress(corpo, mtime=0)).decode()
    partes = [b64[i:i + largura] for i in range(0, len(b64), largura)] or [""]
    return [f"BRUTO {nome} {sha} {i}/{len(partes)} {p}" for i, p in enumerate(partes, 1)]


RE_FATIA = re.compile(r"BRUTO (\S+) ([0-9a-f]{64}) (\d+)/(\d+) ([A-Za-z0-9+/=]*)")


def remontar(log: str, destino: Path) -> dict[str, str]:
    """Junta as fatias do log. Só grava o arquivo cujo sha256 confere.

    Devolve {arquivo: "confere" | "sha256 não confere" | "faltam fatias ..."}.
    """
    pedacos: dict[str, dict[int, str]] = {}
    shas: dict[str, str] = {}
    totais: dict[str, int] = {}
    for m in RE_FATIA.finditer(log):
        nome, sha, n, tot, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5)
        pedacos.setdefault(nome, {})[n] = b
        shas[nome], totais[nome] = sha, tot
    destino.mkdir(parents=True, exist_ok=True)
    resultado = {}
    for nome, ps in sorted(pedacos.items()):
        faltam = [i for i in range(1, totais[nome] + 1) if i not in ps]
        if faltam:
            resultado[nome] = f"faltam fatias {faltam}"
            continue
        corpo = gzip.decompress(base64.b64decode("".join(ps[i] for i in range(1, totais[nome] + 1))))
        if hashlib.sha256(corpo).hexdigest() != shas[nome]:
            resultado[nome] = "sha256 não confere"
            continue
        (destino / nome).write_bytes(corpo)
        resultado[nome] = "confere"
    return resultado


def main() -> int:
    ap = argparse.ArgumentParser()
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--saida", type=Path, help="pasta onde gravar a captura (no runner)")
    grupo.add_argument("--remontar", nargs=2, metavar=("LOG", "DESTINO"),
                       help="remonta os corpos a partir do log do job")
    args = ap.parse_args()

    if args.remontar:
        log, destino = args.remontar
        resultado = remontar(Path(log).read_text(encoding="utf-8", errors="replace"), Path(destino))
        for nome, estado in resultado.items():
            print(f"{nome}: {estado}")
        return 0 if resultado and all(v == "confere" for v in resultado.values()) else 1

    linhas = capturar(ALVOS, args.saida)
    manifesto = {
        "capturado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user_agent": USER_AGENT,
        "alvos": linhas,
    }
    (args.saida / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for l in linhas:
        print(f"ALVO {l['estado']:18} http={l['http']} bytes={l['bytes']:>7} "
              f"{l['cidade']:11} {l['url']}" + (f"  motivo: {l['motivo']}" if l.get("motivo") else ""))
    for l in linhas:
        if l["sha256"]:
            for linha in fatias(l["arquivo"], (args.saida / l["arquivo"]).read_bytes()):
                print(linha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
