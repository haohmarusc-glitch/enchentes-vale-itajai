#!/usr/bin/env python3
"""
Sonda: chuva das cidades sem cobertura, e a posição das réguas.

DUAS PERGUNTAS numa passada só, porque cada rodada custa uma ida e volta com
quem tem acesso à VPS.

O problema: a Defesa Civil de Itajaí publica pluviômetro só em Itajaí, Brusque,
Ilhota e Rio do Sul. Vidal Ramos, Botuverá, Guabiruba, Taió, Ituporanga,
Ibirama, Apiúna, Indaial, Blumenau e Gaspar ficam sem chuva na tela — e
Blumenau é a cidade com a série histórica mais longa do projeto.

Isto NÃO é um coletor. É reconhecimento, para rodar uma vez na VPS (que alcança
os sites) e colar a saída de volta. O analisador de verdade só é escrito depois,
contra o retorno real. Este projeto já pagou três vezes por parser escrito às
cegas: a tábua de maré era montada em JavaScript, o <h2> das estações mora
dentro de um <header>, e cinco réguas de Itajaí foram misturadas numa só.

Três candidatas, em ordem de cobertura:

1. **CEMADEN** — rede nacional de pluviômetros automáticos, com aparelhos na
   maioria dos municípios de risco de SC. É a única que cobriria a bacia
   inteira. O acesso oficial em massa é por formulário com envio por e-mail; o
   mapa interativo consome endpoints próprios, que é o que a sonda procura.
   Dado do CEMADEN é **cru** (sem tratamento, podendo conter inconsistência) e
   vem em **UTC** — as duas coisas mudam o coletor e precisam estar escritas.
2. **AlertaBlu** — vários pluviômetros em Blumenau, a cidade que mais importa
   e que hoje não tem nem nível ao vivo.
3. **Defesa Civil de SC** — cobertura estadual.

A SEGUNDA PERGUNTA: onde fica cada régua
----------------------------------------
Para o bot responder a uma localização enviada no Telegram ("qual régua está
perto de mim?"), é preciso a coordenada de cada estação. Isso não se inventa: a
Defesa Civil de Itajaí tem uma página de mapa, e se ela traz latitude e
longitude das estações, essa é a fonte — posição de régua tirada de palpite
apontaria a pessoa para o rio errado.

Vale lembrar o limite que nenhuma coordenada resolve: saber que a régua mais
próxima está a 3 km NÃO diz se a rua de quem perguntou alaga. Quem sabe isso é
a Defesa Civil municipal. O bot vai dizer a distância e dizer que não sabe o
resto.

O que a sonda imprime, por endereço: status, tamanho, tipo. Se for JSON, a
forma (chaves do topo, quantos registros, o primeiro inteiro). Se for HTML, os
`<script src>` e toda URL que cheire a API — foi assim que achamos o
`ajax/mares.php` escondido no JavaScript da página de marés.

Uso na VPS:
    python3 scripts/sonda_fontes_chuva.py
    python3 scripts/sonda_fontes_chuva.py --salvar /tmp/sondas   # guarda os corpos
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"

#: Intervalo entre chamadas. São serviços públicos e de graça: não se martela.
INTERVALO_S = 1.5

#: 42 é o código do IBGE para Santa Catarina, que é como o mapa do CEMADEN
#: costuma separar os dados por estado.
ALVOS: list[tuple[str, str]] = [
    ("CEMADEN — mapa novo", "https://mapainterativo.cemaden.gov.br/"),
    ("CEMADEN — mapa antigo", "http://www2.cemaden.gov.br/mapainterativo/"),
    ("CEMADEN — dados SC (endereço histórico)",
     "http://sjc.salvar.cemaden.gov.br/resources/dados/42.json"),
    ("CEMADEN — dados SC (no domínio novo)",
     "https://mapainterativo.cemaden.gov.br/resources/dados/42.json"),
    ("CEMADEN — dados abertos", "https://dadosabertos.cemaden.gov.br/"),
    ("AlertaBlu", "https://alertablu.blumenau.sc.gov.br/"),
    ("AlertaBlu — pluviômetros", "https://alertablu.blumenau.sc.gov.br/d/pluviometros"),
    ("Defesa Civil SC — monitoramento", "https://monitoramento.defesacivil.sc.gov.br/"),
    # --- Onde ficam as réguas ---
    ("Itajaí — mapa das estações", "https://defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php"),
    ("Itajaí — mapa (caminho alternativo)",
     "https://defesacivil.itajai.sc.gov.br/monitoramento/mapa"),
]

#: Coordenada em qualquer formato reconhecível: par de decimais com sinal, ou
#: chaves nomeadas. Santa Catarina fica perto de -26,9 / -48,7, então o filtro
#: por faixa evita confundir coordenada com qualquer outro par de números.
RE_COORD = re.compile(
    r"""(?:lat(?:itude)?["'\s:=]+(-2[0-9]\.\d+)|(-2[0-9]\.\d{4,})[,\s]+(-4[89]\.\d{4,}))""",
    re.I,
)

#: Qualquer coisa que cheire a endpoint dentro de HTML ou JavaScript.
RE_URL = re.compile(
    r"""['"]([^'"\s]*(?:/resources/|/api/|/dados/|/ajax/|\.json|\.php|/rest/)[^'"\s]*)['"]""",
    re.I,
)


def forma_do_json(texto: str) -> list[str]:
    """A forma do JSON, sem despejar o conteúdo inteiro na tela."""
    try:
        d = json.loads(texto)
    except ValueError as e:
        return [f"não é JSON válido: {e}"]

    linhas = []
    if isinstance(d, dict):
        linhas.append(f"objeto com as chaves: {list(d)[:20]}")
        for chave, valor in list(d.items())[:6]:
            if isinstance(valor, list):
                linhas.append(f"  {chave!r}: lista de {len(valor)}")
                if valor:
                    linhas.append(f"    primeiro: {json.dumps(valor[0], ensure_ascii=False)[:400]}")
            else:
                linhas.append(f"  {chave!r}: {json.dumps(valor, ensure_ascii=False)[:200]}")
    elif isinstance(d, list):
        linhas.append(f"lista de {len(d)}")
        if d:
            linhas.append(f"  primeiro: {json.dumps(d[0], ensure_ascii=False)[:400]}")
    else:
        linhas.append(f"valor solto: {json.dumps(d, ensure_ascii=False)[:200]}")
    return linhas


def forma_do_html(texto: str) -> list[str]:
    linhas = []
    scripts = re.findall(r"<script[^>]+src=['\"]([^'\"]+)['\"]", texto, re.I)
    linhas.append(f"<script src>: {len(scripts)}")
    for s in scripts[:15]:
        linhas.append(f"    {s}")
    urls = sorted(set(RE_URL.findall(texto)))
    linhas.append(f"URLs com cara de API: {len(urls)}")
    for u in urls[:25]:
        linhas.append(f"    {u}")
    if not scripts and not urls:
        linhas.append("    (nada — a página pode montar tudo em JavaScript externo)")
    return linhas


def sondar(nome: str, url: str, guardar: Path | None) -> None:
    import requests

    print(f"\n=== {nome}\n    {url}")
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30, allow_redirects=True)
    except Exception as e:
        print(f"    FALHOU: {e}")
        return

    tipo = (r.headers.get("Content-Type") or "?").split(";")[0]
    print(f"    HTTP {r.status_code} · {len(r.content)} bytes · {tipo}")
    if r.url != url:
        print(f"    redirecionou para: {r.url}")
    if r.status_code != 200:
        print(f"    corpo (início): {r.text[:200]!r}")
        return

    if guardar:
        guardar.mkdir(parents=True, exist_ok=True)
        alvo = guardar / (re.sub(r"[^a-zA-Z0-9]+", "-", url)[:80] + ".txt")
        alvo.write_text(r.text, encoding="utf-8", errors="replace")
        print(f"    corpo salvo em {alvo}")

    corpo = r.text.lstrip()
    if "json" in tipo or corpo[:1] in "{[":
        for linha in forma_do_json(r.text):
            print(f"    {linha}")
    else:
        for linha in forma_do_html(r.text):
            print(f"    {linha}")

    # O que interessa é chuva: se estes termos não aparecem, o endereço até
    # responde, mas provavelmente não é o que procuramos.
    achados = [p for p in ("chuva", "pluviom", "precipita", "acumulad", "mm")
               if p in r.text.lower()]
    print(f"    termos de chuva presentes: {achados or 'nenhum'}")

    # Coordenadas: só interessa a faixa de Santa Catarina, para não confundir
    # par de números qualquer com posição de estação.
    coords = [c for grupo in RE_COORD.findall(r.text) for c in grupo if c]
    if coords:
        print(f"    coordenadas na faixa de SC: {len(coords)} — amostra: {coords[:8]}")
    else:
        print("    coordenadas: nenhuma reconhecida")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salvar", metavar="PASTA", help="guarda os corpos das respostas")
    args = ap.parse_args()

    try:
        import requests  # noqa: F401
    except ImportError:
        sys.exit("Instale a dependência: pip install requests")

    guardar = Path(args.salvar) if args.salvar else None
    for i, (nome, url) in enumerate(ALVOS):
        if i:
            time.sleep(INTERVALO_S)
        sondar(nome, url, guardar)

    print("\n\nCole esta saída de volta. Com ela eu escrevo o coletor contra o")
    print("retorno real, em vez de adivinhar a forma dos dados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
