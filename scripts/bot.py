#!/usr/bin/env python3
"""
Bot de consulta no Telegram: nível, chuva e previsão sob demanda.

Complementa o `alerta_cotas.py`, que fala sozinho quando um rio cruza cota.
Aqui é o contrário: a pessoa pergunta quando quer — de madrugada, sem abrir o
site, com internet ruim. Uma mensagem de texto passa onde uma página não passa.

Comandos:
    /nivel [cidade]      nível agora, cota e idade da leitura
    /chuva [cidade]      acumulado de 1 h, 12 h, 24 h e 48 h
    /previsao [cidade]   se o pico fosse agora, quando chega a jusante
    /cotas [cidade]      cotas de referência daquela régua
    /rios                panorama de tudo que é medido, numa tela
    /emergencia          telefones e fontes oficiais
    /ajuda               esta lista

TRÊS REGRAS QUE VALEM PARA TODA RESPOSTA
----------------------------------------
1. **Nunca inventa número.** Sem dado, a resposta diz que não tem. "Não sei" é
   uma resposta útil; um número errado, não.
2. **Toda leitura vem com a idade.** Um nível de três horas atrás pode ser o
   melhor que existe, mas quem lê precisa saber que é de três horas atrás.
3. **Toda resposta lembra que isto não é alerta oficial.** Quem decide
   evacuação é a Defesa Civil; emergência é 199.

QUEM PODE PERGUNTAR
-------------------
Qualquer pessoa. Isto é uma diferença deliberada em relação ao bot do
Fila-Disney, que restringe os comandos a um único chat — lá é um bot pessoal, e
o token vazado daria a um estranho acesso ao histórico de alguém.

Aqui o público é a razão de existir: um morador de Gaspar às três da manhã não
vai pedir autorização a ninguém. Tudo que estes comandos devolvem já é público
— o mesmo número que a Defesa Civil publica na web e que o site mostra. Não há
nada a proteger, e restringir tornaria o bot inútil justamente para quem ele
serve.

O que continua restrito é o AVISO AUTOMÁTICO de cota: ele vai só para o
`TELEGRAM_CHAT_ID` do `.env`. Transformar isso em lista de inscritos é outra
conversa, com outras consequências (limite de envio do Telegram, gente que
recebe aviso de cidade onde não mora, responsabilidade sobre quem não recebeu).

Uso:
    python3 scripts/bot.py            # fica escutando (long polling)
    python3 scripts/bot.py --uma-vez  # processa o que está na fila e sai
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import notificador
from comum import DADOS, le_json
from transito import caminho, faixa_horas, janela_chegada

ULTIMO = DADOS / "tempo-real" / "ultimo.json"
ESTADO = DADOS / "tempo-real" / "estado_bot.json"
FUSO = ZoneInfo("America/Sao_Paulo")
SITE = "https://haohmarusc-glitch.github.io/enchentes-vale-itajai/"

#: Quanto o Telegram segura a conexão esperando mensagem nova.
ESPERA_S = 25

#: Uma resposta por chat a cada tantos segundos. Não é para punir ninguém: é
#: para um chat sozinho não consumir a fila numa hora em que muita gente
#: pergunta ao mesmo tempo — que é justamente a hora da cheia.
INTERVALO_POR_CHAT_S = 2

RODAPE = (
    "\n\n<i>Não é alerta oficial. Siga a Defesa Civil do seu município, "
    "a Defesa Civil de SC e o AlertaBlu. Emergência: <b>199</b>.</i>"
)

ROTULO_COTA = {
    "atencao": "Atenção",
    "alerta": "Alerta",
    "inundacao": "Inundação",
    "inundacao_historica": "Inundação histórica",
}


# --- texto ------------------------------------------------------------------

def sem_acento(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn"
    )


def metros(v: float) -> str:
    return f"{v:.2f}".replace(".", ",") + " m"


def milimetros(v: float) -> str:
    return f"{v:.1f}".replace(".", ",") + " mm"


def texto_idade(minutos: float | None) -> str:
    if minutos is None:
        return "sem horário de medição"
    m = int(minutos)
    if m < 1:
        return "agora mesmo"
    if m < 60:
        return f"há {m} min"
    h, resto = divmod(m, 60)
    return f"há {h} h {resto:02d}" if resto else f"há {h} h"


def idade_min(medido_em: str | None, agora: datetime) -> float | None:
    if not medido_em:
        return None
    try:
        q = datetime.fromisoformat(medido_em)
    except ValueError:
        return None
    if q.tzinfo is None:
        q = q.replace(tzinfo=FUSO)
    return (agora - q).total_seconds() / 60


def quando(d: datetime) -> str:
    return d.astimezone(FUSO).strftime("%d/%m às %H:%M")


# --- dados ------------------------------------------------------------------

class Base:
    """Tudo que o bot precisa, lido do disco. Sem rede além do Telegram."""

    def __init__(self, ultimo: dict, estacoes: dict, transito: dict, enchentes: dict):
        self.ultimo = ultimo
        self.estacoes = estacoes
        self.transito = transito["trechos"]
        self.enchentes = enchentes["eventos"]

    @classmethod
    def do_disco(cls) -> "Base":
        ultimo = json.loads(ULTIMO.read_text(encoding="utf-8")) if ULTIMO.exists() else {}
        return cls(ultimo, le_json("estacoes.json"), le_json("transito.json"),
                   le_json("enchentes.json"))

    def cidades(self) -> list[dict]:
        saida = []
        for rio_id, rio in self.estacoes["rios"].items():
            for c in sorted(rio["cidades"], key=lambda x: x["ordem"]):
                saida.append({**c, "rio": rio_id})
        return saida

    def achar_cidade(self, texto: str) -> list[dict]:
        """
        Cidades que casam com o que a pessoa escreveu.

        Devolve LISTA de propósito: "itajai" existe nos dois rios, e escolher um
        deles em silêncio esconderia metade da resposta.
        """
        alvo = sem_acento(texto).strip()
        if not alvo:
            return []
        exatas = [c for c in self.cidades() if sem_acento(c["nome"]) == alvo or c["id"] == alvo]
        if exatas:
            return exatas
        return [c for c in self.cidades() if alvo in sem_acento(c["nome"]) or alvo in c["id"]]

    def leituras_da_cidade(self, cidade_id: str) -> list[dict]:
        return [l for l in (self.ultimo.get("leituras") or []) if l.get("cidade") == cidade_id]

    def chuva_da_cidade(self, cidade_id: str) -> list[dict]:
        return [c for c in (self.ultimo.get("chuva") or []) if c.get("cidade") == cidade_id]


# --- respostas --------------------------------------------------------------

def ajuda() -> str:
    return (
        "<b>Cheias do Vale do Itajaí</b>\n\n"
        "/nivel <i>cidade</i> — nível do rio agora\n"
        "/chuva <i>cidade</i> — quanto choveu em 1 h, 12 h, 24 h e 48 h\n"
        "/previsao <i>cidade</i> — se o pico fosse agora, quando chega embaixo\n"
        "/cotas <i>cidade</i> — cotas de referência daquela régua\n"
        "/rios — panorama de tudo que é medido\n"
        "/emergencia — telefones e fontes oficiais\n\n"
        f"Mapa e histórico: {SITE}"
        + RODAPE
    )


def emergencia() -> str:
    return (
        "<b>Em emergência, ligue 199</b> (Defesa Civil) ou <b>193</b> (Bombeiros).\n\n"
        "Fontes oficiais, que mandam mais que este bot:\n"
        "• Defesa Civil de SC — monitoramento.defesacivil.sc.gov.br\n"
        "• AlertaBlu (Blumenau) — alertablu.blumenau.sc.gov.br\n"
        "• Defesa Civil de Itajaí — defesacivil.itajai.sc.gov.br\n\n"
        "Se mandaram você sair, saia. Este bot mostra número; "
        "ele não sabe o que está acontecendo na sua rua."
        + RODAPE
    )


def resposta_nivel(base: Base, cidade: dict, agora: datetime) -> list[str]:
    linhas = [f"<b>{notificador.esc(cidade['nome'])}</b> — nível do rio"]
    leituras = base.leituras_da_cidade(cidade["id"])
    if not leituras:
        linhas.append("\nSem leitura ao vivo desta cidade na fonte que coletamos.")
        if cidade.get("fonte_tempo_real"):
            linhas.append(f"Fonte oficial: {notificador.esc(cidade['fonte_tempo_real'])}")
        return linhas

    for l in sorted(leituras, key=lambda x: x.get("estacao", "")):
        idade = idade_min(l.get("medido_em"), agora)
        linhas.append(
            f"\n<b>{metros(l['nivel_m'])}</b> — {notificador.esc(l.get('estacao', ''))}"
            f"\n<i>{texto_idade(idade)}</i>"
        )
    if len(leituras) > 1:
        linhas.append(
            "\n⚠️ Esta cidade tem mais de uma régua, com zeros diferentes: "
            "os números acima <b>não se comparam entre si</b>."
        )
    return linhas


def resposta_chuva(base: Base, cidade: dict, agora: datetime) -> list[str]:
    linhas = [f"<b>{notificador.esc(cidade['nome'])}</b> — chuva acumulada"]
    todas = base.chuva_da_cidade(cidade["id"])
    boas = [c for c in todas if c.get("coerente")]
    if not todas:
        linhas.append("\nNão há pluviômetro desta cidade na fonte que coletamos.")
        return linhas
    if not boas:
        linhas.append(
            "\n⚠️ Os pluviômetros desta cidade estão publicando dado inconsistente "
            "(acumulado que diminui com o tempo). Sem número, para não enganar."
        )
        return linhas

    for chave, rotulo in (("h1", "1 h"), ("h12", "12 h"), ("h24", "24 h"), ("h48", "48 h")):
        valores = [c["mm"][chave] for c in boas if c["mm"].get(chave) is not None]
        if not valores:
            continue
        if max(valores) - min(valores) < 0.5:
            texto = milimetros(max(valores))
        else:
            texto = f"{milimetros(min(valores))[:-3]}–{milimetros(max(valores))}"
        destaque = "<b>" + texto + "</b>" if chave == "h24" else texto
        linhas.append(f"\n{rotulo}: {destaque}")

    idades = [idade_min(c.get("medido_em"), agora) for c in boas]
    idades = [i for i in idades if i is not None]
    rodape = f"\n\n{len(boas)} pluviômetro"
    rodape += f"s, maior valor de cada janela" if len(boas) > 1 else ""
    if idades:
        rodape += f" · {texto_idade(min(idades))}"
    linhas.append(rodape)
    if len(todas) > len(boas):
        linhas.append(f"\n{len(todas) - len(boas)} descartado(s) por dado inconsistente na fonte.")
    return linhas


def resposta_previsao(base: Base, cidade: dict, agora: datetime) -> list[str]:
    linhas = [f"<b>Se o pico em {notificador.esc(cidade['nome'])} fosse agora</b>"]
    leituras = base.leituras_da_cidade(cidade["id"])
    if len(leituras) != 1:
        motivo = (
            "esta cidade tem mais de uma régua e não dá para dizer qual representa o rio"
            if leituras else "não há leitura ao vivo desta cidade"
        )
        linhas.append(f"\nNão dá para calcular: {motivo}.")
        return linhas

    l = leituras[0]
    idade = idade_min(l.get("medido_em"), agora)
    linhas.append(f"\n{notificador.esc(cidade['nome'])} está em <b>{metros(l['nivel_m'])}</b>"
                  f" ({texto_idade(idade)}).")

    partida = agora
    if l.get("medido_em"):
        try:
            p = datetime.fromisoformat(l["medido_em"])
            partida = p.replace(tzinfo=FUSO) if p.tzinfo is None else p
        except ValueError:
            pass

    rio_id = cidade["rio"]
    ordem = [c for c in base.cidades() if c["rio"] == rio_id]
    depois = [c for c in ordem if c["ordem"] > cidade["ordem"]]

    achou = False
    fora_de_ordem = False
    maior_inicio = None
    for destino in depois:
        c = caminho(base.transito, rio_id, cidade["id"], destino["id"])
        if not c:
            continue
        achou = True
        inicio, fim = janela_chegada(partida, c)

        # A água passa por cada cidade na ordem do rio, então a janela de uma
        # cidade nunca deveria começar antes da janela da cidade acima dela.
        # Quando começa, é porque os trechos vêm de fontes diferentes que não
        # concordam entre si — e isso precisa ser dito, não escondido. Não se
        # "conserta" empurrando o horário: seria inventar precisão que a fonte
        # não tem.
        if maior_inicio is not None and inicio < maior_inicio:
            fora_de_ordem = True
        maior_inicio = inicio if maior_inicio is None else max(maior_inicio, inicio)

        if inicio == fim:
            horario = f"por volta de {quando(inicio)}"
        else:
            horario = f"entre {quando(inicio)} e {quando(fim)}"
        linhas.append(
            f"\n• <b>{notificador.esc(destino['nome'])}</b>: {horario}"
            f"\n  <i>{faixa_horas(c)} · confiança {c.confianca}</i>"
        )

    if not achou:
        linhas.append("\nNão há tempo de descida levantado desta cidade para nenhuma abaixo.")
        return linhas

    if fora_de_ordem:
        linhas.append(
            "\n\n⚠️ <b>Os horários acima não estão em ordem de rio abaixo.</b> "
            "Os tempos de descida vêm de fontes diferentes que não concordam entre si, "
            "e por isso alguma cidade aparece recebendo a água antes de outra que fica "
            "acima dela. Trate cada linha como a estimativa daquele trecho, não como "
            "uma sequência."
        )

    linhas.append(
        "\n\n<b>Isto é uma conta condicional.</b> O tempo de descida é de pico a pico, "
        "e o rio pode continuar subindo por horas — nesse caso tudo acima se desloca junto. "
        "A conta não prevê altura, só horário, e ignora a chuva que cair no caminho, "
        "manobra de barragem e, em Itajaí, a maré."
    )
    return linhas


def resposta_cotas(base: Base, cidade: dict) -> list[str]:
    linhas = [f"<b>{notificador.esc(cidade['nome'])}</b> — cotas de referência"]
    cotas = cidade.get("cotas_m") or {}
    if not cotas:
        linhas.append("\nAs cotas desta cidade ainda não foram levantadas.")
        return linhas
    for chave in ("atencao", "alerta", "inundacao", "inundacao_historica"):
        if chave in cotas:
            linhas.append(f"\n{ROTULO_COTA.get(chave, chave)}: <b>{metros(cotas[chave])}</b>")
    if cidade.get("regua"):
        linhas.append(f"\n\nRégua: {notificador.esc(cidade['regua'])}")
    linhas.append("\n<i>Cada cidade tem sua própria régua: estes metros não se "
                  "comparam com os de outra cidade.</i>")
    return linhas


def resposta_rios(base: Base, agora: datetime) -> list[str]:
    leituras = base.ultimo.get("leituras") or []
    if not leituras:
        return ["Não há coleta disponível agora."]
    linhas = ["<b>Tudo que está sendo medido</b>"]
    por_cidade: dict[str, list[dict]] = {}
    for l in leituras:
        por_cidade.setdefault(str(l.get("cidade")), []).append(l)
    nomes = {c["id"]: c["nome"] for c in base.cidades()}
    for cid, ls in sorted(por_cidade.items()):
        nome = nomes.get(cid, cid)
        maior = max(ls, key=lambda x: x["nivel_m"])
        idade = idade_min(maior.get("medido_em"), agora)
        sufixo = f" (maior de {len(ls)} réguas, que não se comparam)" if len(ls) > 1 else ""
        linhas.append(f"\n<b>{notificador.esc(nome)}</b>: {metros(maior['nivel_m'])}"
                      f"{sufixo} · {texto_idade(idade)}")
    coletado = base.ultimo.get("coletado_em")
    if coletado:
        try:
            linhas.append(f"\n\n<i>Coleta de {quando(datetime.fromisoformat(coletado))}</i>")
        except ValueError:
            pass
    return linhas


def responder(texto: str, base: Base, agora: datetime) -> str | None:
    """
    A resposta a uma mensagem. None quando não é para responder nada.

    Função pura: recebe os dados e o relógio, não vai ao disco nem à rede.
    """
    bruto = (texto or "").strip()
    if not bruto.startswith("/"):
        return None

    partes = bruto.split(maxsplit=1)
    comando = sem_acento(partes[0].split("@")[0].lstrip("/"))
    argumento = partes[1].strip() if len(partes) > 1 else ""

    if comando in ("start", "ajuda", "help"):
        return ajuda()
    if comando in ("emergencia", "199"):
        return emergencia()
    if comando == "rios":
        return "".join(resposta_rios(base, agora)) + RODAPE

    if comando not in ("nivel", "chuva", "previsao", "cotas"):
        return None  # comando de outro bot, ou digitado errado: silêncio

    if not argumento:
        nomes = ", ".join(sorted({c["nome"] for c in base.cidades()}))
        return (f"Diga a cidade. Exemplo: <code>/{comando} Blumenau</code>\n\n"
                f"Cidades: {notificador.esc(nomes)}")

    achadas = base.achar_cidade(argumento)
    if not achadas:
        return (f"Não conheço “{notificador.esc(argumento)}”.\n\n"
                f"Use /ajuda para ver as cidades.")
    if len(achadas) > 4:
        return (f"“{notificador.esc(argumento)}” casa com "
                f"{len(achadas)} cidades. Seja mais específico.")

    if comando in ("nivel", "chuva"):
        # Itajaí aparece nos dois rios. Nível e chuva são por CIDADE — a
        # pergunta "quanto choveu em Itajaí" tem uma resposta só, e repeti-la
        # duas vezes fazia a mensagem parecer defeito. Previsão e cotas
        # dependem do rio e seguem saindo uma vez por rio.
        vistas: set[str] = set()
        unicas = []
        for c in achadas:
            if c["id"] not in vistas:
                vistas.add(c["id"])
                unicas.append(c)
        achadas = unicas

    blocos = []
    for cidade in achadas:
        if comando == "nivel":
            blocos.append("".join(resposta_nivel(base, cidade, agora)))
        elif comando == "chuva":
            blocos.append("".join(resposta_chuva(base, cidade, agora)))
        elif comando == "previsao":
            blocos.append("".join(resposta_previsao(base, cidade, agora)))
        else:
            blocos.append("".join(resposta_cotas(base, cidade)))
    return "\n\n———\n\n".join(blocos) + RODAPE


# --- laço -------------------------------------------------------------------

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
    temporario.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    temporario.replace(ESTADO)


#: O menu que aparece no botão "/" do Telegram. Sem isto a pessoa precisa
#: adivinhar os comandos — e adivinhar durante uma cheia não acontece.
MENU = [
    ("nivel", "Nível do rio agora, numa cidade"),
    ("chuva", "Quanto choveu em 1 h, 12 h, 24 h e 48 h"),
    ("previsao", "Se o pico fosse agora, quando chega embaixo"),
    ("cotas", "Cotas de referência da régua da cidade"),
    ("rios", "Panorama de tudo que está sendo medido"),
    ("emergencia", "Telefones e fontes oficiais"),
    ("ajuda", "Lista de comandos"),
]


def registrar_menu() -> None:
    """Publica os comandos no Telegram. Falhar aqui não impede o bot de rodar."""
    import requests

    token, _ = notificador._credenciais()
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/setMyCommands",
            json={"commands": [{"command": c, "description": d} for c, d in MENU]},
            timeout=15,
        )
    except Exception as e:
        print(f"não deu para registrar o menu de comandos: {e}", file=sys.stderr)


def descartar_pendentes() -> int:
    """
    Joga fora o que se acumulou enquanto o bot esteve fora do ar.

    Copiado do Fila-Disney, e aqui vale ainda mais: sem isso, ao voltar de uma
    queda de seis horas o bot responderia de uma vez a todas as perguntas
    daquelas seis horas — com o nível de AGORA. A pessoa perguntou "e o rio?"
    às três da manhã e receberia às nove uma resposta que parece daquela hora.
    Resposta velha com cara de nova é pior que resposta nenhuma.
    """
    import requests

    token, _ = notificador._credenciais()
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
                         params={"timeout": 0}, timeout=20)
        pendentes = r.json().get("result", []) if r.status_code == 200 else []
    except Exception:
        return 0
    if not pendentes:
        return 0
    print(f"descartadas {len(pendentes)} mensagem(ns) acumulada(s) enquanto o bot esteve fora.")
    return pendentes[-1]["update_id"] + 1


def rodada(estado: dict, espera: int) -> dict:
    """Busca mensagens novas e responde. Devolve o estado atualizado."""
    import requests

    token, _ = notificador._credenciais()
    resposta = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        params={"offset": estado.get("offset", 0), "timeout": espera},
        timeout=espera + 15,
    )
    if resposta.status_code != 200:
        print(f"getUpdates HTTP {resposta.status_code}", file=sys.stderr)
        time.sleep(5)
        return estado

    atualizacoes = resposta.json().get("result", [])
    if not atualizacoes:
        return estado

    # Recarrega a cada rodada: a coleta reescreve o ultimo.json de 15 em 15 min,
    # e responder com dado carregado na inicialização seria responder com dado
    # de horas atrás sem saber.
    base = Base.do_disco()
    agora = datetime.now(timezone.utc)
    ultima_por_chat = dict(estado.get("ultima_por_chat", {}))

    for u in atualizacoes:
        estado["offset"] = u["update_id"] + 1
        mensagem = u.get("message") or u.get("edited_message") or {}
        chat = str((mensagem.get("chat") or {}).get("id") or "")
        texto = mensagem.get("text") or ""
        if not chat or not texto:
            continue

        agora_s = time.time()
        if agora_s - float(ultima_por_chat.get(chat, 0)) < INTERVALO_POR_CHAT_S:
            continue

        saida = responder(texto, base, agora)
        if saida is None:
            continue
        ultima_por_chat[chat] = agora_s
        notificador.enviar_para(chat, saida)

    estado["ultima_por_chat"] = ultima_por_chat
    return estado


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--uma-vez", action="store_true", help="processa a fila e sai")
    args = ap.parse_args()

    if not notificador.configurado():
        print("Configure TELEGRAM_BOT_TOKEN no .env.", file=sys.stderr)
        return 1

    estado = le_estado()
    if args.uma_vez:
        grava_estado(rodada(estado, espera=0))
        return 0

    registrar_menu()
    novo_offset = descartar_pendentes()
    if novo_offset:
        estado["offset"] = novo_offset
        grava_estado(estado)

    print("bot escutando. Ctrl+C para parar.")
    while True:
        try:
            estado = rodada(estado, espera=ESPERA_S)
            grava_estado(estado)
        except KeyboardInterrupt:
            print("\nparando.")
            return 0
        except Exception as e:  # rede caindo não pode matar o bot
            print(f"erro na rodada: {e}", file=sys.stderr)
            time.sleep(10)


if __name__ == "__main__":
    sys.exit(main())
