#!/usr/bin/env python3
"""
Importa as 554 cotas por rua de Rio do Sul, publicadas pela Defesa Civil.

De onde vem: o portal `defesacivil.riodosul.sc.gov.br` publica "Cota de Cheias
por Rua", e a tabela inteira viaja DENTRO do pacote JavaScript da aplicação —
cada rua com `min` e `max`. Não é raspagem de tela nem endpoint interno: é o
dado que o portal serve a quem abre a página, lido de onde ele já vem.

Por que importa: `cotas-ruas.json` tinha 57 pontos de três cidades. Rio do Sul
sozinha traz dez vezes isso, e é a cidade mais a montante com gente e cheia
frequente — quem mora lá pergunta "a minha rua" e hoje ouve "não tenho".

**O que os números são, e o que não são.** São NÍVEL DO RIO na régua de Rio do
Sul: `min` é o nível em que a rua começa a alagar; `max`, o nível em que ela
alaga inteira. Não são altitude do terreno — a cidade está a cerca de 340 m
acima do mar, e a tabela vai de 8 a 20 m. Essa checagem não é preciosismo:
Itajaí publica um serviço chamado `Relevo_Ponto_Cotado_Altimetrico`, com um
campo `cota` em metros, que é altura do solo. Os dois números se parecem e
significam coisas opostas.

Regras que este script cumpre:

* **robots.txt primeiro.** O AlertaBlu foi recusado por isso; a mesma régua
  vale aqui. Se o robots proibir o caminho, o script para e não importa nada.
* **União, nunca substituição.** Registro de outra cidade não é tocado, e
  registro de Rio do Sul que já exista é atualizado no lugar, pela identidade
  (cidade, rua, ponto).
* **Idempotente.** Rodar duas vezes dá o mesmo arquivo.
* **Faixa plausível.** Valor fora de 0 a 25 m não entra: não é nível de rio
  desta bacia. O que for recusado aparece na tela, com o motivo.

Uso na VPS (daqui do sandbox o portal não responde):
    python3 scripts/importar_cotas_rio_do_sul.py --seco     # mostra e não grava
    python3 scripts/importar_cotas_rio_do_sul.py            # grava
"""

import argparse
import json
import re
import sys
from datetime import date
from urllib.parse import urlparse

from comum import DADOS

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"

PORTAL = "https://defesacivil.riodosul.sc.gov.br/"
TABELA = PORTAL + "index.php?r=soscota-rua%2Ftabela"
ROBOTS = PORTAL + "robots.txt"

CIDADE = "rio-do-sul"
RIO = "itajai-acu"
ARQUIVO = DADOS / "cotas-ruas.json"

#: Nenhuma régua desta bacia chega perto disso; acima é outra grandeza.
COTA_MAXIMA_M = 25.0

#: A fonte usa 20 como topo da escala: "acima disto, não medido". Guardar 20
#: como se fosse a cota em que a rua alaga inteira seria inventar precisão.
TETO_DA_FONTE = 20.0

RE_SCRIPT = re.compile(r"""<script[^>]+src\s*=\s*['"]([^'"]+)['"]""", re.I)
RE_REGISTRO = re.compile(
    r"""\{[^{}]{0,200}?['"`]?name['"`]?\s*:\s*['"`]([^'"`]{1,90})['"`][^{}]{0,200}?\}""")
RE_MIN = re.compile(r"""['"`]?min['"`]?\s*:\s*(-?\d+(?:\.\d+)?)""")
RE_MAX = re.compile(r"""['"`]?max['"`]?\s*:\s*(-?\d+(?:\.\d+)?)""")


def robots_permite(texto: str, caminho: str) -> bool:
    """
    Lê o robots.txt como robô educado: só as regras do agente `*`.

    Sem `Disallow` que case com o caminho, pode. Um `Disallow:` vazio é
    permissão explícita, e é assim que a norma define.
    """
    atual, proibidos = None, []
    for linha in texto.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if not linha or ":" not in linha:
            continue
        chave, valor = (p.strip() for p in linha.split(":", 1))
        chave = chave.lower()
        if chave == "user-agent":
            atual = valor
        elif chave == "disallow" and atual == "*":
            if valor:
                proibidos.append(valor)
    return not any(caminho.startswith(p) for p in proibidos)


def extrair(js: str) -> tuple[list[dict], list[str]]:
    """
    As ruas dentro do pacote, e o que foi recusado.

    Devolve `(ruas, recusas)`. Objeto sem `min` numérico não é rua: é item de
    menu, estação, qualquer outra coisa com um campo `name`. Some em silêncio,
    porque são centenas e nenhum deles é perda.
    """
    ruas, recusas, vistos = [], [], set()
    for m in RE_REGISTRO.finditer(js):
        bloco, nome = m.group(0), m.group(1).strip()
        achou_min = RE_MIN.search(bloco)
        if not achou_min or not nome:
            continue
        minimo = float(achou_min.group(1))
        achou_max = RE_MAX.search(bloco)
        maximo = float(achou_max.group(1)) if achou_max else None

        if not 0 < minimo < COTA_MAXIMA_M:
            recusas.append(f"{nome}: mínima {minimo} fora da faixa de nível de rio")
            continue
        if maximo is not None and not 0 < maximo <= COTA_MAXIMA_M:
            recusas.append(f"{nome}: máxima {maximo} fora da faixa — guardada só a mínima")
            maximo = None
        if maximo is not None and maximo < minimo:
            recusas.append(f"{nome}: máxima {maximo} abaixo da mínima {minimo} — guardada só a mínima")
            maximo = None

        chave = nome.upper()
        if chave in vistos:
            recusas.append(f"{nome}: repetido no pacote, mantido o primeiro")
            continue
        vistos.add(chave)
        ruas.append({"rua": nome, "min": minimo, "max": maximo})
    return ruas, recusas


def cota_de_inundacao_da_cidade() -> float | None:
    """A cota mais baixa que a cidade cadastra — o piso do que é cheia lá."""
    estacoes = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    for c in estacoes["rios"].get(RIO, {}).get("cidades", []):
        if c["id"] == CIDADE:
            valores = [v for v in (c.get("cotas_m") or {}).values()
                       if isinstance(v, (int, float))]
            return min(valores) if valores else None
    return None


def como_registro(rua: dict, fonte: str, quando: str,
                  piso_da_cidade: float | None = None) -> dict:
    """
    Um registro no formato de `cotas-ruas.json`.

    `cota_m` recebe a MÍNIMA — o nível em que a água chega à rua. É o número
    que serve para avisar; a máxima diz quando a rua está inteira embaixo
    d'água, e vai em `cota_max_m`, sem substituir a outra.

    Duas coisas viram NOTA em vez de número, porque número que não se sustenta
    é pior que número ausente:

    * o teto da escala da fonte (20 m), que quer dizer "acima disto não foi
      medido" e não "a rua alaga inteira aqui";
    * cota abaixo da menor cota que a própria cidade cadastra. Rio do Sul
      publica ruas alagando a 3,11 m, e a régua marca 3,35 m num dia seco: sem
      a ressalva, o bot diria "este nível já foi alcançado" com tempo bom, que
      é o alarme falso que ensina a ignorar o aviso de verdade. O dado entra —
      é oficial e publicado —, mas entra dizendo que precisa de conferência.
    """
    registro = {
        "cidade": CIDADE,
        "rio": RIO,
        "rua": rua["rua"],
        "bairro": None,
        "ponto": "ponto mais baixo (mínima publicada pela fonte)",
        "cota_m": rua["min"],
        "fonte": fonte,
        "data_fonte": quando,
        "confianca": "alta",
        "referencia": "régua",
    }

    notas = []
    if rua["max"] is not None and rua["max"] < TETO_DA_FONTE:
        registro["cota_max_m"] = rua["max"]
    elif rua["max"] is not None:
        notas.append(f"A fonte publica máxima {rua['max']:.2f} m, que é o teto da escala "
                     "dela — não a cota em que a rua alaga inteira.")

    if piso_da_cidade is not None and rua["min"] < piso_da_cidade:
        notas.append(f"Esta cota ({rua['min']:.2f} m) fica ABAIXO da menor cota de "
                     f"referência de Rio do Sul ({piso_da_cidade:.2f} m): a rua alagaria "
                     "com o rio em nível quase normal. Vem assim da fonte e ainda não foi "
                     "conferida com a Defesa Civil — não use como aviso sozinha.")

    if notas:
        registro["nota"] = " ".join(notas)
    return registro


def mesclar(existentes: list[dict], novos: list[dict]) -> tuple[list[dict], int, int]:
    """
    União pela identidade (cidade, rua, ponto). Cidade nenhuma perde registro.
    """
    def chave(r: dict) -> tuple:
        return (r.get("cidade"), (r.get("rua") or "").upper(), r.get("ponto"))

    indice = {chave(r): i for i, r in enumerate(existentes)}
    saida = list(existentes)
    novos_n = atualizados = 0
    for r in novos:
        k = chave(r)
        if k in indice:
            saida[indice[k]] = r
            atualizados += 1
        else:
            saida.append(r)
            novos_n += 1
    return saida, novos_n, atualizados


def baixar_pacote() -> tuple[str, str]:
    """O pacote da aplicação, e a URL dele para registrar como fonte."""
    import requests

    cabecalhos = {"User-Agent": UA}
    caminho = urlparse(TABELA).path
    robots = requests.get(ROBOTS, headers=cabecalhos, timeout=30)
    if robots.status_code == 200 and not robots_permite(robots.text, caminho):
        raise SystemExit(f"robots.txt proíbe {caminho}. Nada importado — "
                         "esta tabela se pede à Defesa Civil.")

    pagina = requests.get(TABELA, headers=cabecalhos, timeout=30)
    pagina.raise_for_status()
    alvos = [s for s in RE_SCRIPT.findall(pagina.text) if "/assets/" in s]
    if not alvos:
        raise SystemExit("não achei o pacote da aplicação na página")
    url = alvos[0] if alvos[0].startswith("http") else PORTAL.rstrip("/") + alvos[0]
    js = requests.get(url, headers=cabecalhos, timeout=60)
    js.raise_for_status()
    return js.text, url


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem gravar")
    ap.add_argument("--de-arquivo", help="lê o pacote de um arquivo local, em vez da rede")
    args = ap.parse_args()

    if args.de_arquivo:
        js = open(args.de_arquivo, encoding="utf-8").read()
        url = f"arquivo local: {args.de_arquivo}"
    else:
        js, url = baixar_pacote()

    ruas, recusas = extrair(js)
    print(f"{len(ruas)} rua(s) com cota no pacote.")
    for r in ruas[:5]:
        print(f"  {r['rua']}: mínima {r['min']:.2f} m · máxima "
              f"{r['max'] if r['max'] is not None else '—'}")
    if recusas:
        print(f"\n{len(recusas)} recusa(s):")
        for m in recusas[:20]:
            print(f"  {m}")

    if not ruas:
        print("\nNada a importar.")
        return 1

    menor = min(r["min"] for r in ruas)
    maior = max(r["min"] for r in ruas)
    print(f"\nfaixa das mínimas: {menor:.2f} m a {maior:.2f} m")
    # Mínima abaixo da menor cota da cidade seria rua alagando antes de o rio
    # dar sinal de cheia — possível, mas é o tipo de coisa que se confere antes
    # de virar aviso.
    piso = cota_de_inundacao_da_cidade()
    abaixo = [r for r in ruas if piso is not None and r["min"] < piso]
    if abaixo:
        print(f"ATENÇÃO: {len(abaixo)} rua(s) com mínima abaixo da menor cota de "
              f"referência da cidade ({piso:.2f} m). Entram com nota de ressalva:")
        for r in abaixo[:10]:
            print(f"  {r['rua']}: {r['min']:.2f} m")

    fonte = (f"Defesa Civil de Rio do Sul — \"Cota de Cheias por Rua\", "
             f"{TABELA} (dado publicado em {url})")
    quando = date.today().isoformat()
    registros = [como_registro(r, fonte, quando, piso) for r in ruas]

    base = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    mesclados, novos, atualizados = mesclar(base.get("cotas", []), registros)
    print(f"\ncotas-ruas.json: {len(base.get('cotas', []))} → {len(mesclados)} "
          f"({novos} novo(s), {atualizados} atualizado(s))")

    if args.seco:
        print("\n--seco: nada gravado.")
        return 0

    base["cotas"] = mesclados
    ARQUIVO.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(f"gravado em {ARQUIVO}")
    print("Agora rode: python3 scripts/validar_dados.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
