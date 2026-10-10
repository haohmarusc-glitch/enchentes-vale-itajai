#!/usr/bin/env python3
"""As réguas do Itajaí do Sul e do Itajaí do Oeste em Rio do Sul, em arquivo próprio (decisão do Jefferson, 10/10/2026).

POR QUE EXISTE. Rio do Sul mede os três rios (`docs/reguas-rio-do-sul.md`): o Açu (Ponte Dom Tito Buss, já no site
pela `coleta_asthon.py`), o Itajaí do Sul (Ponte Ricardo Kanitz e Ponte Hannelore Hartmann Eyng) e o Itajaí do Oeste
(Ponte BR 470, que não aparecia na captura de 01/09/2026 e está no painel da Asthon desde, pelo menos, 10/10/2026).
As duas entradas e a saída medidas na mesma cidade, com minutos de diferença, são o melhor ponto de calibração da
bacia: a contribuição de cada cabeceira medida, não inferida.

O QUE FAZ. Uma consulta ao painel público da Asthon (o mesmo que o portal da Defesa Civil de Rio do Sul usa), com o
User-Agent do projeto. Das estações, só as da LISTA FECHADA abaixo, por `station_id` e com o rio conferido (barragem,
altitude e estação de outro rio ficam de fora, como em `coleta_asthon.py`). Grava:

* `data/tempo-real/ultimo_rio_do_sul_rios.json` — a última leitura de cada régua, com a idade e as cotas como a
  fonte publica (`band_thresholds`). ARQUIVO PRÓPRIO, NUNCA em `leituras`: não pinta o mapa, não muda a
  classificação nem o aviso, e não está no cadastro (`estacoes.json`). Mostrar na tela é outra decisão.
* `data/tempo-real/rio-do-sul-rios-AAAA-MM.ndjson` — a série, acumulada sem repetir (`station_id`, `medido_em`), para
  a calibração. Vai para o `arquivo-series` pela cópia semanal (`copiar_series.sh` copia todo `*.ndjson`).

FUSO. A Asthon publica `last_reading_at` em UTC (com `Z`); o projeto grava `medido_em` em hora de Brasília, sem fuso.
A conversão é a de `coleta_asthon.de_utc_para_brasilia`, na entrada, e em lugar nenhum mais.

FALHA. Rede, HTTP ou JSON inesperado apagam o `ultimo_…json` anterior (uma leitura velha não passa por atual) e nunca
seguram a publicação do nível: o `publicar_tempo_real.sh` segue sem o arquivo.

Uso:
    python3 scripts/coleta_riodosul_rios.py              # imprime o que coletaria
    python3 scripts/coleta_riodosul_rios.py --publicar   # grava os dois arquivos (uma consulta)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from coleta_asthon import URL_PAINEL, baixar, de_utc_para_brasilia
from comum import DADOS, nivel_plausivel

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")
ARQUIVO_PUBLICAVEL = "tempo-real/ultimo_rio_do_sul_rios.json"
SERIE = "tempo-real/rio-do-sul-rios-{mes}.ndjson"
FONTE = "Asthon — painel público usado pela Defesa Civil de Rio do Sul (public.asthon.com.br)"
#: Leitura com mais que isto não é "de agora" (a Asthon publica a cada 5 min).
FRESCA_MIN = 60

#: `station_id` -> (rio esperado em `river_name`, ramo, nome curto). LISTA FECHADA, conferida no painel de 10/10/2026.
#: A Tito Buss entra para a calibração ter a saída no mesmo arquivo e no mesmo instante; ela continua sendo
#: a régua da cidade pela `coleta_asthon.py`, e nada aqui muda isso.
REGUAS = {
    "30475400-b7ba-4551-9646-19df0c3bfa38": ("Rio Itajaí do Sul", "itajai_do_sul", "Ponte Ricardo Kanitz"),
    "039a5d4f-f58d-4fca-bef6-5d37e132a6f0": ("Rio Itajaí do Sul", "itajai_do_sul", "Ponte Hannelore Hartmann Eyng"),
    "3167e629-3bbe-48f2-9244-c65dfe6882d8": ("Rio Itajaí do Oeste", "itajai_do_oeste", "Ponte BR 470"),
    "f6360951-219f-4859-935f-b2e2d13962f1": ("Rio Itajaí-Açu", "tronco_acu", "Ponte Dom Tito Buss"),
}


def cotas_na_fonte(estacao: dict) -> dict:
    """As cotas que a Asthon publica para a régua, como estão (`authored`/`derived`). Informativas: não pintam."""
    saida = {}
    for b in estacao.get("band_thresholds") or []:
        if isinstance(b, dict) and isinstance(b.get("cota_m"), (int, float)) and b.get("band_key"):
            saida[b["band_key"]] = {"cota_m": round(float(b["cota_m"]), 3), "origem": b.get("origin")}
    return saida


def extrair(dados) -> tuple[list[dict], list[str]]:
    """As réguas da lista fechada, conferidas, e o que ficou de fora com o porquê."""
    estacoes = dados.get("stations") if isinstance(dados, dict) else dados
    vistas = {e.get("station_id"): e for e in estacoes or [] if isinstance(e, dict)}
    reguas, recusas = [], []
    for sid, (rio, ramo, nome) in REGUAS.items():
        e = vistas.get(sid)
        if e is None:
            recusas.append(f"{nome}: ausente do painel")
            continue
        if e.get("river_name") != rio:
            recusas.append(f"{nome}: o painel diz rio {e.get('river_name')!r}, não {rio!r}; não substituir")
            continue
        nivel = e.get("level_m")
        if not isinstance(nivel, (int, float)) or not nivel_plausivel(nivel):
            recusas.append(f"{nome}: nível {nivel!r} ausente ou fora da faixa de rio")
            continue
        quando = e.get("last_reading_at")
        medido = de_utc_para_brasilia(quando) if isinstance(quando, str) else None
        if not medido:
            recusas.append(f"{nome}: sem horário de leitura")
            continue
        reguas.append({"station_id": sid, "nome": nome, "rio": rio, "ramo": ramo, "medido_em": medido,
                       "nivel_m": round(float(nivel), 2), "cotas_na_fonte": cotas_na_fonte(e)})
    return reguas, recusas


def resumo_publicavel(reguas: list[dict], recusas: list[str], agora: datetime, gerado_em: str) -> dict:
    """O arquivo pequeno: a última leitura de cada régua, com a idade refeita no relógio de Brasília."""
    saida = []
    for r in reguas:
        idade = round((agora - datetime.fromisoformat(r["medido_em"])).total_seconds() / 60)
        saida.append({**r, "idade_min_na_coleta": idade,
                      "situacao": "fresca" if -15 <= idade <= FRESCA_MIN else "antiga"})
    return {
        "versao": 1,
        "gerado_em": gerado_em,
        "fonte": FONTE,
        "fonte_url": URL_PAINEL,
        "cidade": "rio-do-sul",
        "reguas": saida,
        "fora": recusas,
        "aviso": ("Réguas do Itajaí do Sul e do Itajaí do Oeste em Rio do Sul, para calibração (decisão do Jefferson, "
                  "10/10/2026). Cada régua tem o zero dela: os metros não se comparam entre elas nem com a régua de "
                  "outra cidade. Não é alerta deste site, não pinta o mapa e não está no cadastro."),
    }


def acumular(reguas: list[dict], raiz: Path) -> int:
    """Anexa à série do mês as leituras que ainda não estão lá (chave: station_id + medido_em)."""
    novas = 0
    por_mes: dict[str, list[dict]] = {}
    for r in reguas:
        por_mes.setdefault(r["medido_em"][:7], []).append(r)
    for mes, linhas in por_mes.items():
        caminho = raiz / SERIE.format(mes=mes)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        vistas = set()
        if caminho.exists():
            for linha in caminho.read_text(encoding="utf-8").splitlines():
                try:
                    d = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                vistas.add((d.get("station_id"), d.get("medido_em")))
        with caminho.open("a", encoding="utf-8") as f:
            for r in linhas:
                if (r["station_id"], r["medido_em"]) in vistas:
                    continue
                f.write(json.dumps({"estacao": r["nome"], "rio": r["rio"], "ramo": r["ramo"], "cidade": "rio-do-sul",
                                    "station_id": r["station_id"], "medido_em": r["medido_em"],
                                    "nivel_m": r["nivel_m"]}, ensure_ascii=False) + "\n")
                novas += 1
    return novas


def publicar(agora: datetime, buscador=baixar, raiz: Path | None = None) -> int:
    raiz = raiz or DADOS
    destino = raiz / ARQUIVO_PUBLICAVEL
    gerado = datetime.now(tz=ZoneInfo("UTC")).isoformat(timespec="seconds")
    try:
        reguas, recusas = extrair(buscador())
    except Exception as e:  # noqa: BLE001 — esta coleta nunca segura a publicação do nível
        destino.unlink(missing_ok=True)
        print(f"aviso: réguas dos rios de Rio do Sul indisponíveis ({e}); nada publicado", file=sys.stderr)
        return 1
    if not reguas:
        destino.unlink(missing_ok=True)
        print(f"aviso: nenhuma régua dos rios de Rio do Sul passou: {recusas}", file=sys.stderr)
        return 1
    saida = resumo_publicavel(reguas, recusas, agora, gerado)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    novas = acumular(reguas, raiz)
    for r in saida["reguas"]:
        print(f"{r['nivel_m']:6.2f} m  {r['medido_em']}  {r['nome']} ({r['rio']}, {r['situacao']})")
    for f in recusas:
        print(f"  fora: {f}", file=sys.stderr)
    print(f"-> data/{ARQUIVO_PUBLICAVEL}; {novas} linha(s) nova(s) na série")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--publicar", action="store_true", help=f"grava data/{ARQUIVO_PUBLICAVEL} e a série (uma consulta)")
    p.add_argument("--arquivo", help="JSON do painel já salvo, para conferir sem rede")
    args = p.parse_args(argv)
    agora = datetime.now(tz=FUSO_BRASILIA).replace(tzinfo=None)
    if args.publicar:
        return publicar(agora)
    dados = json.loads(Path(args.arquivo).read_text(encoding="utf-8")) if args.arquivo else baixar()
    reguas, recusas = extrair(dados)
    print(json.dumps(resumo_publicavel(reguas, recusas, agora, "(não publicado)"), ensure_ascii=False, indent=1))
    return 0 if reguas else 1


if __name__ == "__main__":
    sys.exit(main())
