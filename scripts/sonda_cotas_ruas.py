#!/usr/bin/env python3
"""
Sonda das tabelas OFICIAIS de cota por rua.

Por que existe: `data/cotas-ruas.json` tem 57 pontos, e eles vieram do que a
imprensa reproduziu. As tabelas oficiais existem e são muito maiores — Rio do
Sul publica **555 ruas** com mínima e máxima. Enquanto o bot responde por 57
pontos, a resposta certa para quase todo mundo é "não tenho a sua rua", que é
honesto e inútil.

Esta sonda NÃO baixa dado nem escreve em `data/`. Ela só descobre por onde o
dado sai, porque em três dos quatro portais ele está atrás de JavaScript:

* **Rio do Sul** — portal Yii (`index.php?r=controlador/acao`) com uma tabela de
  555 itens e botão "Exportar Dados". Duas hipóteses: a tabela já vem montada no
  HTML (aí basta paginar e ler) ou a exportação chama uma rota própria. A sonda
  testa as duas.
* **Gaspar** — mapa "Pesquise sua cota", do estudo do CEOPS/FURB feito rua por
  rua. Procura o link do mapa e os endereços citados no JavaScript dele.
* **Itajaí** — ArcGIS da prefeitura. O REST é público; falta achar a pasta da
  Defesa Civil e o FeatureServer das cotas de inundação.

**Blumenau fica de fora de propósito.** O `robots.txt` do AlertaBlu proíbe
acesso automatizado, e a tabela de cotas está sob essa proibição. A sonda lê o
`robots.txt` — que é feito para ser lido por robô — e mostra a regra, para a
decisão ficar registrada em vez de virar hábito. A tabela de lá se pede à
Defesa Civil de Blumenau.

Uso na VPS (daqui do sandbox nenhum destes domínios responde):
    python3 scripts/sonda_cotas_ruas.py 2>&1 | tee /tmp/cotas_ruas.txt
"""

import re
import sys
import time
from urllib.parse import urljoin

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"

#: Uma requisição por segundo. São portais de prefeitura, com orçamento de
#: prefeitura, e a sonda roda de madrugada uma vez — não vale apertar.
PAUSA_S = 1.0

RIO_DO_SUL = "https://defesacivil.riodosul.sc.gov.br/index.php?r=soscota-rua%2Ftabela"
RIO_DO_SUL_BASE = "https://defesacivil.riodosul.sc.gov.br/"
GASPAR = "https://defesacivil.gaspar.sc.gov.br/"
ARCGIS = "https://arcgis.itajai.sc.gov.br/server/rest/services"
ALERTABLU_ROBOTS = "https://alertablu.blumenau.sc.gov.br/robots.txt"

#: Palavras que denunciam serviço de cota/inundação no meio de dezenas de
#: serviços de urbanismo, iluminação e cadastro imobiliário.
INTERESSE = re.compile(r"cota|inunda|enchent|defesa|civil|risco|alag", re.I)

RE_LINK = re.compile(r"""href\s*=\s*['"]([^'"]+)['"]""", re.I)
RE_SCRIPT = re.compile(r"""<script[^>]+src\s*=\s*['"]([^'"]+)['"]""", re.I)
RE_ROTA_YII = re.compile(r"""r=([a-z0-9\-]+%2F[a-z0-9\-]+|[a-z0-9\-]+/[a-z0-9\-]+)""", re.I)
RE_ENDPOINT = re.compile(
    r"""['"]([^'"\s]{4,140}?(?:\.json|\.php|\.csv|\.xlsx?|/api/|/rest/|/query)[^'"\s]{0,80})['"]""",
    re.I,
)


def buscar(url: str, **extra):
    """GET identificado, com pausa. Nunca desliga a verificação de certificado."""
    import requests

    time.sleep(PAUSA_S)
    return requests.get(url, headers={"User-Agent": UA}, timeout=30, **extra)


def cabecalho(titulo: str, url: str) -> None:
    print(f"\n{'=' * 70}\n=== {titulo}\n    {url}")


def resumo(r) -> None:
    tipo = r.headers.get("Content-Type", "?")
    print(f"    HTTP {r.status_code} · {len(r.content)} bytes · {tipo}")


# --- Rio do Sul -------------------------------------------------------------

def sondar_rio_do_sul() -> None:
    """
    555 ruas com mínima e máxima. É a maior tabela conhecida da bacia — dez
    vezes tudo que temos hoje.
    """
    cabecalho("Rio do Sul — Cota de Cheias por Rua (555 itens)", RIO_DO_SUL)
    try:
        r = buscar(RIO_DO_SUL)
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    resumo(r)
    if r.status_code != 200:
        return
    html = r.text

    # Hipótese 1: a tabela já vem no HTML. Portal Yii costuma renderizar
    # GridView no servidor — nesse caso não há endpoint a descobrir, e o
    # trabalho vira paginar e ler.
    linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I)
    celulas = [re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", l, re.S | re.I) for l in linhas]
    com_numero = [c for c in celulas if any(re.search(r"\d+[,.]\d+", x) for x in c)]
    print(f"    linhas <tr> no HTML: {len(linhas)} · com número decimal: {len(com_numero)}")
    for c in com_numero[:5]:
        limpo = [re.sub(r"<[^>]+>", "", x).strip()[:40] for x in c]
        print(f"      exemplo de linha: {limpo}")
    if com_numero:
        print("    >>> A TABELA VEM NO HTML. Não precisa de endpoint: dá para ler")
        print("        direto, respeitando a paginação. Procure o parâmetro de página")
        print("        nos links abaixo.")

    # Hipótese 2: a exportação chama uma rota própria.
    rotas = sorted(set(RE_ROTA_YII.findall(html)))
    print(f"    rotas Yii citadas na página: {len(rotas)}")
    for rota in rotas:
        marca = " <<< parece exportação" if re.search(r"export|excel|csv|pdf|down", rota, re.I) else ""
        print(f"      r={rota}{marca}")

    scripts = [urljoin(RIO_DO_SUL_BASE, s) for s in RE_SCRIPT.findall(html)]
    proprios = [s for s in scripts if "riodosul" in s and "jquery" not in s.lower()]
    print(f"    scripts próprios: {len(proprios)}")
    for s in proprios[:6]:
        print(f"      {s}")
        try:
            js = buscar(s)
        except Exception as e:
            print(f"        FALHOU: {e}")
            continue
        achados = sorted(set(RE_ENDPOINT.findall(js.text)) | set(RE_ROTA_YII.findall(js.text)))
        for a in achados[:12]:
            print(f"        cita: {a}")


# --- Gaspar -----------------------------------------------------------------

def sondar_gaspar() -> None:
    """
    O estudo do CEOPS/FURB fez Gaspar rua por rua, referenciado à régua da ANA
    na Círculo. Temos 23 pontos que a imprensa publicou; a base inteira está
    atrás do mapa "Pesquise sua cota".
    """
    cabecalho("Gaspar — mapa \"Pesquise sua cota\"", GASPAR)
    try:
        r = buscar(GASPAR)
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    resumo(r)
    if r.status_code != 200:
        return

    links = sorted(set(RE_LINK.findall(r.text)))
    interessantes = [l for l in links if INTERESSE.search(l)]
    print(f"    links na página: {len(links)} · com cara de cota/inundação: {len(interessantes)}")
    for l in interessantes[:20]:
        print(f"      {urljoin(GASPAR, l)}")

    for l in interessantes[:4]:
        alvo = urljoin(GASPAR, l)
        try:
            p = buscar(alvo)
        except Exception as e:
            print(f"    {alvo}\n        FALHOU: {e}")
            continue
        print(f"    {alvo}")
        print(f"        HTTP {p.status_code} · {len(p.content)} bytes")
        if p.status_code != 200:
            continue
        achados = sorted(set(RE_ENDPOINT.findall(p.text)))
        for a in achados[:15]:
            print(f"        cita: {a}")


# --- Itajaí, ArcGIS ---------------------------------------------------------

def sondar_arcgis() -> None:
    """
    "Cota por endereço" de Itajaí. Se o FeatureServer responder, é a fonte sem
    raspagem nenhuma — e Itajaí é hoje a cidade com manchas de inundação no
    repositório e nenhuma cota de rua.
    """
    cabecalho("Itajaí — ArcGIS REST", ARCGIS)
    try:
        r = buscar(ARCGIS, params={"f": "json"})
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    resumo(r)
    if r.status_code != 200:
        return
    try:
        raiz = r.json()
    except ValueError:
        print("    resposta não é JSON — o servidor pode exigir token")
        print(f"    início: {r.text[:200]}")
        return

    pastas = raiz.get("folders") or []
    servicos = raiz.get("services") or []
    print(f"    pastas: {len(pastas)} · serviços na raiz: {len(servicos)}")
    print(f"      pastas: {', '.join(pastas) if pastas else '(nenhuma)'}")

    alvos = [p for p in pastas if INTERESSE.search(p)]
    if not alvos:
        # Sem nome óbvio, vale olhar todas — mas com teto, para não varrer o
        # servidor de uma prefeitura por curiosidade.
        alvos = pastas[:8]
        print("      nenhuma pasta com nome de cota/inundação; olhando as primeiras")

    for pasta in alvos:
        url = f"{ARCGIS}/{pasta}"
        try:
            p = buscar(url, params={"f": "json"})
            dados = p.json()
        except Exception as e:
            print(f"    {pasta}: FALHOU: {e}")
            continue
        lista = dados.get("services") or []
        print(f"    pasta {pasta}: {len(lista)} serviço(s)")
        for s in lista:
            nome, tipo = s.get("name", "?"), s.get("type", "?")
            marca = " <<<" if INTERESSE.search(nome) else ""
            print(f"      {nome} ({tipo}){marca}")

    for s in servicos:
        nome, tipo = s.get("name", "?"), s.get("type", "?")
        if INTERESSE.search(nome):
            print(f"    serviço na raiz com cara de cota: {nome} ({tipo})")
            print(f"      teste: {ARCGIS}/{nome}/{tipo}/0/query"
                  "?where=1%3D1&outFields=*&resultRecordCount=3&f=geojson")


# --- Blumenau ---------------------------------------------------------------

def mostrar_robots_blumenau() -> None:
    """
    Não raspar não é timidez: é a regra que o site publica para robôs, e um
    projeto que pede dado às Defesas Civis não começa desrespeitando o robots
    de uma delas. Isto aqui só registra a regra.
    """
    cabecalho("Blumenau — por que a sonda NÃO entra", ALERTABLU_ROBOTS)
    try:
        r = buscar(ALERTABLU_ROBOTS)
    except Exception as e:
        print(f"    FALHOU: {e}")
        print("    (a falha de certificado do AlertaBlu já é conhecida)")
        return
    resumo(r)
    if r.status_code == 200:
        for linha in r.text.splitlines()[:20]:
            print(f"      {linha}")
    print("    A tabela de cotas de Blumenau se PEDE à Defesa Civil.")
    print("    A FURB está refazendo o levantamento (~20 mil edificações);")
    print("    quando sair, substitui o que temos.")


def main() -> int:
    # Sem isto, `python3 sonda.py | tee arquivo.txt` — que é como a sonda é
    # usada — guarda tudo em bloco e só descarrega no fim: quem roda fica
    # olhando um terminal parado por meio minuto, sem saber se travou.
    sys.stdout.reconfigure(line_buffering=True)
    print(__doc__)
    sondar_rio_do_sul()
    sondar_gaspar()
    sondar_arcgis()
    mostrar_robots_blumenau()
    print("\n" + "=" * 70)
    print("Cole a saída inteira no Claude Code. O que interessa: se a tabela de")
    print("Rio do Sul vem no HTML, se o ArcGIS de Itajaí responde sem token, e")
    print("qual endereço o mapa de Gaspar chama.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
