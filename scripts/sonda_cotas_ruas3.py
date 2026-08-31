#!/usr/bin/env python3
"""
Terceira sonda: as 555 ruas de Rio do Sul e as camadas que faltaram em Itajaí.

O que a segunda achou, e o que ficou em aberto:

* **Rio do Sul** — o pacote da aplicação tem a tabela DENTRO dele, ao que tudo
  indica. O trecho `po.filter(t=>go(t.name).includes(e))` e a ordenação
  `(e.min??1/0)-(t.min??1/0)` são busca e ordenação sobre uma lista em
  memória, com `name`, `min` e `max` — e o cabeçalho da tabela é
  "Logradouro". Se for isso, as 555 ruas não vêm de API nenhuma: estão no
  JavaScript, e basta lê-las. Esta sonda conta quantos registros com esse
  formato existem no pacote e mostra os primeiros.
  Apareceram também endpoints de verdade — `/public/flood-points`,
  `/public/risk-sectors`, `/public/shelters`, `/public/evacuation-routes` —
  sem o endereço base à vista. Esta sonda imprime o contexto ao redor deles,
  que é onde a base costuma estar montada.
* **Itajaí** — `historico_inundacoes` tem **10 camadas** e a segunda sonda
  imprimiu só 6, por um limite meu. Faltam a 6, 7, 8 e 9. A pasta
  `defesacivil` pede token (`499 Token Required`), então a cota por endereço,
  se existe, está atrás dele — o que já é uma resposta: não é fonte aberta, e
  se for necessária, se pede à prefeitura.

**Não confundir:** `Relevo_Ponto_Cotado_Altimetrico` tem um campo chamado
`cota`, com valores como 5,50 e 6,39 m. É altura do TERRENO acima do nível do
mar. A cota que este projeto usa é o NÍVEL DO RIO na régua da cidade a partir
do qual a rua alaga. São grandezas diferentes com o mesmo nome; ligar uma na
outra exige perfil de linha d'água, e chutar essa ligação produziria
exatamente o número que faz alguém dormir em casa numa noite em que devia
sair. Esta sonda nem toca nesse serviço.

Uso na VPS:
    python3 scripts/sonda_cotas_ruas3.py 2>&1 | tee /tmp/cotas_ruas3.txt
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
ARCGIS = "https://arcgis.itajai.sc.gov.br/server/rest/services"
HISTORICO = f"{ARCGIS}/historico_inundacoes/FeatureServer"

RE_SCRIPT = re.compile(r"""<script[^>]+src\s*=\s*['"]([^'"]+)['"]""", re.I)

#: `{name:"Rua Tal",min:7.2,max:7.8}` em qualquer ordem de campo, com aspas
#: simples, duplas ou crase — o minificador escolhe.
#: A chave pode vir nua (`name:`) ou entre aspas (`"name":`): o minificador
#: tira as aspas, mas um JSON embutido no pacote as mantém.
RE_REGISTRO = re.compile(
    r"""\{[^{}]{0,200}?['"`]?name['"`]?\s*:\s*['"`]([^'"`]{3,90})['"`][^{}]{0,200}?\}""")
RE_MIN = re.compile(r"""['"`]?min['"`]?\s*:\s*(-?\d+(?:\.\d+)?)""")
RE_MAX = re.compile(r"""['"`]?max['"`]?\s*:\s*(-?\d+(?:\.\d+)?)""")

ENDPOINTS = ["/public/flood-points", "/public/risk-sectors", "/public/shelters",
             "/public/evacuation-routes", "/public/city-layers", "/files/serve/"]


def buscar(url: str, **extra):
    import requests

    time.sleep(PAUSA_S)
    return requests.get(url, headers={"User-Agent": UA}, timeout=30, **extra)


def cabecalho(titulo: str, url: str = "") -> None:
    print(f"\n{'=' * 70}\n=== {titulo}" + (f"\n    {url}" if url else ""))


# --- Rio do Sul -------------------------------------------------------------

def sondar_pacote() -> None:
    cabecalho("Rio do Sul — a tabela está dentro do pacote?", RIO_DO_SUL)
    try:
        pagina = buscar(RIO_DO_SUL)
        alvos = [urljoin(RIO_DO_SUL_BASE, s) for s in RE_SCRIPT.findall(pagina.text)
                 if "riodosul" in urljoin(RIO_DO_SUL_BASE, s)]
    except Exception as e:
        print(f"    FALHOU: {e}")
        return

    for url in alvos:
        print(f"\n    --- {url}")
        try:
            js = buscar(url).text
        except Exception as e:
            print(f"        FALHOU: {e}")
            continue
        print(f"        {len(js)} caracteres")

        registros = [m for m in RE_REGISTRO.finditer(js)]
        com_faixa = [m for m in registros if RE_MIN.search(m.group(0))]
        print(f"        objetos com campo `name`: {len(registros)}")
        print(f"        destes, com `min`: {len(com_faixa)}  <<< candidatos a rua")
        for m in com_faixa[:8]:
            texto = m.group(0)
            mn = RE_MIN.search(texto)
            mx = RE_MAX.search(texto)
            print(f"          {m.group(1)[:50]} · min={mn.group(1) if mn else '?'} "
                  f"· max={mx.group(1) if mx else '?'}")
        if len(com_faixa) > 100:
            print("        >>> A TABELA ESTÁ NO PACOTE. Não precisa de API: dá para")
            print("            ler daqui, com a fonte registrada como o portal da")
            print("            Defesa Civil de Rio do Sul.")
        elif not com_faixa:
            print("        (nenhum — então a lista vem de fora; ver endpoints abaixo)")

        # Onde mora a base dos /public/*: o contexto largo mostra a montagem.
        print("\n        contexto dos endpoints:")
        for caminho in ENDPOINTS:
            for m in list(re.finditer(re.escape(caminho), js))[:2]:
                ini, fim = max(0, m.start() - 220), min(len(js), m.end() + 80)
                print(f"          [{caminho}] …{js[ini:fim]}…\n")

        # Qualquer host absoluto citado: se a API for em outro domínio,
        # aparece aqui.
        hosts = sorted({h for h in re.findall(r"""https?://([a-z0-9.\-]{4,60})""", js, re.I)})
        print(f"        hosts citados: {', '.join(hosts[:25])}")

        # `import.meta.env` vira literal na build; vale ver o que sobrou.
        for chave in ("VITE_", "apiBase", "API_URL", "baseURL", "baseUrl"):
            for m in list(re.finditer(re.escape(chave), js))[:3]:
                ini, fim = max(0, m.start() - 120), min(len(js), m.end() + 120)
                print(f"        [{chave}] …{js[ini:fim]}…")


# --- Itajaí -----------------------------------------------------------------

def sondar_camadas_que_faltaram() -> None:
    cabecalho("Itajaí — as 10 camadas de historico_inundacoes", HISTORICO)
    try:
        info = buscar(HISTORICO, params={"f": "json"}).json()
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    camadas = info.get("layers") or []
    print(f"    {len(camadas)} camada(s)")

    for c in camadas:
        cid, nome = c.get("id"), c.get("name", "?")
        print(f"\n    camada {cid}: {nome}")
        try:
            meta = buscar(f"{HISTORICO}/{cid}", params={"f": "json"}).json()
        except Exception as e:
            print(f"        FALHOU: {e}")
            continue
        campos = [f"{f.get('name')}:{f.get('type', '').replace('esriFieldType', '')}"
                  for f in (meta.get("fields") or [])]
        print(f"        campos ({len(campos)}): {', '.join(campos[:30])}")
        print(f"        geometria: {meta.get('geometryType')}")
        try:
            amostra = buscar(f"{HISTORICO}/{cid}/query", params={
                "where": "1=1", "outFields": "*", "returnGeometry": "false",
                "resultRecordCount": 3, "f": "json",
            }).json()
        except Exception as e:
            print(f"        amostra FALHOU: {e}")
            continue
        if amostra.get("error"):
            print(f"        amostra recusada: {amostra['error']}")
            continue
        for f in (amostra.get("features") or []):
            print(f"        registro: "
                  f"{json.dumps(f.get('attributes'), ensure_ascii=False)[:280]}")
        if not amostra.get("features"):
            print("        (camada vazia)")

    # Quantos polígonos tem cada camada: decide se vale baixar.
    print("\n    contagem por camada:")
    for c in camadas:
        cid = c.get("id")
        try:
            n = buscar(f"{HISTORICO}/{cid}/query", params={
                "where": "1=1", "returnCountOnly": "true", "f": "json",
            }).json()
            print(f"      camada {cid}: {n.get('count', '?')} feição(ões)")
        except Exception as e:
            print(f"      camada {cid}: FALHOU: {e}")


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    print(__doc__)
    sondar_pacote()
    sondar_camadas_que_faltaram()
    print("\n" + "=" * 70)
    print("O que decide: quantos candidatos a rua existem dentro do pacote de")
    print("Rio do Sul (se passar de 100, a tabela é aquela) e o que são as")
    print("camadas 6 a 9 de Itajaí.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
