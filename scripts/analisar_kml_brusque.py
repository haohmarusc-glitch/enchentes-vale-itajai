#!/usr/bin/env python3
"""
Decide se o KML de cotas de Brusque pode ser importado — e conclui que não pode.

O arquivo `data/brutos/brusque-mymaps-cotas.json` traz 3.688 pontos do Google My
Maps da Defesa Civil de Brusque. Só a pasta "Cotas de Cheia 2011" tem números:
1.679 pontos com um campo chamado `cota`. Um conversor que veio junto com os
dados grava esses 1.679 pontos com `referencia: "régua"` e `confianca: "alta"`.
Este script existe para testar essa afirmação antes de qualquer importação, e o
resultado é que ela não se sustenta.

O que a análise mostra, sobre o próprio arquivo:

1. **A pasta se contradiz.** Ela se chama "Cotas de Cheia 2011" e o pico de 2011
   em Brusque foi de 10,03 m na régua (`confianca: alta`). Mesmo assim 64% dos
   pontos trazem valor ACIMA de 10,03 m, e 55% acima do maior pico já registrado
   na cidade, 10,50 m. O maior valor do arquivo é 29,53 m — quase três vezes o
   recorde histórico.

2. **Parte do arquivo É régua.** Das 13 ruas que também estão no nosso cadastro
   (lista da Defesa Civil de Brusque, out/2023), 4 batem no centavo — e sempre no
   menor valor daquela rua no KML. Um teste de embaralhamento diz que 4 acertos
   exatos sairiam por acaso com probabilidade 0,0001. Não é coincidência: há
   cotas de régua verdadeiras aqui dentro.

3. **O resto não é a mesma grandeza, nem a mesma com deslocamento.** As outras 9
   ruas em comum ficam de 0,5 m a 2,3 m acima do nosso valor, sem offset
   constante — então não é uma referência única deslocada, como o caso
   régua/IBGE de Blumenau. E a mediana sobe com a distância do rio (10,16 m perto,
   12,43 m a 4–8 km), que é o comportamento de altitude do terreno.

Ou seja: o arquivo é uma MISTURA, e não há campo que diga, ponto a ponto, qual é
qual. Importar dá uma de duas coisas para quem procurar a própria rua: a cota
certa, ou um número que pode errar por até 19 m. É a mesma armadilha do
`Relevo_Ponto_Cotado_Altimetrico` de Itajaí, já registrada em
`docs/cotas-de-ruas.md`: um campo chamado `cota` que é altura do terreno, não
nível de régua.

O que resolveria: o KML original, com os campos `obs`, `esquina` e as
coordenadas UTM que a conversão perdeu, ou a planilha da Defesa Civil de Brusque
pedida diretamente. Enquanto não vier, Brusque fica com os 27 pontos que já tem.

Uso:
    python3 scripts/analisar_kml_brusque.py
"""

import json
import math
import random
import statistics
import sys
import unicodedata
from typing import Any

from comum import DADOS

CIDADE = "brusque"
PASTA_COM_COTA = "Cotas de Cheia 2011"
ANO_DA_PASTA = "2011"
BRUTO = "brutos/brusque-mymaps-cotas.json"

# Régua da Ponte Estaiada, aproximada, só para medir distância relativa.
# Não entra em nenhum número publicado — serve para ordenar os pontos.
REGUA_LON, REGUA_LAT = -48.9175, -27.0975

TOLERANCIA_M = 0.005  # dois valores "iguais" ao centavo


def normalizar(texto: Any) -> str:
    """Nome de rua comparável: sem acento, sem prefixo, sem pontuação dupla."""
    sem_acento = unicodedata.normalize("NFD", str(texto or ""))
    sem_acento = sem_acento.encode("ascii", "ignore").decode().upper()
    for prefixo in ("RUA ", "AV. ", "AV ", "AVENIDA ", "R. ", "TRAVESSA ", "RODOVIA ", "ESTRADA "):
        if sem_acento.startswith(prefixo):
            sem_acento = sem_acento[len(prefixo):]
            break
    return " ".join(sem_acento.replace(".", " ").split())


def e_numero(valor: Any) -> bool:
    """Número de verdade. `isinstance(True, int)` é True em Python, e True não é cota."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def carregar_bruto(caminho=None) -> list[dict[str, Any]]:
    caminho = caminho or (DADOS / BRUTO)
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)["pontos"]


def com_cota(pontos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [p for p in pontos if e_numero(p.get("cota"))]


def censo_por_pasta(pontos: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Quantos pontos e que faixa de valor cada pasta do KML tem."""
    censo: dict[str, dict[str, Any]] = {}
    for ponto in pontos:
        pasta = ponto.get("pasta") or "(sem pasta)"
        linha = censo.setdefault(pasta, {"total": 0, "com_cota": 0, "valores": []})
        linha["total"] += 1
        if e_numero(ponto.get("cota")):
            linha["com_cota"] += 1
            linha["valores"].append(ponto["cota"])
    for linha in censo.values():
        valores = linha.pop("valores")
        linha["min"] = min(valores) if valores else None
        linha["mediana"] = statistics.median(valores) if valores else None
        linha["max"] = max(valores) if valores else None
    return censo


def pico_da_cidade(eventos: list[dict[str, Any]], cidade: str, ano: str | None = None) -> float | None:
    """Maior pico registrado na cidade — no ano dado, ou em toda a série."""
    picos = [
        e["pico_m"]
        for e in eventos
        if e.get("cidade") == cidade
        and e_numero(e.get("pico_m"))
        and (ano is None or str(e.get("data", "")).startswith(ano))
    ]
    return max(picos) if picos else None


def acima_de(pontos: list[dict[str, Any]], limite: float) -> tuple[int, int]:
    """Quantos pontos passam do limite, e de quantos."""
    valores = [p["cota"] for p in com_cota(pontos)]
    return sum(1 for v in valores if v > limite), len(valores)


def cruzar_com_cadastro(
    pontos: list[dict[str, Any]], cadastro: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Para cada rua nossa que também está no KML: o nosso valor e os de lá."""
    por_rua: dict[str, list[float]] = {}
    for ponto in com_cota(pontos):
        por_rua.setdefault(normalizar(ponto.get("rua")), []).append(ponto["cota"])

    comuns = []
    for registro in cadastro:
        if not e_numero(registro.get("cota_m")):
            continue
        chave = normalizar(registro.get("rua"))
        if chave not in por_rua:
            continue
        valores = sorted(por_rua[chave])
        comuns.append(
            {
                "rua": registro.get("rua"),
                "nosso_m": registro["cota_m"],
                "kml_m": valores,
                "bate": any(abs(registro["cota_m"] - v) < TOLERANCIA_M for v in valores),
                "bate_no_menor": abs(registro["cota_m"] - valores[0]) < TOLERANCIA_M,
            }
        )
    return comuns


def probabilidade_por_acaso(
    comuns: list[dict[str, Any]],
    cotas_nossas: list[float],
    rodadas: int = 20000,
    semente: int = 7,
) -> float:
    """
    P(sair tanto acerto exato quanto o observado, se os valores não tivessem relação).

    Embaralha quais cotas nossas caem em quais ruas e reconta. Sem isso, quatro
    acertos em treze ruas seria só uma impressão.
    """
    observado = sum(1 for c in comuns if c["bate"])
    if not comuns or len(cotas_nossas) < len(comuns):
        return float("nan")
    sorteio = random.Random(semente)
    tao_bons = 0
    for _ in range(rodadas):
        embaralhado = sorteio.sample(cotas_nossas, len(comuns))
        acertos = sum(
            1
            for cota, caso in zip(embaralhado, comuns)
            if any(abs(cota - v) < TOLERANCIA_M for v in caso["kml_m"])
        )
        tao_bons += acertos >= observado
    return tao_bons / rodadas


def _km(lon: float, lat: float) -> float:
    return math.hypot((lon - REGUA_LON) * 101.0, (lat - REGUA_LAT) * 110.6)


def cota_por_distancia(pontos: list[dict[str, Any]]) -> list[tuple[str, int, float]]:
    """Mediana da cota por faixa de distância da régua. Altitude sobe; cota de régua também."""
    pares = []
    for ponto in com_cota(pontos):
        partes = str(ponto.get("coord") or "").split(",")
        if len(partes) < 2:
            continue
        try:
            pares.append((_km(float(partes[0]), float(partes[1])), ponto["cota"]))
        except ValueError:
            continue
    faixas = [("0–1 km", 0, 1), ("1–2 km", 1, 2), ("2–4 km", 2, 4), ("4–8 km", 4, 8), ("8+ km", 8, 1e9)]
    saida = []
    for rotulo, menor, maior in faixas:
        sel = [cota for dist, cota in pares if menor <= dist < maior]
        if sel:
            saida.append((rotulo, len(sel), statistics.median(sel)))
    return saida


def importavel(fracao_acima_do_pico: float, acertos: int, total_comum: int) -> bool:
    """
    O arquivo só seria importável se as duas coisas fossem verdade ao mesmo tempo:
    quase nenhum ponto acima do pico do ano que dá nome à pasta, e as ruas em
    comum batendo com o cadastro. Hoje nenhuma das duas é.
    """
    quase_nenhum_acima = fracao_acima_do_pico <= 0.05
    cadastro_confirma = total_comum > 0 and acertos == total_comum
    return quase_nenhum_acima and cadastro_confirma


def main() -> int:
    try:
        pontos = carregar_bruto()
    except (OSError, ValueError, KeyError) as erro:
        print(f"não deu para ler {BRUTO}: {erro}", file=sys.stderr)
        return 1

    eventos = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))["eventos"]
    cadastro = [
        r
        for r in json.loads((DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
        if r.get("cidade") == CIDADE
    ]

    print(f"{len(pontos)} pontos no KML\n")
    print(f"{'pasta':28} {'total':>6} {'c/ cota':>8} {'min':>7} {'mediana':>8} {'max':>7}")
    for pasta, linha in sorted(censo_por_pasta(pontos).items(), key=lambda i: -i[1]["total"]):
        faixa = (
            f"{linha['min']:7.2f} {linha['mediana']:8.2f} {linha['max']:7.2f}"
            if linha["com_cota"]
            else f"{'—':>7} {'—':>8} {'—':>7}"
        )
        print(f"{pasta[:28]:28} {linha['total']:6} {linha['com_cota']:8} {faixa}")

    numerados = [p for p in pontos if p.get("pasta") == PASTA_COM_COTA]
    pico_ano = pico_da_cidade(eventos, CIDADE, ANO_DA_PASTA)
    pico_serie = pico_da_cidade(eventos, CIDADE)

    print(f"\n1) A pasta {PASTA_COM_COTA!r} se contradiz")
    fracao = 0.0
    for rotulo, limite in ((f"pico de {ANO_DA_PASTA}", pico_ano), ("maior pico da série", pico_serie)):
        if limite is None:
            continue
        acima, total = acima_de(numerados, limite)
        print(f"   acima do {rotulo} ({limite:.2f} m): {acima} de {total} = {100 * acima / total:.1f}%")
        if rotulo.startswith("pico de"):
            fracao = acima / total
    valores = [p["cota"] for p in com_cota(numerados)]
    print(f"   maior valor do arquivo: {max(valores):.2f} m")

    comuns = cruzar_com_cadastro(numerados, cadastro)
    acertos = sum(1 for c in comuns if c["bate"])
    no_menor = sum(1 for c in comuns if c["bate_no_menor"])
    print(f"\n2) Parte do arquivo é régua: {acertos} de {len(comuns)} ruas em comum batem no centavo")
    for caso in comuns:
        if caso["bate"]:
            print(f"   {caso['rua'][:32]:34} nosso={caso['nosso_m']:5.2f}  kml={caso['kml_m']}")
    print(f"   desses, {no_menor} batem no MENOR valor daquela rua no KML")
    nossas = [r["cota_m"] for r in cadastro if e_numero(r.get("cota_m"))]
    print(f"   P(tantos acertos por acaso) = {probabilidade_por_acaso(comuns, nossas):.4f}")

    print("\n3) O resto não é a mesma grandeza")
    for caso in comuns:
        if not caso["bate"]:
            print(
                f"   {caso['rua'][:32]:34} nosso={caso['nosso_m']:5.2f}  "
                f"kml={caso['kml_m'][0]:5.2f}..{caso['kml_m'][-1]:5.2f}"
            )
    for rotulo, quantos, mediana in cota_por_distancia(numerados):
        print(f"   {rotulo:8} n={quantos:5}  mediana={mediana:6.2f} m")

    print()
    if importavel(fracao, acertos, len(comuns)):
        print("VEREDITO MUDOU: os dois testes passaram. Reabrir a decisão antes de importar.")
        return 2
    print(
        "VEREDITO: não importar. O arquivo mistura cotas de régua verdadeiras com valores\n"
        "de outra grandeza, e nenhum campo separa uns dos outros. Brusque fica com os\n"
        f"{len(cadastro)} pontos que já tem. Pedir o KML original ou a planilha à Defesa Civil."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
