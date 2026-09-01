#!/usr/bin/env python3
"""
Confere Gaspar contra o Plano de Contingência da Defesa Civil do município.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
Gaspar tinha 1.618 cotas de rua e **nenhuma cota de régua**. O validador dizia a
frase inteira: "gaspar tem rua alagando a 6.20 m, mas a cidade não tem NENHUMA
cota cadastrada em estacoes.json — o aviso por Telegram não cobre esta cidade".
A tabela de monitoramento do município publica o nível e nenhuma faixa; o
caminho que sobrava era o Plano de Contingência, e ele responde.

O Plano traz duas coisas que este script guarda transcritas e confere contra o
repositório, para que a transcrição não vire afirmação sem prova:

1. **As faixas da régua** (item 4.2.3, fluxograma "MONITORAMENTO RIO ITAJAÍ AÇU",
   p. 25). São quatro, e é delas que saem as cotas de Gaspar em `estacoes.json`.

2. **26 vias com cota de inundação** (item 4.2.2, p. 23-24), publicadas "de forma
   exemplificativa" — não é o cadastro inteiro, é uma amostra dele. Serve como
   terceira conferência independente da importação do KML.

A ARMADILHA DA PÁGINA 25
------------------------
O fluxograma é uma **imagem**, e a imagem escreve "7 a 8 metros / RESPOSTA" na
caixa vermelha. Mas o PDF, depois de desenhar a imagem, pinta por cima **outra
caixa vermelha opaca** (`1 0 0 rg`, cantos arredondados, x 177-269 / y 304-351)
e escreve nela, em branco, "Acima de 7 metros / RESPOSTA". Quem abre o PDF lê
"Acima de 7 metros"; quem extrai a imagem lê "7 a 8 metros". A faixa vale do
mesmo jeito a partir de 7,00 m — o que muda é o teto, e ler "até 8 m" teria
inventado um limite superior que o documento vigente removeu de propósito.

A REFERÊNCIA
------------
O Plano **não nomeia o zero** da régua. O que sustenta tratá-la como a mesma
régua das cotas de rua é a coerência interna, e ela é conferida aqui:

- as 26 vias do Plano vão de 6,20 m a 7,33 m e batem, ao centavo, com as cotas
  de rua que já estavam no repositório, vindas do KML da mesma Defesa Civil;
- a faixa de RESPOSTA começa em 7,00 m, dentro dessa mesma escala;
- a leitura em tempo real do município marcava 3,85 m em 31/08/2026 — dentro da
  faixa "0 a 5 m NORMALIDADE" do mesmo fluxograma.

Três fontes do mesmo órgão, uma escala só. Não é o zero publicado, e por isso
`verificado` continua `false` (o código ANA segue desconhecido); é o suficiente
para a cota entrar como `régua` e valer para aviso.

Uso:
    python3 scripts/conferir_gaspar_plano.py
"""

import sys
import unicodedata
import re

from comum import le_json

CIDADE = "gaspar"
RIO = "itajai-acu"

FONTE = (
    "Plano de Contingência da Superintendência Municipal de Proteção e Defesa "
    "Civil de Gaspar, item 4.2.3 — fluxograma \"MONITORAMENTO RIO ITAJAÍ AÇU\", "
    "p. 25 — data/brutos/gaspar-plano-de-contingencia.pdf"
)

#: Dois valores "iguais" ao centavo.
TOLERANCIA_M = 0.005

#: As quatro faixas do fluxograma da p. 25, na ordem em que ele as encadeia.
#: `ate` é None na última porque o PDF vigente diz "Acima de 7 metros" — ver a
#: seção "A ARMADILHA DA PÁGINA 25" acima.
FAIXAS_DO_PLANO = [
    {"de": 0.0, "ate": 5.0, "nome": "NORMALIDADE", "chave": None, "acao": None},
    {"de": 5.0, "ate": 6.0, "nome": "ATENÇÃO/ALERTA", "chave": "atencao",
     "acao": "Ativar Plantão Monitoramento e comunicação do nível do Rio. "
             "Previsão de continuar subindo acionar o GRAC"},
    {"de": 6.0, "ate": 7.0, "nome": "ALERTA/ALARME", "chave": "alerta",
     "acao": "Ocorrências via 199, site, GRP e WHATS; Reunião do GRAC; "
             "Preenchimento dos Formulários; Ativação Abrigo; "
             "Previsão de continuidade do Rio"},
    {"de": 7.0, "ate": None, "nome": "RESPOSTA", "chave": "emergencia",
     "acao": None},
]

#: As 26 vias do quadro do item 4.2.2 (p. 23-24), como o Plano publica:
#: (bairro, rua, ponto quando a fonte informa, cota).
RUAS_DO_PLANO = [
    ("Margem Esquerda", "Rua Costa Rica", "344", 6.20),
    ("Margem Esquerda", "Rua Sertão Verde", None, 6.34),
    ("Margem Esquerda", "Rua das Palmeiras", None, 6.93),
    ("Margem Esquerda", "Rua Imaruí", None, 7.02),
    ("Margem Esquerda", "Rua Santa Isabel", None, 7.00),
    ("Figueira", "Rua Manoel Bernardo da Silva", None, 7.33),
    ("Figueira", "Rua Petúnia", None, 6.20),
    ("Figueira", "Avenida Hilberto Gaertner", None, 6.25),
    ("Figueira", "Rua Alfazema", None, 6.46),
    ("Figueira", "Rua Lírio", None, 6.57),
    ("Figueira", "Rua Maestro Egon Bohn", None, 6.58),
    ("Figueira", "Rua Flor de Laranjeira", None, 6.60),
    ("Figueira", "Rua Rio do Sul", None, 6.63),
    ("Figueira", "Rua Amor Perfeito", None, 6.78),
    ("Figueira", "Rua Magnólia", None, 6.85),
    ("Figueira", "Rua Olga Sabel", None, 6.97),
    ("Figueira", "Rua Gerânio", None, 7.19),
    ("Coloninha", "Rua Maestro Egon Bohn", None, 6.58),
    ("Coloninha", "Rua Francisco Wessling", None, 6.73),
    ("Coloninha", "Rua Alício Hugo Hostins", None, 6.82),
    ("Coloninha", "Rua Maria da Silva", None, 6.99),
    ("Coloninha", "Rua Heinrich Gorisch", None, 7.00),
    ("Coloninha", "Rua José Eberhardt", None, 7.08),
    ("Coloninha", "Rua Frei Canisio", None, 7.10),
    ("Coloninha", "Rua Hilário dos Santos", None, 7.20),
    ("Coloninha", "Rua Otto Pawlowsky", None, 7.26),
]

#: Nível publicado pela tabela de monitoramento do município em 31/08/2026
#: 22:59, lido de `data/brutos/gaspar-monitoramento-2026-08-31.html`. Está aqui
#: como prova de escala: se ele não caísse na faixa de normalidade, a hipótese
#: de que faixas e cotas de rua usam a mesma régua estaria errada.
NIVEL_EM_31_08_2026_M = 3.85

_PREFIXO = re.compile(
    r"^(rua|avenida|av\.|r\.|travessa|rodovia|estrada|servidao|alameda|praca)\s+"
)


def normalizar(nome: str) -> str:
    """Nome de rua comparável: sem acento, sem caixa, sem prefixo de logradouro."""
    s = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode()
    s = _PREFIXO.sub("", s.lower())
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def cotas_de_gaspar() -> dict:
    """As cotas de régua de Gaspar como estão hoje em `estacoes.json`."""
    estacoes = le_json("estacoes.json")
    for c in estacoes["rios"][RIO]["cidades"]:
        if c["id"] == CIDADE:
            return c.get("cotas_m") or {}
    return {}


def ruas_de_gaspar() -> dict[str, list[float]]:
    """Cotas do nosso cadastro, agrupadas por nome de rua normalizado."""
    por_rua: dict[str, list[float]] = {}
    for r in le_json("cotas-ruas.json")["cotas"]:
        if r.get("cidade") != CIDADE or not isinstance(r.get("cota_m"), (int, float)):
            continue
        por_rua.setdefault(normalizar(r["rua"]), []).append(float(r["cota_m"]))
    return {k: sorted(v) for k, v in por_rua.items()}


def confere_faixas() -> list[str]:
    """
    As cotas do repositório são as faixas do Plano?

    Só as faixas com `chave` viram cota: NORMALIDADE é a ausência de faixa, e
    cadastrá-la como cota faria o aviso tocar com o rio no leito.
    """
    problemas = []
    cotas = cotas_de_gaspar()
    esperado = {f["chave"]: f["de"] for f in FAIXAS_DO_PLANO if f["chave"]}
    for chave, valor in esperado.items():
        atual = cotas.get(chave)
        if not isinstance(atual, (int, float)):
            problemas.append(f"estacoes.json: gaspar sem cota '{chave}' (Plano: {valor:.2f} m)")
        elif abs(float(atual) - valor) > TOLERANCIA_M:
            problemas.append(
                f"estacoes.json: gaspar '{chave}' = {atual:.2f} m, "
                f"mas o Plano diz {valor:.2f} m"
            )
    for chave in cotas:
        if chave not in esperado:
            problemas.append(
                f"estacoes.json: gaspar tem cota '{chave}' que o Plano não publica — "
                "toda cota de Gaspar precisa de fonte"
            )
    return problemas


def confere_margem() -> tuple[float | None, list[str]]:
    """
    O aviso sai ANTES de a água entrar na primeira rua?

    Esta é a pergunta que decide se a cota serve para alguma coisa. Em Brusque a
    resposta é não — a primeira cota conhecida é o nível em que a via marginal já
    está alagando. Aqui ela precisa ser sim, e com quanto de margem.
    """
    problemas = []
    ruas = ruas_de_gaspar()
    if not ruas:
        return None, ["cotas-ruas.json: nenhuma cota de rua de gaspar"]
    primeira = min(v[0] for v in ruas.values())
    atencao = cotas_de_gaspar().get("atencao")
    if not isinstance(atencao, (int, float)):
        return primeira, problemas
    if float(atencao) >= primeira:
        problemas.append(
            f"a cota de atenção ({atencao:.2f} m) não é menor que a primeira rua "
            f"({primeira:.2f} m): o aviso sairia depois da água"
        )
    return primeira, problemas


def confere_escala() -> list[str]:
    """A leitura em tempo real cai na faixa de normalidade do mesmo fluxograma?"""
    normalidade = FAIXAS_DO_PLANO[0]
    if not normalidade["de"] <= NIVEL_EM_31_08_2026_M < normalidade["ate"]:
        return [
            f"a leitura de 31/08/2026 ({NIVEL_EM_31_08_2026_M:.2f} m) está fora da "
            f"faixa de normalidade do Plano ({normalidade['de']:.2f}–"
            f"{normalidade['ate']:.2f} m) — faixas e leitura podem não ser a mesma régua"
        ]
    return []


def confere_ruas() -> tuple[list[dict], list[str]]:
    """
    Cada via do quadro do Plano contra o nosso cadastro.

    O critério é "existe um ponto nosso nesta rua com exatamente esta cota".
    Não é "a mínima da rua bate": uma rua comprida tem vários pontos, e o Plano
    publica um deles.
    """
    nossas = ruas_de_gaspar()
    linhas = []
    for bairro, rua, ponto, cota in RUAS_DO_PLANO:
        pontos = nossas.get(normalizar(rua), [])
        if not pontos:
            estado = "ausente"
        elif any(abs(v - cota) <= TOLERANCIA_M for v in pontos):
            estado = "bate"
        else:
            estado = "difere"
        linhas.append({
            "bairro": bairro, "rua": rua, "ponto": ponto, "plano_m": cota,
            "estado": estado,
            "nossos_m": pontos,
            "mais_proxima_m": min(pontos, key=lambda v: abs(v - cota)) if pontos else None,
        })
    return linhas, []


def main() -> int:
    print("Gaspar × Plano de Contingência da Defesa Civil de Gaspar\n")

    print("FAIXAS DA RÉGUA (item 4.2.3, p. 25)")
    for f in FAIXAS_DO_PLANO:
        faixa = (f"{f['de']:.2f} a {f['ate']:.2f} m" if f["ate"] is not None
                 else f"acima de {f['de']:.2f} m")
        chave = f"  -> cotas_m.{f['chave']}" if f["chave"] else "  (sem cota: é o leito)"
        print(f"  {faixa:20} {f['nome']:16}{chave}")

    problemas = confere_faixas()
    primeira, p2 = confere_margem()
    problemas += p2
    problemas += confere_escala()

    print("\nCOERÊNCIA")
    atencao = cotas_de_gaspar().get("atencao")
    if primeira is not None and isinstance(atencao, (int, float)):
        print(f"  primeira rua alaga a {primeira:.2f} m; atenção a {atencao:.2f} m "
              f"— {primeira - float(atencao):.2f} m de margem")
    print(f"  leitura de 31/08/2026: {NIVEL_EM_31_08_2026_M:.2f} m "
          f"(faixa de normalidade, 0,00–5,00 m)")

    linhas, _ = confere_ruas()
    print("\nAS 26 VIAS DO QUADRO (item 4.2.2, p. 23-24)")
    for l in linhas:
        nosso = (f"{l['mais_proxima_m']:.2f}" if l["mais_proxima_m"] is not None else "  -  ")
        marca = {"bate": "ok", "difere": "DIFERE", "ausente": "AUSENTE"}[l["estado"]]
        print(f"  {l['bairro']:16} {l['rua']:30} plano {l['plano_m']:.2f}  "
              f"nosso {nosso}  {marca}")

    from collections import Counter
    conta = Counter(l["estado"] for l in linhas)
    print(f"\n  batem ao centavo: {conta['bate']} · diferem: {conta['difere']} · "
          f"ausentes: {conta['ausente']} · de {len(linhas)}")

    if problemas:
        print("\nPROBLEMAS")
        for p in problemas:
            print(f"  ✗ {p}")
        return 1
    print("\nsem divergência entre o Plano e o repositório nas faixas de régua.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
