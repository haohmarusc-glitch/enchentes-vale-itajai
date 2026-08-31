#!/usr/bin/env python3
"""
Segunda sonda das cotas por rua: entrar onde a primeira parou.

O que a primeira achou, e que motiva esta:

* **Rio do Sul** — a página tem 2 kB e nenhuma linha de tabela: é aplicação
  Vite (`assets/index-<hash>.js`). Os 555 registros vêm de uma API que o
  pacote chama, e o pacote é minificado — o endereço aparece concatenado, que
  é por que a primeira sonda não achou nada. Esta procura com o CONTEXTO ao
  redor de cada palavra-chave, que é como se lê código minificado.
* **Itajaí** — o ArcGIS respondeu sem token, com 200 serviços na raiz e três
  com cara de inundação. Esta sonda entra em cada um: quais camadas, quais
  campos e três registros de exemplo. É o que decide se existe cota por
  endereço ou se é só desenho.
* **Gaspar** — caiu por timeout de conexão. O host responde na coleta de
  níveis, então vale insistir; esta usa o `comum.baixar`, que já sabe insistir
  sem virar martelo.

**Alerta que vale mais que o dado:** `Relevo_Ponto_Cotado_Altimetrico` é
altimetria — altura do TERRENO acima do nível do mar. Não é cota de régua.
Dizer "sua rua alaga a 3,20 m" com um número que é altitude do solo, e não
nível do rio, seria o erro da referência de Blumenau outra vez, com um zero
ainda mais distante. Se um dia for usado, é como entrada de estudo, com perfil
de linha d'água no meio — nunca copiado para `cotas-ruas.json`.

Uso na VPS:
    python3 scripts/sonda_cotas_ruas2.py 2>&1 | tee /tmp/cotas_ruas2.txt
"""

import json
import re
import sys
import time
from urllib.parse import urljoin

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
PAUSA_S = 1.0

RIO_DO_SUL_BASE = "https://defesacivil.riodosul.sc.gov.br/"
RIO_DO_SUL = RIO_DO_SUL_BASE + "index.php?r=soscota-rua%2Ftabela"
GASPAR = "https://defesacivil.gaspar.sc.gov.br/"
GASPAR_TABELA = GASPAR + "monitoramento/tabela"
ARCGIS = "https://arcgis.itajai.sc.gov.br/server/rest/services"

#: Os três que a primeira sonda marcou, em ordem de promessa.
SERVICOS = ["historico_inundacoes", "Hidrografia_Terreno_Sujeito_Inundacao",
            "Relevo_Ponto_Cotado_Altimetrico"]

#: Palavras que, num pacote minificado, ficam ao lado do endereço da API.
CHAVES_JS = ["soscota", "cota", "rua", "logradouro", "api/", "axios", "baseURL",
             "minima", "maxima", "export"]

RE_SCRIPT = re.compile(r"""<script[^>]+src\s*=\s*['"]([^'"]+)['"]""", re.I)
RE_CAMINHO = re.compile(r"""['"`](/[A-Za-z0-9_\-./]{3,80})['"`]""")


def buscar(url: str, **extra):
    import requests

    time.sleep(PAUSA_S)
    return requests.get(url, headers={"User-Agent": UA}, timeout=30, **extra)


def cabecalho(titulo: str, url: str = "") -> None:
    print(f"\n{'=' * 70}\n=== {titulo}" + (f"\n    {url}" if url else ""))


# --- Rio do Sul -------------------------------------------------------------

def sondar_rio_do_sul() -> None:
    cabecalho("Rio do Sul — dentro do pacote da aplicação", RIO_DO_SUL)
    try:
        pagina = buscar(RIO_DO_SUL)
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    scripts = [urljoin(RIO_DO_SUL_BASE, s) for s in RE_SCRIPT.findall(pagina.text)]
    print(f"    scripts na página: {len(scripts)}")
    for url in scripts:
        print(f"\n    --- {url}")
        try:
            js = buscar(url)
        except Exception as e:
            print(f"        FALHOU: {e}")
            continue
        print(f"        HTTP {js.status_code} · {len(js.content)} bytes")
        if js.status_code != 200:
            continue
        texto = js.text

        # Caminhos absolutos: em aplicação Vite é assim que a rota da API
        # aparece, mesmo minificada.
        caminhos = sorted(set(RE_CAMINHO.findall(texto)))
        uteis = [c for c in caminhos
                 if not re.search(r"\.(css|png|jpe?g|svg|woff2?|ttf|ico|map)$", c, re.I)]
        print(f"        caminhos absolutos citados: {len(uteis)}")
        for c in uteis[:60]:
            print(f"          {c}")

        # Contexto ao redor das palavras-chave: é como se lê minificado.
        for chave in CHAVES_JS:
            for m in list(re.finditer(re.escape(chave), texto, re.I))[:4]:
                ini, fim = max(0, m.start() - 90), min(len(texto), m.end() + 90)
                trecho = texto[ini:fim].replace("\n", " ")
                print(f"        [{chave}] …{trecho}…")


# --- Itajaí, ArcGIS ---------------------------------------------------------

def campos_e_amostra(servico: str, tipo: str = "FeatureServer") -> None:
    base = f"{ARCGIS}/{servico}/{tipo}"
    try:
        r = buscar(base, params={"f": "json"})
        info = r.json()
    except Exception as e:
        print(f"    {servico}/{tipo}: FALHOU: {e}")
        return
    camadas = info.get("layers") or []
    tabelas = info.get("tables") or []
    print(f"    {servico}/{tipo}: {len(camadas)} camada(s), {len(tabelas)} tabela(s)")
    if info.get("error"):
        print(f"      erro do servidor: {info['error']}")
        return

    for c in camadas[:6]:
        cid, nome = c.get("id"), c.get("name", "?")
        print(f"      camada {cid}: {nome}")
        try:
            meta = buscar(f"{base}/{cid}", params={"f": "json"}).json()
        except Exception as e:
            print(f"        FALHOU: {e}")
            continue
        campos = [f"{f.get('name')}:{f.get('type', '').replace('esriFieldType', '')}"
                  for f in (meta.get("fields") or [])]
        print(f"        campos ({len(campos)}): {', '.join(campos[:25])}")
        print(f"        geometria: {meta.get('geometryType')} · "
              f"registros: {meta.get('maxRecordCount')} por página")

        # Três registros, sem geometria: o que importa aqui é o ATRIBUTO —
        # existe cota por ponto, ou é só polígono desenhado?
        try:
            amostra = buscar(f"{base}/{cid}/query", params={
                "where": "1=1", "outFields": "*", "returnGeometry": "false",
                "resultRecordCount": 3, "f": "json",
            }).json()
        except Exception as e:
            print(f"        amostra FALHOU: {e}")
            continue
        feicoes = amostra.get("features") or []
        if amostra.get("error"):
            print(f"        amostra recusada: {amostra['error']}")
        for f in feicoes:
            print(f"        registro: {json.dumps(f.get('attributes'), ensure_ascii=False)[:300]}")
        if not feicoes and not amostra.get("error"):
            print("        (camada vazia)")


def sondar_arcgis() -> None:
    cabecalho("Itajaí — ArcGIS, dentro dos serviços", ARCGIS)

    # A pasta defesacivil apareceu com 0 serviços. Ou está vazia, ou o
    # servidor respondeu outra coisa — vale ver o corpo cru.
    try:
        r = buscar(f"{ARCGIS}/defesacivil", params={"f": "json"})
        print(f"    pasta defesacivil: HTTP {r.status_code} · corpo: {r.text[:400]}")
    except Exception as e:
        print(f"    pasta defesacivil: FALHOU: {e}")

    # Todos os nomes da raiz: a primeira sonda filtrou por palavra-chave, e um
    # serviço pode se chamar qualquer coisa.
    try:
        raiz = buscar(ARCGIS, params={"f": "json"}).json()
        nomes = sorted({s.get("name", "?") for s in (raiz.get("services") or [])})
        print(f"\n    todos os {len(nomes)} serviços da raiz:")
        for i in range(0, len(nomes), 4):
            print("      " + " · ".join(nomes[i:i + 4]))
    except Exception as e:
        print(f"    raiz: FALHOU: {e}")

    for s in SERVICOS:
        print()
        campos_e_amostra(s)


# --- Gaspar -----------------------------------------------------------------

def sondar_gaspar() -> None:
    cabecalho("Gaspar — segunda tentativa (o host responde na coleta)")
    from comum import baixar

    for nome, url in (("raiz", GASPAR), ("tabela de monitoramento", GASPAR_TABELA)):
        print(f"    {nome}: {url}")
        try:
            html = baixar(url)
        except Exception as e:
            print(f"        FALHOU: {e}")
            continue
        print(f"        {len(html)} bytes")
        links = sorted(set(re.findall(r"""href\s*=\s*['"]([^'"]+)['"]""", html, re.I)))
        cota = [l for l in links if re.search(r"cota|inunda|enchent|mapa", l, re.I)]
        print(f"        links com cara de cota/mapa: {len(cota)}")
        for l in cota[:15]:
            print(f"          {urljoin(url, l)}")


def main() -> int:
    # Sem isto, `sonda.py | tee arquivo.txt` guarda tudo em bloco e o terminal
    # fica parado até o fim.
    sys.stdout.reconfigure(line_buffering=True)
    print(__doc__)
    sondar_rio_do_sul()
    sondar_arcgis()
    sondar_gaspar()
    print("\n" + "=" * 70)
    print("O que decide: se algum serviço do ArcGIS tem cota POR ENDEREÇO nos")
    print("atributos, e qual rota o pacote de Rio do Sul chama para as 555 ruas.")
    print("Lembrete: ponto cotado altimétrico é altura do terreno, NÃO cota de")
    print("régua — não vai para cotas-ruas.json de jeito nenhum.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
