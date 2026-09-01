#!/usr/bin/env python3
"""
Bot de consulta no Telegram: nível, chuva e previsão sob demanda.

Complementa o `alerta_cotas.py`, que fala sozinho quando um rio cruza cota.
Aqui é o contrário: a pessoa pergunta quando quer — de madrugada, sem abrir o
site, com internet ruim. Uma mensagem de texto passa onde uma página não passa.

Comandos:
    /rua [cidade] [rua]  a partir de quantos metros aquela rua alaga
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

O TOKEN NÃO PODE APARECER EM LOG
--------------------------------
Ele viaja no CAMINHO da URL do Telegram (`/bot<token>/getUpdates`), então todo
erro de rede o carrega no texto. Por isso nenhum erro sai daqui sem passar por
`notificador.sem_segredo()` — nem impresso, nem devolvido para quem imprime, e
nem como traceback: `--uma-vez` captura a falha em vez de deixá-la subir. Log é
o que se copia e cola para pedir ajuda, e o token vale acesso ao bot.

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

#: Quantos timeouts seguidos do long polling ainda são rotina.
#:
#: O Telegram segura a conexão por ESPERA_S e devolve lista vazia; de vez em
#: quando a conexão fica pendurada e estoura o timeout de leitura. Isso não
#: perde mensagem — o `offset` só avança depois de processar, então a chamada
#: seguinte refaz a mesma consulta. Registrar cada um como "erro" enche o
#: journal de alarme falso, e log que grita à toa ensina quem opera a ignorar
#: o log inteiro: é o mesmo defeito de um aviso que toca com a maré. A partir
#: daqui, porém, não é mais soluço de rede — é o bot surdo, e isso precisa
#: aparecer.
TIMEOUTS_TOLERADOS = 3

#: Depois do primeiro aviso, repete só de tantas falhas em tantas.
REPETE_AVISO = 20

#: Uma resposta por chat a cada tantos segundos. Não é para punir ninguém: é
#: para um chat sozinho não consumir a fila numa hora em que muita gente
#: pergunta ao mesmo tempo — que é justamente a hora da cheia.
INTERVALO_POR_CHAT_S = 2

#: Idade máxima da leitura para /previsao responder com horário.
#:
#: A conta é "se o pico fosse AGORA": ela usa o instante da medição como
#: partida. Com leitura velha, "agora" é mentira e os horários saem no passado —
#: com uma de 30 h, o bot anunciava chegada em Apiúna para o dia anterior, com
#: cara de previsão. Três horas é o mesmo limite que o site usa para marcar
#: leitura como velha (MIN_VELHA).
IDADE_MAXIMA_PREVISAO_MIN = 180

#: A partir de quantos minutos de diferença entre o pluviômetro mais velho e o
#: mais novo vale dizer as duas idades. Abaixo disso, a do mais velho já conta a
#: história e duas idades só encompridam a mensagem.
DIFERENCA_DE_IDADE_MIN = 15

RODAPE = (
    "\n\n<i>Não é alerta oficial. Siga a Defesa Civil do seu município, "
    "a Defesa Civil de SC e o AlertaBlu. Emergência: <b>199</b>.</i>"
)

ROTULO_COTA = {
    "atencao": "Atenção",
    "alerta": "Alerta",
    "emergencia": "Emergência",
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


def regua_de(leitura: dict) -> str:
    """
    A régua de uma leitura. A leitura de RESGATE cai na régua da primária:
    `resgate_de` traz o título da primária, e as duas medem a MESMA régua, com o
    MESMO zero — em Blumenau, a estação ANA 83800002, que a Defesa Civil e o
    AlertaBlu publicam. Sem juntá-las, a primária e o resgate contam como duas
    réguas "que não se comparam", e o bot some com o nível da cidade justamente
    quando a primária falha e o resgate assume — foi o que houve com Blumenau em
    cheia. É o mesmo colapso que o `leituraDaCidade` faz no site.
    """
    return str(leitura.get("resgate_de") or leitura.get("estacao") or "")


def por_regua(leituras: list[dict], agora: datetime) -> list[dict]:
    """
    Uma leitura por régua distinta — a mais fresca de cada.

    Junta primária e resgate (mesma régua) e mantém a leitura mais recente das
    duas. NÃO mistura réguas distintas: as onze de Itajaí, com zeros diferentes,
    continuam onze. A ordem de saída é a de primeira aparição de cada régua na
    lista, para não embaralhar o que já era estável.
    """
    def idade(l: dict) -> float:
        # Menor = mais fresca; leitura sem horário vai para o fim do desempate.
        m = idade_min(l.get("medido_em"), agora)
        return m if m is not None else float("inf")

    melhor: dict[str, dict] = {}
    ordem: list[str] = []
    for l in leituras:
        r = regua_de(l)
        if r not in melhor:
            ordem.append(r)
            melhor[r] = l
        elif idade(l) < idade(melhor[r]):
            melhor[r] = l
    return [melhor[r] for r in ordem]


# --- dados ------------------------------------------------------------------

class Base:
    """Tudo que o bot precisa, lido do disco. Sem rede além do Telegram."""

    def __init__(self, ultimo: dict, estacoes: dict, transito: dict, enchentes: dict,
                 cotas_ruas: dict | None = None):
        self.ultimo = ultimo
        self.estacoes = estacoes
        self.transito = transito["trechos"]
        self.enchentes = enchentes["eventos"]
        cotas_ruas = cotas_ruas or {"cotas": [], "_meta": {}}
        # REGRA BLOQUEANTE do CLAUDE.md, item 4: só régua. A cota de rua é
        # comparada com o nível ao vivo da Defesa Civil, que é régua; uma cota
        # em outra referência daria "faltam 2,30 m" com 20 cm de erro embutido
        # e nada na mensagem denunciando.
        self.cotas_ruas = [
            c for c in cotas_ruas.get("cotas", [])
            if c.get("referencia", "régua") == "régua"
        ]

    @classmethod
    def do_disco(cls) -> "Base":
        ultimo = json.loads(ULTIMO.read_text(encoding="utf-8")) if ULTIMO.exists() else {}
        try:
            cotas = le_json("cotas-ruas.json")
        except FileNotFoundError:
            cotas = None
        return cls(ultimo, le_json("estacoes.json"), le_json("transito.json"),
                   le_json("enchentes.json"), cotas)

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

    def reguas_com_cota(self, cidade_id: str) -> list[dict]:
        """
        As réguas da cidade que têm cota cadastrada, em qualquer calha.

        Existe porque `cotas_m` da cidade só serve para cidade de uma régua só.
        Itajaí tem onze — duas no Açu, quatro no Mirim, três em ribeirões e a de
        Limoeiro — e Ilhota tem uma que mora em `estacoes_tempo_real`. Sem isto,
        o bot respondia "as cotas desta cidade ainda não foram levantadas" para
        duas cidades cujas cotas estão publicadas no Plano de Contingência.
        Dizer que não há dado quando há manda a pessoa procurar em outro lugar
        na hora em que ela tem menos tempo.

        Pluviômetro fica de fora: ele mede chuva, e cota ao lado dele seria
        outra grandeza.
        """
        saida = []
        for e in self.estacoes.get("estacoes_tempo_real") or []:
            if e.get("cidade") != cidade_id or e.get("tipo") == "pluviometro":
                continue
            cotas = {k: float(v) for k, v in (e.get("cotas_m") or {}).items()
                     if isinstance(v, (int, float))}
            if not cotas:
                continue
            nome = e.get("nome_no_plano") or e.get("titulo") or ""
            codigo = e.get("codigo")
            if codigo and not nome.startswith(codigo):
                nome = f"{codigo} — {nome}"
            saida.append({
                "nome": nome,
                "cotas": cotas,
                # Só `false` explícito tira do aviso automático; ausente é
                # régua comum de rio, como a de Ilhota.
                "alerta_automatico": e.get("alerta_automatico") is not False,
                "fonte": e.get("fonte_cotas"),
            })
        return saida

    def leituras_da_cidade(self, cidade_id: str, agora: datetime) -> list[dict]:
        """
        As leituras ao vivo da cidade, UMA por régua (primária e resgate juntas).

        Recebe `agora` porque juntar primária e resgate exige saber qual das duas
        é a mais fresca. Sem o agrupamento, Blumenau — primária + AlertaBlu —
        parecia ter duas réguas e o bot recusava dizer o nível dela.
        """
        cruas = [l for l in (self.ultimo.get("leituras") or []) if l.get("cidade") == cidade_id]
        return por_regua(cruas, agora)

    def chuva_da_cidade(self, cidade_id: str) -> list[dict]:
        return [c for c in (self.ultimo.get("chuva") or []) if c.get("cidade") == cidade_id]

    def cidades_com_ruas(self) -> list[dict]:
        """Cidades que têm alguma cota de rua levantada."""
        ids = {c["cidade"] for c in self.cotas_ruas}
        vistas, saida = set(), []
        for c in self.cidades():
            if c["id"] in ids and c["id"] not in vistas:
                vistas.add(c["id"])
                saida.append(c)
        return saida

    def separar_cidade(self, argumento: str) -> tuple[dict | None, str]:
        """
        Reparte "Blumenau São Rafael" em (cidade, "São Rafael").

        Casa o PREFIXO MAIS LONGO, porque há nome de cidade que é começo de
        outro e nome de rua que começa com nome de cidade — "Rua Rio do Sul",
        em Gaspar, é rua. Sem cidade reconhecida, devolve (None, argumento
        inteiro) e quem chama procura em todas, rotulando cada resultado.
        """
        alvo = sem_acento(argumento)
        melhor, resto = None, argumento
        for c in self.cidades_com_ruas():
            nome = sem_acento(c["nome"])
            if alvo == nome:
                return c, ""
            if alvo.startswith(nome + " ") and (melhor is None or len(nome) > len(sem_acento(melhor["nome"]))):
                melhor, resto = c, argumento[len(c["nome"]):].strip()
        return melhor, resto

    def ruas(self, cidade_id: str | None, termo: str) -> list[dict]:
        """
        Ruas que casam com o termo, da cota mais baixa para a mais alta.

        Sem cota vai por último: a fonte cita a rua e não publica o número, e
        essa resposta é legítima — só não pode empurrar para baixo quem tem
        número, que é quem a pessoa precisa ver primeiro.
        """
        alvo = sem_acento(termo)
        if len(alvo) < 2:
            return []
        achadas = [
            c for c in self.cotas_ruas
            if (cidade_id is None or c["cidade"] == cidade_id)
            and (alvo in sem_acento(c.get("rua", "")) or alvo in sem_acento(c.get("bairro") or ""))
        ]
        return sorted(achadas, key=lambda c: (c["cota_m"] is None, c["cota_m"] or 0, c["rua"]))


# --- respostas --------------------------------------------------------------

def ajuda() -> str:
    return (
        "<b>Cheias do Vale do Itajaí</b>\n\n"
        "/rua <i>cidade rua</i> — a partir de quantos metros a sua rua alaga\n"
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
    leituras = base.leituras_da_cidade(cidade["id"], agora)
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
        # A IDADE DO MAIS VELHO, não a do mais novo. O número exibido é o MAIOR
        # de cada janela, e ele pode vir de um pluviômetro parado há horas. Com
        # a idade do mais novo, "80 mm em 24 h · há 5 min" saía de uma leitura
        # de seis horas atrás — e quem lê conclui que está chovendo forte agora.
        # A idade tem de ser um limite: nenhuma leitura aqui é mais velha que
        # isto.
        rodape += f" · {texto_idade(max(idades))}"
        if len(idades) > 1 and max(idades) - min(idades) >= DIFERENCA_DE_IDADE_MIN:
            rodape += f" no mais velho, {texto_idade(min(idades))} no mais novo"
    linhas.append(rodape)
    if len(todas) > len(boas):
        linhas.append(f"\n{len(todas) - len(boas)} descartado(s) por dado inconsistente na fonte.")
    return linhas


def resposta_previsao(base: Base, cidade: dict, agora: datetime) -> list[str]:
    linhas = [f"<b>Se o pico em {notificador.esc(cidade['nome'])} fosse agora</b>"]
    leituras = base.leituras_da_cidade(cidade["id"], agora)
    if len(leituras) != 1:
        motivo = (
            "esta cidade tem mais de uma régua e não dá para dizer qual representa o rio"
            if leituras else "não há leitura ao vivo desta cidade"
        )
        linhas.append(f"\nNão dá para calcular: {motivo}.")
        return linhas

    l = leituras[0]
    idade = idade_min(l.get("medido_em"), agora)
    if idade is not None and idade > IDADE_MAXIMA_PREVISAO_MIN:
        linhas.append(
            f"\nA última leitura de {notificador.esc(cidade['nome'])} é de "
            f"{texto_idade(idade)}: <b>3,52</b>".replace("<b>3,52</b>", metros(l["nivel_m"]))
        )
        linhas.append(
            "\n\n<b>Não dá para calcular com ela.</b> Esta conta parte de "
            "\"se o pico fosse agora\", e com leitura velha o \"agora\" é falso — "
            "os horários sairiam no passado, com cara de previsão. "
            f"Volte quando a coleta se recuperar, ou veja {SITE}."
        )
        return linhas
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

        # Janela inteiramente no passado não é previsão. Acontece nos trechos
        # curtos — Apiúna→Indaial é de 1 h — quando a leitura já tem algumas
        # horas. Dizer "por volta de" um horário que já passou faz a pessoa
        # procurar no relógio uma água que, se veio, veio antes.
        if fim < agora:
            horario = f"janela já passou ({quando(fim)})"
        elif inicio == fim:
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


#: Quantas ruas cabem numa mensagem. O Telegram recusa acima de 4096
#: caracteres, e uma resposta recusada é silêncio — o pior resultado possível.
MAX_RUAS = 10


def nome_do_ponto(c: dict) -> str:
    """`Rua São Rafael (final da rua)` — o ponto faz parte da identidade."""
    ponto = c.get("ponto")
    return f"{c['rua']} ({ponto})" if ponto and ponto != c["rua"] else c["rua"]


def resposta_rua(base: Base, cidade: dict | None, termo: str, agora: datetime) -> list[str]:
    """
    "A partir de quantos metros a minha rua alaga?"

    É a pergunta que a pessoa realmente faz. Tudo o mais que o bot responde
    está em metros de régua, que é a linguagem de quem opera o rio.

    Não há previsão nenhuma aqui: é leitura de tabela. A tabela diz o que
    acontece SE o rio chegar naquele nível; quem diz se vai chegar é a Defesa
    Civil.
    """
    e = notificador.esc
    if not termo:
        nomes = ", ".join(c["nome"] for c in base.cidades_com_ruas())
        return [
            "<b>Cotas de rua</b>\n\n"
            "Diga a cidade e a rua. Exemplo: <code>/rua Blumenau São Rafael</code>\n\n"
            f"Cidades com cotas levantadas: {e(nomes) or 'nenhuma ainda'}.\n"
            "Também funciona sem a cidade: <code>/rua Beira Rio</code>."
        ]

    achadas = base.ruas(cidade["id"] if cidade else None, termo)
    onde = f" em {e(cidade['nome'])}" if cidade else ""
    if not achadas:
        quantas = len(base.cotas_ruas) if cidade is None else len(base.ruas(cidade["id"], ""))
        return [
            f"Nenhuma rua com “{e(termo)}”{onde} entre as levantadas.\n\n"
            "<b>Isso não quer dizer que a sua rua não alaga.</b> Quer dizer que ela "
            "não está nesta lista, que está longe de completa — são poucas centenas "
            "de pontos, vindos do que as Defesas Civis publicaram.\n\n"
            "Quem sabe se a sua rua alaga é a Defesa Civil do seu município."
        ]

    # O nível de agora só entra quando a cidade tem UMA régua: com várias, não
    # dá para dizer qual delas representa o rio, e "faltam 2,30 m" sairia
    # medido contra a régua errada.
    niveis: dict[str, tuple[float, float | None]] = {}
    #: Por que a cidade ficou sem comparação. Silêncio aqui parece esquecimento;
    #: a pessoa perguntou "a minha rua alaga com quantos metros" e a pergunta
    #: seguinte é sempre "e onde está o rio agora".
    sem_nivel: dict[str, str] = {}
    for c in {x["cidade"] for x in achadas}:
        leituras = base.leituras_da_cidade(c, agora)
        if len(leituras) == 1 and isinstance(leituras[0].get("nivel_m"), (int, float)):
            niveis[c] = (float(leituras[0]["nivel_m"]),
                         idade_min(leituras[0].get("medido_em"), agora))
        elif len(leituras) > 1:
            sem_nivel[c] = (f"tem {len(leituras)} réguas com zeros diferentes, e nenhuma "
                            "delas sozinha é “o nível da cidade”")
        else:
            sem_nivel[c] = "não aparece na fonte de tempo real que coletamos"

    nomes_cidade = {c["id"]: c["nome"] for c in base.cidades()}
    linhas = [f"<b>Cotas de rua</b> — “{e(termo)}”{onde}"]

    for c in achadas[:MAX_RUAS]:
        rotulo = e(nome_do_ponto(c))
        cidade_nome = e(nomes_cidade.get(c["cidade"], c["cidade"]))
        if c["cota_m"] is None:
            linhas.append(f"\n\n<b>{rotulo}</b> — {cidade_nome}"
                          f"\n<i>{e(c.get('nota') or 'a fonte não publica a cota exata')}</i>")
            continue
        linhas.append(f"\n\n<b>{rotulo}</b> — {cidade_nome}"
                      f"\nAlaga a partir de <b>{metros(c['cota_m'])}</b>")
        # A máxima é informação, não gatilho: quem decide sair de casa decide
        # pela mínima, que é quando a água chega à rua.
        if isinstance(c.get("cota_max_m"), (int, float)):
            linhas.append(f" · toda a rua a {metros(c['cota_max_m'])}")
        # O abrigo vem logo abaixo da cota porque é a outra metade da mesma
        # decisão: a cota diz que é hora de sair, o abrigo diz para onde. Só
        # Blumenau tem, por enquanto, e é do PDF oficial da Defesa Civil.
        if c.get("abrigo"):
            codigo = f" ({e(c['abrigo_codigo'])})" if c.get("abrigo_codigo") else ""
            linhas.append(f"\nAbrigo: <b>{e(c['abrigo'])}</b>{codigo}")
        # A ressalva sai JUNTO do número, e não só quando ele falta: Rio do Sul
        # publica ruas alagando abaixo da menor cota da cidade, e sem isto o bot
        # diria "já foi alcançado" com tempo bom.
        if c.get("nota"):
            linhas.append(f"\n<i>{e(c['nota'])}</i>")
        atual = niveis.get(c["cidade"])
        # Registro marcado para não mover aviso não vira "já foi alcançado":
        # a comparação daria uma frase assustadora a partir de um número que o
        # próprio registro diz não estar conferido. A nota, acima, explica.
        if c.get("usar_para_aviso") is False:
            atual = None
        if atual:
            falta = round(c["cota_m"] - atual[0], 2)
            if falta > 0:
                linhas.append(f"\nO rio está em {metros(atual[0])} ({texto_idade(atual[1])}) — "
                              f"faltam <b>{metros(falta)}</b> de subida.")
            else:
                linhas.append(f"\n⚠️ O rio está em {metros(atual[0])} ({texto_idade(atual[1])}) — "
                              "este nível <b>já foi alcançado</b>.")

    # A explicação sai UMA vez por cidade, no fim: repetida em cada rua ocupava
    # metade da mensagem. Mas sai — silêncio aqui parece esquecimento, e a
    # pergunta seguinte a "minha rua alaga a quantos metros" é sempre "e onde
    # está o rio agora".
    faltando = sorted({c["cidade"] for c in achadas[:MAX_RUAS]} & set(sem_nivel))
    for cid in faltando:
        linhas.append(f"\n\n<i>Quanto falta subir em {e(nomes_cidade.get(cid, cid))}, não dá "
                      f"para dizer: a cidade {sem_nivel[cid]}.</i>")

    if len(achadas) > MAX_RUAS:
        linhas.append(f"\n\n<i>Mais {len(achadas) - MAX_RUAS} rua(s) casaram. "
                      "Escreva o nome com mais letras para reduzir.</i>")

    if cidade is None and len({c["cidade"] for c in achadas}) > 1:
        linhas.append("\n\n⚠️ <b>Os resultados são de cidades diferentes.</b> Cada cidade tem "
                      "sua própria régua: estes metros <b>não se comparam</b> entre si.")

    linhas.append("\n\n<i>Cotas são aproximadas e envelhecem: obra e enchente nova mudam os "
                  "valores. Isto é leitura de tabela, não previsão — não diz se o rio vai "
                  "chegar nesse nível.</i>")
    return linhas


ORDEM_COTAS = ("atencao", "alerta", "emergencia", "inundacao", "inundacao_historica")


def ordenar_cotas(cotas: dict) -> list[tuple[str, float]]:
    """Na ordem em que a água sobe; cota nova, ainda sem posição, vai no fim."""
    conhecidas = [k for k in ORDEM_COTAS if k in cotas]
    outras = sorted(k for k in cotas if k not in ORDEM_COTAS)
    return [(k, cotas[k]) for k in conhecidas + outras]


def linhas_de_cotas(cotas: dict) -> list[str]:
    return [f"\n{ROTULO_COTA.get(k, k)}: <b>{metros(v)}</b>" for k, v in ordenar_cotas(cotas)]


#: Quanto da observação da cidade cabe na resposta de /cotas. O texto inteiro de
#: algumas cidades passa de mil caracteres e empurraria as réguas para fora do
#: limite do Telegram; cortado, ele vira convite para abrir o site.
LIMITE_OBSERVACAO = 600


def resposta_cotas(base: Base, cidade: dict) -> list[str]:
    linhas = [f"<b>{notificador.esc(cidade['nome'])}</b> — cotas de referência"]
    cotas = cidade.get("cotas_m") or {}
    reguas = base.reguas_com_cota(cidade["id"])

    if cotas:
        linhas.extend(linhas_de_cotas(cotas))
        if cidade.get("regua"):
            linhas.append(f"\n\nRégua: {notificador.esc(cidade['regua'])}")
    elif not reguas:
        linhas.append("\nAs cotas desta cidade ainda não foram levantadas.")
        return linhas

    if reguas:
        if cotas:
            linhas.append("\n\n<b>Outras réguas desta cidade</b>")
        else:
            # Cidade sem cota única: são as réguas que têm cota, cada uma com
            # seu zero. Escolher uma como "a cota da cidade" inventaria um
            # número que não existe em documento nenhum.
            plural = "s" if len(reguas) > 1 else ""
            linhas.append(f"\n\n{len(reguas)} régua{plural} com cota oficial cadastrada:")
        for r in reguas:
            marca = "" if r["alerta_automatico"] else " *"
            valores = " · ".join(
                f"{ROTULO_COTA.get(k, k)} {metros(v)}"
                for k, v in ordenar_cotas(r["cotas"])
            )
            # Uma linha por régua, e não um bloco: com onze réguas, o bloco
            # estourava o limite do Telegram e a mensagem chegava cortada
            # justamente na última régua.
            linhas.append(f"\n\n<b>{notificador.esc(r['nome'])}</b>{marca}\n{valores}")

        fontes = []
        for r in reguas:
            if r["fonte"] and r["fonte"] not in fontes:
                fontes.append(r["fonte"])
        # Cota sem fonte é número solto: quem quiser conferir precisa saber de
        # que documento ele saiu.
        for f in fontes:
            linhas.append(f"\n\n<i>Fonte: {notificador.esc(f)}</i>")

        if any(not r["alerta_automatico"] for r in reguas):
            # A explicação sai UMA vez, no fim: repetida em cada régua ela
            # ocupava metade da mensagem.
            linhas.append("\n\n<i>* Régua no estuário: sobe e desce com a maré, e passa da "
                          "cota de atenção em dia de sol. A cota é oficial, mas cruzá-la nessas "
                          "réguas, sozinha, não quer dizer que há cheia — por isso o bot não "
                          "dispara aviso automático por elas.</i>")

    linhas.append("\n\n<i>Cada régua tem seu próprio zero: estes metros não se "
                  "comparam com os de outra régua nem com os de outra cidade.</i>")
    # A observação da cidade é onde moram as ressalvas que o número sozinho não
    # conta — em Brusque, que a cota de 4,80 m é a via marginal JÁ alagando, e
    # que não existe faixa de aviso antes dela. O site já mostrava isso; o bot,
    # que é o canal de quem consulta às três da manhã, mostrava só os números.
    observacao = (cidade.get("observacao") or "").strip()
    if observacao:
        if len(observacao) > LIMITE_OBSERVACAO:
            observacao = observacao[:LIMITE_OBSERVACAO].rsplit(" ", 1)[0] + "… (o resto no site)"
        linhas.append(f"\n\n<i>{notificador.esc(observacao)}</i>")

    return linhas
def nome_curto(leitura: dict) -> str:
    """
    O nome da régua sem a calha repetida em todas.

    "DC-07 Ribeirão da Murta - Portal" vira "DC-07 Portal": num panorama de
    treze linhas, o que muda entre elas é o local, não o nome do rio. O código
    fica, porque é por ele que se acha a régua na página da Defesa Civil.
    """
    titulo = (leitura.get("estacao") or "").strip()
    codigo = ""
    if titulo[:2].isalpha() and titulo[2:3] == "-":
        codigo, _, titulo = titulo.partition(" ")
    # A fonte separa calha e local por hífen, comum ou longo.
    for sep in (" – ", " - ", " — "):
        if sep in titulo:
            titulo = titulo.split(sep)[-1]
            break
    return f"{codigo} {titulo}".strip() if codigo else titulo


def resposta_rios(base: Base, agora: datetime) -> list[str]:
    leituras = base.ultimo.get("leituras") or []
    if not leituras:
        return ["Não há coleta disponível agora."]
    linhas = ["<b>Tudo que está sendo medido</b>"]
    por_cidade: dict[str, list[dict]] = {}
    for l in leituras:
        por_cidade.setdefault(str(l.get("cidade")), []).append(l)
    cidades = base.cidades()
    nomes = {c["id"]: c["nome"] for c in cidades}
    # Na ordem do RIO, montante -> jusante: o Açu inteiro (terminando na foz,
    # Itajaí) e depois o Mirim — a mesma sequência das telas. Alfabético
    # embaralhava Rio do Sul (cabeceira) com Brusque. A régua da foz herda a
    # posição da primeira aparição (fim do Açu); cidade fora do cadastro vai ao
    # fim.
    ordem_rio: dict[str, int] = {}
    for i, c in enumerate(cidades):
        ordem_rio.setdefault(c["id"], i)
    for cid, ls in sorted(por_cidade.items(),
                          key=lambda kv: ordem_rio.get(kv[0], len(ordem_rio))):
        nome = nomes.get(cid, cid)
        # Junta primária e resgate antes de decidir: Blumenau tem duas leituras
        # da MESMA régua (Defesa Civil + AlertaBlu) e não pode virar "2 réguas
        # que não se comparam".
        ls = por_regua(ls, agora)
        if len(ls) == 1:
            l = ls[0]
            idade = idade_min(l.get("medido_em"), agora)
            linhas.append(f"\n<b>{notificador.esc(nome)}</b>: {metros(l['nivel_m'])}"
                          f" · {texto_idade(idade)}")
            continue

        # Cidade com mais de uma régua NÃO tem um número.
        #
        # Aqui havia `max(ls, key=nivel_m)`: elegia o maior metro como se fosse
        # o nível da cidade, comparando réguas de zeros diferentes — a operação
        # que todo o resto do projeto recusa (`leituraDaCidade` devolve nulo,
        # `resposta_previsao` recusa, `cotas_da_leitura` recusa). A ressalva ao
        # lado não desfazia o número: em Itajaí saía "4,88 m" num dia calmo,
        # que é a régua de Limoeiro, 20 km rio acima e com zero mais alto — e,
        # pior, uma subida de metro e meio nas outras nove não mudava o número,
        # porque o vencedor é sempre a mesma régua.
        linhas.append(f"\n<b>{notificador.esc(nome)}</b> — {len(ls)} réguas, "
                      "com zeros diferentes (não se comparam):")
        for l in sorted(ls, key=lambda x: x.get("estacao", "")):
            idade = idade_min(l.get("medido_em"), agora)
            linhas.append(f"\n  {metros(l['nivel_m'])} — {notificador.esc(nome_curto(l))}"
                          f" · {texto_idade(idade)}")
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

    if comando in ("rua", "ruas", "minharua"):
        cidade, resto = base.separar_cidade(argumento)
        return "".join(resposta_rua(base, cidade, resto.strip(), agora)) + RODAPE

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

    if comando in ("nivel", "chuva", "cotas"):
        # Itajaí aparece nos dois rios. Nível, chuva e cota são por CIDADE — a
        # pergunta "quanto choveu em Itajaí" tem uma resposta só, e repeti-la
        # duas vezes fazia a mensagem parecer defeito. A cota entrou aqui
        # quando passou a listar as réguas: as onze de Itajaí, com os ribeirões
        # junto, saem de uma vez e não picadas por calha. Previsão continua
        # saindo uma vez por rio, porque ela É por rio.
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
    ("rua", "A partir de quantos metros a sua rua alaga"),
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
        print(f"não deu para registrar o menu de comandos: {notificador.sem_segredo(e)}",
              file=sys.stderr)


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
        # Só o código: o corpo da resposta do Telegram repete a URL chamada.
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


def eh_timeout(erro: BaseException) -> bool:
    """
    Comparação por NOME de classe, de propósito: assim este módulo continua
    importável sem o `requests` instalado, como os testes de resposta exigem.
    """
    return type(erro).__name__ in ("ReadTimeout", "ConnectTimeout", "Timeout")


def aviso_de_falha(erro: BaseException, seguidas: int) -> str | None:
    """
    O que escrever no log depois de uma rodada que falhou — ou nada.

    Timeout do long polling é rotina até `TIMEOUTS_TOLERADOS` seguidos; daí em
    diante vira linha de log, porque o bot está sem falar com o Telegram. Todo
    o resto sai na hora: erro que ninguém previu é justamente o que precisa
    aparecer.
    """
    if eh_timeout(erro):
        # Na travessia do limite, e depois de tantas em tantas: uma queda longa
        # do Telegram escreveria uma linha a cada meio minuto, e log que rola
        # sozinho esconde tanto quanto log que não existe.
        primeira = seguidas == TIMEOUTS_TOLERADOS
        if seguidas < TIMEOUTS_TOLERADOS or not (primeira or seguidas % REPETE_AVISO == 0):
            return None
        return (f"sem resposta do Telegram em {seguidas} chamadas seguidas "
                f"({type(erro).__name__}) — o bot está sem receber mensagens")
    # O texto do erro de rede carrega a URL chamada, e a URL do Telegram carrega
    # o token no caminho. Sem esta limpeza, `journalctl` guarda a credencial em
    # texto puro — e log é justamente o que se copia e cola para pedir ajuda.
    return f"erro na rodada: {notificador.sem_segredo(erro)}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--uma-vez", action="store_true", help="processa a fila e sai")
    args = ap.parse_args()

    if not notificador.configurado():
        print("Configure TELEGRAM_BOT_TOKEN no .env.", file=sys.stderr)
        return 1

    estado = le_estado()
    if args.uma_vez:
        # Sem este try, uma falha de rede sobe até o topo e o Python imprime o
        # traceback inteiro — com a URL do Telegram, que carrega o token. E
        # `--uma-vez` é o que roda em cron e o que a gente digita para depurar,
        # ou seja, exatamente a saída que acaba colada em outro lugar.
        try:
            grava_estado(rodada(estado, espera=0))
        except Exception as e:
            print(f"não deu para processar a fila: {notificador.sem_segredo(e)}",
                  file=sys.stderr)
            return 1
        return 0

    registrar_menu()
    novo_offset = descartar_pendentes()
    if novo_offset:
        estado["offset"] = novo_offset
        grava_estado(estado)

    print("bot escutando. Ctrl+C para parar.")
    seguidas = 0
    while True:
        try:
            estado = rodada(estado, espera=ESPERA_S)
            grava_estado(estado)
            seguidas = 0
        except KeyboardInterrupt:
            print("\nparando.")
            return 0
        except Exception as e:  # rede caindo não pode matar o bot
            seguidas += 1
            aviso = aviso_de_falha(e, seguidas)
            if aviso:
                print(aviso, file=sys.stderr)
            # Timeout já gastou o tempo de espera pendurado na conexão; dormir
            # de novo seria mais tempo de bot calado sem motivo.
            if not eh_timeout(e):
                time.sleep(10)


if __name__ == "__main__":
    sys.exit(main())
