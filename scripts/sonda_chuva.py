#!/usr/bin/env python3
"""
Sonda: descobre o que a página de chuvas da Defesa Civil de Itajaí publica.

Isto NÃO é um coletor. É um script de reconhecimento, para rodar uma vez na
VPS (que alcança o site) e colar a saída de volta. O coletor de verdade só é
escrito depois, contra o HTML real — foi assim que descobrimos que a página de
marés era renderizada em JS e que o <h2> das estações mora dentro de um
<header>. Escrever analisador às cegas já custou caro neste projeto.

O que ele imprime, por página:
  - todo <h2> encontrado (o título exato de cada estação);
  - todo par "rótulo: valor" dentro do bloco daquela estação;
  - o conjunto de rótulos distintos (é daí que sai quais janelas de
    acumulado a fonte realmente oferece — 1 h, 12 h, 24 h, 48 h…);
  - qualquer URL de ajax/fetch citada no HTML, caso a página seja montada
    por JavaScript e o dado esteja em outro endereço.

Uso na VPS:
    python3 scripts/sonda_chuva.py
    python3 scripts/sonda_chuva.py --salvar /tmp/chuvas.html   # guarda o HTML cru
"""
import argparse
import re
import sys
from collections import Counter

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Instale a dependência: pip install beautifulsoup4")

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"

PAGINAS = [
    "https://defesacivil.itajai.sc.gov.br/monitoramento/chuvas",
    # A página de níveis é sondada junto de propósito: se ela já trouxer campos
    # de chuva que o coletor atual ignora, não precisamos de uma segunda fonte.
    "https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios",
]

RE_FETCH = re.compile(r"""(?:fetch|ajax|url|src)\s*[:(=]\s*['"]([^'"]*(?:ajax|\.php|\.json)[^'"]*)['"]""", re.I)


def bloco_da_estacao(h2):
    """Mesma subida do coleta_itajai.py: o <h2> vive dentro de um <header>."""
    for candidato in (h2.find_parent("li"), h2.find_parent("article"),
                      h2.parent.parent if h2.parent else None, h2.parent):
        if candidato is not None:
            return candidato
    return h2


def pares(bloco) -> list[tuple[str, str]]:
    """Todo 'rótulo: valor' do bloco, sem supor quais rótulos existem."""
    achados = []
    for span in bloco.find_all("span", class_="label"):
        rotulo = span.get_text(" ", strip=True).rstrip(": ").strip()
        pai = span.parent
        texto = " ".join(pai.get_text(" ", strip=True).split()) if pai else ""
        valor = texto[len(" ".join(span.get_text(" ", strip=True).split())):].lstrip(": ").strip()
        achados.append((rotulo, valor))
    if not achados:
        # Sem <span class="label">: cai para linhas de lista com dois pontos.
        for li in bloco.find_all("li"):
            texto = " ".join(li.get_text(" ", strip=True).split())
            if ":" in texto:
                rotulo, _, valor = texto.partition(":")
                achados.append((rotulo.strip(), valor.strip()))
    return achados


def sondar(html: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    rotulos = Counter()
    titulos = [h2.get_text(" ", strip=True) for h2 in soup.find_all("h2")]
    print(f"  <h2> encontrados: {len(titulos)}")
    for h2 in soup.find_all("h2"):
        titulo = h2.get_text(" ", strip=True)
        if not titulo:
            continue
        conteudo = pares(bloco_da_estacao(h2))
        print(f"  ── {titulo!r}")
        for rotulo, valor in conteudo:
            rotulos[rotulo] += 1
            print(f"       {rotulo!r} = {valor!r}")
        if not conteudo:
            print("       (nenhum par rótulo/valor neste bloco)")

    print("\n  rótulos distintos (quantas estações têm cada um):")
    for rotulo, n in rotulos.most_common():
        print(f"    {n:3d}x  {rotulo!r}")
    if not rotulos:
        print("    (nenhum) — a página provavelmente é montada por JavaScript")

    urls = sorted(set(RE_FETCH.findall(html)))
    print("\n  URLs de ajax/JSON citadas no HTML:")
    for u in urls:
        print(f"    {u}")
    if not urls:
        print("    (nenhuma)")
    scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    print("  <script src> da página:")
    for s in scripts:
        print(f"    {s}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salvar", metavar="ARQUIVO", help="grava o HTML cru da primeira página")
    ap.add_argument("--arquivo", metavar="ARQUIVO", help="sonda um HTML já salvo, sem rede")
    args = ap.parse_args()

    if args.arquivo:
        print(f"=== {args.arquivo}")
        sondar(open(args.arquivo, encoding="utf-8", errors="replace").read())
        return 0

    import requests

    for i, url in enumerate(PAGINAS):
        print(f"\n=== {url}")
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        except requests.RequestException as exc:
            print(f"  FALHOU: {exc}")
            continue
        print(f"  HTTP {r.status_code} · {len(r.text)} bytes")
        if r.status_code != 200:
            continue
        if i == 0 and args.salvar:
            open(args.salvar, "w", encoding="utf-8").write(r.text)
            print(f"  HTML salvo em {args.salvar}")
        sondar(r.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
