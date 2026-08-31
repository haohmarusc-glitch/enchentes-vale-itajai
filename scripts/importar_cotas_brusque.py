#!/usr/bin/env python3
"""
Importa as cotas por rua de Brusque da camada de 2023 — e só dela.

De onde vem: o Google My Maps "Cotas Enchente de Brusque", da própria Defesa
Civil (bit.ly/novascotasbrusque). O KML tem quatro camadas; esta importação usa
uma, e o motivo de recusar a outra está abaixo.

A PROVA DE QUE ISTO É COTA DE RÉGUA
-----------------------------------
Cada ponto da camada de 2023 traz duas coisas: o NOME do marcador e um campo
"Nível registrado no local". Somados, dão sempre o mesmo número:

    Bartolomeu Pruner   nome 7,65  +  lâmina 1,31  =  8,96
    Dorval Luz          nome 8,27  +  lâmina 0,69  =  8,96
    Vicente Schaeffer   nome 7,94  +  lâmina 1,02  =  8,96

8,96 m é o pico de Brusque em 17/11/2023, que já está em `enchentes.json`. Ou
seja: o nome do marcador é a **cota da régua da Ponte Estaiada** em que aquele
ponto começa a alagar, e o outro campo é a **lâmina d'água** medida ali naquele
dia.

A conta fecha em **338 dos 344 pontos** que têm lâmina, com erro de 1 cm. Não é
suposição sobre a referência: é aritmética contra um pico conhecido. Por isso
esta camada entra com `confianca: alta`, diferente dos 1.938 de Blumenau, que
vieram por imprensa e ficaram em `media`.

`verificar()` refaz essa conta a cada importação e RECUSA tudo se ela deixar de
fechar. Se a fonte trocar o significado dos campos, a importação para em vez de
gravar número errado. E o ponto que não fecha a própria conta NÃO entra: quando
os dois números discordam, não se sabe qual dos dois está errado, e cota errada
manda alguém sair de casa na hora errada — ou não sair.

POR QUE A CAMADA DE 2011 NÃO ENTRA
----------------------------------
"Cotas de Cheia 2011", no mesmo arquivo, tem 1.679 pontos e NÃO é cota de régua.
Duas evidências, ambas refazíveis:

* 64% dos pontos trazem valor acima do pico de 2011 (10,03 m), e o maior é
  29,53 m — quase três vezes o recorde da cidade
  (`scripts/analisar_kml_brusque.py`).
* Cruzando as duas camadas por vizinho mais próximo, os oito pares a menos de
  30 m diferem em **+2,04 m na mediana, até +5,36 m**. Pontos a vinte metros um
  do outro não discordam cinco metros na mesma grandeza — e o sinal
  sistematicamente positivo bate com altitude de terreno.

Uso:
    python3 scripts/importar_cotas_brusque.py --seco
    python3 scripts/importar_cotas_brusque.py
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date

from comum import DADOS

CIDADE = "brusque"
RIO = "itajai-mirim"
BRUTO = "brutos/brusque-cotas-2023.json"

#: O pico de 17/11/2023 em Brusque, como está em `enchentes.json`. É contra ele
#: que a soma cota + lâmina é conferida.
PICO_2023_M = 8.96

#: O maior pico já registrado em Brusque (`enchentes.json`, 1984). Cota acima
#: disto é ponto que nunca alagou na série conhecida — entra, com a ressalva.
MAIOR_PICO_CONHECIDO_M = 10.5

#: Quanto a soma pode desviar do pico e ainda contar como conferida. A fonte
#: publica com duas casas, então um centímetro é o arredondamento dela.
TOLERANCIA_M = 0.011

#: Quantos, dos pontos com lâmina, precisam fechar a conta para a importação
#: seguir. Um punhado de pontos soltos é erro de digitação da fonte; muitos
#: seriam sinal de que os campos não significam o que se pensa — e aí a
#: importação inteira para.
FRACAO_MINIMA_CONFERIDA = 0.95

FONTE = (
    "Defesa Civil de Brusque — mapa \"Cotas Enchente de Brusque\" (Google My Maps), "
    "camada \"Cotas de cheia 2023\", levantada após a enchente de 17/11/2023. "
    "Cota conferida pela soma com a lâmina d'água medida no local, que fecha no "
    "pico de 8,96 m. Bruto em data/brutos/brusque-cotas-2023.json"
)

#: "7,65", "7.65", "0,87 m", "1,21 m." — a fonte mistura os quatro no mesmo
#: campo. Ignorar a unidade não é tolerância a lixo: sem isto, 160 dos 344
#: pontos com lâmina sairiam da conferência calados, e a prova ficaria apoiada
#: em metade da amostra.
RE_UNIDADE = re.compile(r"\s*m\.?$", re.IGNORECASE)


def numero(texto) -> float | None:
    """`7,65`, `7.65` e `0,87 m` viram float. Texto que não é número vira None."""
    if texto is None:
        return None
    limpo = RE_UNIDADE.sub("", str(texto).strip()).replace(",", ".").strip()
    try:
        return float(limpo)
    except ValueError:
        return None


def normalizar(texto) -> str:
    sem = unicodedata.normalize("NFD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(sem.upper().split())


def fecha_a_conta(p: dict) -> bool | None:
    """
    True/False se dá para refazer `cota + lâmina = pico` neste ponto; None se a
    fonte não publica a lâmina e não há o que conferir.
    """
    cota = numero(p.get("cota_rotulo"))
    lamina = numero(p.get("nivel_registrado_no_local"))
    if cota is None or lamina is None:
        return None
    return abs((cota + lamina) - PICO_2023_M) <= TOLERANCIA_M


def verificar(pontos: list[dict]) -> tuple[int, int, list[str]]:
    """
    Refaz a conta em toda a camada. Devolve (conferidos, com_lamina, falhas).

    É esta função que autoriza a importação. Sem ela, "a camada de 2023 é cota
    de régua" seria uma afirmação minha; com ela, é uma conta que qualquer um
    refaz e que quebra sozinha se a fonte mudar.
    """
    conferidos = com_lamina = 0
    falhas: list[str] = []
    for p in pontos:
        ok = fecha_a_conta(p)
        if ok is None:
            continue
        com_lamina += 1
        if ok:
            conferidos += 1
            continue
        cota = numero(p.get("cota_rotulo"))
        lamina = numero(p.get("nivel_registrado_no_local"))
        falhas.append(
            f"{p.get('rua') or '?'}: {cota:.2f} + {lamina:.2f} = "
            f"{cota + lamina:.2f}, e não {PICO_2023_M:.2f} "
            f"(erro {abs(cota + lamina - PICO_2023_M):.2f} m)"
        )
    return conferidos, com_lamina, falhas


def autorizado(conferidos: int, com_lamina: int) -> bool:
    """
    A importação pode seguir? Só se a conta fechar na quase totalidade da
    camada. Fica aqui, e não solta dentro de `main()`, para ser testável: é a
    linha entre gravar cota de régua e gravar número de significado desconhecido.
    """
    if com_lamina == 0:
        return False
    return conferidos / com_lamina >= FRACAO_MINIMA_CONFERIDA


def piso_da_cidade() -> float | None:
    """A cota mais baixa que Brusque cadastra — o piso do que é cheia lá."""
    estacoes = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    for c in estacoes["rios"].get(RIO, {}).get("cidades", []):
        if c["id"] == CIDADE:
            valores = [v for v in (c.get("cotas_m") or {}).values()
                       if isinstance(v, (int, float))]
            return min(valores) if valores else None
    return None


def como_registro(p: dict, piso: float | None = None) -> dict | None:
    """Um ponto do bruto vira um registro de `cotas-ruas.json`, ou nada."""
    cota = numero(p.get("cota_rotulo"))
    rua = (p.get("rua") or "").strip()
    if cota is None or not rua:
        return None
    if fecha_a_conta(p) is False:
        # Os dois números da fonte discordam entre si. Qual está errado não dá
        # para saber daqui, e chutar seria gravar cota de rua sem base.
        return None

    # A esquina, quando a fonte informa, é o que distingue dois pontos da mesma
    # rua. Sem ela sobra o número da casa, que vem dentro do próprio nome da rua
    # em vários registros ("Dorval Luz - parede casa n 174 fundos").
    ponto = (p.get("esquina") or "").strip() or None
    registro = {
        "cidade": CIDADE,
        "rio": RIO,
        "rua": rua,
        "bairro": (p.get("bairro") or "").strip() or None,
        "ponto": ponto,
        "cota_m": round(cota, 2),
        "fonte": FONTE,
        "data_fonte": "2023-11",
        "confianca": "alta",
        "referencia": "régua",
    }

    notas = []
    lamina = numero(p.get("nivel_registrado_no_local"))
    if lamina is not None:
        # A lâmina medida é a evidência da cota, e guardá-la deixa a conta
        # refazível sem voltar ao bruto.
        notas.append(f"Na cheia de 17/11/2023, que chegou a {PICO_2023_M:.2f} m, a água "
                     f"cobriu {lamina:.2f} m neste ponto.")
    else:
        notas.append("A fonte não publica a lâmina d'água medida neste ponto, "
                     "então a conferência aritmética da cota não pôde ser refeita aqui.")

    if cota > MAIOR_PICO_CONHECIDO_M:
        notas.append(f"A cota fica acima do maior pico já registrado em Brusque "
                     f"({MAIOR_PICO_CONHECIDO_M:.2f} m): este ponto não alagou "
                     "em nenhuma cheia da série conhecida.")

    if piso is not None and cota < piso:
        notas.append(f"Esta cota ({cota:.2f} m) fica ABAIXO da menor cota de referência "
                     f"de Brusque ({piso:.2f} m): o ponto alagaria com o rio em nível "
                     "quase normal. Vem assim da fonte e ainda não foi conferida com a "
                     "Defesa Civil — não use como aviso sozinha.")
        # Mesmo conceito do `alerta_automatico: false` das réguas de estuário e
        # do que já se faz em Rio do Sul: o número aparece na tela, com a
        # ressalva, e não move aviso nenhum. Sem isto, o validador exigiria
        # baixar a cota de atenção de Brusque por causa de um ponto só, e o
        # aviso passaria a tocar com o rio em nível normal. O caminho certo
        # para fechar essa lacuna é o ofício à Defesa Civil de Brusque, não
        # um limiar que este script inventa.
        registro["usar_para_aviso"] = False

    registro["nota"] = " ".join(notas)
    return registro


def chave(r: dict) -> tuple:
    """
    A identidade de um ponto: cidade, rua, ponto e a COTA.

    A cota entra pelo mesmo motivo de Blumenau: a fonte descreve pontos
    distintos com o mesmo texto — "General Osório" aparece 17 vezes, sem
    esquina em quase todas —, e uma chave sem ela juntaria dois e apagaria um
    em silêncio.
    """
    return (r["cidade"], normalizar(r["rua"]), normalizar(r.get("ponto")),
            round(r["cota_m"], 2))


def mesclar(atuais: list[dict], novos: list[dict]) -> tuple[list[dict], int, int]:
    """União, nunca substituição. Devolve (lista, acrescentados, já existentes)."""
    vistos = {chave(r) for r in atuais if r.get("cota_m") is not None}
    saida = list(atuais)
    novos_n = repetidos = 0
    for r in novos:
        if chave(r) in vistos:
            repetidos += 1
            continue
        vistos.add(chave(r))
        saida.append(r)
        novos_n += 1
    return saida, novos_n, repetidos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem gravar")
    args = ap.parse_args()

    try:
        pontos = json.loads((DADOS / BRUTO).read_text(encoding="utf-8"))["pontos"]
    except (OSError, ValueError, KeyError) as erro:
        print(f"não deu para ler {BRUTO}: {erro}", file=sys.stderr)
        return 1

    conferidos, com_lamina, falhas = verificar(pontos)
    fracao = conferidos / com_lamina if com_lamina else 0.0
    print(f"{len(pontos)} pontos na camada de 2023")
    print(f"conferência: {conferidos} de {com_lamina} com lâmina fecham em "
          f"{PICO_2023_M:.2f} m ({fracao:.1%})")
    for f in falhas:
        print(f"  fora — {f}")

    if not autorizado(conferidos, com_lamina):
        print(
            "\nRECUSADO: a conta que prova que isto é cota de régua não fecha.\n"
            "Sem ela, os números seriam gravados como cota de régua sem evidência\n"
            "de que são. Conferir a fonte antes de importar.",
            file=sys.stderr,
        )
        return 2

    piso = piso_da_cidade()
    registros = [r for r in (como_registro(p, piso) for p in pontos) if r]
    print(f"{len(registros)} viram registro "
          f"({len(pontos) - len(registros)} ficam de fora: sem rua, sem cota, "
          "ou com a própria conta não fechando)")
    sem_aviso = [r for r in registros if r.get("usar_para_aviso") is False]
    for r in sem_aviso:
        print(f"  sem mover aviso — {r['rua']} a {r['cota_m']:.2f} m, abaixo do piso "
              f"de {piso:.2f} m da cidade")

    arquivo = DADOS / "cotas-ruas.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    lista, novos, repetidos = mesclar(dados["cotas"], registros)
    print(f"acrescenta {novos}, já existiam {repetidos}; "
          f"total de {len(dados['cotas'])} para {len(lista)}")

    if args.seco:
        for r in registros[:5]:
            print(f"  {r['cota_m']:5.2f} m  {r['rua'][:44]:46} {r.get('bairro') or ''}")
        return 0

    dados["cotas"] = lista
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\ngravado em {arquivo} ({date.today().isoformat()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
