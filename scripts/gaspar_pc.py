"""Valida a leitura municipal transportada pelo PC; nunca renova a medição."""
import json
import math
import re
from datetime import datetime, timedelta, timezone

from comum import DADOS

ARQUIVO = DADOS / 'tempo-real/gaspar-pc.json'
ESTACAO = 'Gaspar — Rio Itajaí-Açu (Defesa Civil de Gaspar)'
FONTE = 'https://defesacivil.gaspar.sc.gov.br/estacao/ver/21'


#: Teto da idade da CONSULTA feita pelo PC (s). A ponte reenvia a cada 15 min;
#: mais de 30 min sem envio quer dizer que o PC parou.
TETO_CONSULTA_PC_S = 1800

#: Teto da idade da MEDIÇÃO (s): o mesmo limite de leitura velha do monitor.
TETO_MEDICAO_S = 10800


def validar(corpo, agora=None, teto_consulta_s=TETO_CONSULTA_PC_S):
    """A leitura, se o corpo for da estação 21 e a medição tiver até 3 h.

    `teto_consulta_s=None` dispensa o teto da idade da consulta e exige só que
    ela tenha fuso e não esteja no futuro. É o caso do GitHub Actions
    (`gaspar_actions.py`), que só regrava o arquivo quando a leitura muda: lá o
    `coletado_em` é a hora em que a leitura foi vista pela primeira vez, e quem
    decide se ela vale é a idade da MEDIÇÃO, que nunca é renovada.
    """
    agora = agora or datetime.now(timezone.utc)
    try:
        if corpo.get('fonte') != FONTE:
            return None
        coleta = datetime.fromisoformat(corpo['coletado_em'])
        if coleta.tzinfo is None:
            return None
        idade_consulta = (agora - coleta).total_seconds()
        if teto_consulta_s is None:
            if idade_consulta < -300:
                return None
        elif not 0 <= idade_consulta <= teto_consulta_s:
            return None
        l = corpo['leitura']
        if (l.get('cidade'), l.get('rio'), l.get('estacao')) != ('gaspar', 'itajai-acu', ESTACAO):
            return None
        v = l['nivel_m']
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v < 25:
            return None
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', l['medido_em']):
            return None
        medicao = datetime.fromisoformat(l['medido_em']).replace(tzinfo=timezone(timedelta(hours=-3)))
        if not 0 <= (agora - medicao).total_seconds() <= TETO_MEDICAO_S:
            return None
        return {'cidade': 'gaspar', 'rio': 'itajai-acu', 'estacao': ESTACAO,
                'nivel_m': v, 'medido_em': l['medido_em'], 'usar_para_cota': True}
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def ler(arquivo=None, agora=None):
    try:
        return validar(json.loads((arquivo or ARQUIVO).read_text(encoding='utf-8')), agora)
    except (OSError, ValueError):
        return None
