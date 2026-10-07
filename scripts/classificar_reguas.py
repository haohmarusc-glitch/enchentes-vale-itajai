#!/usr/bin/env python3
"""Classificação MUNICIPAL e ESTADUAL de cada cidade, calculadas em separado (PR 1: em paralelo ao site).

POR QUE EXISTE (plano de 07/10/2026, decisões do Jefferson). Hoje quem decide a cor de uma cidade é o
site (`web/src/logica/tempoReal.ts::faixaDaCidade` e `web/src/dados/usarAoVivo.ts::estadoDaCidade`).
Este módulo faz a mesma conta do lado Python e entrega, por cidade, as DUAS classificações e qual delas
pintaria o rio, com a régua e a fonte de cada uma. O site AINDA NÃO LÊ o arquivo que sai daqui: o
consumo é o PR 2, depois que a saída rodar em paralelo e bater com a tela.

AS REGRAS, nesta ordem:
  1. Régua da leitura = régua das faixas. A municipal só classifica quando a leitura é da régua das
     cotas da cidade, por IDENTIDADE (código), nunca por proximidade nem por título parecido.
     Conversão entre réguas não existe neste PR: só com vínculo oficial, fórmula e fonte, e nenhum
     está cadastrado.
  2. A estadual é a faixa que a PRÓPRIA Defesa Civil de SC publica para a estação (`rio_alarmes`,
     validada em `coleta_nivel_sc.classificar_alarmes`). Nenhum metro é comparado com limite nenhum
     do lado estadual: comparação numérica fica fora até haver limites oficiais e referência de
     régua validada (decisão de 07/10/2026).
  3. `estacoes.json` é só LIDO. Campo novo nele depende de proposta e aprovação do Jefferson.
  4. A municipal manda. A estadual só pinta quando a cidade não tem leitura municipal de agora — o
     mesmo critério do site —, e a saída marca isso como `fallback`.
  5. Leitura velha, do futuro, sem carimbo ou fora de (0, 25) m não classifica. O número continua na
     saída, com o motivo, para nunca parecer atual.

PILOTO: só Brusque (`CIDADES_PILOTO`). É a cidade em que leitura e faixas estão comprovadamente na
mesma estação (DCSC-00019, `coleta_estadual_com_cota.REGUAS_COM_COTA_PROPRIA` e `docs/BRUSQUE-DCSC-00019.md`)
e em que a Defesa Civil de SC também publica faixa própria, então as duas classificações existem.
As outras cidades entram uma a uma, em PRs seguintes; `--inventario` lista o que bloqueia cada uma.

A COR. A saída diz a FAIXA (`normal`, `atencao`…), não o hexadecimal: a cor de cada faixa é token do
site (tema claro e escuro, `global.css`), e "cor = faixa, nunca metro" continua sendo regra da tela.

Uso:
    python3 scripts/classificar_reguas.py                 # imprime o estado do piloto
    python3 scripts/classificar_reguas.py --gravar        # grava data/tempo-real/ultimo_classificacao.json
    python3 scripts/classificar_reguas.py --inventario    # o que falta para cada cidade entrar
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coleta_estadual_com_cota import REGUAS_COM_COTA_PROPRIA  # noqa: E402
from comum import DADOS, le_json, nivel_plausivel, regua_de  # noqa: E402

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")
TEMPO_REAL = DADOS / "tempo-real"
LEITURAS = TEMPO_REAL / "ultimo.json"
NIVEL_SC = TEMPO_REAL / "ultimo_nivel_sc.json"
SAIDA = TEMPO_REAL / "ultimo_classificacao.json"

#: Cidades que o motor classifica neste PR. Entrar aqui é decisão, com o inventário limpo.
CIDADES_PILOTO: tuple[str, ...] = ("brusque",)

# --- Espelho do site (o teste de paridade, `data/classificacao-esperada.json`, cobra os dois lados) ---

#: `web/src/logica/cotasOperacionais.ts::ORDEM_COTAS` — só fases de acionamento pintam.
ORDEM_COTAS: tuple[str, ...] = ("monitoramento", "atencao", "alerta", "emergencia", "inundacao")
#: `web/src/logica/tempoReal.ts`: até aqui é "agora"; depois, "atrasada"; depois de MIN_VELHA, velha.
MIN_AGORA = 90
MIN_VELHA = 180
#: O AlertaBlu publica de hora em hora; em Blumenau a leitura fica velha depois de 2 h.
MIN_VELHA_BLUMENAU = 120
#: Adiantamento até aqui é relógio; acima, é fuso trocado e a leitura fica de instante desconhecido.
MIN_FUTURO_TOLERADO = 15
#: `web/src/dados/nivelSc.ts::brutoValido`: a rede estadual aceita até 30 m (zero próprio).
NIVEL_MAXIMO_ESTADUAL_M = 30.0
#: `web/src/dados/nivelSc.ts::FAIXAS_ESTADUAIS` — o que `classificar_alarmes` pode publicar.
FAIXAS_ESTADUAIS: tuple[str, ...] = ("normal", "atencao", "alerta", "emergencia")

#: Cidades em que o site compara com regra própria, diferente da "cota mais alta alcançada (>=)".
#: O motor recusa classificá-las até a regra ser transcrita aqui, com o mesmo comparador da fonte.
COMPARADOR_ESPECIAL: dict[str, str] = {
    "ascurra": "faixas do C18 com extremos próprios (faixaC18 no site)",
    "gaspar": "legenda da estação 21 com 'maior que' e 5 m exatos indefinidos",
}

TIPOS_APLICADOS = ("municipal", "estadual", "nenhuma")
#: `web/src/dados/tempoReal.ts::RE_SEM_FUSO`.
RE_SEM_FUSO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")
STATUS_QUE_PINTAM = ("valida", "atrasada")


# --- Tempo -------------------------------------------------------------------------------------------

def de_brasilia(sem_fuso: str | None) -> datetime | None:
    """`medido_em` sem fuso é hora de Brasília (regra do CLAUDE.md). Devolve o instante em UTC."""
    # O mesmo formato que o site aceita (`RE_SEM_FUSO`); carimbo com offset aqui é campo trocado.
    if not isinstance(sem_fuso, str) or not RE_SEM_FUSO.match(sem_fuso):
        return None
    try:
        t = datetime.fromisoformat(sem_fuso)
    except ValueError:
        return None
    return t.replace(tzinfo=FUSO_BRASILIA).astimezone(timezone.utc)


def idade_min(medido: datetime, agora: datetime) -> int:
    """Minutos entre a medição e agora, como `idadeMin` do site (inclusive o arredondamento do JS)."""
    bruto = (agora - medido).total_seconds() / 60
    minutos = math.floor(bruto + 0.5)  # Math.round: .5 sobe, também nos negativos
    return minutos if minutos < -MIN_FUTURO_TOLERADO else max(0, minutos)


def frescor(idade: int, cidade_id: str | None) -> str:
    """`agora`, `atrasada` ou `velha` — `frescorDaCidade` do site."""
    if idade < 0:
        return "velha"
    if cidade_id == "blumenau" and idade > MIN_VELHA_BLUMENAU:
        return "velha"
    if idade <= MIN_AGORA:
        return "agora"
    if idade <= MIN_VELHA:
        return "atrasada"
    return "velha"


def status_da_leitura(nivel, medido: datetime | None, agora: datetime, cidade_id: str,
                      nivel_valido) -> tuple[str, int | None]:
    """O estado da leitura para classificar: valida, atrasada, antiga, carimbo_no_futuro, sem_carimbo…"""
    if not nivel_valido(nivel):
        return "valor_impossivel", None
    if medido is None:
        return "sem_carimbo", None
    idade = idade_min(medido, agora)
    if idade < 0:
        return "carimbo_no_futuro", idade
    f = frescor(idade, cidade_id)
    return {"agora": "valida", "atrasada": "atrasada", "velha": "antiga"}[f], idade


MOTIVO_DO_STATUS = {
    "valor_impossivel": "nível fora de qualquer régua da bacia — não é leitura de rio",
    "sem_carimbo": "leitura sem hora de medição — não dá para dizer que é de agora",
    "carimbo_no_futuro": "hora de medição no futuro — fuso trocado; instante desconhecido",
    "antiga": "leitura antiga — o número de horas atrás não diz a faixa de agora",
}


# --- Cadastro ----------------------------------------------------------------------------------------

def cidades_do_cadastro(estacoes: dict) -> dict[str, dict]:
    """(rio, id) não é único (Itajaí está nos dois rios); a chave aqui é `rio/id`."""
    saida: dict[str, dict] = {}
    for rio_id, rio in estacoes["rios"].items():
        for c in rio["cidades"]:
            saida[f"{rio_id}/{c['id']}"] = {**c, "rio": rio_id}
    return saida


def cidade_do_piloto(estacoes: dict, cidade_id: str) -> dict | None:
    achadas = [c for c in cidades_do_cadastro(estacoes).values() if c["id"] == cidade_id]
    return achadas[0] if len(achadas) == 1 else None


def cotas_que_pintam(cidade: dict) -> list[tuple[str, float]]:
    cotas = cidade.get("cotas_m") or {}
    return [(k, float(cotas[k])) for k in ORDEM_COTAS
            if isinstance(cotas.get(k), (int, float)) and not isinstance(cotas.get(k), bool)
            and math.isfinite(float(cotas[k]))]


def regua_das_cotas(cidade: dict) -> tuple[str | None, str | None]:
    """(id da régua das cotas, motivo quando não há). Por IDENTIDADE, de duas fontes que concordam.

    Hoje o único caminho provado é o da estação estadual que É a régua das cotas: o código está em
    `REGUAS_COM_COTA_PROPRIA` apontando para esta cidade E em `codigo_dcsc` da cidade. Réguas municipais
    sem código (os títulos das Defesas Civis) entram quando a cidade delas entrar no motor.
    """
    codigo = cidade.get("codigo_dcsc")
    cfg = REGUAS_COM_COTA_PROPRIA.get(codigo or "")
    if cfg and cfg.get("cidade") == cidade["id"] and cfg.get("rio") == cidade["rio"]:
        return codigo, None
    donos = [c for c, v in REGUAS_COM_COTA_PROPRIA.items()
             if v.get("cidade") == cidade["id"] and v.get("rio") == cidade["rio"]]
    if donos:
        return None, (f"REGUAS_COM_COTA_PROPRIA aponta {', '.join(donos)} para a cidade, mas o "
                      f"codigo_dcsc dela é {codigo!r} — as duas fontes não concordam")
    return None, "régua das cotas sem identificador que o motor saiba casar com a leitura (fora do piloto)"


def problemas_do_cadastro(cidade: dict) -> list[str]:
    """O que impede o motor de classificar a cidade pelo lado municipal. Lista vazia = pode entrar."""
    nome = cidade.get("nome") or cidade["id"]
    problemas: list[str] = []
    if cidade["id"] in COMPARADOR_ESPECIAL:
        problemas.append(f"{nome} / municipal: comparador especial ainda não transcrito "
                         f"({COMPARADOR_ESPECIAL[cidade['id']]})")
    cotas = cotas_que_pintam(cidade)
    if not cotas:
        problemas.append(f"{nome} / municipal: cotas_m sem fase de acionamento")
    for (k1, v1), (k2, v2) in zip(cotas, cotas[1:]):
        if not v1 < v2:
            problemas.append(f"{nome} / municipal: cotas_m fora de ordem ({k1} {v1} >= {k2} {v2})")
    regua, motivo = regua_das_cotas(cidade)
    if regua is None:
        problemas.append(f"{nome} / municipal: {motivo}")
    if not (cidade.get("regua_das_cotas_fonte") or "").strip():
        problemas.append(f"{nome} / municipal / {regua or '?'}: fonte das faixas ausente (regua_das_cotas_fonte)")
    if cidade.get("cotas_verificado") is not True:
        problemas.append(f"{nome} / municipal / {regua or '?'}: cotas não confirmadas (cotas_verificado "
                         f"= {cidade.get('cotas_verificado')!r})")
    return problemas


# --- Motor -------------------------------------------------------------------------------------------

def sem_classificacao(base: dict, motivo: str) -> dict:
    return {**base, "faixa": None, "motivo": motivo}


def faixa_pelas_cotas(cotas: list[tuple[str, float]], nivel: float) -> str:
    """A cota mais ALTA alcançada (>=), como `cotaAlcancadaEntre`; nenhuma alcançada = normal."""
    alcancadas = [(k, v) for k, v in cotas if nivel >= v]
    if not alcancadas:
        return "normal"
    return max(alcancadas, key=lambda kv: kv[1])[0]


def escolher_leitura(candidatas: list[dict]) -> dict | None:
    """A mais recente COM carimbo; sem carimbo nenhum, a primeira — `leituraDaCidade` do site."""
    melhor = None
    melhor_t = None
    for l in candidatas:
        t = de_brasilia(l.get("medido_em"))
        if t is None:
            continue
        if melhor_t is None or t > melhor_t:
            melhor, melhor_t = l, t
    return melhor if melhor is not None else (candidatas[0] if candidatas else None)


def leituras_municipais_da_cidade(cidade: dict, leituras: list[dict]) -> list[dict]:
    """As linhas de `ultimo.json` da cidade no rio dela, só as que o site aceitaria (`leituraValida`)."""
    saida = []
    for l in leituras:
        if l.get("cidade") != cidade["id"] or l.get("rio") != cidade["rio"]:
            continue
        if not isinstance(l.get("estacao"), str) or not l["estacao"].strip():
            continue
        if not nivel_plausivel(l.get("nivel_m")):
            continue
        saida.append(l)
    return sorted(saida, key=lambda l: l["estacao"])


def classificar_municipal(cidade: dict, leituras: list[dict], agora: datetime) -> dict:
    regua, _ = regua_das_cotas(cidade)
    base = {
        "tipo": "municipal",
        "regua_id": regua,
        "regua_nome": cidade.get("regua_das_cotas"),
        "cotas_m": dict(cotas_que_pintam(cidade)),
        "fonte_faixas": cidade.get("regua_das_cotas_fonte"),
        "status_faixas": "confirmada" if cidade.get("cotas_verificado") is True else "nao_confirmada",
        "regua_da_leitura": None,
        "nivel_m": None,
        "medido_em": None,
        "idade_min": None,
        "status_leitura": "indisponivel",
        "fonte_leitura": None,
        "de_agora": False,
        "varias_reguas": False,
    }
    candidatas = leituras_municipais_da_cidade(cidade, leituras)
    if len({regua_de(l) for l in candidatas}) > 1:
        return sem_classificacao({**base, "varias_reguas": True, "status_leitura": "varias_reguas"},
                                 "a cidade tem várias réguas publicadas — eleger uma seria escolher a cor")
    leitura = escolher_leitura(candidatas)
    if leitura is not None:
        medido = de_brasilia(leitura.get("medido_em"))
        status, idade = status_da_leitura(leitura.get("nivel_m"), medido, agora, cidade["id"], nivel_plausivel)
        base.update({
            "regua_da_leitura": leitura.get("codigo") or regua_de(leitura),
            "estacao": leitura.get("estacao"),
            "nivel_m": leitura.get("nivel_m"),
            "medido_em": leitura.get("medido_em"),
            "idade_min": idade,
            "status_leitura": status,
            "fonte_leitura": leitura.get("fonte"),
            # O critério do site para a estadual NÃO aparecer: há leitura municipal com carimbo e não velha.
            "de_agora": status in STATUS_QUE_PINTAM,
        })
    problemas = problemas_do_cadastro(cidade)
    if problemas:
        return sem_classificacao(base, "; ".join(p.split(": ", 1)[-1] for p in problemas))
    if leitura is None:
        return sem_classificacao(base, "sem leitura municipal publicada")
    if base["regua_da_leitura"] != regua:
        return sem_classificacao(base, f"a leitura ({base['regua_da_leitura']}) e as cotas ({regua}) são de "
                                       "réguas diferentes — sem conversão oficial, não se compara")
    if base["status_leitura"] not in STATUS_QUE_PINTAM:
        return sem_classificacao(base, MOTIVO_DO_STATUS[base["status_leitura"]])
    return {**base, "faixa": faixa_pelas_cotas(cotas_que_pintam(cidade), float(leitura["nivel_m"])),
            "motivo": None}


def _estadual_valido(nivel) -> bool:
    return (isinstance(nivel, (int, float)) and not isinstance(nivel, bool)
            and 0 < float(nivel) < NIVEL_MAXIMO_ESTADUAL_M)


def classificar_estadual(cidade: dict, nivel_sc: dict, agora: datetime) -> dict:
    """A faixa que a Defesa Civil de SC publica para a estação da cidade. Nenhum metro é comparado aqui."""
    base = {
        "tipo": "estadual",
        "regua_id": None,
        "estacao": None,
        "nivel_m": None,
        "zero": "o da própria estação estadual (a faixa é a que a DCSC publica para ela)",
        "medido_em": None,
        "idade_min": None,
        "status_leitura": "indisponivel",
        "fonte_faixas": None,
    }
    candidatas = [l for l in (nivel_sc.get("leituras") or [])
                  if l.get("cidade") == cidade["id"] and isinstance(l.get("estacao"), str)
                  and l["estacao"].strip() and _estadual_valido(l.get("nivel_bruto_m"))]
    leitura = escolher_leitura(candidatas)
    if leitura is None:
        motivo = "sem leitura da rede estadual para a cidade"
        for balde in ("suspeitas", "sem_leitura", "altimetricas"):
            for l in nivel_sc.get(balde) or []:
                if l.get("cidade") == cidade["id"] and l.get("motivo"):
                    return sem_classificacao({**base, "regua_id": l.get("codigo"), "estacao": l.get("estacao")},
                                             f"rede estadual: {l['motivo']}")
        return sem_classificacao(base, motivo)
    medido = de_brasilia(leitura.get("medido_em"))
    status, idade = status_da_leitura(leitura.get("nivel_bruto_m"), medido, agora, cidade["id"], _estadual_valido)
    cls = leitura.get("classificacao_estadual") if isinstance(leitura.get("classificacao_estadual"), dict) else {}
    base.update({
        "regua_id": leitura.get("codigo"),
        "estacao": leitura.get("estacao"),
        "nivel_m": leitura.get("nivel_bruto_m"),
        "medido_em": leitura.get("medido_em"),
        "idade_min": idade,
        "status_leitura": status,
        "fonte_faixas": cls.get("fonte"),
    })
    if status not in STATUS_QUE_PINTAM:
        return sem_classificacao(base, MOTIVO_DO_STATUS[status])
    faixa = cls.get("faixa")
    if faixa not in FAIXAS_ESTADUAIS:
        return sem_classificacao(base, cls.get("motivo") or "a Defesa Civil de SC não publicou faixa para a estação")
    return {**base, "faixa": faixa, "motivo": None}


def rotulo(c: dict) -> str:
    if c["tipo"] == "municipal":
        return f"Classificação municipal — {c.get('regua_nome') or c['regua_id']} ({c['regua_id']})"
    return f"Classificação estadual (Defesa Civil de SC) — {c['regua_id']}"


def escolher_aplicada(municipal: dict, estadual: dict) -> dict:
    """Qual classificação pinta o rio. A municipal manda; a estadual só sem municipal de agora."""
    if municipal.get("faixa"):
        return {"tipo": "municipal", "faixa": municipal["faixa"], "regua_id": municipal["regua_id"],
                "fallback": False, "rotulo": rotulo(municipal), "aviso": None, "motivo": None}
    if not municipal.get("varias_reguas") and not municipal.get("de_agora") and estadual.get("faixa"):
        return {"tipo": "estadual", "faixa": estadual["faixa"], "regua_id": estadual["regua_id"],
                "fallback": True, "rotulo": rotulo(estadual),
                "aviso": (f"Cor pela classificação que a Defesa Civil de SC publica para a estação "
                          f"{estadual['regua_id']}, no zero dela. Não são as cotas do município."),
                "motivo": None}
    if municipal.get("varias_reguas"):
        motivo = municipal["motivo"]
    elif municipal.get("de_agora"):
        motivo = f"leitura municipal de agora sem classificação: {municipal['motivo']}"
    else:
        motivo = f"municipal: {municipal['motivo']}; estadual: {estadual['motivo']}"
    return {"tipo": "nenhuma", "faixa": None, "regua_id": None, "fallback": False,
            "rotulo": None, "aviso": None, "motivo": motivo}


def classificar_cidade(cidade: dict, leituras: list[dict], nivel_sc: dict, agora: datetime) -> dict:
    municipal = classificar_municipal(cidade, leituras, agora)
    estadual = classificar_estadual(cidade, nivel_sc, agora)
    aplicada = escolher_aplicada(municipal, estadual)
    return {
        "cidade": cidade.get("nome") or cidade["id"],
        "rio": cidade["rio"],
        "classificacoes": {"municipal": municipal, "estadual": estadual},
        "classificacao_aplicada": aplicada,
        "faixa_do_rio": aplicada["faixa"],
    }


def montar_estado(estacoes: dict, ultimo: dict, nivel_sc: dict, agora: datetime,
                  piloto: tuple[str, ...] = CIDADES_PILOTO) -> dict:
    cidades = {}
    for cid in piloto:
        cidade = cidade_do_piloto(estacoes, cid)
        if cidade is None:
            raise ValueError(f"cidade do piloto {cid!r} ausente ou repetida em estacoes.json")
        cidades[cid] = classificar_cidade(cidade, ultimo.get("leituras") or [], nivel_sc, agora)
    return {
        "versao": 1,
        "gerado_em": agora.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "aviso": ("Saída em PARALELO (PR 1): o site ainda não lê este arquivo. Duas classificações "
                  "independentes por cidade; a faixa diz a cor, nunca o metro."),
        "piloto": list(piloto),
        "entradas": {
            "leituras_coletadas_em": ultimo.get("coletado_em"),
            "nivel_sc_coletado_em": nivel_sc.get("coletado_em"),
        },
        "cidades": cidades,
    }


# --- Validação da saída ------------------------------------------------------------------------------

def validar_estado(estado: dict, agora: datetime) -> list[str]:
    """Erros que impedem a saída de ser gravada. Mensagem com cidade, classificação, régua e campo."""
    erros: list[str] = []
    for cid, c in (estado.get("cidades") or {}).items():
        nome = c.get("cidade") or cid
        cls = c.get("classificacoes") or {}
        ap = c.get("classificacao_aplicada") or {}
        for tipo in ("municipal", "estadual"):
            x = cls.get(tipo) or {}
            onde = f"{nome} / {tipo} / {x.get('regua_id') or '?'}"
            if x.get("tipo") != tipo:
                erros.append(f"{onde}: classificação {x.get('tipo')!r} guardada como {tipo}")
            if not x.get("faixa"):
                if not x.get("motivo"):
                    erros.append(f"{onde}: sem faixa e sem motivo")
                continue
            if x.get("status_leitura") not in STATUS_QUE_PINTAM:
                erros.append(f"{onde}: faixa com leitura {x.get('status_leitura')!r}")
            medido = de_brasilia(x.get("medido_em"))
            if medido is None or idade_min(medido, agora) < 0:
                erros.append(f"{onde}: faixa com medido_em ausente ou no futuro")
            if not (x.get("fonte_faixas") or "").strip():
                erros.append(f"{onde}: fonte_faixas ausente")
            if tipo == "municipal":
                if x.get("regua_da_leitura") != x.get("regua_id"):
                    erros.append(f"{onde}: leitura da régua {x.get('regua_da_leitura')!r} classificada com "
                                 f"as cotas de {x.get('regua_id')!r}")
                if x.get("status_faixas") != "confirmada":
                    erros.append(f"{onde}: faixas {x.get('status_faixas')!r} produzindo cor")
                if not nivel_plausivel(x.get("nivel_m")):
                    erros.append(f"{onde}: nivel_m impossível {x.get('nivel_m')!r}")
                if x.get("faixa") not in ORDEM_COTAS + ("normal",):
                    erros.append(f"{onde}: faixa {x.get('faixa')!r} fora do vocabulário municipal")
            else:
                if x.get("faixa") not in FAIXAS_ESTADUAIS:
                    erros.append(f"{onde}: faixa {x.get('faixa')!r} fora das publicadas pela DCSC")
                if not _estadual_valido(x.get("nivel_m")):
                    erros.append(f"{onde}: nivel_m impossível {x.get('nivel_m')!r}")
        tipo = ap.get("tipo")
        if tipo not in TIPOS_APLICADOS:
            erros.append(f"{nome} / aplicada: tipo {tipo!r} fora de {TIPOS_APLICADOS}")
            continue
        if tipo == "nenhuma":
            if ap.get("faixa") is not None or not ap.get("motivo"):
                erros.append(f"{nome} / aplicada: 'nenhuma' com faixa ou sem motivo")
        else:
            origem = cls.get(tipo) or {}
            if ap.get("faixa") != origem.get("faixa") or ap.get("regua_id") != origem.get("regua_id"):
                erros.append(f"{nome} / aplicada / {ap.get('regua_id')}: faixa ou régua diferente da "
                             f"classificação {tipo}")
            if not (ap.get("rotulo") or "").startswith(f"Classificação {tipo}"):
                erros.append(f"{nome} / aplicada / {ap.get('regua_id')}: rótulo não diz que é {tipo}")
            if ap.get("fallback") is not (tipo == "estadual"):
                erros.append(f"{nome} / aplicada / {ap.get('regua_id')}: fallback incoerente com {tipo}")
            if tipo == "estadual" and not ap.get("aviso"):
                erros.append(f"{nome} / aplicada / {ap.get('regua_id')}: estadual pintando sem aviso")
        if c.get("faixa_do_rio") != ap.get("faixa"):
            erros.append(f"{nome}: faixa_do_rio diferente da classificação aplicada")
    return erros


def validar_cadastro_piloto(estacoes: dict, piloto: tuple[str, ...] = CIDADES_PILOTO) -> list[str]:
    """Para o `validar_dados.py`: cidade do piloto com cadastro que o motor não aceita."""
    erros = []
    for cid in piloto:
        cidade = cidade_do_piloto(estacoes, cid)
        if cidade is None:
            erros.append(f"{cid}: cidade do piloto ausente ou repetida em estacoes.json")
            continue
        erros.extend(problemas_do_cadastro(cidade))
    return erros


# --- CLI ---------------------------------------------------------------------------------------------

def _le(caminho: Path) -> dict:
    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return d if isinstance(d, dict) else {}


def inventario(estacoes: dict) -> list[tuple[str, list[str]]]:
    return [(chave, problemas_do_cadastro(c)) for chave, c in cidades_do_cadastro(estacoes).items()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--gravar", action="store_true", help="grava data/tempo-real/ultimo_classificacao.json")
    ap.add_argument("--inventario", action="store_true", help="o que bloqueia cada cidade no motor")
    a = ap.parse_args(argv)
    estacoes = le_json("estacoes.json")
    if a.inventario:
        for chave, problemas in inventario(estacoes):
            print(f"{chave}: {'pode entrar' if not problemas else 'bloqueada'}")
            for p in problemas:
                print(f"    - {p.split(': ', 1)[-1]}")
        return 0
    agora = datetime.now(timezone.utc)
    estado = montar_estado(estacoes, _le(LEITURAS), _le(NIVEL_SC), agora)
    erros = validar_estado(estado, agora)
    if erros:
        print("ERRO: classificação recusada, nada gravado:\n  " + "\n  ".join(erros), file=sys.stderr)
        if a.gravar and SAIDA.exists():
            SAIDA.unlink()  # melhor nenhum arquivo que um de outra coleta passando por atual
        return 1
    for cid, c in estado["cidades"].items():
        ap_ = c["classificacao_aplicada"]
        m, e = c["classificacoes"]["municipal"], c["classificacoes"]["estadual"]
        print(f"{c['cidade']}: rio {ap_['faixa'] or 'sem cor'} ({ap_['rotulo'] or ap_['motivo']})")
        print(f"  municipal: {m['faixa'] or '—'}  {m['nivel_m']} m {m['medido_em']}  {m['motivo'] or ''}")
        print(f"  estadual:  {e['faixa'] or '—'}  {e['nivel_m']} m {e['medido_em']}  {e['motivo'] or ''}")
    if a.gravar:
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        tmp = SAIDA.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        tmp.replace(SAIDA)
        print(f"→ {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
