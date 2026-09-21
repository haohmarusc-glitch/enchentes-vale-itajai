#!/usr/bin/env python3
"""
Níveis das réguas DC no portal NOVO da Defesa Civil de Itajaí.

    https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O portal antigo (`coleta_itajai.py`, `defesacivil.itajai.sc.gov.br/monitoramento/
nivel-rios`) responde 404 desde algum ponto antes de 19/09/2026, quando uma
auditoria externa deu pela falta. Não foi só Itajaí que caiu: aquela página
servia TAMBÉM Brusque, Blumenau e Rio do Sul (ver `comum._FALLBACK`), então a
mudança de endereço apagou quatro cidades de uma vez — e a de Blumenau só não
sumiu da tela porque o AlertaBlu é resgate dela.

O CONTRATO, lido no corpo real (87.637 bytes, capturado em 19/09/2026 13h38)
-----------------------------------------------------------------------------
É um app Inertia: o HTML traz `<div id="app" data-page="{...}">`, e o atributo,
com as entidades decodificadas, é o JSON da página. As estações estão em
`props.estacoes`, uma lista de onze para `props.municipioId == 1`.

De cada estação interessa:

    codigo        "DC01" … "DC11"  — SEM hífen, ao contrário do cadastro
    nome          "Rio Itajaí-Açu - ICMBio/CEPSUL"  — sem o código na frente
    latitude/longitude
    nivel_rio_m   número em metros
    medido_em     ISO **em UTC, com offset explícito** e microssegundos
    qualidade.nivel_rio_m.{estado, medido_em}   carimbo DA GRANDEZA
    atencao_m / alerta_m / emergencia_m         (NÃO usados — ver abaixo)

AS QUATRO REGRAS DESTE COLETOR, cada uma por um motivo medido
--------------------------------------------------------------
1. **A IDENTIDADE É PROVADA PELA COORDENADA, não pelo código nem pelo nome.**
   Casar "DC01" com "DC-01" por string é vínculo por NOME — o erro que o
   Salseiro custou em Vidal Ramos e a "Ponte Estaiada" em Brusque. Pior aqui:
   o cadastro REGISTRA que entre edições do Plano de Contingência houve
   REMANEJAMENTO de estação (a DC-09 era "Ribeirão Ariribá" numa edição e
   "Ribeirão da Murta" na v17 — rio diferente). Um código reaproveitado em
   outro ponto entraria como se fosse a mesma régua.
   Conferido em 19/09/2026: as ONZE batem com o cadastro a **0,0 m**. Por isso
   o código escolhe o candidato e a coordenada CONFIRMA; fora de
   TOLERANCIA_COORD_M a estação é recusada, com o motivo no stderr.

2. **O TÍTULO SAI DO CADASTRO**, nunca de concatenar código + nome. `estacao`
   é a chave de identidade de todo o resto do projeto — `regua_de`, a memória
   do vigia, `estacao_por_titulo` para as cotas, a série. Montar o título aqui
   mudaria silenciosamente a identidade de onze réguas.

3. **`medido_em` VIRA HORÁRIO DE BRASÍLIA SEM FUSO.** O portal publica UTC com
   offset; o contrato do repositório é Brasília sem fuso (CLAUDE.md). Confundir
   os dois já custou uma sessão inteira aqui. E o carimbo preferido é o de
   `qualidade.nivel_rio_m.medido_em` — é o da GRANDEZA, e pode ser mais antigo
   que o da estação.

4. **`props.consultadoEm` NÃO entra.** É o instante da consulta, não da
   medição: usá-lo renovaria a idade de uma leitura velha, que é exatamente a
   mentira que a idade existe para impedir.

O QUE ESTE COLETOR NÃO FAZ
--------------------------
* **Não lê as cotas do portal.** Quatro das onze (DC-01, DC-07, DC-08, DC-09)
  divergem do Plano de Contingência v17 que o cadastro usa — conferido aqui,
  número a número. São duas fontes oficiais do MESMO município discordando, e
  em DC-07 e DC-08 o portal é MAIS BAIXO, não mais alto. Trocar cota é decisão
  do Jefferson, com o documento na mão; ver as Pendências do README.
* **Não busca os outros municípios — e agora o CORPO de `?municipio_id=2` foi lido.**
  `props.municipios` lista Itajaí (1), Brusque (2), Blumenau (3) e Rio do Sul (4).
  Em 19/09/2026 uma auditoria externa abriu `…/rios?municipio_id=2` no navegador
  e viu Brusque; em 21/09/2026 o Jefferson salvou o corpo
  (`data/brutos/itajai-portal-rios-municipio-2-brusque-2026-09-21.html`, 44.334
  bytes, `consultadoEm` 2026-09-21T11:12:48Z), e o corpo diz:

      props.municipioId = 2; UMA estação: codigo "DCSC-00019", nome "Estação MKS
      DCSC-00019", municipio_id 2, fonte "Brusque", **latitude e longitude NULL**,
      atualizacao_esperada_segundos 600, nivel_rio_m 1.97, medido_em
      "2026-09-21T11:00:00+00:00" (UTC com offset, SEM microssegundos — a forma
      varia), qualidade.nivel_rio_m.{estado "atual", medido_em idem}, tendencia
      "descendo", situacao "monitoramento", atencao_m 3.5, alerta_m 5,
      emergencia_m 6, serie_12_h com 145 pontos de 5 em 5 minutos.

  **Continua não ligado, e agora por um motivo medido, não por falta de captura:**
  a estação vem SEM coordenada, e a identidade neste coletor é provada pela
  coordenada (regra 1). Ligar seria vínculo por nome: "DCSC-00019" é o código
  que o cadastro de Brusque cita como `identificada_pelo_monitor_de_itajai_como`,
  e código igual não prova régua igual (foi assim com o Salseiro). Fecha com a
  coordenada da DCSC-00019 vinda da própria DCSC, ou com o operador dizendo que
  ponto o portal de Itajaí republica.
  ⚠️ **A armadilha do cabeçalho está confirmada NO CORPO:** a página de Brusque
  traz "Situação atual em Itajaí — Normalidade — Atualizado em 18/09/2026,
  17:35" (HTML da moldura, fora do `data-page`) enquanto o cartão da estação diz
  21/09/2026 08:00. Quem lê o cabeçalho lê a situação de OUTRA cidade, com data
  de três dias antes. Por isso existem `municipio_da_carga()` e
  `conferir_municipio()`: o município pedido, o `props.municipioId`, o
  `municipio_id` de cada estação e a `fonte` têm que concordar, e `parse()`
  recusa a página inteira quando `props.municipioId` não é o de Itajaí. Nunca
  inferir a cidade pelo domínio do portal.
  ⚠️ E a TERCEIRA escala de cotas da DCSC-00019 (3,50/5,00/6,00) agora está
  lida no corpo, não só na tela: ver `cotas_divergencia.nao_adotada_portal_itajai`
  no cadastro de Brusque. Continua não entrando: o portal de Itajaí publica
  escala de estação que não é dele.

Uso:
    python3 scripts/coleta_itajai_portal.py --arquivo pagina.html   # sem rede
    python3 scripts/coleta_itajai_portal.py
"""
from __future__ import annotations

import argparse
import html as _html
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from comum import (NIVEL_MAXIMO_M, NIVEL_MINIMO_M, estacoes_tempo_real,
                   nivel_plausivel)

URL = "https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios"
FUSO = ZoneInfo("America/Sao_Paulo")

#: Quanto a coordenada do portal pode afastar-se da cadastrada e ainda ser a
#: MESMA régua. As onze bateram a 0,0 m em 19/09/2026; a folga existe para
#: arredondamento de publicação, não para acomodar régua mudada de lugar.
TOLERANCIA_COORD_M = 50.0

RE_DATA_PAGE = re.compile(r'<div[^>]*\bid="app"[^>]*\bdata-page="([^"]*)"', re.I)

#: `props.municipioId` da página que este coletor lê. Os outros três (Brusque 2,
#: Blumenau 3, Rio do Sul 4) existem no mesmo portal e NÃO são lidos aqui.
MUNICIPIO_ITAJAI = 1


def carga(pagina: str) -> dict:
    """O JSON do `data-page`, ou {} quando a página não é a esperada."""
    m = RE_DATA_PAGE.search(pagina)
    if not m:
        return {}
    try:
        return json.loads(_html.unescape(m.group(1)))
    except json.JSONDecodeError:
        return {}


def _sem_acento(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", texto)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def municipio_da_carga(dados: dict) -> dict | None:
    """{id, nome} do município que a PÁGINA diz servir, ou None se ela não diz.

    Vem de `props.municipioId` cruzado com `props.municipios`. Nunca do domínio:
    o portal é de Itajaí e serve quatro cidades."""
    props = dados.get("props") or {}
    mid = props.get("municipioId")
    if not isinstance(mid, int):
        return None
    nome = next((m.get("nome") for m in (props.get("municipios") or [])
                 if isinstance(m, dict) and m.get("id") == mid), None)
    return {"id": mid, "nome": nome}


def conferir_municipio(dados: dict, esperado: int) -> str | None:
    """None quando pedido, página, estações e fonte concordam; senão, o motivo.

    Quatro coisas têm que apontar para a mesma cidade: o `municipio_id` pedido,
    o `props.municipioId` respondido, o `municipio_id` de cada estação e a
    `fonte` que ela declara. A página de Brusque com cabeçalho "Situação atual
    em Itajaí" (21/09/2026) é o motivo de conferir os quatro, e não um."""
    m = municipio_da_carga(dados)
    if m is None:
        return "a página não diz de que município é (sem props.municipioId)"
    if m["id"] != esperado:
        return f"pedido municipio_id={esperado}; a página respondeu {m['id']} ({m['nome']!r})"
    for e in (dados.get("props") or {}).get("estacoes") or []:
        if not isinstance(e, dict):
            continue
        if e.get("municipio_id") not in (None, esperado):
            return (f"estação {e.get('codigo')!r} é do município {e.get('municipio_id')}, "
                    f"não de {esperado}")
        fonte, nome = e.get("fonte"), m["nome"]
        if isinstance(fonte, str) and isinstance(nome, str) \
                and _sem_acento(nome) not in _sem_acento(fonte):
            return (f"estação {e.get('codigo')!r} declara fonte {fonte!r}, e o município da "
                    f"página é {nome!r}")
    return None


def distancia_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    raio = 6_371_000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * raio * math.asin(math.sqrt(h))


def para_brasilia(iso: str | None) -> str | None:
    """UTC com offset -> Brasília SEM fuso, o contrato do repositório."""
    if not isinstance(iso, str) or not iso.strip():
        return None
    try:
        q = datetime.fromisoformat(iso)
    except ValueError:
        return None
    if q.tzinfo is None:
        # Sem offset não dá para saber o fuso, e assumir seria inventar a idade.
        return None
    return q.astimezone(FUSO).replace(tzinfo=None, microsecond=0).isoformat()


def _por_codigo() -> dict[str, dict]:
    saida = {}
    for e in estacoes_tempo_real():
        cod = e.get("codigo")
        if isinstance(cod, str) and cod.startswith("DC-"):
            saida[cod] = e
    return saida


def parse(pagina: str) -> list[dict]:
    dados = carga(pagina)
    estacoes = ((dados.get("props") or {}).get("estacoes")) or []
    if not isinstance(estacoes, list):
        return []
    # A página de OUTRO município tem a mesma moldura e o mesmo cabeçalho
    # "Situação atual em Itajaí". Nada dela pode virar leitura de Itajaí.
    motivo = conferir_municipio(dados, MUNICIPIO_ITAJAI)
    if motivo is not None:
        print(f"recusada a página inteira — {motivo}", file=sys.stderr)
        return []

    cadastro = _por_codigo()
    leituras: list[dict] = []
    recusadas: list[str] = []

    for e in estacoes:
        if not isinstance(e, dict):
            continue
        cru = str(e.get("codigo") or "")
        m = re.fullmatch(r"DC-?(\d{2})", cru)
        if not m:
            recusadas.append(f"código não reconhecido: {cru!r}")
            continue
        codigo = f"DC-{m.group(1)}"
        nossa = cadastro.get(codigo)
        if nossa is None:
            recusadas.append(f"{codigo}: não está no cadastro — entraria sem rio, cidade nem cota")
            continue

        # REGRA 1: a coordenada confirma a identidade.
        lat, lon = nossa.get("lat"), nossa.get("lon")
        plat, plon = e.get("latitude"), e.get("longitude")
        if not all(isinstance(v, (int, float)) for v in (lat, lon, plat, plon)):
            recusadas.append(f"{codigo}: sem coordenada dos dois lados — não dá para provar "
                             "que é a mesma régua")
            continue
        dist = distancia_m((lat, lon), (plat, plon))
        if dist > TOLERANCIA_COORD_M:
            recusadas.append(f"{codigo}: o portal a publica a {dist:.0f} m da cadastrada "
                             f"(teto {TOLERANCIA_COORD_M:.0f} m) — pode ser remanejamento de "
                             "estação, e o cadastro registra que já houve")
            continue

        nivel = e.get("nivel_rio_m")
        if not nivel_plausivel(nivel):
            recusadas.append(f"{codigo}: {nivel!r} não é nível de rio desta bacia "
                             f"(fora de {NIVEL_MINIMO_M:.0f}–{NIVEL_MAXIMO_M:.0f} m)")
            continue

        # REGRA 3: o carimbo da GRANDEZA vem antes do da estação.
        q = (e.get("qualidade") or {}).get("nivel_rio_m") or {}
        medido_em = para_brasilia(q.get("medido_em")) or para_brasilia(e.get("medido_em"))
        if medido_em is None:
            recusadas.append(f"{codigo}: sem horário de medição legível — sem idade, a leitura "
                             "não pode entrar")
            continue

        leituras.append({
            # REGRA 2: o título é o do cadastro.
            "estacao": nossa["titulo"],
            "rio": nossa.get("rio"),
            "cidade": nossa.get("cidade"),
            "nivel_m": float(nivel),
            "medido_em": medido_em,
        })

    for msg in recusadas:
        print(f"recusada — {msg}", file=sys.stderr)
    return leituras


def coletar(pagina: str | None = None) -> dict:
    if pagina is None:
        from comum import baixar
        pagina = baixar(URL)
    return {
        "fonte": URL,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
        "leituras": parse(pagina),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", type=Path, help="HTML salvo, para rodar sem rede")
    args = ap.parse_args()
    d = coletar(args.arquivo.read_text(encoding="utf-8") if args.arquivo else None)
    for l in d["leituras"]:
        print(f"{l['nivel_m']:6.2f} m  {l['medido_em']}  {l['estacao']}")
    print(f"\n{len(d['leituras'])} leitura(s).", file=sys.stderr)
