#!/usr/bin/env python3
"""
Decide em que referência está a série histórica de Blumenau, cruzando a tabela
oficial do AlertaBlu com a nossa.

O problema, em uma frase: 113 registros de Blumenau em `enchentes.json`, 72
rotulados `IBGE (régua + 0,20 m)` e 41 sem rótulo, e a `REGRA_REFERENCIA_BLUMENAU`
proibindo qualquer conversão até se saber qual é qual. A tabela do AlertaBlu —
102 enchentes de 1852 a 2024, publicada pela **própria Defesa Civil** — é a
terceira leitura que faltava para responder.

Este script **não converte nada**. Ele mede o deslocamento e diz qual dos quatro
casos é, para a decisão ser tomada sobre número e não sobre impressão.

OS QUATRO CASOS
---------------
1. **AlertaBlu ≈ nosso rótulo IBGE.** A série da Defesa Civil já está em IBGE, e
   é o site que precisa subtrair 0,20 m para exibir na régua.
2. **AlertaBlu ≈ nosso − 0,20.** O AlertaBlu está na régua e é a tabela do
   Cordero que soma. Aí o rótulo dos 72 está certo e os 41 sem rótulo herdam
   a régua.
3. **O deslocamento MUDA com a época.** Os eventos antigos batem de um jeito e os
   recentes de outro. Isso não é diferença de referência, é mudança de prática ou
   de instrumento no meio da série — e nesse caso não existe um número para
   somar ou subtrair. **Não converter.**
4. **Irregular.** Nem constante nem separável por época: há uma terceira
   referência no meio, e a pergunta vai para a FURB.

O caso 3 é o que os indícios apontam e é o que uma média sozinha esconderia: em
set/2011 o CEOPS registrou 13,00 m e o AlertaBlu publica 12,60 m — 0,40 m, não
0,20 m —, enquanto 1880, 1983 e 1984 batem ao centavo com o rótulo IBGE. Por isso
o script separa os pares **rotulados** dos **sem rótulo** e compara os dois
grupos, em vez de tirar uma mediana só.

O ARQUIVO
---------
`data/brutos/blumenau-enchentes-registradas-alertablu.json`, da página
`/p/enchentes` do AlertaBlu. Ele **ainda não chegou ao repositório** — quando
chegar, este script roda sozinho.

Uso:
    python3 scripts/conferir_blumenau_alertablu.py
"""

import json
import re
import statistics
import sys
from typing import Any

from comum import DADOS

CIDADE = "blumenau"
BRUTO = "brutos/blumenau-enchentes-registradas-alertablu.json"
ROTULO_IBGE = "IBGE (régua + 0,20 m)"

#: Dois valores "iguais" ao centavo.
TOLERANCIA_M = 0.005

#: O deslocamento que separa as duas referências conhecidas.
DESLOCAMENTO_IBGE_M = 0.20

#: Quantos pares o grupo precisa ter para a sua mediana valer alguma coisa.
#: Abaixo disto, um evento atípico manda na resposta.
MINIMO_POR_GRUPO = 8

#: Que fração dos pares do grupo precisa cair perto da mediana para o
#: deslocamento ser chamado de constante. Um deslocamento de datum é constante
#: por definição; se metade dos pares foge dele, não é datum.
FRACAO_CONSTANTE = 0.80

RE_DATA = re.compile(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?")


def numero(valor: Any) -> float | None:
    """`12,60`, `12.60` e `12.6` viram float. O resto vira None."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return float(valor)
    if valor is None:
        return None
    texto = str(valor).strip().replace(",", ".")
    texto = re.sub(r"[^\d.\-]", "", texto)
    try:
        return float(texto)
    except ValueError:
        return None


def chave_de_data(valor: Any) -> tuple[str, str | None, str | None] | None:
    """(ano, mês, dia) do que a fonte escrever. Mês e dia podem faltar."""
    achado = RE_DATA.search(str(valor or ""))
    if not achado:
        return None
    return achado.group(1), achado.group(2), achado.group(3)


def eventos_do_alertablu(dados: Any) -> list[dict]:
    """
    A lista de eventos, seja qual for o invólucro que a página deu ao JSON.

    Aceita lista solta ou objeto com `enchentes`/`eventos`/`registros`; de cada
    item tira a data e a cota pelos nomes de campo mais prováveis. É tolerante
    de propósito: o arquivo ainda não chegou e o formato exato não se sabe.
    """
    itens = dados
    if isinstance(dados, dict):
        for nome in ("enchentes", "eventos", "registros", "dados", "itens"):
            if isinstance(dados.get(nome), list):
                itens = dados[nome]
                break
    if not isinstance(itens, list):
        return []

    saida = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        data = next((item[c] for c in ("data", "date", "dia", "ano", "year")
                     if item.get(c) not in (None, "")), None)
        cota = next((item[c] for c in ("cota", "cota_m", "nivel", "nivel_m", "pico",
                                       "pico_m", "valor") if item.get(c) not in (None, "")),
                    None)
        quando, quanto = chave_de_data(data), numero(cota)
        if quando and quanto is not None:
            saida.append({"data": data, "ano": quando[0], "mes": quando[1],
                          "dia": quando[2], "cota_m": quanto})
    return saida


def nossos_eventos() -> list[dict]:
    eventos = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
    saida = []
    for e in eventos:
        if e.get("cidade") != CIDADE or numero(e.get("pico_m")) is None:
            continue
        quando = chave_de_data(e.get("data"))
        if quando:
            saida.append({"data": e.get("data"), "ano": quando[0], "mes": quando[1],
                          "dia": quando[2], "pico_m": float(e["pico_m"]),
                          "referencia": e.get("referencia")})
    return saida


def parear(deles: list[dict], nossos: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Um par por evento que as duas fontes descrevem. Devolve (pares, ambíguos).

    A data casa pelo que as duas trazem: dia com dia, mês com mês, ano com ano.
    **Ano solto só casa quando aquele ano tem um evento só do nosso lado** — 1928
    tem cinco e 1973 tem seis; casar pelo ano ali seria sortear qual, e um par
    sorteado envenena a mediana inteira.
    """
    por_ano: dict[str, list[dict]] = {}
    for n in nossos:
        por_ano.setdefault(n["ano"], []).append(n)

    pares, ambiguos = [], []
    for d in deles:
        candidatos = por_ano.get(d["ano"], [])
        if not candidatos:
            continue
        if d["mes"]:
            candidatos = [c for c in candidatos if c["mes"] == d["mes"]] or candidatos
        if d["dia"]:
            exatos = [c for c in candidatos if c["dia"] == d["dia"]]
            if exatos:
                candidatos = exatos
        if len(candidatos) != 1:
            ambiguos.append(f"{d['data']}: {len(candidatos)} eventos nossos no mesmo período")
            continue
        nosso = candidatos[0]
        pares.append({
            "data": nosso["data"],
            "ano": int(nosso["ano"]),
            "nosso_m": nosso["pico_m"],
            "deles_m": d["cota_m"],
            "diferenca": round(d["cota_m"] - nosso["pico_m"], 3),
            "rotulado_ibge": nosso["referencia"] == ROTULO_IBGE,
        })
    return pares, ambiguos


def resumo(pares: list[dict]) -> dict[str, Any]:
    """Mediana, dispersão e quanto do grupo cabe perto da mediana."""
    if not pares:
        return {"n": 0, "mediana": None, "constante": False}
    difs = [p["diferenca"] for p in pares]
    mediana = statistics.median(difs)
    perto = sum(1 for d in difs if abs(d - mediana) <= TOLERANCIA_M)
    return {
        "n": len(difs),
        "mediana": round(mediana, 3),
        "min": min(difs),
        "max": max(difs),
        "fracao_perto": perto / len(difs),
        "constante": perto / len(difs) >= FRACAO_CONSTANTE,
    }


def veredito(pares: list[dict]) -> tuple[str, str]:
    """
    Qual dos quatro casos é. Devolve (chave, explicação).

    Compara os pares **rotulados IBGE** com os **sem rótulo** em vez de tirar uma
    mediana só, porque é exatamente aí que o caso 3 se esconde: uma mediana
    única sobre grupos que se comportam diferente devolve um número que não
    descreve nenhum dos dois.
    """
    rotulados = [p for p in pares if p["rotulado_ibge"]]
    sem_rotulo = [p for p in pares if not p["rotulado_ibge"]]
    a, b = resumo(rotulados), resumo(sem_rotulo)

    if a["n"] < MINIMO_POR_GRUPO:
        return "indeciso", (f"só {a['n']} pares com registro rotulado IBGE; "
                            f"são precisos {MINIMO_POR_GRUPO} para a mediana valer")
    if not a["constante"]:
        return "irregular", (f"nos rotulados o deslocamento vai de {a['min']:+.2f} a "
                             f"{a['max']:+.2f} m e só {a['fracao_perto']:.0%} ficam na "
                             "mediana — não é deslocamento de referência")

    # Os dois grupos discordam? Então não há um número para somar em toda a série.
    if b["n"] >= MINIMO_POR_GRUPO and b["constante"] and \
            abs(a["mediana"] - b["mediana"]) > TOLERANCIA_M:
        return "muda_com_a_epoca", (
            f"os rotulados deslocam {a['mediana']:+.2f} m e os sem rótulo "
            f"{b['mediana']:+.2f} m. Não é diferença de referência: é mudança no meio "
            "da série. NÃO converter — nenhum número serve para os dois trechos")

    if abs(a["mediana"]) <= TOLERANCIA_M:
        return "alertablu_em_ibge", (
            f"o AlertaBlu bate com o rótulo IBGE ({a['mediana']:+.2f} m em {a['n']} "
            "pares). A série da Defesa Civil já está em IBGE, e é a tela que precisa "
            f"subtrair {DESLOCAMENTO_IBGE_M:.2f} m para exibir na régua")
    if abs(a["mediana"] + DESLOCAMENTO_IBGE_M) <= TOLERANCIA_M:
        return "alertablu_em_regua", (
            f"o AlertaBlu fica {a['mediana']:+.2f} m abaixo do rótulo IBGE em {a['n']} "
            "pares: ele está na RÉGUA e a tabela do Cordero é que soma os 0,20 m")
    return "terceira_referencia", (
        f"deslocamento constante de {a['mediana']:+.2f} m, que não é 0,00 nem "
        f"-{DESLOCAMENTO_IBGE_M:.2f}. Há uma terceira referência — perguntar à FURB "
        "antes de converter qualquer coisa")


def main() -> int:
    caminho = DADOS / BRUTO
    if not caminho.exists():
        print(f"{caminho} não está aqui.\n\n"
              "A tabela vem da página /p/enchentes do AlertaBlu (102 enchentes,\n"
              "1852–2024). Sem ela esta conferência não roda — e é ela que decide\n"
              "a referência da série de Blumenau.", file=sys.stderr)
        return 1

    deles = eventos_do_alertablu(json.loads(caminho.read_text(encoding="utf-8")))
    nossos = nossos_eventos()
    pares, ambiguos = parear(deles, nossos)
    rotulados = [p for p in pares if p["rotulado_ibge"]]

    print(f"AlertaBlu: {len(deles)} eventos · nosso: {len(nossos)} · pares: {len(pares)} "
          f"({len(rotulados)} com registro rotulado IBGE)")
    for a in ambiguos[:5]:
        print(f"  sem par — {a}")

    for titulo, grupo in (("rotulados IBGE", rotulados),
                          ("sem rótulo", [p for p in pares if not p["rotulado_ibge"]])):
        r = resumo(grupo)
        if r["n"]:
            print(f"\n{titulo}: {r['n']} pares · mediana {r['mediana']:+.2f} m · "
                  f"de {r['min']:+.2f} a {r['max']:+.2f} · "
                  f"{r['fracao_perto']:.0%} na mediana")

    fora = sorted((p for p in pares if abs(p["diferenca"]) > TOLERANCIA_M),
                  key=lambda p: -abs(p["diferenca"]))[:8]
    if fora:
        print("\nmaiores diferenças:")
        for p in fora:
            print(f"  {p['data']}: nosso {p['nosso_m']:.2f} · AlertaBlu "
                  f"{p['deles_m']:.2f} · {p['diferenca']:+.2f} m"
                  + ("  [rotulado IBGE]" if p["rotulado_ibge"] else ""))

    chave, porque = veredito(pares)
    print(f"\nVEREDITO: {chave}\n  {porque}")
    return 0 if chave in ("alertablu_em_ibge", "alertablu_em_regua") else 2


if __name__ == "__main__":
    raise SystemExit(main())
