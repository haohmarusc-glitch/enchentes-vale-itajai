#!/usr/bin/env python3
"""
O que o navegador do morador recebe é o que a VPS acabou de publicar?

POR QUE ESTE SCRIPT EXISTE (04/09/2026)
---------------------------------------
O vigia (`saude_coleta.py`) responde duas perguntas, lendo os arquivos LOCAIS
da VPS: "a coleta rodou?" e "a fonte publicou?". Nenhuma das duas cobre o
ÚLTIMO trecho do caminho:

    VPS  →  branch `tempo-real`  →  raw.githubusercontent.com  →  navegador

E é desse trecho que o site depende de verdade: `web/src/dados/serie.ts`,
`tempoReal.ts` e `nivelSc.ts` buscam os três arquivos por `raw.…`. Se esse
trecho travar, a coleta continua verde na VPS e o morador vê nível velho.

O caso que motivou: uma sessão leu o `serie-recente.json` pelo `raw.…`, viu um
arquivo gerado 15:16 UTC enquanto a VPS tinha 22:01, e concluiu "o `raw` serve
cache de CDN; nunca verifique deploy por ele". A conclusão pode estar certa ou
errada — o que ela NÃO era é medida: uma leitura só não distingue

  (a) o `raw` servindo cache velho,
  (b) a publicação da VPS travada há horas (o caso GRAVE — o site inteiro
      congela, porque o site lê pelo mesmo `raw`),
  (c) a leitura ter caído no minuto de uma publicação em andamento.

Este script distingue os três, e não depende de memória de ninguém.

O MÉTODO
--------
Três relógios, lidos no mesmo instante:

  1. `gerado_em` do arquivo que o `raw` entrega  — o que o morador recebe
  2. `gerado_em` do arquivo LOCAL, se existir     — o que a VPS produziu
  3. a data do commit no topo de `tempo-real`,
     pela API do GitHub, que não passa pelo mesmo cache do `raw`

Depois:

* **topo da API ≈ conteúdo do `raw`**, e ambos recentes → caminho inteiro vivo.
* **topo da API recente, `raw` velho** → é (a): cache. A regra da outra sessão
  vale, e o site está entregando dado velho ao morador — é defeito de produção,
  não só de verificação.
* **topo da API velho** → é (b): a publicação parou. O `raw` está certo em
  servir o que está lá. O problema é na VPS, e o vigia devia ter pegado.
* **local muito mais novo que o topo** → (b) confirmado do lado de cá.

Sem rede para a API, o script diz "NÃO DÁ PARA DIZER" em vez de escolher —
"não sei" é resposta, e um palpite aqui manda consertar a coisa errada.

O SCRIPT NÃO GRAVA NADA e não publica nada. Só mede e conta.

Uso:
    python3 scripts/conferir_publicado.py
    python3 scripts/conferir_publicado.py --arquivo ultimo.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from comum import DADOS, baixar

BRUTO = ("https://raw.githubusercontent.com/haohmarusc-glitch/"
         "enchentes-vale-itajai/tempo-real/{arquivo}")
API = ("https://api.github.com/repos/haohmarusc-glitch/"
       "enchentes-vale-itajai/commits/tempo-real")

#: Os três arquivos que o site busca por `raw.…` (web/src/dados/*.ts).
PUBLICADOS = ("serie-recente.json", "ultimo.json", "ultimo_nivel_sc.json")

#: O carimbo de geração NÃO tem o mesmo nome nos três: a série usa `gerado_em`,
#: os dois `ultimo*.json` usam `coletado_em`. Os DOIS são UTC — é o outro campo,
#: `medido_em`, que é horário de Brasília sem fuso (CLAUDE.md). Nunca trocar
#: nenhum destes por `medido_em` aqui: `medido_em` é quando a FONTE mediu, e
#: uma fonte parada com publicação viva daria "caminho morto" por engano. Quem
#: vigia `medido_em` é o `saude_coleta.py`, que é outra pergunta.
CARIMBOS = ("gerado_em", "coletado_em")


def carimbo(doc: dict) -> tuple[datetime | None, str | None]:
    """Devolve (instante, nome do campo usado). None se nenhum dos dois existe."""
    for campo in CARIMBOS:
        d = utc(doc.get(campo))
        if d is not None:
            return d, campo
    return None, None

#: O cron publica a cada 15 min. Duas rodadas perdidas ainda é ruído; a partir
#: da terceira já não dá para chamar de atraso normal.
NORMAL_MIN = 45.0

#: Diferença entre o topo do branch e o conteúdo servido pelo `raw` abaixo da
#: qual não dá para separar cache de uma publicação em andamento.
JANELA_PUBLICACAO_MIN = 5.0


def utc(texto: str | None) -> datetime | None:
    """Carimbo ISO -> datetime em UTC. `gerado_em` e a API do GitHub são UTC."""
    if not texto:
        return None
    try:
        d = datetime.fromisoformat(str(texto).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def minutos(depois: datetime | None, antes: datetime | None) -> float | None:
    if depois is None or antes is None:
        return None
    return (depois - antes).total_seconds() / 60.0


def veredito(idade_raw, idade_topo, entre_topo_e_raw) -> tuple[str, str]:
    """
    Devolve (veredito, explicação). Só quatro respostas, e uma delas é não sei.

    A ordem importa: sem a data do topo não há como separar cache de
    publicação travada, então a ignorância vem antes de qualquer diagnóstico.
    """
    if idade_raw is None:
        return ("NÃO DÁ PARA DIZER",
                "não deu para ler o carimbo do arquivo servido pelo raw (ver o erro acima)")
    if idade_topo is None:
        return ("NÃO DÁ PARA DIZER",
                "sem a data do topo do branch (API do GitHub fora de alcance) não dá "
                "para separar cache do raw de publicação travada")
    if idade_topo > NORMAL_MIN:
        return ("PUBLICAÇÃO PARADA",
                f"o topo do branch tem {idade_topo:.0f} min — a VPS parou de publicar. "
                "O raw está servindo o que existe. O site mostra dado velho ao morador; "
                "consertar na VPS (cron, rede, credencial), não no raw")
    if entre_topo_e_raw is not None and entre_topo_e_raw > JANELA_PUBLICACAO_MIN:
        return ("CACHE DO RAW",
                f"o topo do branch tem {idade_topo:.0f} min, mas o raw entrega conteúdo "
                f"{entre_topo_e_raw:.0f} min mais velho que ele. O site lê pelo raw — "
                "então isso é dado velho chegando ao morador, não só um estorvo de "
                "verificação")
    if idade_raw > NORMAL_MIN:
        return ("NÃO DÁ PARA DIZER",
                f"o conteúdo tem {idade_raw:.0f} min mas o topo do branch é recente e "
                "bate com ele — provavelmente a coleta gerou um arquivo com carimbo "
                "antigo; ver `saude_coleta.py`")
    return ("CAMINHO VIVO",
            f"conteúdo com {idade_raw:.0f} min, topo do branch com {idade_topo:.0f} min, "
            "e os dois batem")


def medir(arquivo: str, agora: datetime, buscar=baixar) -> dict:
    """Lê os três relógios. Falha de rede vira None, nunca um palpite."""
    m: dict = {"arquivo": arquivo}

    try:
        m["gerado_raw"], m["campo"] = carimbo(json.loads(buscar(BRUTO.format(arquivo=arquivo))))
        if m["gerado_raw"] is None:
            m["erro_raw"] = f"nenhum dos carimbos {CARIMBOS} no arquivo servido"
    except Exception as e:
        m["gerado_raw"], m["campo"], m["erro_raw"] = None, None, str(e)

    local = DADOS / "tempo-real" / arquivo
    try:
        m["gerado_local"], _ = carimbo(json.loads(local.read_text(encoding="utf-8")))
    except Exception:
        m["gerado_local"] = None

    try:
        c = json.loads(buscar(API))
        m["topo"] = utc(((c.get("commit") or {}).get("committer") or {}).get("date"))
        m["topo_sha"] = (c.get("sha") or "")[:8]
    except Exception as e:
        m["topo"], m["topo_sha"], m["erro_api"] = None, None, str(e)

    m["idade_raw"] = minutos(agora, m["gerado_raw"])
    m["idade_topo"] = minutos(agora, m["topo"])
    m["idade_local"] = minutos(agora, m["gerado_local"])
    m["entre_topo_e_raw"] = minutos(m["topo"], m["gerado_raw"])
    m["veredito"], m["porque"] = veredito(m["idade_raw"], m["idade_topo"], m["entre_topo_e_raw"])
    return m


def contar(m: dict) -> None:
    def linha(rotulo: str, quando, idade) -> None:
        if quando is None:
            print(f"  {rotulo:<28} —")
        else:
            print(f"  {rotulo:<28} {quando.isoformat(timespec='seconds')}  ({idade:.0f} min)")

    print(f"\n{m['arquivo']}")
    linha(f"o navegador recebe ({m.get('campo') or '?'})", m["gerado_raw"], m["idade_raw"])
    linha("a VPS gerou (local)", m["gerado_local"], m["idade_local"])
    linha(f"topo de tempo-real {m.get('topo_sha') or ''}".strip(), m["topo"], m["idade_topo"])
    if m.get("erro_raw"):
        print(f"  raw fora de alcance: {m['erro_raw']}")
    if m.get("erro_api"):
        print(f"  API do GitHub fora de alcance: {m['erro_api']}")
    print(f"  → {m['veredito']}: {m['porque']}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--arquivo", action="append",
                   help=f"arquivo publicado a conferir (padrão: {', '.join(PUBLICADOS)})")
    a = p.parse_args(argv)

    agora = datetime.now(timezone.utc)
    print(f"agora (UTC): {agora.isoformat(timespec='seconds')}")

    ruim = False
    for arquivo in (a.arquivo or list(PUBLICADOS)):
        m = medir(arquivo, agora)
        contar(m)
        if m["veredito"] in ("PUBLICAÇÃO PARADA", "CACHE DO RAW"):
            ruim = True
    return 1 if ruim else 0


if __name__ == "__main__":
    sys.exit(main())
