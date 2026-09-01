#!/usr/bin/env python3
"""
Baixa do ArcGIS público da Prefeitura de Itajaí as três camadas que faltam.

Por que existe: as camadas foram baixadas pelo navegador, para a pasta de
Downloads de quem baixou, e nunca chegaram ao repositório. Documento que aponta
para arquivo que não existe é pior que documento sem arquivo — quem lê presume
que o dado está lá. Os serviços na raiz do ArcGIS são **públicos** e servem
GeoJSON direto, então isto não precisa de navegador nenhum.

O que traz:

* `historico_inundacoes` — 10 camadas: manchas totais de 1983, 1984, 2001, 2008
  e 2011, e cotas com lâmina d'água (campo `situa`) de set/2011, jul/2013,
  set/2013, jun/2014 e out/2015;
* `Relevo_Ponto_Cotado_Altimetrico` — 5.237 pontos com elevação;
* `Hidrografia_Terreno_Sujeito_Inundacao` — 110 polígonos de terreno inundável.

**O que o ponto cotado NÃO serve para fazer.** O campo dele se chama `cota` e é
**altura do terreno acima do nível do mar**. O nível das estações da Defesa Civil
de Itajaí é leitura **na régua de cada uma**, com zero próprio e não publicado.
Subtrair um do outro para dizer "faltam Z m para a água chegar aqui" dá um número
com duas casas decimais e nenhum significado físico — e com toda a aparência de
medição. Está proibido em `docs/tela-itajai.md`, e baixar o arquivo não muda
isso: o que ele destrava é o cruzamento com as MANCHAS, que é fato sobre
polígonos e não depende de referência nenhuma.

Uso:
    python3 scripts/baixar_itajai_arcgis.py --seco
    python3 scripts/baixar_itajai_arcgis.py
"""

import argparse
import json
import sys
from urllib.parse import urlparse

from comum import USER_AGENT, baixar, espera_turno
from importar_cotas_rio_do_sul import robots_permite
from comum import DADOS

BASE = "https://arcgis.itajai.sc.gov.br/server/rest/services"
ROBOTS = "https://arcgis.itajai.sc.gov.br/robots.txt"

#: Quantas feições por página. É o teto que o próprio serviço aplica.
POR_PAGINA = 1000

#: Teto de páginas por camada. Serviço que ignore `resultOffset` devolveria a
#: mesma página para sempre; sem isto, o laço não termina.
MAXIMO_DE_PAGINAS = 40

CAMADAS = [
    {
        "arquivo": "itajai-arcgis-inundacoes.geojson.json",
        "servico": "historico_inundacoes/FeatureServer",
        "camadas": list(range(10)),
        "descricao": "manchas de inundação de Itajaí — 10 camadas, 1983 a 2015",
    },
    {
        "arquivo": "itajai-pontos-cotados-altimetricos.geojson.json",
        "servico": "Relevo_Ponto_Cotado_Altimetrico/MapServer",
        "camadas": [0],
        "descricao": "pontos cotados altimétricos — ALTURA DO TERRENO, não cota de régua",
    },
    {
        "arquivo": "itajai-terreno-sujeito-inundacao.geojson.json",
        "servico": "Hidrografia_Terreno_Sujeito_Inundacao/MapServer",
        "camadas": [0],
        "descricao": "terreno sujeito a inundação — 110 polígonos",
    },
]


def url_da_pagina(servico: str, camada: int, deslocamento: int) -> str:
    return (f"{BASE}/{servico}/{camada}/query?where=1%3D1&outFields=*&outSR=4326"
            f"&f=geojson&resultOffset={deslocamento}&resultRecordCount={POR_PAGINA}")


def ler_pagina(texto: str) -> dict:
    """
    O GeoJSON de uma página — ou um erro claro.

    O ArcGIS responde **HTTP 200 com um corpo de erro** quando a consulta não
    presta (token, camada que não existe, parâmetro recusado). Sem esta
    checagem, o erro viraria uma página de zero feições e a camada seria salva
    vazia como se estivesse completa.
    """
    dados = json.loads(texto)
    if isinstance(dados.get("error"), dict):
        erro = dados["error"]
        raise ValueError(f"ArcGIS recusou: {erro.get('code')} {erro.get('message')}")
    if not isinstance(dados.get("features"), list):
        raise ValueError("resposta sem lista de feições")
    return dados


def baixar_camada(servico: str, camada: int, buscar=baixar, pausa=espera_turno) -> list[dict]:
    """Todas as feições de uma camada, paginando até o serviço parar de mandar."""
    feicoes: list[dict] = []
    for pagina in range(MAXIMO_DE_PAGINAS):
        pausa()
        dados = ler_pagina(buscar(url_da_pagina(servico, camada, pagina * POR_PAGINA)))
        lote = dados["features"]
        feicoes.extend(lote)
        # Duas formas de saber que acabou: o serviço diz que não excedeu o
        # limite, ou a página veio menor que o pedido. A primeira é a que o
        # ArcGIS documenta; a segunda cobre quem não manda o campo.
        if not dados.get("exceededTransferLimit") or len(lote) < POR_PAGINA:
            return feicoes
    raise ValueError(f"{servico}/{camada}: passou de {MAXIMO_DE_PAGINAS} páginas — "
                     "o serviço parece ignorar resultOffset")


def permitido(buscar=baixar) -> bool:
    """
    O robots.txt do host libera as consultas? Fonte nova, mesma régua de sempre.

    Host sem robots.txt é permissão por omissão — a norma trata ausência como
    "sem restrição". Erro de rede, não: aí não se sabe, e não saber é motivo
    para não baixar.
    """
    caminho = urlparse(BASE).path
    try:
        texto = buscar(ROBOTS)
    except Exception as erro:
        texto = None
        motivo = str(erro)
    else:
        motivo = None
    if texto is None:
        # 404 vem como exceção do `baixar`; é o caso comum e significa liberado.
        if motivo and ("404" in motivo or "Not Found" in motivo):
            return True
        print(f"não deu para ler {ROBOTS}: {motivo}", file=sys.stderr)
        return False
    return robots_permite(texto, caminho)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que baixaria, sem baixar")
    args = ap.parse_args()

    if args.seco:
        for c in CAMADAS:
            print(f"{c['arquivo']}\n  {c['descricao']}")
            for camada in c["camadas"]:
                print(f"  {url_da_pagina(c['servico'], camada, 0)}")
        print(f"\nUser-Agent: {USER_AGENT}")
        return 0

    if not permitido():
        print("\nRECUSADO: o robots.txt de arcgis.itajai.sc.gov.br não libera "
              "estas consultas, ou não deu para lê-lo. Fonte nova só entra com "
              "o robots conferido — foi por isso que o AlertaBlu ficou de fora.",
              file=sys.stderr)
        return 2

    for c in CAMADAS:
        colecoes = []
        total = 0
        for camada in c["camadas"]:
            try:
                feicoes = baixar_camada(c["servico"], camada)
            except Exception as erro:
                # Parar na primeira camada que falha, em vez de gravar o
                # arquivo pela metade: meio acervo com cara de acervo inteiro é
                # o tipo de coisa que ninguém confere depois.
                print(f"{c['servico']}/{camada}: {erro}", file=sys.stderr)
                return 1
            total += len(feicoes)
            colecoes.append({"camada": camada, "feicoes": feicoes})
            print(f"  {c['servico']}/{camada}: {len(feicoes)} feições")
        if total == 0:
            print(f"{c['arquivo']}: nenhuma feição — não gravo arquivo vazio",
                  file=sys.stderr)
            return 1
        (DADOS / "brutos" / c["arquivo"]).write_text(
            json.dumps({"_meta": {"descricao": c["descricao"],
                                  "origem": f"{BASE}/{c['servico']}",
                                  "total": total}, "camadas": colecoes},
                       ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{c['arquivo']}: {total} feições gravadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
