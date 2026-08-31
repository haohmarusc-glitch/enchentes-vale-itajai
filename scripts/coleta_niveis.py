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
busca o nível ao vivo. Rode os dois em sequência no cron:

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
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from comum import DADOS, USER_AGENT, espera_turno

SERIE = DADOS / "tempo-real"
ULTIMO = SERIE / "ultimo.json"


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


def acumular(leituras: list[dict]) -> tuple[int, int]:
    """Acrescenta só o que é medição nova. Devolve (novas, repetidas)."""
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
        arquivo = SERIE / f"{mes}.ndjson"
        vistas = chaves_existentes(arquivo)
        linhas = []
        for l in do_mes:
            chave = (l.get("estacao", ""), l["medido_em"])
            if chave in vistas:
                repetidas += 1
                continue
            vistas.add(chave)
            linhas.append(json.dumps({
                "estacao": l.get("estacao"),
                "rio": l.get("rio"),
                "cidade": l.get("cidade"),
                "medido_em": l["medido_em"],
                "nivel_m": l["nivel_m"],
            }, ensure_ascii=False))
            novas += 1
        if linhas:
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")

    return novas, repetidas


def compactar() -> int:
    """Comprime os meses já fechados. O mês corrente fica intocado."""
    mes_atual = datetime.now().strftime("%Y-%m")
    feitos = 0
    for arquivo in sorted(SERIE.glob("*.ndjson")):
        if arquivo.stem >= mes_atual:
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
    except Exception as e:  # rede, HTTP, HTML inesperado
        print(f"ERRO ao coletar: {e}", file=sys.stderr)
        return 1

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
    print(f"\n{novas} medição(ões) nova(s), {repetidas} já registrada(s).")
    print(f"{len(chuva)} estação(ões) com chuva publicada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
