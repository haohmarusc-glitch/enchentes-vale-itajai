#!/usr/bin/env python3
"""Coleta contínua dos níveis dos rios, para guardar a série de uma cheia.

Diferença para `coleta_itajai.py`, que imprime uma leitura por vez: este
acumula. Grava uma linha por medição em `data/tempo-real/AAAA-MM.ndjson`, para
que depois `extrair_picos.py` encontre o pico de cada cidade com data e hora —
que é o que falta em quase todos os registros de `enchentes.json`.

Duas decisões que mantêm o arquivo pequeno e correto:

* **Deduplica pelo carimbo da medição.** A página atualiza a cada 15-30 min. Se
  o cron rodar de 5 em 5, dois terços das coletas trazem a MESMA medição. Só
  entra linha nova quando a fonte publicou leitura nova, então o arquivo
  reflete medições, não a frequência do cron.
* **Um arquivo por mês, uma linha por leitura.** ~110 bytes por linha; com 14
  estações a cada 15 min, algo como 40 MB por ano — e `--compactar` reduz os
  meses fechados a cerca de um décimo disso.

Os `.ndjson` ficam fora do git (veja o `.gitignore`): são matéria-prima, e o
que vale versionar é o pico destilado deles, em `enchentes.json`.

`ultimo.json` também NÃO é versionado no `main`. Ele é publicado à parte, no
branch `tempo-real`, por `scripts/publicar_tempo_real.sh` — é de lá que o site
busca o nível ao vivo. Ao lado dele vai `serie-recente.json`, as últimas horas
de nível por cidade recortadas da série ndjson, para a linha do tempo do site.
Rode os dois em sequência no cron:

    */15 * * * * cd /caminho/do/repo && python3 scripts/coleta_niveis.py >> /var/log/niveis.log 2>&1 \
                 && scripts/publicar_tempo_real.sh >> /var/log/niveis.log 2>&1

Uso:
    python3 scripts/coleta_niveis.py              # coleta e acumula
    python3 scripts/coleta_niveis.py --no-save    # só mostra
    python3 scripts/coleta_niveis.py --compactar  # gzip nos meses já fechados

No cron, de 15 em 15 minutos:
    */15 * * * * cd /caminho/do/repo && python3 scripts/coleta_niveis.py >> /var/log/niveis.log 2>&1
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from comum import DADOS, USER_AGENT, espera_turno

SERIE = DADOS / "tempo-real"
ULTIMO = SERIE / "ultimo.json"
SERIE_RECENTE = SERIE / "serie-recente.json"

#: Quantas horas da série o site recebe para desenhar a linha do tempo. 48 para
#: um slider de "últimas 24h" ter folga, sem virar um arquivo grande no celular.
HORAS_SERIE_RECENTE = 48

#: `medido_em` é hora de Brasília sem fuso (regra do projeto). Para recortar a
#: janela, o "agora" tem de estar no MESMO relógio — senão a série entraria
#: deslocada, o mesmo erro de fuso que já custou uma sessão.
FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


def baixar_niveis() -> list[dict]:
    """Leituras da página da Defesa Civil de Itajaí, já mapeadas para cidades."""
    try:
        import requests  # noqa: F401  (só para dar erro claro se faltar)
    except ImportError:  # pragma: no cover
        sys.exit("Para baixar é preciso o requests: pip install -r scripts/requirements.txt")

    # Reaproveita o analisador de coleta_itajai.py — é a mesma página.
    from coleta_itajai import URL, parse
    from comum import baixar

    espera_turno()
    return parse(baixar(URL))


def baixar_chuva() -> tuple[list[dict], bool]:
    """
    Chuva acumulada, da segunda página da mesma fonte.

    Falha aqui NUNCA derruba a coleta de nível. O nível é o que decide se
    alguém sai de casa; a chuva é contexto valioso, mas secundário. Uma página
    de chuva fora do ar não pode apagar o nível do site — devolve lista vazia,
    e a tela simplesmente não mostra chuva.
    """
    try:
        from coleta_chuva import URL as URL_CHUVA, parse as parse_chuva
        from comum import baixar

        espera_turno()
        return parse_chuva(baixar(URL_CHUVA)), True
    except Exception as e:
        print(f"aviso: chuva não coletada ({e}) — o nível segue normalmente.",
              file=sys.stderr)
        # A lista vazia vai junto com a marca de que ela é FALHA, não ausência.
        # Sem isso, `chuva: []` significa as duas coisas ao mesmo tempo, e a
        # tela mostra "sem pluviômetro" em toda cidade quando a fonte caiu — o
        # que, no meio de uma chuva, lê-se como "não está chovendo".
        return [], False


def baixar_chuva_sc() -> list[dict]:
    """
    A chuva da Rede Integrada da Defesa Civil de SC, que cobre onze cidades sem
    pluviômetro na fonte de Itajaí — e resgata Brusque e Rio do Sul, onde a
    fonte de Itajaí publica série quebrada (todas as janelas em 0,0 com 0,4 mm
    nos últimos 10 min, o que o validador marca como incoerente e a tela recusa).

    Falha aqui não pode derrubar nada: devolve lista vazia e o resto segue. Só
    chuva — o motivo de o nível não entrar está em `coleta_chuva_sc.py`.
    """
    try:
        from coleta_chuva_sc import baixar_estacoes, converter

        leituras, _recusadas = converter(baixar_estacoes())
        return leituras
    except Exception as e:
        print(f"aviso: chuva da Defesa Civil de SC não coletada ({e}).", file=sys.stderr)
        return []


def baixar_chuva_cemaden() -> list[dict]:
    """
    A chuva dos pluviômetros do CEMADEN — a rede mais densa da bacia (chuva por
    bairro; Blumenau sozinha tem catorze ativos). Contexto, nunca cota.

    Falha aqui não pode derrubar nada: devolve lista vazia e o resto segue. Só
    chuva — o motivo de o nível não entrar está em `coleta_chuva_cemaden.py`.
    """
    try:
        from coleta_chuva_cemaden import baixar_estacoes, converter

        leituras, _recusadas, _sem_dado = converter(baixar_estacoes())
        return leituras
    except Exception as e:
        print(f"aviso: chuva do CEMADEN não coletada ({e}).", file=sys.stderr)
        return []


def baixar_nivel_alertablu(leituras: list[dict]) -> list[dict]:
    """Resgata Blumenau quando a fonte de Itajai o publica vazio OU velho.
    O AlertaBlu publica a serie oficial de Blumenau, independente da pagina de
    Itajai. Se a primaria trouxe Blumenau com menos de 60 min, mantem. Se veio
    vazio ou com carimbo antigo, busca o AlertaBlu e devolve para conviver na
    lista (o site/bot ja mostram o mais recente da mesma cidade)."""
    # `medido_em` é hora de Brasília SEM fuso; o "agora" tem de estar no MESMO
    # relógio. Com `datetime.now()` naive numa VPS em UTC, a idade sai 3 h a mais
    # e o resgate dispara na hora errada — é o mesmo erro de fuso que o projeto
    # já padronizou em todo lugar (ver CLAUDE.md).
    agora = datetime.now(FUSO_BRASILIA).replace(tzinfo=None)
    def idade_min(m):
        for _formato in ("%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(str(m)[:16].replace("T", " "), "%Y-%m-%d %H:%M")
                return (agora - dt).total_seconds() / 60
            except ValueError:
                pass
        try:
            dt = datetime.strptime(str(m), "%d/%m/%Y %H:%M")
            return (agora - dt).total_seconds() / 60
        except ValueError:
            return 9999
    atual = [l for l in leituras if l.get("cidade") == "blumenau" and l.get("nivel_m") is not None]
    if atual and min(idade_min(l.get("medido_em")) for l in atual) < 60:
        return []
    try:
        from coleta_alertablu import URL, baixar, parse
        return parse(baixar(URL))
    except Exception as e:
        print(f"aviso: resgate de Blumenau pelo AlertaBlu falhou ({e}).", file=sys.stderr)
        return []


def baixar_nivel_asthon() -> list[dict]:
    """
    Nível de Vidal Ramos pela API Asthon do Alto Vale — a única cidade sem nível
    na tela que a Asthon cobre com régua própria (mesmo zero das cotas). Só ela,
    por lista fechada de estação; ver `coleta_asthon.py`.

    Falha aqui NUNCA derruba a coleta: devolve lista vazia e o resto segue. É
    nível de mais uma cidade, não a fonte principal.
    """
    try:
        from coleta_asthon import coletar

        return coletar()
    except Exception as e:
        print(f"aviso: Asthon (Vidal Ramos) não coletada ({e}).", file=sys.stderr)
        return []


def baixar_nivel_taio(gravar: bool) -> list[dict]:
    """
    Nível do CENTRO de Taió e, junto, o ESTADO DAS COMPORTAS da Barragem Oeste.

    Taió é cabeceira do Itajaí do Oeste e não tinha nível de cidade na tela: a
    rede estadual só dá leitura bruta ali, que por contrato do projeto nunca
    vira faixa. Esta fonte é municipal, e a régua dela É a que as cotas do Plano
    de Contingência da COMPDEC descrevem — por isso a leitura sai com
    `usar_para_cota: True` e pode pintar cor.

    ALÉM DO NÍVEL: é a única fonte de OPERAÇÃO DE BARRAGEM da bacia. O JICA
    (2011, seção 4.2.2) aponta essa ausência como a causa de a previsão de Rio
    do Sul não funcionar. As comportas não cabem em `leituras` — não são nível
    de rio — então o payload inteiro vai para `data/tempo-real/ultimo_taio.json`,
    que o `publicar_tempo_real.sh` leva junto.

    `gravar` respeita o `--no-save`: sem ele, um ensaio de coleta reescreveria o
    arquivo que o publicador manda ao ar.

    Falha aqui NUNCA derruba a coleta, como no Asthon: devolve lista vazia e o
    resto segue. É uma cidade a mais, não a fonte principal.
    """
    try:
        from coleta_taio import SAIDA, payload

        dados = payload()
        if gravar:
            from comum import grava_json

            grava_json(SAIDA, dados)
        return dados.get("leituras") or []
    except Exception as e:
        print(f"aviso: Taió (barragem Oeste) não coletada ({e}).", file=sys.stderr)
        return []


def baixar_nivel_gaspar(gravar: bool) -> list[dict]:
    """
    Nível do Açu em GASPAR, da tabela da Defesa Civil do município.

    Gaspar tinha cota VERIFICADA (5/6/7 m, do Plano de Contingência, com o PDF
    no repositório) e coletor próprio desde antes — e mesmo assim ficava CINZA
    no mapa, porque a leitura ia só para `ultimo_gaspar.json` e nunca entrava no
    `ultimo.json` que o site lê. É o mesmo elo que faltava a Taió até hoje: o
    coletor existia, o caminho não.

    A ESCOLHA DA LINHA É POR IGUALDADE, e isso é o cuidado central aqui. A mesma
    tabela publica `RIBEIRÃO BELCHIOR CENTRAL` com 1,68 m — nível PLAUSÍVEL, de
    outro curso. Pego por engano, Gaspar apareceria "normal" com 1,68 m enquanto
    o Açu estivesse em 6 m: silêncio no lugar de alarme, que é o pior desfecho
    deste projeto. Ver `ROTULO_REGUA_ACU` no `coleta_gaspar.py`.

    Respeita o `robots.txt` antes de buscar, como o coletor próprio faz.
    Falha nunca derruba a coleta — é uma cidade a mais, não a fonte principal.
    """
    try:
        import coleta_gaspar as cg

        if not cg.permitido():
            print("aviso: robots.txt de Gaspar não permite — pulado.", file=sys.stderr)
            return []
        analise = cg.analisar(cg.baixar(cg.URL))
        if gravar:
            from comum import DADOS

            destino = DADOS / cg.SAIDA
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(json.dumps(analise, ensure_ascii=False, indent=1) + "\n",
                               encoding="utf-8")
        leitura = cg.leitura_da_cidade(analise)
        return [leitura] if leitura else []
    except Exception as e:
        print(f"aviso: Gaspar não coletada ({e}).", file=sys.stderr)
        return []


def estacoes_do_ultimo() -> set[str]:
    """Os títulos que vieram na coleta anterior, do ultimo.json que vamos trocar."""
    try:
        with open(ULTIMO, encoding="utf-8") as f:
            return {l["estacao"] for l in json.load(f).get("leituras", []) if l.get("estacao")}
    except (OSError, ValueError, KeyError, TypeError):
        # Primeira rodada, arquivo ilegível: sem base de comparação, e isso não
        # é motivo para atrapalhar a coleta de agora.
        return set()


def chaves_existentes(arquivo: Path) -> set[tuple[str, str]]:
    """(estação, carimbo de medição) já gravados no mês."""
    if not arquivo.exists():
        return set()
    vistas: set[tuple[str, str]] = set()
    with open(arquivo, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            if d.get("medido_em"):
                vistas.add((d.get("estacao", ""), d["medido_em"]))
    return vistas


def linha_da_serie(l: dict) -> dict:
    """
    O que vai para o `.ndjson`: nível OU chuva, conforme a leitura.

    A chuva guarda as janelas e a marca de coerência. Guardar a incoerente
    marcada, em vez de descartar, é o mesmo critério da tela: descartar calado
    vira "não choveu" quando alguém for ler a série meses depois.
    """
    base = {
        "estacao": l.get("estacao"),
        "rio": l.get("rio"),
        "cidade": l.get("cidade"),
        "medido_em": l["medido_em"],
    }
    # `resgate_de` identifica a RÉGUA: primária e resgate medem a MESMA régua,
    # com o MESMO zero (Blumenau, estação ANA 83800002, publicada pela Defesa
    # Civil e pelo AlertaBlu). Sem guardá-lo, quem lê a série depois conta duas
    # réguas onde há uma — e some com o nível da cidade justamente quando a
    # primária falha e o resgate assume. Ver `comum.regua_de`.
    if l.get("resgate_de"):
        base["resgate_de"] = l["resgate_de"]
    if "mm" in l:
        return {**base, "mm": l["mm"], "coerente": l.get("coerente", True)}
    return {**base, "nivel_m": l["nivel_m"]}


def acumular(leituras: list[dict], prefixo: str = "") -> tuple[int, int]:
    """
    Acrescenta só o que é medição nova. Devolve (novas, repetidas).

    `prefixo` separa as séries por tipo: o nível vai em `AAAA-MM.ndjson` e a
    chuva em `chuva-AAAA-MM.ndjson`. São grandezas diferentes, com campos
    diferentes, e misturá-las num arquivo só obrigaria todo leitor a adivinhar
    qual linha é qual.
    """
    SERIE.mkdir(parents=True, exist_ok=True)
    novas = repetidas = 0
    por_mes: dict[str, list[dict]] = {}

    for l in leituras:
        if not l.get("medido_em"):
            # Sem carimbo de medição não dá para deduplicar nem para achar o
            # horário do pico depois. Guardar seria criar linha inútil.
            continue
        por_mes.setdefault(l["medido_em"][:7], []).append(l)

    for mes, do_mes in sorted(por_mes.items()):
        arquivo = SERIE / f"{prefixo}{mes}.ndjson"
        vistas = chaves_existentes(arquivo)
        linhas = []
        for l in do_mes:
            chave = (l.get("estacao", ""), l["medido_em"])
            if chave in vistas:
                repetidas += 1
                continue
            vistas.add(chave)
            linhas.append(json.dumps(linha_da_serie(l), ensure_ascii=False))
            novas += 1
        if linhas:
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")

    return novas, repetidas


def marcar_zero_suspeito(chuva: list[dict]) -> int:
    """
    Rebaixa para incoerente o pluviômetro preso em ZERO enquanto OUTRA estação
    da MESMA cidade mede chuva.

    Um sensor parado publica 0,0 em toda janela e passa na coerência (0 ≤ 0 ≤ 0),
    então a tela o mostra como "não choveu". Numa cidade onde a outra estação diz
    que está chovendo, isso é a pior mentira possível — foi o caso de Brusque
    Estação Guarani (0,0) enquanto a Rede DC-SC dava 8,2 mm/24 h. NÃO esconde a
    leitura: marca `coerente: false`, que a tela já trata como suspeita, sem
    apagar o dado (uma cidade seca de verdade, com todas as estações em zero,
    continua mostrando zero). Devolve quantas marcou.
    """
    def valores(l: dict) -> list[float]:
        return [v for v in (l.get("mm") or {}).values() if isinstance(v, (int, float))]

    cidades_com_chuva = {
        l.get("cidade") for l in chuva if any(v > 0 for v in valores(l))
    }
    marcadas = 0
    for l in chuva:
        vals = valores(l)
        tudo_zero = bool(vals) and all(v == 0 for v in vals)
        if l.get("coerente", True) and tudo_zero and l.get("cidade") in cidades_com_chuva:
            l["coerente"] = False
            l.setdefault("incoerencias", []).append(
                "zero em todas as janelas enquanto outra estação da cidade mede chuva "
                "— possível sensor parado"
            )
            marcadas += 1
    return marcadas


def _ler_ndjson(arquivo: Path):
    """Gera os dicts de um `.ndjson` ou `.ndjson.gz`, pulando linha quebrada."""
    abrir = (
        (lambda: gzip.open(arquivo, "rt", encoding="utf-8"))
        if arquivo.suffix == ".gz"
        else (lambda: open(arquivo, encoding="utf-8"))
    )
    with abrir() as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                yield json.loads(linha)
            except ValueError:
                continue


def escrever_serie_recente(horas: int = HORAS_SERIE_RECENTE) -> int:
    """
    Monta `serie-recente.json` com as últimas `horas` de NÍVEL, por rio e cidade,
    para o site desenhar a linha do tempo. Lê a série ndjson acumulada — só ela
    tem histórico; o `ultimo.json` é um instante. Devolve quantos pontos entraram.

    Só nível, de propósito: a chuva é outra grandeza e outra série, e dobraria o
    arquivo que o celular baixa. `medido_em` continua sendo hora de Brasília sem
    fuso, igual ao resto do projeto — nada de converter aqui.

    CADA PONTO DIZ DE QUE RÉGUA VEIO — e por quê (04/09/2026)
    ---------------------------------------------------------
    Até aqui este recorte agrupava por (rio, cidade) e jogava fora o campo
    `estacao`, que o ndjson mestre guarda. Numa cidade de uma régua só isso não
    faz diferença. Em ITAJAÍ faz: são onze réguas, com ZEROS DIFERENTES, e a
    série de `itajai-acu/itajai` saía com DC-01, DC-02 e DC-11 intercaladas —
    medido na série publicada de 04/09, um serrilhado de 2,70 → 1,20 → 0,56 →
    2,71 → 1,20 → 0,56, com salto MEDIANO de 1,70 m entre pontos vizinhos. No
    Mirim em Itajaí são cinco réguas e o salto máximo chega a 4,08 m.

    Isso não era só um gráfico feio. A `tendencia()` do site pega o último ponto
    e o de ~1 h antes e devolve cm/h — e é o que decide se uma leitura VELHA
    ainda pode ser lida como o agora. Simulando o site em cada instante da
    janela de 48 h: em `itajai-mirim/itajai`, **736 dos 949 instantes** dariam
    |cm/h| > 30 e **707** dariam > 100, com pico de **+2448 cm/h** — o site
    dizendo a quem mora na foz que o rio sobe 24 metros por hora. Em
    `itajai-acu/itajai`, pico de −13.140. Blumenau também aparece (primária +
    resgate sob a mesma cidade): pico de −264.

    O formato foi escolhido para o CELULAR NA CHUVA: gravar o título inteiro em
    cada ponto engordaria o arquivo em ~70%. Então vai uma legenda por (rio,
    cidade) em `reguas`, e cada ponto leva só `r`, o índice nela — ~7 bytes por
    ponto, +7%. E é RETROCOMPATÍVEL de propósito: a lista de pontos continua
    lista, `r` e `reguas` são campos novos que um site antigo ignora. Publicador
    e site podem ser implantados em qualquer ordem, o que importa quando a
    correção sobe no meio de uma cheia.
    """
    agora = datetime.now(FUSO_BRASILIA).replace(tzinfo=None)
    corte = agora - timedelta(hours=horas)

    # Quais meses ler: o de agora e, se a janela recua para o mês anterior, ele
    # também. Passar de dois é desnecessário — a janela é de horas.
    meses = {agora.strftime("%Y-%m"), corte.strftime("%Y-%m")}
    arquivos = [
        SERIE / nome
        for mes in meses
        for nome in (f"{mes}.ndjson", f"{mes}.ndjson.gz")
        if (SERIE / nome).exists()
    ]

    series: dict[str, dict[str, list[dict]]] = {}
    reguas: dict[str, dict[str, list[str]]] = {}
    pontos = 0
    for arquivo in arquivos:
        for d in _ler_ndjson(arquivo):
            if d.get("nivel_m") is None or not d.get("medido_em"):
                continue
            try:
                quando = datetime.fromisoformat(str(d["medido_em"]).replace(" ", "T"))
            except ValueError:
                continue
            if quando < corte:
                continue
            rio, cidade = d.get("rio"), d.get("cidade")
            if not rio or not cidade:
                continue
            ponto = {"medido_em": d["medido_em"], "nivel_m": d["nivel_m"]}
            # A FONTE, não a régua — e a diferença foi MEDIDA (04/09/2026).
            #
            # A primeira versão disto agrupava por `resgate_de or estacao`, a
            # regra do `comum.regua_de`, porque primária e resgate medem a MESMA
            # régua (Blumenau = estação ANA 83800002, publicada pela Defesa Civil
            # de Itajaí e pelo AlertaBlu). Para o ALARME isso continua certo: sem
            # juntá-las, Blumenau fica muda justamente quando a primária falha.
            #
            # Para a SÉRIE está errado, e o dado diz por quê. Comparando as duas
            # publicações no mesmo instante (interpolação linear, nos dois
            # sentidos), sobre as 48 h publicadas em 04/09:
            #
            #     AlertaBlu − Defesa Civil de Itajaí
            #     mediana  +0,065 m   ·   máximo  +0,245 m
            #     214 de 214 pares comparáveis com sinal POSITIVO
            #
            # Não é ruído nem defasagem: no período o rio caía 2,3 cm/h, então
            # explicar 6 cm por atraso exigiria 2 h 30 min entre as leituras, e
            # elas saem com minutos de diferença. As duas fontes DISCORDAM em
            # ~6 cm de forma sistemática.
            #
            # Fundi-las numa série só produzia um serrilhado de ±6 cm — a leitura
            # do AlertaBlu, que sai só no minuto :00, ficava sempre acima das
            # vizinhas — e a `tendencia` do site atravessava esse degrau: 4,60 m
            # às 13:00 contra 4,35 m às 13:05 dá **300 cm/h**, três metros por
            # hora num rio de baixo vale.
            #
            # Então: identidade de régua (alarme) e comparabilidade ponto a ponto
            # (série) são coisas diferentes. Aqui vale a FONTE. O `resgate_de`
            # continua gravado no ndjson, para quem precisar saber que as duas
            # cobrem a mesma régua.
            titulo = d.get("estacao")
            if titulo:
                ponto["_regua"] = str(titulo)
            series.setdefault(rio, {}).setdefault(cidade, []).append(ponto)
            pontos += 1

    for rio, por_cidade in series.items():
        for cidade, linha in por_cidade.items():
            linha.sort(key=lambda p: p["medido_em"])
            titulos = sorted({p["_regua"] for p in linha if "_regua" in p})
            if titulos:
                reguas.setdefault(rio, {})[cidade] = titulos
            indice = {t: i for i, t in enumerate(titulos)}
            for ponto in linha:
                titulo = ponto.pop("_regua", None)
                if titulo is not None:
                    ponto["r"] = indice[titulo]

    SERIE.mkdir(parents=True, exist_ok=True)
    SERIE_RECENTE.write_text(
        json.dumps(
            {
                "_meta": {
                    "descricao": "Últimas horas de nível por rio e cidade, para a linha do tempo do site.",
                    "medido_em": "hora de Brasília sem fuso, como no resto do projeto",
                    "gerado_em": "UTC, do momento em que este arquivo foi montado",
                    "so_nivel": "chuva é outra série; este arquivo é só nível",
                    "r": (
                        "índice da RÉGUA do ponto dentro de reguas[rio][cidade]. "
                        "Uma cidade pode ter várias réguas com ZEROS DIFERENTES "
                        "(Itajaí tem onze), e sem este campo a série da cidade sai "
                        "com todas intercaladas — um serrilhado que não é o rio. "
                        "Ponto sem 'r' é ponto de régua desconhecida: trate como "
                        "não comparável, nunca como 'a mesma de antes'."
                    ),
                },
                "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "janela_horas": horas,
                "reguas": reguas,
                "series": series,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return pontos


#: O `AAAA-MM` no fim do nome do arquivo de série, com ou sem prefixo.
MES_NO_NOME = re.compile(r"(\d{4}-\d{2})$")


def compactar() -> int:
    """Comprime os meses já fechados. O mês corrente fica intocado."""
    mes_atual = datetime.now().strftime("%Y-%m")
    feitos = 0
    for arquivo in sorted(SERIE.glob("*.ndjson")):
        # O mês vem do FIM do nome, não do nome inteiro. Com a série de chuva o
        # stem virou `chuva-2026-08`, e comparar isso com `2026-08` como texto
        # dá sempre "maior" — "c" vem depois de "2" —, então nenhum arquivo de
        # chuva jamais seria compactado, em silêncio.
        mes = MES_NO_NOME.search(arquivo.stem)
        if not mes or mes.group(1) >= mes_atual:
            continue
        destino = arquivo.with_suffix(".ndjson.gz")
        if destino.exists():
            continue
        with open(arquivo, "rb") as origem, gzip.open(destino, "wb") as saida:
            shutil.copyfileobj(origem, saida)
        antes, depois = arquivo.stat().st_size, destino.stat().st_size
        arquivo.unlink()
        print(f"{arquivo.name}: {antes // 1024} kB -> {depois // 1024} kB")
        feitos += 1
    return feitos


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--no-save", action="store_true", help="só mostra, não grava")
    ap.add_argument("--compactar", action="store_true", help="gzip nos meses fechados e sai")
    args = ap.parse_args()

    if args.compactar:
        n = compactar()
        print(f"{n} arquivo(s) compactado(s)." if n else "Nada a compactar.")
        return 0

    try:
        leituras = baixar_niveis()
        leituras = leituras + baixar_nivel_alertablu(leituras)
    except Exception as e:  # rede, HTTP, HTML inesperado
        print(f"ERRO ao coletar: {e}", file=sys.stderr)
        return 1

    # Vidal Ramos (Asthon) entra depois: fonte à parte, e a falha dela já é
    # engolida em baixar_nivel_asthon, então não pode derrubar a coleta acima.
    leituras = leituras + baixar_nivel_asthon()

    # Taió (municipal) pelo mesmo motivo, e traz as comportas da Barragem Oeste
    # no arquivo próprio. `--no-save` não pode reescrever o que vai ao ar.
    leituras = leituras + baixar_nivel_taio(gravar=not args.no_save)

    # Gaspar (municipal), pelo mesmo motivo e com o mesmo cuidado: a tabela dela
    # traz outra régua plausível, de outro curso, que não pode virar o nível da
    # cidade.
    leituras = leituras + baixar_nivel_gaspar(gravar=not args.no_save)

    for l in leituras:
        alvo = f"{l['cidade']} ({l['rio']})" if l.get("cidade") else "não mapeada"
        print(f"{l['nivel_m']:6.2f} m  {l.get('medido_em') or '   -   '}  {l['estacao']}  [{alvo}]")

    if not leituras:
        print(
            "AVISO: nenhuma leitura encontrada — a estrutura da página pode ter mudado.",
            file=sys.stderr,
        )
        return 1

    if args.no_save:
        return 0

    # Página que volta pela metade não é erro visível: `if not leituras` só pega
    # o caso de ZERO estação. Caindo de catorze para duas, a coleta segue,
    # publica, e as doze somem da tela como se não existissem. O vigia detecta,
    # mas roda de hora em hora enquanto a coleta roda a cada quinze minutos —
    # três de cada quatro coletas nunca são olhadas.
    #
    # O aviso NÃO muda o código de saída, de propósito: o cron encadeia
    # `coleta_niveis.py && publicar_tempo_real.sh`, e sair com erro impediria a
    # publicação. O site congelaria no dado anterior em vez de receber as
    # leituras que chegaram — pior do que publicar parte com a idade à vista.
    sumidas = sorted(estacoes_do_ultimo() - {l["estacao"] for l in leituras})
    if sumidas:
        print(
            f"AVISO: {len(sumidas)} estação(ões) que vieram na coleta anterior não vieram "
            f"agora: {', '.join(sumidas)}. A página pode ter voltado incompleta.",
            file=sys.stderr,
        )

    novas, repetidas = acumular(leituras)

    chuva, chuva_ok = baixar_chuva()
    # As duas fontes convivem na mesma lista: o site e o bot já mostram o maior
    # de vários pluviômetros por cidade, e cada leitura carrega a sua própria
    # idade. Nomes não colidem porque os da Defesa Civil de SC vêm com o código
    # DCSC na frente.
    chuva = chuva + baixar_chuva_sc()
    # E o CEMADEN, a rede mais densa — chuva por bairro. Mesma lista: o site e o
    # bot já mostram o maior de vários pluviômetros por cidade, e o código do
    # CEMADEN (420…A) não colide com o DCSC nem com os nomes de Itajaí.
    chuva = chuva + baixar_chuva_cemaden()
    # Com as duas fontes juntas dá para cruzar: um pluviômetro preso em ZERO em
    # toda janela numa cidade onde OUTRA estação mede chuva é sensor parado, não
    # "não choveu". Aqui é o único ponto em que as estações da cidade estão lado
    # a lado.
    marcar_zero_suspeito(chuva)

    # A chuva também vira série. Sem isto ela vivia só no ultimo.json, que é
    # sobrescrito a cada rodada: quinze minutos depois, o dado tinha sumido.
    # Com o nível de montante explicando pouco o de jusante (r² = 0,21), a
    # chuva é a candidata mais forte a preditor de verdade — e preditor se
    # constrói com série pareada aos picos, que só existe se for guardada
    # desde já. Um ciclo perdido é histórico perdido para sempre.
    novas_chuva, repetidas_chuva = acumular(chuva, prefixo="chuva-")

    # A linha do tempo do site: as últimas horas de nível, recortadas da série
    # acumulada. Publicada junto do ultimo.json pelo publicar_tempo_real.sh.
    pontos_serie = escrever_serie_recente()

    SERIE.mkdir(parents=True, exist_ok=True)
    ULTIMO.write_text(
        json.dumps(
            {
                "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "fonte": "https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios",
                "leituras": leituras,
                "fonte_chuva": "https://defesacivil.itajai.sc.gov.br/monitoramento/chuvas",
                "chuva": chuva,
                # Falso só quando a coleta da chuva FALHOU. Lista vazia com
                # chuva_ok verdadeiro é "a fonte não publica pluviômetro"; com
                # falso é "não conseguimos buscar". Sem esta marca a tela conta
                # a mesma história nos dois casos, e num deles ela é falsa.
                "chuva_ok": chuva_ok,
                # Quem veio na coleta anterior e não veio agora. Vai no arquivo
                # publicado para o vigia enxergar a rodada exata em que sumiu,
                # e não só a que ele por acaso amostrou.
                "estacoes_ausentes": sumidas,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{novas} medição(ões) nova(s) de nível, {repetidas} já registrada(s).")
    print(f"{len(chuva)} estação(ões) com chuva publicada; "
          f"{novas_chuva} nova(s) na série, {repetidas_chuva} já registrada(s).")
    print(f"serie-recente.json: {pontos_serie} ponto(s) de nível nas últimas "
          f"{HORAS_SERIE_RECENTE} h.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
