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
#: O bruto estadual (Taió, Ituporanga, Rio do Sul e as outras cabeceiras). Roda
#: por um cron próprio; quando esse some — como sumiu na migração pro /opt, e o
#: vigia ficou 13 h cego —, é justamente a cabeceira, onde a cheia começa, que
#: congela. Por isso ele entra na vigilância.
ULTIMO_NIVEL_SC = DADOS / "tempo-real" / "ultimo_nivel_sc.json"
ESTADO = DADOS / "tempo-real" / "estado_saude.json"
FUSO = ZoneInfo("America/Sao_Paulo")

#: A coleta roda a cada 15 min. Três ciclos perdidos já é falha, não atraso.
TOLERANCIA_COLETA_MIN = 45

#: A fonte mais lenta que acompanhamos (a estação MKS de Rio do Sul) publica
#: com quase uma hora de atraso. O dobro disso é folga honesta antes de dizer
#: que a fonte parou.
TOLERANCIA_FONTE_MIN = 120

#: O bruto estadual tem muita estação que fica silenciosa por horas (das 25, é
#: normal só umas 7 publicarem num instante). Então a folga da fonte aqui é
#: maior: o que importa vigiar é o COLETOR rodar (coletado_em) e a mais nova
#: entre todas não passar disto — não cada régua, uma a uma.
TOLERANCIA_BRUTO_FONTE_MIN = 180

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


def regua_de(leitura: dict) -> str:
    """
    Identidade da RÉGUA de uma leitura — não da linha.

    A mesma régua pode aparecer duas vezes quando há fonte de resgate (Blumenau
    vem da Defesa Civil de Itajaí e, quando essa esfria, do AlertaBlu). O resgate
    carrega `resgate_de` com o título da régua primária que ele cobre; por ele as
    duas leituras contam como UMA régua. Sem `resgate_de`, a régua é o próprio
    título — e as onze de Itajaí seguem distintas, cada uma vigiada por si.
    """
    return leitura.get("resgate_de") or leitura.get("estacao", "?")


def avaliar(dados: dict | None, agora: datetime,
            vistas_antes: set[str] | None = None) -> Diagnostico:
    """
    Função pura: o relógio entra por parâmetro para o teste poder mentir.

    `vistas_antes` são os títulos das estações que vieram na coleta anterior.
    Sem eles não há comparação — é o que acontece na primeira rodada.
    """
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

        # Cada RÉGUA, e não só a mais nova nem cada linha.
        #
        # Duas coisas se cruzam aqui:
        #  - `max(medidos)` responde só "a fonte publicou ALGUMA coisa", e uma
        #    régua viva mascarava as outras. Com doze congeladas há seis horas e
        #    uma publicando, o vigia dizia "tudo em dia" — a hora de gritar.
        #    Por isso a conta é por régua.
        #  - a mesma régua pode vir DUAS vezes (primária + resgate). As duas são
        #    a mesma régua, viva se QUALQUER uma está fresca; sem juntar, o vigia
        #    gritaria "Blumenau parada" com a primária velha ao lado do resgate
        #    novo. `regua_de` junta pelo `resgate_de`.
        idade_da_regua: dict[str, float | None] = {}
        for l in leituras:
            regua = regua_de(l)
            m = l.get("medido_em")
            idade = None
            if m:
                try:
                    q = datetime.fromisoformat(m)
                    if q.tzinfo is None:
                        q = q.replace(tzinfo=FUSO)
                    idade = _idade_min(q, agora)
                except ValueError:
                    idade = None
            if idade is not None:
                anterior = idade_da_regua.get(regua)
                if anterior is None or idade < anterior:
                    idade_da_regua[regua] = idade  # fica com a leitura mais nova
            else:
                idade_da_regua.setdefault(regua, None)
        paradas = []
        for regua in sorted(idade_da_regua):
            idade = idade_da_regua[regua]
            if idade is None:
                paradas.append(f"{regua} (sem horário)")
            elif idade > TOLERANCIA_FONTE_MIN:
                paradas.append(f"{regua} (há {idade:.0f} min)")
        if paradas:
            problemas.append(
                f"{len(paradas)} de {len(leituras)} estação(ões) sem leitura nova: "
                + ", ".join(paradas[:5])
                + (f" e mais {len(paradas) - 5}" if len(paradas) > 5 else "")
            )

    # Estações que vieram na rodada ANTERIOR e sumiram nesta.
    #
    # A página da Defesa Civil já veio parcial antes. Sem esta conta, uma régua
    # some do arquivo e nada denuncia: a tela deixa de mostrá-la, o aviso deixa
    # de vigiá-la, e o vigia continua dizendo que está tudo bem.
    #
    # A comparação é com a rodada anterior, e não com o cadastro, de propósito:
    # Blumenau está cadastrada e nunca vem, e um vigia permanentemente vermelho
    # ensina quem opera a ignorá-lo — que é o oposto do que ele serve.
    if vistas_antes:
        agora_vistas = {regua_de(l) for l in leituras if l.get("estacao")}
        sumidas = sorted(t for t in vistas_antes if t not in agora_vistas)
        if sumidas:
            problemas.append(
                f"{len(sumidas)} estação(ões) que vieram na coleta anterior sumiram: "
                + ", ".join(sumidas[:5])
                + (f" e mais {len(sumidas) - 5}" if len(sumidas) > 5 else "")
            )

    if problemas:
        return Diagnostico(False, "; ".join(problemas), detalhes)
    return Diagnostico(True, "coleta e fonte em dia", detalhes)


def avaliar_bruto(dados: dict | None, agora: datetime) -> Diagnostico:
    """
    Vigia o bruto estadual, e SÓ o essencial dele: o coletor rodou
    (`coletado_em`) e a leitura mais nova entre as estações não está velha demais.

    De propósito NÃO faz a conta por régua do `avaliar`: no bruto estadual a
    maioria das estações fica sem leitura num instante qualquer, e cobrar cada
    uma deixaria o vigia permanentemente vermelho — que é o mesmo que mudo.
    """
    if dados is None:
        return Diagnostico(False, "o nível estadual (cabeceiras) não tem arquivo de coleta", [])

    detalhes: list[str] = []
    problemas: list[str] = []

    bruto = dados.get("coletado_em")
    if not bruto:
        problemas.append("o nível estadual não diz quando foi coletado")
    else:
        try:
            coletado = datetime.fromisoformat(bruto)
            if coletado.tzinfo is None:  # `coletado_em` é UTC por contrato
                coletado = coletado.replace(tzinfo=timezone.utc)
            idade = _idade_min(coletado, agora)
            detalhes.append(f"nível estadual: coletor rodou há {idade:.0f} min")
            if idade > TOLERANCIA_COLETA_MIN:
                problemas.append(f"o coletor de nível estadual não roda há {idade:.0f} min")
        except ValueError:
            problemas.append(f"nível estadual: coletado_em ilegível: {bruto!r}")

    medidos = []
    for l in dados.get("leituras") or []:
        m = l.get("medido_em")
        if not m:
            continue
        try:
            q = datetime.fromisoformat(m)
        except ValueError:
            continue
        medidos.append(q.replace(tzinfo=FUSO) if q.tzinfo is None else q)
    if medidos:
        idade = _idade_min(max(medidos), agora)
        detalhes.append(f"nível estadual: medição mais recente há {idade:.0f} min")
        if idade > TOLERANCIA_BRUTO_FONTE_MIN:
            problemas.append(f"o nível estadual não tem leitura nova há {idade:.0f} min")

    if problemas:
        return Diagnostico(False, "; ".join(problemas), detalhes)
    return Diagnostico(True, "nível estadual em dia", detalhes)


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
    ilegivel = None
    if caminho.exists():
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            # Arquivo ilegível é DIAGNÓSTICO, não saída silenciosa.
            #
            # Antes daqui saía `return 1` antes do `--avisar`: no único caso em
            # que o site está sem dado nenhum, o vigia se calava. E só o
            # JSONDecodeError era pego — permissão negada ou disco com erro
            # estouravam em traceback, que para o cron é o mesmo silêncio.
            ilegivel = f"{caminho.name} não pôde ser lido: {exc}"

    agora = datetime.now(timezone.utc)
    estado = le_estado()
    vistas_antes = set(estado.get("estacoes_vistas") or [])
    diag = (Diagnostico(False, ilegivel, []) if ilegivel
            else avaliar(dados, agora, vistas_antes))

    # O bruto estadual entra na mesma nota. Só no caminho de produção: um
    # `--arquivo` de teste aponta só o ultimo.json, e não deve arrastar o
    # arquivo real do estadual para dentro do teste.
    if not args.arquivo:
        bruto_dados = None
        if ULTIMO_NIVEL_SC.exists():
            try:
                bruto_dados = json.loads(ULTIMO_NIVEL_SC.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                bruto_dados = None  # ilegível cai no "sem arquivo" do avaliar_bruto
        diag_bruto = avaliar_bruto(bruto_dados, agora)
        if not diag_bruto.ok:
            motivo = diag_bruto.motivo if diag.ok else f"{diag.motivo}; {diag_bruto.motivo}"
            diag = Diagnostico(False, motivo, diag.detalhes + diag_bruto.detalhes)
        else:
            diag.detalhes.extend(diag_bruto.detalhes)

    print(diag)

    if args.avisar:
        if deve_avisar(diag, estado, agora):
            notificador.enviar(texto(diag))
            estado = {"falhando": not diag.ok, "avisado_em": agora.isoformat()}

        # A lista de estações é gravada em TODA rodada, e não só quando há
        # aviso: é ela que faz a comparação da próxima. Guardada só junto do
        # aviso, uma coleta parcial logo depois de um aviso passaria batida.
        if dados:
            estado["estacoes_vistas"] = sorted(
                {regua_de(l) for l in (dados.get("leituras") or []) if l.get("estacao")}
            )
        ESTADO.parent.mkdir(parents=True, exist_ok=True)
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")

    return 0 if diag.ok else 1


if __name__ == "__main__":
    sys.exit(main())
