#!/usr/bin/env python3
"""
Confere a relação de cotas de Blumenau contra o PDF oficial de 2014.

Os 1.938 pontos de Blumenau que estão em `cotas-ruas.json` entraram por
**imprensa** — a relação da Defesa Civil reproduzida pela NSC. Por isso estavam
em `confianca: media`: o número podia ter sido digitado errado no caminho entre
a prefeitura e a matéria, e não havia como saber.

Agora existe o documento da própria Secretaria Municipal de Defesa Civil,
"Cotas das ruas de Blumenau", 111 páginas, 2.034 registros
(`data/brutos/blumenau-cotas-2014.pdf`). Este script cruza os dois.

O QUE A CONFERÊNCIA RESPONDE
----------------------------
1. **Os números batem?** Se batessem em quase todos e divergissem em alguns, a
   relação da imprensa teria erro de transcrição e cada divergência seria uma
   rua com cota errada na tela.
2. **É a mesma referência?** Uma diferença sistemática de 0,20 m entre as duas
   listas seria a assinatura do caso régua/IBGE que o `CLAUDE.md` trata como
   regra bloqueante — e apareceria aqui como um deslocamento constante.

E o PDF traz uma coisa que a relação da imprensa não tem: **o abrigo de cada
rua**, com código. Saber que a rua alaga a 7,40 m diz para sair de casa; saber
que o abrigo é a Igreja Evangélica Livre diz para onde ir.

Uso:
    python3 scripts/conferir_blumenau_2014.py
"""

import json
import re
import statistics
import sys
import unicodedata
from typing import Any

from comum import DADOS

CIDADE = "blumenau"
BRUTO = "brutos/blumenau-cotas-2014.json"
DATA_FONTE = "2014-06"

#: Dois valores "iguais" ao centavo.
TOLERANCIA_M = 0.005

#: Abaixo disto o cruzamento não prova nada: pouca rua em comum é coincidência
#: barata. Com mais de mil pares, uma divergência já é notícia.
MINIMO_DE_PARES = 1000

#: "R", "Rua", "Av." — a fonte de 2014 abrevia e a nossa não. O importador de
#: Blumenau normaliza sem tirar o prefixo, porque lá os dois lados vêm da mesma
#: fonte; aqui os lados são fontes diferentes e o prefixo tem de sair.
RE_PREFIXO = re.compile(
    r"^(r|rua|av|avenida|al|alameda|tr|travessa|rod|rodovia|estr|estrada)\.?\s+")


def normalizar_rua(texto: Any) -> str:
    """
    Nome de rua comparável entre as duas fontes.

    CORRIGIDO em 06/09/2026: tirava UM prefixo. O PDF escreve "AL Alameda Rio
    Branco" e "R Praça Victor Konder" — abreviação E palavra —, então sobrava
    "alameda rio branco" de um lado e "rio branco" do outro, e 21 registros da
    imprensa "não existiam" no documento oficial. Pior: como não existiam, o
    importador os trouxe do PDF como pontos NOVOS, com o nome expandido em cima
    da palavra que já estava lá — "Alameda Alameda Adolfo Schmalz", 19 vezes,
    duplicando ponto por ponto o que a imprensa já tinha. Um bug de um prefixo
    virou nome errado na tela e cota em dobro na busca.

    Agora o prefixo sai quantas vezes aparecer, e uma palavra (ou par de
    palavras) repetida no início cai — "praca praca victor konder" e "via
    expressa via expressa paul fritz" são artefatos de importação, não nomes.
    """
    sem = "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower())
                  if unicodedata.category(c) != "Mn")
    sem = " ".join(sem.replace(".", " ").replace("º", "").replace("°", "").split())
    while True:
        menos = RE_PREFIXO.sub("", sem).strip()
        if menos == sem:
            break
        sem = menos
    palavras = sem.split()
    if len(palavras) >= 2 and palavras[0] == palavras[1]:
        palavras = palavras[1:]
    elif len(palavras) >= 4 and palavras[0:2] == palavras[2:4]:
        palavras = palavras[2:]
    return " ".join(palavras)


def normalizar_ponto(texto: Any) -> str:
    sem = "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower())
                  if unicodedata.category(c) != "Mn")
    return " ".join(sem.replace(".", " ").replace("º", "").split())


#: Redações que as duas fontes usam para o MESMO ponto. Cada par foi visto no
#: cruzamento de 06/09/2026, lado a lado, e a cota independente bateu em todos.
RE_PARENTESES = re.compile(r"\s*\([^)]*\)")
RE_SEPARADOR = re.compile(r"\s*[/\-]\s*")
RE_PROXIMO_AO_N = re.compile(r"\bproximo ao n (\d)")
RE_DA_RUA = re.compile(r"\bda rua\b")


def ponto_canonico(texto: Any) -> str:
    """
    O ponto em forma comparável ENTRE redações — a segunda chance do pareamento.

    A primeira chance é `normalizar_ponto`, texto igual. Esta reconhece o que a
    relação da imprensa e o PDF escrevem de jeitos diferentes para o mesmo
    lugar: "esquina com Rua X" e "Esquina - Rua X"; "próximo ao nº 169" e "Casa
    nº 169"; "ponto mais baixo" e "Ponto mais baixo da rua"; "início / ponto
    mais baixo" e "Início da rua - ponto mais baixo da rua"; e o parêntese que só
    o PDF tem, "(pega só uma casa)".

    O que ela NÃO faz é olhar a cota. A cota é comparada DEPOIS, sozinha: se um
    par canônico divergir, aparece como divergência e derruba a confirmação,
    como qualquer outro.
    """
    s = normalizar_ponto(texto)
    s = RE_PARENTESES.sub("", s)
    s = RE_SEPARADOR.sub(" ", s)
    s = s.replace("esquina com ", "esquina ")
    s = RE_PROXIMO_AO_N.sub(r"casa n \1", s)
    s = RE_DA_RUA.sub("", s)
    return " ".join(s.split())


def numero(texto: Any) -> float | None:
    if texto is None:
        return None
    try:
        return float(str(texto).strip().replace(",", "."))
    except ValueError:
        return None


def carregar_pdf(caminho=None) -> list[dict]:
    caminho = caminho or (DADOS / BRUTO)
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)["registros"]


def carregar_cadastro() -> list[dict]:
    dados = json.loads((DADOS / "cotas-ruas.json").read_text(encoding="utf-8"))
    return [c for c in dados["cotas"]
            if c.get("cidade") == CIDADE and c.get("data_fonte") != DATA_FONTE]


def indexar(registros: list[dict]) -> dict[tuple, list[float]]:
    """Do PDF: (rua, ponto) -> cotas."""
    indice: dict[tuple, list[float]] = {}
    for r in registros:
        cota = numero(r.get("cota_rotulo"))
        if cota is None:
            continue
        indice.setdefault(
            (normalizar_rua(r.get("rua")), normalizar_ponto(r.get("observacao"))), []
        ).append(cota)
    return indice


def parear(pdf: list[dict], cadastro: list[dict]) -> list[dict]:
    """
    Um par por registro nosso que o PDF também descreve, pelo MESMO ponto.

    O casamento é por (rua, ponto), e não por (rua, cota): casar pela cota
    esconderia justamente o que se quer ver, porque só acharia par onde os
    números já são iguais.

    Duas camadas, na ordem:

    1. **texto igual** (`normalizar_ponto`), como sempre foi;
    2. **redação equivalente** (`ponto_canonico`), OU o nosso ponto sendo o
       COMEÇO do ponto do PDF em fronteira de palavra — a relação da imprensa
       cortou o texto longo ("…a rua foi" em vez de "…a rua foi atingida até o
       nº 168"), e cortar não muda o lugar.

    A segunda camada só vale quando o candidato é ÚNICO naquela rua e ainda não
    foi tomado por um par da primeira. Ambíguo não pareia — e a cota nunca entra
    na escolha do candidato, só na comparação depois. `nivel` diz qual camada
    fez o par, para o relatório distinguir.
    """
    indice = indexar(pdf)
    por_rua: dict[str, list[dict]] = {}
    for r in pdf:
        if numero(r.get("cota_rotulo")) is not None:
            por_rua.setdefault(normalizar_rua(r.get("rua")), []).append(r)

    pares = []
    tomados: set[int] = set()
    segunda: list[tuple[dict, tuple]] = []
    for c in cadastro:
        if c.get("cota_m") is None:
            continue
        chave = (normalizar_rua(c.get("rua")), normalizar_ponto(c.get("ponto")))
        do_pdf = indice.get(chave)
        if do_pdf:
            perto = min(do_pdf, key=lambda v: abs(v - c["cota_m"]))
            for r in por_rua.get(chave[0], []):
                if normalizar_ponto(r.get("observacao")) == chave[1]:
                    tomados.add(id(r))
            pares.append(_par(c, chave, perto, "exato"))
        else:
            segunda.append((c, chave))

    for c, chave in segunda:
        nosso = ponto_canonico(c.get("ponto"))
        if not nosso:
            continue
        candidatos = []
        for r in por_rua.get(chave[0], []):
            if id(r) in tomados:
                continue
            deles = ponto_canonico(r.get("observacao"))
            if deles == nosso or deles.startswith(nosso + " "):
                candidatos.append(r)
        if len(candidatos) != 1:
            continue
        r = candidatos[0]
        tomados.add(id(r))
        pares.append(_par(c, chave, numero(r.get("cota_rotulo")), "canonico"))
    return pares


def _par(c: dict, chave: tuple, pdf_m: float, nivel: str) -> dict:
    return {
        "rua": c.get("rua"),
        "ponto": c.get("ponto"),
        "chave": chave,
        "nosso_m": c["cota_m"],
        "pdf_m": pdf_m,
        "bate": abs(pdf_m - c["cota_m"]) < TOLERANCIA_M,
        "nivel": nivel,
    }


def deslocamento(pares: list[dict]) -> float | None:
    """
    A mediana de (PDF − nosso). Zero quer dizer mesma referência.

    Existe por causa da regra bloqueante do `CLAUDE.md`: se as duas listas
    estivessem em referências diferentes, o número apareceria aqui como um
    deslocamento constante — 0,20 m, no caso régua/IBGE.
    """
    if not pares:
        return None
    return statistics.median(p["pdf_m"] - p["nosso_m"] for p in pares)


def sem_par_no_cadastro(pdf: list[dict], cadastro: list[dict]) -> list[dict]:
    """
    Registros do PDF que o cadastro não tem — nem pelo ponto, nem pela cota.

    A segunda tentativa, pela cota, existe porque as duas fontes descrevem o
    mesmo lugar com palavras diferentes ("final da rua" e "Final da rua (pega
    só uma casa)"). Sem ela, o mesmo ponto entraria duas vezes.
    """
    por_ponto = {(normalizar_rua(c.get("rua")), normalizar_ponto(c.get("ponto")))
                 for c in cadastro}
    # A redação equivalente também conta como "já tem" — foi a falta disto,
    # somada ao prefixo único em `normalizar_rua`, que importou 19 pontos em
    # dobro em 01/09/2026.
    canonicos: dict[str, list[str]] = {}
    for c in cadastro:
        canonicos.setdefault(normalizar_rua(c.get("rua")), []).append(
            ponto_canonico(c.get("ponto")))
    por_cota = {(normalizar_rua(c.get("rua")), round(c["cota_m"], 2))
                for c in cadastro if c.get("cota_m") is not None}
    novos = []
    for r in pdf:
        cota = numero(r.get("cota_rotulo"))
        if cota is None:
            continue
        rua = normalizar_rua(r.get("rua"))
        if (rua, normalizar_ponto(r.get("observacao"))) in por_ponto:
            continue
        deles = ponto_canonico(r.get("observacao"))
        if any(n and (n == deles or deles.startswith(n + " ")) for n in canonicos.get(rua, [])):
            continue
        if (rua, round(cota, 2)) in por_cota:
            continue
        novos.append(r)
    return novos


def confirmado(pares: list[dict]) -> bool:
    """
    A relação da imprensa está confirmada pelo documento oficial?

    Só com pares suficientes E nenhuma divergência. Uma divergência que seja
    significa que alguém digitou errado no caminho, e aí não dá para saber
    quais outras também estão — a confiança do lote inteiro cai junto.
    """
    if len(pares) < MINIMO_DE_PARES:
        return False
    return all(p["bate"] for p in pares)


def main() -> int:
    pdf = carregar_pdf()
    cadastro = carregar_cadastro()
    pares = parear(pdf, cadastro)
    divergem = [p for p in pares if not p["bate"]]

    print(f"PDF de 2014: {len(pdf)} registros · cadastro atual: {len(cadastro)}")
    canonicos = sum(1 for p in pares if p["nivel"] == "canonico")
    print(f"pares pelo mesmo ponto: {len(pares)} "
          f"({len(pares) - canonicos} texto igual, {canonicos} redação equivalente)")
    print(f"batem ao centavo: {len(pares) - len(divergem)} · divergem: {len(divergem)}")
    for p in divergem[:10]:
        print(f"  DIVERGE — {p['rua']} ({p['ponto']}): nosso {p['nosso_m']:.2f}, "
              f"PDF {p['pdf_m']:.2f}")

    desloc = deslocamento(pares)
    if desloc is not None:
        print(f"\ndeslocamento mediano (PDF − nosso): {desloc:+.2f} m")
        if abs(desloc) < TOLERANCIA_M:
            print("  zero: as duas listas estão na MESMA referência. Não é o caso")
            print("  régua/IBGE, que apareceria aqui como 0,20 m constante.")
        else:
            print("  NÃO é zero — conferir a referência antes de mexer no cadastro.")

    novos = sem_par_no_cadastro(pdf, cadastro)
    com_abrigo = sum(1 for r in pdf if r.get("abrigo"))
    print(f"\no PDF acrescenta {len(novos)} pontos que o cadastro não tem")
    print(f"e traz o ABRIGO de {com_abrigo} deles, que a relação da imprensa não tem")

    veredito = confirmado(pares)
    print("\nVEREDITO: " + (
        "relação CONFIRMADA pelo documento oficial." if veredito else
        "NÃO confirmada — ver as divergências acima."))
    return 0 if veredito else 2


if __name__ == "__main__":
    raise SystemExit(main())
