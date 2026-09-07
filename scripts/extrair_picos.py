#!/usr/bin/env python3
"""Encontra os picos de cheia na série coletada e PROPÕE registros para enchentes.json.

Por que existe: dos 116 registros de `enchentes.json`, só 2 têm o horário do
pico. Sem horário não dá para medir quanto tempo a cheia leva de uma cidade
até a outra, e os tempos de descida continuam vindo do hidrograma de projeto da
JICA — um evento sintético — em vez de cheias que aconteceram. Este script lê a
série que o coletor foi juntando e destila dela o que fica para sempre: o pico
de cada cidade em cada evento, com data e hora.

O que ele NÃO faz: gravar sozinho. O padrão é imprimir a proposta para alguém
conferir contra o boletim da Defesa Civil. Dado de enchente não entra no
arquivo sem uma pessoa olhar. `--escrever` existe para depois da conferência,
e recusa duplicar registro que já esteja lá.

Uso:
    python3 scripts/extrair_picos.py                      # propõe, não grava
    python3 scripts/extrair_picos.py --mes 2026-08        # só um mês
    python3 scripts/extrair_picos.py --cidade blumenau
    python3 scripts/extrair_picos.py --escrever           # grava o que propôs
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from comum import DADOS, cota_da_estacao, cota_de_referencia, grava_json, le_json

SERIE = DADOS / "tempo-real"

#: Intervalo sem leitura acima da cota que separa duas cheias. Uma cheia do
#: Itajaí-Açu leva mais de um dia para passar; 18 h de rio abaixo da cota
#: separa episódios sem partir um só em pedaços.
INTERVALO_ENTRE_EVENTOS_H = 18

#: Mínimo de leituras acima da cota para chamar de evento. Uma leitura isolada
#: acima do limiar é mais provavelmente falha de sensor que cheia.
MIN_LEITURAS = 2

#: Variação entre leituras vizinhas acima da qual o valor é marcado como
#: suspeito. NÃO é descartado: em 2026 Blumenau subiu mais de 4 m em menos de
#: 24 h, e jogar fora o extremo é justamente perder o que importa.
SALTO_SUSPEITO_M_POR_H = 1.5


class Leitura:
    __slots__ = ("quando", "nivel_m", "estacao", "so_horario")

    def __init__(self, quando: datetime, nivel_m: float, estacao: str,
                 so_horario: bool = False):
        self.quando = quando
        self.nivel_m = nivel_m
        self.estacao = estacao
        #: True quando o nível vem da rede estadual, cujo zero NÃO é o da régua
        #: municipal. O HORÁRIO do pico continua válido — um máximo é um máximo
        #: em qualquer datum —, mas o VALOR não pode virar `pico_m`. Ver
        #: `--serie-estadual` no rodapé deste arquivo.
        self.so_horario = so_horario


class Evento:
    def __init__(self, leituras: list[Leitura]):
        self.leituras = leituras
        pico = max(leituras, key=lambda l: l.nivel_m)
        self.pico_m = pico.nivel_m
        self.quando = pico.quando
        self.inicio = leituras[0].quando
        self.fim = leituras[-1].quando
        self.estacoes = sorted({l.estacao for l in leituras})
        #: Basta UMA leitura de datum não calibrado para o valor do pico ficar
        #: sem sentido: o máximo pode ter caído justamente nela.
        self.so_horario = any(l.so_horario for l in leituras)

    @property
    def suspeitos(self) -> list[Leitura]:
        """Leituras com salto grande demais em relação à anterior."""
        fora = []
        for anterior, atual in zip(self.leituras, self.leituras[1:]):
            horas = (atual.quando - anterior.quando).total_seconds() / 3600
            if horas <= 0:
                continue
            if abs(atual.nivel_m - anterior.nivel_m) / horas > SALTO_SUSPEITO_M_POR_H:
                fora.append(atual)
        return fora


#: Prefixo dos arquivos da série ESTADUAL. Forma diferente da municipal:
#: `nivel_bruto_m` em vez de `nivel_m`, e sem `rio`/`cidade` — a cidade sai do
#: `codigo` (DCSC-xxxxx) cruzado com estacoes.json.
PREFIXO_ESTADUAL = "nivel-sc-"


def cidades_por_codigo_dcsc() -> dict[str, tuple[str, str]]:
    """`DCSC-00024` -> `("itajai-mirim", "vidal-ramos")`, de estacoes.json."""
    mapa: dict[str, tuple[str, str]] = {}
    for rio_id, rio in le_json("estacoes.json")["rios"].items():
        for cidade in rio["cidades"]:
            if cidade.get("codigo_dcsc"):
                mapa[cidade["codigo_dcsc"]] = (rio_id, cidade["id"])
    return mapa


def ler_serie_estadual(mes: str | None) -> dict[str, dict]:
    """
    A série da rede estadual, para HORÁRIO de pico — nunca para valor.

    POR QUE ELA ENTRA (07/09/2026). Os três elos de trânsito do Itajaí-Mirim
    (`vidal-ramos → botuvera → guabiruba → brusque`) são a lógica que a Defesa
    Civil de Brusque de fato usa, e nenhum deles pode ser medido: Botuverá e
    Guabiruba não têm régua municipal, então nenhuma cheia futura produziria o
    par de horários. Mas a rede estadual PUBLICA Botuverá e Vidal Ramos, e a
    coleta já vem acumulando esses números em `nivel-sc-AAAA-MM.ndjson`.

    O que destrava é uma observação simples: **tempo de trânsito se mede entre
    horários, e horário não depende do zero da régua.** Um máximo é um máximo em
    qualquer datum. O que o zero desconhecido impede é dizer QUANTOS METROS o
    pico teve — e é exatamente isso que `so_horario` bloqueia daqui para a
    frente.

    Duas travas, e as duas em código, não em comentário:

    1. Toda leitura sai com `so_horario=True`, e `--escrever` recusa gravar
       qualquer evento marcado assim. Sem isso, um `pico_m` em datum estadual
       entraria no enchentes.json parecendo régua municipal.
    2. O limiar TEM de vir por `--limiar`. As cotas de estacoes.json são da
       régua municipal, e aplicá-las ao número estadual é o erro que este
       projeto já mediu: Indaial marcou 5,98 m na rede estadual num dia sem
       chuva, contra emergência municipal de 5,50 m. Separar episódios com a
       cota errada inventaria cheia onde não houve.
    """
    por_estacao: dict[str, dict] = {}
    if not SERIE.exists():
        return por_estacao
    de_codigo = cidades_por_codigo_dcsc()
    padroes = ([f"{PREFIXO_ESTADUAL}{mes}.ndjson", f"{PREFIXO_ESTADUAL}{mes}.ndjson.gz"]
               if mes else [f"{PREFIXO_ESTADUAL}*.ndjson", f"{PREFIXO_ESTADUAL}*.ndjson.gz"])
    arquivos: list[Path] = []
    for padrao in padroes:
        arquivos.extend(sorted(SERIE.glob(padrao)))

    for arquivo in arquivos:
        abrir = gzip.open if arquivo.suffix == ".gz" else open
        with abrir(arquivo, "rt", encoding="utf-8") as f:
            for numero, linha in enumerate(f, start=1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = json.loads(linha)
                    quando = datetime.fromisoformat(d["medido_em"])
                    nivel = float(d["nivel_bruto_m"])
                except (ValueError, KeyError, TypeError) as e:
                    print(f"aviso: {arquivo.name}:{numero} ignorada ({e})", file=sys.stderr)
                    continue
                # Reservatório tem datum próprio e não é régua de rio: fora.
                if d.get("datum") != "bruto_estadual":
                    continue
                par = de_codigo.get(d.get("codigo") or "")
                if not par:
                    continue  # estação estadual sem cidade nossa
                rio, cidade = par
                estacao = d.get("estacao") or d.get("codigo") or "?"
                grupo = por_estacao.setdefault(
                    estacao, {"rio": rio, "cidade": cidade, "leituras": []}
                )
                grupo["leituras"].append(Leitura(quando, nivel, estacao, so_horario=True))
    for grupo in por_estacao.values():
        grupo["leituras"].sort(key=lambda l: l.quando)
    return por_estacao


#: Séries que NÃO são nível de régua municipal e não podem entrar no glob dele.
#: `chuva-` é outra grandeza; `nivel-sc-` é outro DATUM. Sem esta lista, o
#: `*.ndjson` do modo sem `--mes` varre os três e o leitor municipal cospe um
#: aviso por linha — ruído que ensina a ignorar avisos — além de arriscar somar
#: régua estadual à municipal se um dia os campos coincidirem.
PREFIXOS_DE_OUTRA_SERIE = ("chuva-", PREFIXO_ESTADUAL)


def arquivos_da_serie(mes: str | None) -> list[Path]:
    """Só a série de nível MUNICIPAL — a que está no datum das cotas."""
    if not SERIE.exists():
        return []
    padroes = [f"{mes}.ndjson", f"{mes}.ndjson.gz"] if mes else ["*.ndjson", "*.ndjson.gz"]
    achados: list[Path] = []
    for padrao in padroes:
        achados.extend(
            p for p in sorted(SERIE.glob(padrao))
            if not p.name.startswith(PREFIXOS_DE_OUTRA_SERIE)
        )
    return achados


def ler_serie(mes: str | None) -> dict[str, dict]:
    """
    Leituras agrupadas por ESTAÇÃO — nunca por cidade.

    Itajaí tem cinco réguas só no Itajaí-Mirim (DC-03 a DC-06 e DC-10), com
    zeros diferentes: numa mesma hora elas leem 0,92 m, 1,14 m, 1,07 m, 0,97 m
    e 4,82 m. Juntar isso num balde por cidade e chamar a maior de "pico" seria
    comparar réguas — exatamente o que este projeto avisa em toda tela para
    ninguém fazer.
    """
    por_estacao: dict[str, dict] = {}
    for arquivo in arquivos_da_serie(mes):
        abrir = gzip.open if arquivo.suffix == ".gz" else open
        with abrir(arquivo, "rt", encoding="utf-8") as f:
            for numero, linha in enumerate(f, start=1):
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = json.loads(linha)
                    quando = datetime.fromisoformat(d["medido_em"])
                    nivel = float(d["nivel_m"])
                except (ValueError, KeyError, TypeError) as e:
                    print(f"aviso: {arquivo.name}:{numero} ignorada ({e})", file=sys.stderr)
                    continue
                if not d.get("rio") or not d.get("cidade"):
                    continue  # estação não mapeada para uma cidade do projeto
                estacao = d.get("estacao") or "?"
                grupo = por_estacao.setdefault(
                    estacao, {"rio": d["rio"], "cidade": d["cidade"], "leituras": []}
                )
                grupo["leituras"].append(Leitura(quando, nivel, estacao))
    for grupo in por_estacao.values():
        grupo["leituras"].sort(key=lambda l: l.quando)
    return por_estacao


def limiar_da_estacao(
    estacao: str, rio: str, cidade: str, quantas_na_cidade: int
) -> tuple[float | None, str | None]:
    """
    Cota a partir da qual vale considerar cheia NESTA régua.

    Na ordem: a cota da própria estação, quando cadastrada em `estacoes.json`;
    depois a cota da cidade, mas só se a cidade tiver uma régua só.

    Onde a cidade tem várias — Itajaí — a cota da cidade não serve: os zeros
    são diferentes, e aplicar a mesma a todas produziria evento onde não há e
    esconderia onde há. Nesse caso o script recusa e pede `--limiar`, em vez de
    escolher no escuro.
    """
    propria, nome = cota_da_estacao(estacao)
    if propria is not None:
        return propria, f"{nome} da própria estação"
    if quantas_na_cidade > 1:
        return None, "varias-reguas"
    return cota_de_referencia(rio, cidade)


def separar_eventos(leituras: list[Leitura], limiar: float) -> list[Evento]:
    """Períodos acima da cota, separados por INTERVALO_ENTRE_EVENTOS_H sem cheia."""
    acima = [l for l in leituras if l.nivel_m >= limiar]
    if not acima:
        return []

    grupos: list[list[Leitura]] = [[acima[0]]]
    for anterior, atual in zip(acima, acima[1:]):
        if atual.quando - anterior.quando > timedelta(hours=INTERVALO_ENTRE_EVENTOS_H):
            grupos.append([atual])
        else:
            grupos[-1].append(atual)

    return [Evento(g) for g in grupos if len(g) >= MIN_LEITURAS]


def ja_registrado(eventos_json: list[dict], rio: str, cidade: str, data: str) -> bool:
    return any(e["rio"] == rio and e["cidade"] == cidade and e["data"] == data for e in eventos_json)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--mes", help="analisa só um mês (AAAA-MM)")
    ap.add_argument("--cidade", help="analisa só uma cidade (id de estacoes.json)")
    ap.add_argument("--limiar", type=float, help="cota mínima, para cidades sem cota cadastrada")
    ap.add_argument("--escrever", action="store_true", help="grava as propostas em enchentes.json")
    ap.add_argument(
        "--serie-estadual", action="store_true",
        help="lê a série da rede estadual — SÓ para horário de pico, nunca para o valor. "
             "Exige --limiar, e o que sair dela não pode ser gravado.",
    )
    args = ap.parse_args()

    if args.serie_estadual and args.limiar is None:
        print(
            "ERRO: --serie-estadual exige --limiar.\n"
            "  As cotas de estacoes.json são da régua MUNICIPAL, e o número estadual está "
            "noutro zero.\n"
            "  Medido em 07/09/2026: Rio do Sul deu 3,92 m na rede estadual e 5,24 m na régua "
            "municipal\n"
            "  no mesmo minuto. Separar episódios com a cota errada inventaria cheia onde não "
            "houve —\n"
            "  Indaial marcou 5,98 m estadual num dia SEM CHUVA, contra emergência municipal de "
            "5,50 m.\n"
            "  Escolha o limiar olhando a própria série estadual daquela estação.",
            file=sys.stderr,
        )
        return 2

    if args.serie_estadual and args.escrever:
        print(
            "ERRO: --serie-estadual não grava.\n"
            "  Da série estadual vale o HORÁRIO do pico (um máximo é um máximo em qualquer "
            "datum),\n"
            "  mas NÃO o valor: gravar `pico_m` em zero estadual poria no enchentes.json um "
            "número\n"
            "  que parece régua municipal e não é. Anote o horário à mão, com a ressalva do "
            "datum.",
            file=sys.stderr,
        )
        return 2

    por_estacao = ler_serie_estadual(args.mes) if args.serie_estadual else ler_serie(args.mes)
    if not por_estacao:
        print(
            f"Nenhuma leitura em {SERIE.relative_to(DADOS.parent)}. "
            f"Rode scripts/{'coleta_nivel_sc.py' if args.serie_estadual else 'coleta_niveis.py'} "
            "primeiro — a série é construída ao longo do tempo, e só cobre cheias que "
            "aconteceram depois de a coleta começar.",
        )
        return 0

    enchentes = le_json("enchentes.json")
    propostas: list[dict] = []

    # Quantas réguas cada cidade tem na série coletada.
    reguas_por_cidade: dict[tuple[str, str], int] = {}
    for grupo in por_estacao.values():
        chave = (grupo["rio"], grupo["cidade"])
        reguas_por_cidade[chave] = reguas_por_cidade.get(chave, 0) + 1

    for estacao, grupo in sorted(por_estacao.items()):
        rio, cidade, leituras = grupo["rio"], grupo["cidade"], grupo["leituras"]
        if args.cidade and cidade != args.cidade:
            continue

        if args.limiar:
            limiar, nome_cota = args.limiar, "informada na linha de comando"
        else:
            limiar, nome_cota = limiar_da_estacao(
                estacao, rio, cidade, reguas_por_cidade[(rio, cidade)]
            )

        if limiar is None:
            motivo = (
                f"{cidade} tem {reguas_por_cidade[(rio, cidade)]} réguas na série e a cota "
                "de estacoes.json é por cidade — não dá para saber a qual delas ela se refere"
                if nome_cota == "varias-reguas"
                else "sem cota de referência em estacoes.json"
            )
            print(f"\n{estacao} ({cidade}/{rio}): {motivo}.")
            print(f"  {len(leituras)} leituras guardadas; use --limiar para analisar mesmo assim.")
            continue

        eventos = separar_eventos(leituras, limiar)
        print(
            f"\n{estacao} ({cidade}/{rio}): {len(leituras)} leituras, "
            f"cota de {nome_cota} = {limiar:.2f} m -> {len(eventos)} evento(s)"
        )
        if any(l.so_horario for l in leituras):
            print(
                "  ⚠️  DATUM NÃO CALIBRADO (rede estadual): vale o HORÁRIO do pico, "
                "não o valor em metros."
            )

        for ev in eventos:
            data = ev.quando.date().isoformat()
            hora = ev.quando.strftime("%H:%M")
            marca = " [JÁ REGISTRADO]" if ja_registrado(enchentes["eventos"], rio, cidade, data) else ""
            print(
                f"  pico {ev.pico_m:.2f} m em {data} {hora}"
                f" | acima da cota de {ev.inicio:%d/%m %H:%M} a {ev.fim:%d/%m %H:%M}"
                f" | {len(ev.leituras)} leituras{marca}"
            )
            for s_ in ev.suspeitos:
                print(
                    f"     ATENÇÃO: salto grande até {s_.nivel_m:.2f} m em {s_.quando:%d/%m %H:%M}"
                    " — pode ser subida rápida real ou falha de sensor. Confira antes de aceitar."
                )
            if marca:
                continue
            proposta = {
                "rio": rio,
                "cidade": cidade,
                "data": data,
                "hora": hora,
                "pico_m": round(ev.pico_m, 2),
                "confianca": "alta",
                "fonte": f"Defesa Civil de Itajaí, leitura automática ({estacao})",
            }
            if ev.so_horario:
                # Sai marcada para a trava de gravação lá embaixo. O campo começa
                # com `_` para nunca ser confundido com campo de dado.
                proposta["_so_horario"] = True
            propostas.append(proposta)

    if not propostas:
        print("\nNenhuma proposta nova.")
        return 0

    print(f"\n{len(propostas)} registro(s) propostos:")
    for p in propostas:
        print("  " + json.dumps(p, ensure_ascii=False))

    if not args.escrever:
        print(
            "\nNada foi gravado. Confira cada pico contra o boletim da Defesa Civil "
            "e rode de novo com --escrever para incluí-los em enchentes.json."
        )
        return 0

    # Cinto e suspensório: o modo estadual já é recusado lá em cima, mas se um
    # dia as duas séries forem lidas juntas, é aqui que o valor em datum não
    # calibrado para de entrar.
    marcadas = [p for p in propostas if p.get("_so_horario")]
    if marcadas:
        print(
            f"ERRO: {len(marcadas)} proposta(s) vêm de datum não calibrado e não podem ser "
            "gravadas.", file=sys.stderr,
        )
        return 2

    enchentes["eventos"].extend(propostas)
    enchentes["eventos"].sort(key=lambda e: (e["rio"], e["cidade"], e["data"].ljust(10, "0")))
    grava_json("enchentes.json", enchentes)
    print(f"\nenchentes.json atualizado com {len(propostas)} registro(s).")
    print("Rode scripts/validar_dados.py antes de commitar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
