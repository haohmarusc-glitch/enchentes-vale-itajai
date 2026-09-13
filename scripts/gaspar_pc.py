"""Valida a leitura municipal transportada pelo PC; nunca renova a medição."""
import json
import math
import re
from datetime import datetime, timedelta, timezone

from comum import DADOS

ARQUIVO = DADOS / 'tempo-real/gaspar-pc.json'
ESTACAO = 'Gaspar — Rio Itajaí-Açu (Defesa Civil de Gaspar)'
FONTE = 'https://defesacivil.gaspar.sc.gov.br/estacao/ver/21'


def validar(corpo, agora=None):
    agora = agora or datetime.now(timezone.utc)
    try:
        if corpo.get('fonte') != FONTE:
            return None
        coleta = datetime.fromisoformat(corpo['coletado_em'])
        if coleta.tzinfo is None or not 0 <= (agora - coleta).total_seconds() <= 1800:
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
        if not 0 <= (agora - medicao).total_seconds() <= 10800:
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
