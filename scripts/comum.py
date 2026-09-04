"""Utilidades compartilhadas pelos scripts de coleta e análise.

Regras que valem para todos os scripts (CLAUDE.md):

* idempotência: rodar duas vezes não duplica nem apaga registro;
* nada de credencial em código — chaves vêm do `.env`, que está no `.gitignore`;
* todo request se identifica no `User-Agent` e respeita intervalo entre chamadas.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"

#: Identificação do projeto em toda requisição (exigência do CLAUDE.md).
#:
#: SEM ACENTO, E ISSO NÃO É DESCUIDO — é o conserto de um bug provado em
#: 04/09/2026. Cabeçalho HTTP é ASCII; quando o valor tem caractere fora dele,
#: o `requests` codifica em **latin-1**, e "ó" vira o byte solto 0xF3 — que não
#: é UTF-8 válido. Servidor com borda que valida UTF-8 no cabeçalho recusa a
#: requisição antes de a aplicação ver: HTTP 400, corpo vazio, sem
#: Content-Type. Foi o que a API de Taió (Uniparking) fez, e o teste que
#: separou as três formas do mesmo caractere mostrou por quê:
#:
#:     User-Agent com "...\xc3\xb3..." (ó em UTF-8, dois bytes)  -> 200
#:     User-Agent com "...\xf3..."     (ó em latin-1, um byte)   -> 400
#:     User-Agent só ASCII                                       -> 200
#:
#: O bug estava latente desde que esta linha foi escrita e valia para os onze
#: scripts que importam daqui — as outras fontes toleravam o byte inválido, a
#: de Taió não. `teste_comum.py` trava o ASCII para não voltar.
USER_AGENT = (
    "enchentes-vale-itajai/0.1 (projeto aberto de dados de enchentes; "
    "contato via repositorio GitHub)"
)

#: Intervalo mínimo entre chamadas à mesma fonte, em segundos.
INTERVALO_S = 1.5

_ultima_chamada = 0.0


def espera_turno() -> None:
    """Segura a chamada para não sobrecarregar servidor público."""
    global _ultima_chamada
    agora = time.monotonic()
    resta = INTERVALO_S - (agora - _ultima_chamada)
    if resta > 0:
        time.sleep(resta)
    _ultima_chamada = time.monotonic()


# --- HTTP -------------------------------------------------------------------
#
# Toda coleta passa por aqui. Antes cada script fazia `requests.get` seco: um
# soluço de rede num servidor municipal — que é o que estas fontes são —
# derrubava a coleta inteira, e no cron, encadeado com `&&`, derrubava junto a
# publicação. Quinze minutos sem número novo no site por causa de um TCP reset.
#
# A ideia é do Fila-Disney, e o motivo dele vale ainda mais aqui: um ciclo
# perdido é histórico perdido para sempre. Numa cheia, o ciclo perdido pode ser
# justamente o do pico — o dado que depois faltaria para calibrar o tempo de
# descida da próxima.

def regua_de(leitura: dict) -> str:
    """
    Identidade da RÉGUA de uma leitura — não da linha.

    A mesma régua aparece DUAS vezes quando há fonte de resgate: Blumenau vem da
    Defesa Civil de Itajaí e, quando essa esfria, do AlertaBlu. O resgate carrega
    `resgate_de` com o título da primária que ele cobre, e por ele as duas contam
    como UMA régua. Sem `resgate_de`, a régua é o próprio título — e as onze de
    Itajaí seguem distintas, cada uma por si.

    MORA AQUI, e não em um dos consumidores, porque os dois precisam da MESMA
    resposta e a divergência entre eles já custou caro: o vigia contava por
    régua e o `alerta_cotas` contava por linha, então via "Blumenau tem 2
    réguas", recusava a cota da cidade e **Blumenau ficava sem aviso automático
    nenhum** — a cidade com 97 registros históricos desde 1852. Ninguém percebia
    porque o mapa continuava pintando a cor certa; só o Telegram calava.
    """
    return leitura.get("resgate_de") or leitura.get("estacao", "?")


#: Faixa em que um número pode ser nível de rio nesta bacia.
#:
#: Nenhuma régua daqui chega perto de 25 m — o recorde de Blumenau, em 1880, é
#: 17,10 m. Zero ou negativo não é leitura: é sensor mudo ou defeito de
#: análise. A faixa vive aqui porque o site (`web/src/dados/tempoReal.ts`) usa
#: os mesmos limites, e as duas implementações divergirem em silêncio é como
#: uma delas passar a aceitar o que a outra recusa.
NIVEL_MINIMO_M = 0.0
NIVEL_MAXIMO_M = 25.0


def nivel_plausivel(valor) -> bool:
    """Se este número pode ser o nível de um rio da bacia."""
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and NIVEL_MINIMO_M < float(valor) < NIVEL_MAXIMO_M)


HTTP_TIMEOUT_S = 30
HTTP_TENTATIVAS = 3
HTTP_BACKOFF_BASE_S = 2


def baixar(
    url: str,
    *,
    tentativas: int = HTTP_TENTATIVAS,
    dormir=time.sleep,
    transporte=None,
) -> str:
    """
    Baixa a página, insistindo quando vale a pena.

    As três regras que decidem se insiste:

    * **429** — o servidor pediu calma. Espera o `Retry-After` que ele mandou,
      ou o backoff, o que for maior. Ignorar isso é o caminho para levar bloqueio
      de uma fonte pública que estamos usando de graça.
    * **4xx que não é 429** — não vai melhorar sozinho. Página que mudou de
      endereço não aparece na segunda tentativa; insistir só atrasa o resto.
    * **conexão recusada, DNS quebrado, rota inexistente** — também não melhora
      esperando. Duas tentativas e desiste, em vez de empatar a execução por um
      minuto enquanto a rede está fora.

    `dormir` e `transporte` entram por parâmetro para o teste poder rodar sem
    rede e sem esperar de verdade.
    """
    if transporte is None:
        import requests

        def transporte(u, cabecalhos, timeout):  # noqa: E306
            return requests.get(u, headers=cabecalhos, timeout=timeout)

    import requests

    cabecalhos = {"User-Agent": USER_AGENT}
    ultimo: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = transporte(url, cabecalhos, HTTP_TIMEOUT_S)
            if resposta.status_code == 429:
                pedido = resposta.headers.get("Retry-After") if resposta.headers else None
                try:
                    espera = float(pedido) if pedido else HTTP_BACKOFF_BASE_S**tentativa
                except (TypeError, ValueError):
                    espera = HTTP_BACKOFF_BASE_S**tentativa
                ultimo = requests.HTTPError("429 Too Many Requests")
                if tentativa < tentativas:
                    dormir(espera)
                continue
            resposta.raise_for_status()
            return resposta.text
        except (requests.RequestException, ValueError) as exc:
            ultimo = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                break
            if isinstance(exc, requests.ConnectionError) and tentativa >= 2:
                break
            if tentativa < tentativas:
                dormir(HTTP_BACKOFF_BASE_S**tentativa)

    raise requests.RequestException(f"{url}: {ultimo}") from ultimo


def carrega_env(caminho: Path | None = None) -> None:
    """Lê um `.env` simples (CHAVE=valor) para o ambiente, sem sobrescrever."""
    arquivo = caminho or (RAIZ / ".env")
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


def le_json(nome: str) -> Any:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def grava_json(nome: str, conteudo: Any) -> None:
    """Grava com quebra de linha final e acentos preservados.

    Escreve num arquivo temporário e só então substitui o original: se o
    processo morrer no meio, o arquivo bom continua lá. Estes JSONs são a
    fonte de verdade do site — perder um deles é perder o projeto.
    """
    destino = DADOS / nome
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    temporario.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporario.replace(destino)


#: Chave de ordenação montante -> jusante que aguenta rio ramificado. Em rio em
#: fila, `ordem` é 1..N. Em rio em árvore (o Açu), `ordem` é null de propósito e
#: a ordem de exibição é a do arquivo (cabeceiras -> tronco) — o sort estável
#: preserva essa ordem quando a chave é constante. None não se compara com None,
#: então cai para 0.
def chave_montante(c: dict[str, Any]) -> float:
    o = c.get("ordem")
    return o if isinstance(o, (int, float)) else 0


def cidades(rio: str | None = None) -> list[dict[str, Any]]:
    """Cidades de `estacoes.json`, em ordem montante -> jusante."""
    estacoes = le_json("estacoes.json")
    saida: list[dict[str, Any]] = []
    for rio_id, dados in estacoes["rios"].items():
        if rio is not None and rio_id != rio:
            continue
        for cidade in sorted(dados["cidades"], key=chave_montante):
            saida.append({**cidade, "rio": rio_id})
    return saida


# --- Estações de tempo real -------------------------------------------------
#
# A ligação entre o título que a Defesa Civil publica e o par (rio, cidade)
# fica em `estacoes.json`, não aqui: é dado, não código, e quem mantém os dados
# precisa poder acrescentar estação sem mexer em Python. As expressões abaixo
# são só a rede de segurança para um título que ainda não esteja cadastrado.

import re as _re

_FALLBACK: list[tuple[str, str | None, str]] = [
    # DC-00 é pluviômetro puro: aparece só na página de chuvas, sem régua.
    (r"^DC-00\b", None, "itajai"),
    (r"^DC-0[12]\b", "itajai-acu", "itajai"),
    (r"^DC-11\b", "itajai-acu", "ilhota"),
    (r"^DC-0[3456]\b", "itajai-mirim", "itajai"),
    (r"^DC-10\b", "itajai-mirim", "itajai"),
    (r"^DC-07\b|^DC-09\b", "ribeirao-murta", "itajai"),
    (r"^DC-08\b", "ribeirao-canhanduba", "itajai"),
    (r"^Brusque", "itajai-mirim", "brusque"),
    (r"^Blumenau", "itajai-acu", "blumenau"),
    (r"^Rio do Sul", "itajai-acu", "rio-do-sul"),
]


def estacoes_tempo_real() -> list[dict[str, Any]]:
    return le_json("estacoes.json").get("estacoes_tempo_real", [])


def estacao_por_titulo(titulo: str) -> dict[str, Any] | None:
    """
    A estação cadastrada que corresponde a este título.

    Casa pelo título exato e, se não achar, pelo código DC-NN no começo — a
    Defesa Civil já mudou o texto depois do código mais de uma vez, e o código
    é a parte estável.
    """
    cadastradas = estacoes_tempo_real()
    for e in cadastradas:
        if e.get("titulo") == titulo:
            return e
    codigo = _re.match(r"^(DC-\d{2})\b", titulo or "")
    if codigo:
        for e in cadastradas:
            if e.get("codigo") == codigo.group(1):
                return e
    return None


def classificar_estacao(titulo: str) -> tuple[str | None, str | None]:
    """(rio, cidade) da estação, ou (None, None) quando o título é desconhecido."""
    e = estacao_por_titulo(titulo)
    if e:
        return e.get("rio"), e.get("cidade")
    for padrao, rio, cidade in _FALLBACK:
        if _re.search(padrao, titulo or ""):
            return rio, cidade
    return None, None


def cota_da_estacao(titulo: str) -> tuple[float | None, str | None]:
    """
    Cota de referência DESTA régua, quando cadastrada em `estacoes.json`.

    Existe porque a cota da cidade não serve para uma cidade com várias réguas:
    os zeros são diferentes, e aplicar a mesma a todas criaria evento onde não
    há e esconderia onde há.
    """
    e = estacao_por_titulo(titulo)
    for chave in ("atencao", "alerta", "emergencia", "inundacao"):
        valor = (e or {}).get("cotas_m", {}).get(chave)
        if isinstance(valor, (int, float)):
            return float(valor), chave
    return None, None


def cota_de_referencia(rio: str, cidade: str) -> tuple[float | None, str | None]:
    """
    Cota a partir da qual vale considerar que há cheia, pela CIDADE.

    Prefere 'atencao', depois 'alerta', depois 'inundacao'. Devolve (None, None)
    quando a cidade não tem cota levantada — e nesse caso quem chama deve pedir
    um limiar explícito em vez de inventar um.
    """
    estacoes = le_json("estacoes.json")
    rio_dados = estacoes["rios"].get(rio)
    if not rio_dados:
        return None, None
    for c in rio_dados["cidades"]:
        if c["id"] != cidade:
            continue
        for chave in ("atencao", "alerta", "emergencia", "inundacao"):
            if chave in c.get("cotas_m", {}):
                return float(c["cotas_m"][chave]), chave
    return None, None
