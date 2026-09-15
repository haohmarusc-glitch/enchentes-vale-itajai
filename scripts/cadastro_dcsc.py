#!/usr/bin/env python3
"""Cadastro das estações da rede estadual (Defesa Civil de SC) — o que cada código É.

POR QUE EXISTE (15/09/2026). Estas listas nasceram dentro do `coleta_nivel_sc.py`, que é o
coletor do TEMPO REAL. Funcionou enquanto o tempo real era o único lado que lia a rede
estadual. Desde que o `consolidar_historico_dcsc.py` passou a ler o HISTÓRICO das mesmas
estações, o mesmo fato — "Guabiruba mudou de datum", "Blumenau é meteorológica" — precisava
valer nos dois lados, e valia só num.

O sintoma apareceu em 15/09/2026: o coletor ao vivo mandava Guabiruba para `suspeitas` desde
07/09, e o resumo do histórico commitado no repo ainda listava **28,70 m como crista
candidata** da mesma estação. Não era desacordo de opinião — era a lista existir em um arquivo
só. Copiá-la para o outro seria envelhecê-la em um lugar só, que é a mesma armadilha com mais
passos. Daí este módulo: **um cadastro, dois leitores.**

NÃO IMPORTA `requests` de propósito. O consolidador rodava `from coleta_nivel_sc import CADEIA`
dentro de um `try/except` justamente porque o coletor ao vivo arrasta `requests`; aqui não há
dependência nenhuma, e o import pode ser direto — um import que falha calado é como a lista
some sem ninguém ver.

O QUE ENTRA AQUI: fato sobre a ESTAÇÃO (que cidade é, que grandeza mede, se o datum mudou).
O QUE NÃO ENTRA: regra de leitura (limite de plausibilidade, sentinela, cadência) — isso é de
quem lê, e cada leitor tem a sua.
"""

from __future__ import annotations

from datetime import datetime

# --------------------------------------------------------------------------- #
# Quem é quem
# --------------------------------------------------------------------------- #
#: Estações que interessam à cadeia (código → cidade/slug). Fora daqui ainda é coletado,
#: só sem 'cidade'.
CADEIA = {
    "DCSC-00025": "agrolandia", "DCSC-00039": "ituporanga", "DCSC-00033": "pouso-redondo",
    "DCSC-00041": "taio", "DCSC-00031": "laurentino", "DCSC-00001": "agronomica",
    "DCSC-00013": "rio-do-sul", "DCSC-00032": "lontras", "DCSC-00020": "ibirama",
    "DCSC-00043": "presidente-getulio", "DCSC-00021": "jose-boiteux", "DCSC-00003": "ascurra",
    "DCSC-00006": "indaial", "DCSC-00023": "timbo", "DCSC-00004": "benedito-novo",
    "DCSC-00011": "rio-dos-cedros", "DCSC-00028": "doutor-pedrinho", "DCSC-00007": "pomerode",
    "DCSC-00026": "blumenau", "DCSC-00005": "gaspar", "DCSC-00030": "ilhota",
    "DCSC-00163": "ilhota-arraial-dos-cunhas",
    # Mirim
    "DCSC-00024": "vidal-ramos", "DCSC-00018": "botuvera", "DCSC-00027": "botuvera-2",
    "DCSC-00019": "brusque", "DCSC-00029": "guabiruba",
    # barragens (reservatório, datum próprio — nunca cota urbana)
    "DCSC-00040": "barragem-oeste-taio", "DCSC-00038": "barragem-sul-ituporanga",
}

#: Reservatório: o nível é do lago, no datum da barragem. Nunca é cota urbana.
RESERVATORIOS = {"DCSC-00040", "DCSC-00038"}

# Estações Hidro que a API confirma medir nível de rio (`tem_nivel_do_rio=true`, investigação de
# 03/09/2026, docs/API-DCSC-CAMPOS-NOVOS.md), mas cujo valor bruto é implausível para o rio local —
# problema de DATUM/ESCALA da estação, não sensor ou grandeza errada. Vão para 'suspeitas': o valor
# não é usável cru, mas a estação é real e mede a grandeza certa.
SUSPEITAS = {"DCSC-00029": "Guabiruba ~24,8 m: estação Hidro real (tem_nivel_do_rio=true), mas o valor "
                           "bruto é implausível para o ribeirão — datum/escala própria não calibrada. "
                           "CAUSA ENCONTRADA em 07/09/2026, e ela confirma a suspeita: a Prefeitura de "
                           "Brusque informou em ABRIL DE 2026 que o sistema de medição de Guabiruba "
                           "mudou para 'cota automática', referenciada ao NÍVEL DO MAR — na ocasião a "
                           "leitura aparecia como 28,4 m com o rio a cerca de 4 m. Não é sensor "
                           "quebrado nem escala desconhecida: é OUTRA GRANDEZA, altitude em vez de "
                           "régua. CONSEQUÊNCIA: a série anterior de Guabiruba e a atual NÃO podem ser "
                           "juntadas sem reconciliar o datum, e há uma quebra de série datada em "
                           "04/2026 para marcar (ver QUEBRAS_DE_SERIE). ⚠️ O LIMITE_M de 30 m NÃO "
                           "teria pego isto: 28,4 m passa por baixo dele. Quem pegou foi esta lista, "
                           "escrita à mão — o que diz que a régua de plausibilidade por valor absoluto "
                           "é rede de segurança, não a primeira linha. Fonte: Prefeitura de Brusque, "
                           "abril de 2026, via levantamento externo de 07/09/2026.",
             "DCSC-00007": "Pomerode: estação Hidro real (tem_nivel_do_rio=true), mas oscila de forma "
                           "implausível entre leituras — datum/escala própria não calibrada"}

# Estações que a mesma investigação confirma NÃO medirem nível de rio nesta rede
# (`tem_nivel_do_rio=false`; Blumenau é `type="Meteo"`). Ao vivo, `value` vem null sempre — não é
# "sensor mudo agora", é ausência estrutural. Vão para 'nao_mede_nivel', não para 'sem_leitura'.
#
# ⚠️ NO HISTÓRICO É DIFERENTE, e foi medido em 15/09/2026: o endpoint `historic` devolve uma
# coluna `rio_nivel` para Gaspar (135.969 leituras, máximo 0,84 m) mesmo a estação não medindo o
# rio. "Tem número" não é "mede o rio": 0,84 m no Açu em Gaspar não é nível de rio nenhum, e as
# cinco "cristas candidatas" que o resumo listava para ela eram uma leitura de 0,84 m e quatro
# platôs de zero com 135 mil leituras. Blumenau, no mesmo endpoint, vem com campos de estação
# meteorológica (vento, pressão, umidade) e ZERO leituras de nível — coerente com type=Meteo.
NAO_MEDE_NIVEL = {"DCSC-00005": "Gaspar: tem_nivel_do_rio=false na API estadual — não mede nível de rio "
                                 "nesta rede (cota de Gaspar vem da Defesa Civil municipal, não da DCSC)",
                  "DCSC-00026": "Blumenau: type=Meteo, tem_nivel_do_rio=false — estação meteorológica, "
                                 "não mede nível de rio (cota de Blumenau vem do AlertaBlu, não da DCSC)"}

# --------------------------------------------------------------------------- #
# Quebras de série
# --------------------------------------------------------------------------- #
#: Instante a partir do qual o `rio_nivel` da estação passou a ser OUTRA GRANDEZA.
#:
#: Não é "leitura ruim" — é dado bom de outra coisa. Por isso a regra não é descartar a estação
#: nem descartar o valor como implausível: é CORTAR a coluna de nível na data, mantendo o resto
#: da linha (chuva, bateria, variação continuam valendo — o pluviômetro não mudou de datum).
#:
#: `desde` é hora de BRASÍLIA sem fuso, como todo carimbo do projeto (CLAUDE.md), e é inclusivo:
#: a leitura desse instante já é da grandeza nova.
QUEBRAS_DE_SERIE = {
    "DCSC-00029": {
        "desde": "2026-04-01T17:40",
        "grandeza_antes": "régua do ribeirão (bruto estadual, zero próprio da estação)",
        "grandeza_depois": "cota automática referenciada ao NÍVEL DO MAR (altitude)",
        "mantem": "antes",
        "motivo": "Guabiruba: a Prefeitura de Brusque informou em abril de 2026 a troca para "
                  "'cota automática' referenciada ao nível do mar. A troca é visível na série de "
                  "10 em 10 minutos, em UM passo: 17:30 = 0,51 m, 17:40 = 16,21 m, 17:50 = 24,68 m, "
                  "e daí em diante o valor fica na casa dos 24 m. MEDIDO em 15/09/2026 sobre "
                  "data/series/dcsc/DCSC-00029.csv: das 22.054 leituras com nível a partir desse "
                  "instante, NENHUMA fica abaixo de 10 m — não há mistura das duas grandezas depois "
                  "da quebra, o corte é limpo. Junta-las daria uma 'cheia' de 24 m num ribeirão que "
                  "corre a meio metro.",
        "fonte": "Prefeitura de Brusque, abril de 2026, via levantamento externo de 07/09/2026; "
                 "degrau conferido na série DCSC (endpoint historic) em 15/09/2026.",
    },
}


# --------------------------------------------------------------------------- #
# Consultas
# --------------------------------------------------------------------------- #
def mede_nivel(codigo: str) -> bool:
    """Esta estação mede nível de rio nesta rede? (false = ausência estrutural, não intermitência)"""
    return codigo not in NAO_MEDE_NIVEL


def quebra_de(codigo: str) -> dict | None:
    """A quebra de série da estação, ou None."""
    return QUEBRAS_DE_SERIE.get(codigo)


def _quando_da_quebra(codigo: str) -> datetime | None:
    q = QUEBRAS_DE_SERIE.get(codigo)
    return datetime.fromisoformat(q["desde"]) if q else None


def apos_a_quebra(codigo: str, quando: datetime | None) -> bool:
    """A leitura deste instante já está do lado NOVO da quebra (outra grandeza)?

    Inclusivo no instante da quebra. Sem quebra cadastrada, ou sem carimbo, é sempre False —
    "não sei quando foi" nunca vira "descarta".
    """
    corte = _quando_da_quebra(codigo)
    return bool(corte and quando is not None and quando >= corte)
