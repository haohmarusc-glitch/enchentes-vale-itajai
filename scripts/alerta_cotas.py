#!/usr/bin/env python3
"""
Avisa por Telegram quando um rio cruza uma cota de referência.

Por que existe: o site só serve para quem o abre. Este script vai atrás da
pessoa. Roda no mesmo cron da coleta, logo depois dela.

REGRAS DE AVISO — e por que não são as de um bot comum
------------------------------------------------------

*Não há horário de silêncio.* Um bot de notificação normal cala entre 22 h e
7 h para não incomodar. Aqui isso mataria gente: a cheia de 2008 em Blumenau e
a de 2011 subiram de madrugada, e o aviso da madrugada é o único que dá tempo
de tirar carro da garagem e sair de casa. Se alguém quiser silêncio, o lugar
disso é o Telegram da pessoa, não este código.

*O silêncio entre avisos não é um cronômetro.* Repetir "está em alerta" a cada
45 minutos vira ruído, e ruído faz a pessoa desligar o bot justamente antes da
noite em que ele importaria. Então:

  - mudou de faixa (normal -> atenção -> alerta -> inundação): avisa sempre,
    porque é informação nova;
  - continua na mesma faixa: só repete se passou REPETE_H **e** o rio subiu
    pelo menos SUBIDA_M desde o último aviso — de novo, informação nova;
  - baixou de faixa: avisa, inclusive a volta ao normal. Saber que acabou
    também é informação, e é o fim natural da conversa.

*Cada régua tem sua cota.* O limiar sai da própria estação quando cadastrado
em `estacoes.json`. A cota da cidade só vale quando a cidade tem uma régua só:
em Itajaí são onze, com zeros diferentes, e aplicar a mesma cota a todas
criaria alarme onde não há — e, pior, calaria onde há.

Uso:
    python3 scripts/alerta_cotas.py              # avalia e envia o que houver
    python3 scripts/alerta_cotas.py --seco       # mostra o que enviaria
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from comum import DADOS, estacao_por_titulo
import notificador

ULTIMO = DADOS / "tempo-real" / "ultimo.json"
ESTADO = DADOS / "tempo-real" / "estado_alertas.json"
FUSO = ZoneInfo("America/Sao_Paulo")
SITE = "https://haohmarusc-glitch.github.io/enchentes-vale-itajai/"

#: Da mais baixa para a mais alta. 'normal' é o rio abaixo de qualquer cota.
FAIXAS = ["normal", "atencao", "alerta", "inundacao"]

ROTULO = {
    "normal": "abaixo das cotas",
    "atencao": "Atenção",
    "alerta": "Alerta",
    "inundacao": "Inundação",
}

#: Só repete o aviso da mesma faixa depois disto...
REPETE_H = 3
#: ...e ainda assim só se o rio tiver subido pelo menos isto desde o último.
SUBIDA_M = 0.30

#: Acima desta idade a leitura entra no aviso com a ressalva de que é antiga.
#: Não impede o aviso: uma leitura velha mostrando inundação continua sendo a
#: melhor informação que existe naquele momento.
IDADE_RESSALVA_MIN = 90


def faixa_de(nivel_m: float, cotas: dict) -> str:
    """A faixa mais alta que este nível alcança."""
    atual = "normal"
    for nome in FAIXAS[1:]:
        valor = cotas.get(nome)
        if isinstance(valor, (int, float)) and nivel_m >= float(valor):
            atual = nome
    return atual


def subiu(faixa_nova: str, faixa_velha: str) -> bool:
    return FAIXAS.index(faixa_nova) > FAIXAS.index(faixa_velha)


def cotas_da_leitura(leitura: dict, reguas_na_cidade: int) -> tuple[dict, str | None]:
    """
    As cotas que valem para ESTA régua, e de onde vieram.

    Devolve ({}, motivo) quando não dá para saber — e nesse caso não se avisa
    nada. Alarme com cota errada é pior que alarme nenhum: ensina a pessoa a
    ignorar o próximo.
    """
    estacao = estacao_por_titulo(leitura.get("estacao", "")) or {}
    proprias = {
        k: v for k, v in (estacao.get("cotas_m") or {}).items()
        if isinstance(v, (int, float))
    }
    if proprias:
        return proprias, None
    if reguas_na_cidade > 1:
        return {}, "a cidade tem mais de uma régua e a cota cadastrada é por cidade"
    rio, cidade = leitura.get("rio"), leitura.get("cidade")
    if not rio or not cidade:
        return {}, "estação sem rio/cidade cadastrados"
    todas = cotas_da_cidade(rio, cidade)
    if not todas:
        return {}, "sem cota de referência em estacoes.json"
    return todas, None


def cotas_da_cidade(rio: str, cidade: str) -> dict:
    """
    As TRÊS cotas da cidade. `comum.cota_de_referencia` devolve só a primeira,
    porque serve para outra pergunta — "a partir de quando é cheia" — e aqui
    precisamos saber em qual das faixas o rio está.
    """
    estacoes = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    for c in estacoes["rios"].get(rio, {}).get("cidades", []):
        if c["id"] == cidade:
            return {
                k: float(v) for k, v in (c.get("cotas_m") or {}).items()
                if isinstance(v, (int, float)) and k in FAIXAS
            }
    return {}


def idade_min(medido_em: str | None, agora: datetime) -> float | None:
    """Idade da leitura em minutos. `medido_em` é hora de Brasília sem fuso."""
    if not medido_em:
        return None
    try:
        bruto = datetime.fromisoformat(medido_em)
    except ValueError:
        return None
    if bruto.tzinfo is None:
        bruto = bruto.replace(tzinfo=FUSO)
    return (agora - bruto).total_seconds() / 60


def texto_aviso(leitura: dict, faixa: str, anterior: str, cotas: dict,
                idade: float | None) -> str:
    """A mensagem. Curta em cima, ressalvas embaixo — é lida no susto."""
    e = notificador.esc
    cidade = e(str(leitura.get("cidade") or "?").replace("-", " ").title())
    nivel = f"{leitura['nivel_m']:.2f}".replace(".", ",")

    if faixa == "normal":
        cabeca = f"🟢 <b>{cidade}</b> voltou para abaixo das cotas"
    elif subiu(faixa, anterior):
        icone = {"atencao": "🟡", "alerta": "🟠", "inundacao": "🔴"}[faixa]
        cabeca = f"{icone} <b>{cidade}</b> chegou à cota de <b>{ROTULO[faixa]}</b>"
    else:
        cabeca = f"🔵 <b>{cidade}</b> baixou para a faixa de <b>{ROTULO[faixa]}</b>"

    linhas = [cabeca, "", f"{nivel} m — {e(leitura.get('estacao', ''))}"]

    cota_atual = cotas.get(faixa)
    if isinstance(cota_atual, (int, float)):
        linhas.append(f"Cota de {ROTULO[faixa]}: {cota_atual:.2f}".replace(".", ",") + " m")

    if idade is not None:
        if idade >= IDADE_RESSALVA_MIN:
            linhas.append(f"⚠️ Leitura de {int(idade)} min atrás — a fonte não atualiza desde então.")
        else:
            linhas.append(f"Medido há {int(idade)} min.")

    linhas += [
        "",
        "Cada cidade tem sua própria régua: este número não se compara com o de outra cidade.",
        f"Níveis e tempo de descida: {SITE}",
        "",
        "<b>Isto não é alerta oficial.</b> Siga a Defesa Civil do seu município, "
        "a Defesa Civil de SC e o AlertaBlu. Emergência: <b>199</b>.",
    ]
    return "\n".join(linhas)


def resolver(dados: dict) -> tuple[list[dict], list[str]]:
    """
    Quem dá para vigiar e quem não dá, com o porquê.

    Um lugar só decide isso, usado tanto pelo `decidir` quanto pelo panorama
    que o `--seco` imprime: se fossem dois caminhos, o relatório poderia dizer
    que uma estação está vigiada enquanto o aviso a ignora em silêncio.
    """
    leituras = dados.get("leituras") or []
    reguas_na_cidade: dict[tuple, int] = {}
    for l in leituras:
        chave = (l.get("rio"), l.get("cidade"))
        reguas_na_cidade[chave] = reguas_na_cidade.get(chave, 0) + 1

    vigiadas: list[dict] = []
    recusas: list[str] = []
    for leitura in leituras:
        titulo = leitura.get("estacao") or ""
        nivel = leitura.get("nivel_m")
        if not isinstance(nivel, (int, float)):
            recusas.append(f"{titulo}: a leitura não trouxe número de nível")
            continue
        cotas, motivo = cotas_da_leitura(
            leitura, reguas_na_cidade[(leitura.get("rio"), leitura.get("cidade"))]
        )
        if motivo:
            recusas.append(f"{titulo}: {motivo}")
            continue
        vigiadas.append({
            "leitura": leitura,
            "cotas": cotas,
            "faixa": faixa_de(float(nivel), cotas),
        })
    return vigiadas, recusas


def decidir(dados: dict, estado: dict, agora: datetime) -> tuple[list[dict], dict, list[str]]:
    """
    O que avisar agora. Função pura: recebe o relógio, não olha para ele.

    Devolve (avisos, estado novo, recusas). Recusa é estação que ficou de fora
    e por quê — para aparecer no --seco em vez de sumir em silêncio.
    """
    vigiadas, recusas = resolver(dados)
    avisos: list[dict] = []
    novo = dict(estado)

    for item in vigiadas:
        leitura, cotas, faixa = item["leitura"], item["cotas"], item["faixa"]
        titulo = leitura.get("estacao") or ""
        nivel = leitura["nivel_m"]
        antes = novo.get(titulo) or {}
        faixa_antes = antes.get("faixa", "normal")
        nivel_antes = antes.get("nivel_m")
        desde = antes.get("avisado_em")

        manda = False
        if faixa != faixa_antes:
            # Nunca avisa "voltou ao normal" para quem nunca saiu dele.
            manda = not (faixa == "normal" and not antes)
        elif faixa != "normal" and desde:
            try:
                horas = (agora - datetime.fromisoformat(desde)).total_seconds() / 3600
            except ValueError:
                horas = REPETE_H + 1
            # Arredondado ao centímetro de propósito: as fontes publicam com
            # duas casas, e 4,60 + 0,30 em ponto flutuante dá 4,8999...,
            # menos que 4,90. Sem isto, uma subida de exatamente 30 cm — o
            # caso da borda, o mais provável de acontecer — não avisaria.
            cresceu = (
                isinstance(nivel_antes, (int, float))
                and round(float(nivel) - float(nivel_antes), 2) >= SUBIDA_M
            )
            manda = horas >= REPETE_H and cresceu

        if manda:
            avisos.append({
                "estacao": titulo,
                "faixa": faixa,
                "anterior": faixa_antes,
                "texto": texto_aviso(
                    leitura, faixa, faixa_antes, cotas,
                    idade_min(leitura.get("medido_em"), agora),
                ),
            })
            novo[titulo] = {
                "faixa": faixa,
                "nivel_m": float(nivel),
                "avisado_em": agora.isoformat(),
            }
        else:
            # Guarda a faixa mesmo sem avisar, senão a próxima rodada acha que
            # houve mudança. O nível e o horário do último aviso ficam como
            # estavam: é contra eles que se mede "subiu desde o último aviso".
            novo[titulo] = {**antes, "faixa": faixa}

    return avisos, novo, recusas


def le_estado() -> dict:
    if not ESTADO.exists():
        return {}
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def grava_estado(estado: dict) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    temporario = ESTADO.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(ESTADO)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seco", action="store_true", help="mostra sem enviar e sem gravar estado")
    ap.add_argument("--arquivo", help="usa outro ultimo.json (para teste)")
    args = ap.parse_args()

    caminho = Path(args.arquivo) if args.arquivo else ULTIMO
    if not caminho.exists():
        print(f"sem coleta em {caminho} — rode o coletor antes.", file=sys.stderr)
        return 1
    dados = json.loads(caminho.read_text(encoding="utf-8"))

    agora = datetime.now(timezone.utc)
    avisos, estado, recusas = decidir(dados, le_estado(), agora)

    # O panorama vem antes de tudo, e o que ESTÁ vigiado vem antes do que não
    # está. Antes daqui a saída era só uma lista de recusas: quem lesse não
    # tinha como saber que Rio do Sul, Brusque e Blumenau estavam cobertos —
    # só que Itajaí não estava. Num aviso de cheia, saber o alcance do que se
    # vigia é tão importante quanto o aviso.
    vigiadas, _ = resolver(dados)
    print(f"vigiando {len(vigiadas)} estação(ões); {len(recusas)} de fora.\n")
    for item in sorted(vigiadas, key=lambda i: str(i["leitura"].get("cidade"))):
        leitura, cotas, faixa = item["leitura"], item["cotas"], item["faixa"]
        idade = idade_min(leitura.get("medido_em"), agora)
        quando = f"há {int(idade)} min" if idade is not None else "sem horário"
        limites = " · ".join(
            f"{ROTULO[nome]} {cotas[nome]:.2f}".replace(".", ",")
            for nome in FAIXAS[1:] if nome in cotas
        )
        nivel = f"{leitura['nivel_m']:.2f}".replace(".", ",")
        print(f"  {leitura.get('cidade')}: {nivel} m ({quando}) "
              f"— {ROTULO[faixa]} · {leitura.get('estacao')}")
        print(f"      cotas desta régua: {limites}")
        if "atencao" not in cotas:
            # Sem cota de atenção o aviso pula de "normal" para uma faixa alta:
            # não existe aviso adiantado nenhum nesta régua.
            print("      ⚠ sem cota de atenção — esta régua não dá aviso adiantado")
    if recusas:
        print()
    for r in recusas:
        print(f"  sem cota, sem aviso — {r}")

    if not avisos:
        print("\nnenhuma mudança de faixa.")
        if not args.seco:
            grava_estado(estado)
        return 0

    for aviso in avisos:
        print(f"\n--- {aviso['estacao']}: {aviso['anterior']} -> {aviso['faixa']}")
        print(aviso["texto"])
        if not args.seco:
            notificador.enviar(aviso["texto"])

    if not args.seco:
        grava_estado(estado)
    return 0


if __name__ == "__main__":
    sys.exit(main())
