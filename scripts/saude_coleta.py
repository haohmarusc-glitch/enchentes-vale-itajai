#!/usr/bin/env python3
"""
A coleta ainda está viva? Sai 0 se sim, 1 se não.

Por que existe: o cron da VPS não é vigiado por ninguém. Se ele morrer — pacote
quebrado, disco cheio, a fonte mudando de endereço — o site congela num nível
antigo e continua parecendo saudável. O visitante vê a idade da leitura e
entende; **você** não vê nada, porque ninguém fica olhando o próprio site.
Este script é o que percebe.

Duas perguntas diferentes, e as duas importam:

  1. a coleta rodou? (`coletado_em`, hora em que o script correu)
  2. a fonte publicou? (`medido_em` mais recente entre as estações)

A segunda é a que pega o caso mais traiçoeiro: o cron correndo perfeitamente a
cada 15 minutos sobre uma página que parou de ser atualizada há seis horas.
O arquivo fica novo; o dado, velho.

Uso:
    python3 scripts/saude_coleta.py            # diagnóstico, sai 0 ou 1
    python3 scripts/saude_coleta.py --avisar   # e manda Telegram, no máximo
                                               # um a cada SILENCIO_H
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from comum import DADOS
import notificador

ULTIMO = DADOS / "tempo-real" / "ultimo.json"
ESTADO = DADOS / "tempo-real" / "estado_saude.json"
FUSO = ZoneInfo("America/Sao_Paulo")

#: A coleta roda a cada 15 min. Três ciclos perdidos já é falha, não atraso.
TOLERANCIA_COLETA_MIN = 45

#: A fonte mais lenta que acompanhamos (a estação MKS de Rio do Sul) publica
#: com quase uma hora de atraso. O dobro disso é folga honesta antes de dizer
#: que a fonte parou.
TOLERANCIA_FONTE_MIN = 120

#: Não repete o mesmo aviso de falha antes disto. Uma coleta morta continua
#: morta; avisar de 15 em 15 minutos só ensina a ignorar.
SILENCIO_H = 6


class Diagnostico:
    def __init__(self, ok: bool, motivo: str, detalhes: list[str]):
        self.ok = ok
        self.motivo = motivo
        self.detalhes = detalhes

    def __str__(self) -> str:
        return "\n".join([("ok: " if self.ok else "FALHA: ") + self.motivo, *self.detalhes])


def _idade_min(quando: datetime, agora: datetime) -> float:
    return (agora - quando).total_seconds() / 60


def avaliar(dados: dict | None, agora: datetime) -> Diagnostico:
    """Função pura: o relógio entra por parâmetro para o teste poder mentir."""
    if dados is None:
        return Diagnostico(False, "não há arquivo de coleta", [])

    detalhes: list[str] = []
    problemas: list[str] = []

    bruto = dados.get("coletado_em")
    if not bruto:
        problemas.append("o arquivo não diz quando foi coletado")
    else:
        try:
            coletado = datetime.fromisoformat(bruto)
            if coletado.tzinfo is None:  # `coletado_em` é UTC por contrato
                coletado = coletado.replace(tzinfo=timezone.utc)
            idade = _idade_min(coletado, agora)
            detalhes.append(f"coleta rodou há {idade:.0f} min")
            if idade > TOLERANCIA_COLETA_MIN:
                problemas.append(f"a coleta não roda há {idade:.0f} min")
        except ValueError:
            problemas.append(f"coletado_em ilegível: {bruto!r}")

    leituras = dados.get("leituras") or []
    if not leituras:
        problemas.append("a coleta rodou mas não trouxe nenhuma leitura")
    else:
        detalhes.append(f"{len(leituras)} estações no arquivo")
        medidos = []
        for l in leituras:
            m = l.get("medido_em")
            if not m:
                continue
            try:
                q = datetime.fromisoformat(m)
            except ValueError:
                continue
            medidos.append(q.replace(tzinfo=FUSO) if q.tzinfo is None else q)
        if not medidos:
            problemas.append("nenhuma leitura traz horário de medição")
        else:
            idade = _idade_min(max(medidos), agora)
            detalhes.append(f"medição mais recente há {idade:.0f} min")
            if idade > TOLERANCIA_FONTE_MIN:
                problemas.append(f"a fonte não publica leitura nova há {idade:.0f} min")

    if problemas:
        return Diagnostico(False, "; ".join(problemas), detalhes)
    return Diagnostico(True, "coleta e fonte em dia", detalhes)


def deve_avisar(diag: Diagnostico, estado: dict, agora: datetime) -> bool:
    """
    Manda aviso de falha no máximo uma vez a cada SILENCIO_H — e manda a
    recuperação assim que ela acontece, sem esperar silêncio nenhum.
    """
    falhava = bool(estado.get("falhando"))
    if diag.ok:
        return falhava  # avisa que voltou, uma vez só
    if not falhava:
        return True  # primeira falha: avisa na hora
    desde = estado.get("avisado_em")
    if not desde:
        return True
    try:
        return (agora - datetime.fromisoformat(desde)).total_seconds() / 3600 >= SILENCIO_H
    except ValueError:
        return True


def texto(diag: Diagnostico) -> str:
    e = notificador.esc
    if diag.ok:
        cabeca = "✅ <b>A coleta voltou.</b>"
    else:
        cabeca = "🛠 <b>A coleta de nível parou.</b>"
    corpo = [cabeca, "", e(diag.motivo)]
    if diag.detalhes:
        corpo += ["", *[e(d) for d in diag.detalhes]]
    if not diag.ok:
        corpo += [
            "",
            "Enquanto isso o site mostra a última leitura com a idade dela — "
            "não inventa número. Mas ninguém recebe aviso de cota até a coleta voltar.",
        ]
    return "\n".join(corpo)


def le_estado() -> dict:
    if not ESTADO.exists():
        return {}
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--avisar", action="store_true", help="manda Telegram quando muda de estado")
    ap.add_argument("--arquivo", help="usa outro ultimo.json (para teste)")
    args = ap.parse_args()

    caminho = Path(args.arquivo) if args.arquivo else ULTIMO
    dados = None
    if caminho.exists():
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"FALHA: {caminho} não é JSON válido: {exc}", file=sys.stderr)
            return 1

    agora = datetime.now(timezone.utc)
    diag = avaliar(dados, agora)
    print(diag)

    if args.avisar:
        estado = le_estado()
        if deve_avisar(diag, estado, agora):
            notificador.enviar(texto(diag))
            ESTADO.parent.mkdir(parents=True, exist_ok=True)
            ESTADO.write_text(
                json.dumps({"falhando": not diag.ok, "avisado_em": agora.isoformat()},
                           ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    return 0 if diag.ok else 1


if __name__ == "__main__":
    sys.exit(main())
