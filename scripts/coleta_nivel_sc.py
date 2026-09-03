#!/usr/bin/env python3
"""
Coleta o NÍVEL BRUTO das estações da bacia do Itajaí na rede estadual (Defesa Civil de SC, GraphQL).

Fonte: POST https://monitoramento.defesacivil.sc.gov.br/graphql  (query Tags_data)
É a versão em Python do curl validado em 01/09/2026. Irmão do `coleta_chuva_sc.py` (mesma fonte).

REGRA DE FUNDO: o nível estadual é BRUTO — está no zero de régua da estação, NÃO no zero das cotas
municipais. Por isso TODA leitura sai com:
    origem="estadual", datum="bruto_estadual", offset_datum=None, usar_para_cota=False
Nada daqui pinta faixa nem dispara aviso até um offset ser calibrado POR ESTAÇÃO e validado em mais de um
instante (o caso Brusque, 17h "offset ~0" -> 23h diferença de 1,9 m, mostra que um ponto só não basta).

ARMADILHAS que este coletor já trata (todas vistas em 01/09):
  1. `rio_nivel.value` é o NÚMERO; `rio_nivel.show.value` é só flag de exibição (booleano). Lê-se .value,
     e ainda assim com guarda `e_numero` (um booleano não é metro).
  2. `value` null = "sem leitura agora", NÃO "sem sensor" — EXCETO as estações de NAO_MEDE_NIVEL (abaixo),
     que a própria API declara sem `tem_nivel_do_rio`: nessas, null é estrutural, não pontual.
  3. Estações "(H)" reportam ALTITUDE/cota absoluta (Salete 399 m, Petrolândia 876 m…). Descartadas.
     Também descarta qualquer valor > LIMITE_M (30 m) — nenhum rio urbano da bacia chega perto disso.
  4. `rio_nivel_tendencia.value` é LIXO (Pomerode 108, Ibirama 85, Trombudo 113). Ignorado. Tendência se
     calcula da NOSSA série.
  5. FUSO — o mesmo erro que já "custou uma sessão" (ver CLAUDE.md). O GraphQL manda UTC (+00:00), mas o
     contrato do projeto é `medido_em` em hora de BRASÍLIA SEM fuso — é o que `coleta_itajai.py` grava, o
     site lê com `deBrasilia()`, o vigia lê com `FUSO`, e o irmão `coleta_chuva_sc.py` já converte assim.
     Por isso `medido_em` passa por `hora_local()`; guardar UTC cru deslocaria a idade em 3 h. (`coletado_em`
     é outro campo, do momento da coleta, e esse SIM é UTC.)
  6. `position.bacia` pode ser null -> tratado como "" no filtro.
  7. Guabiruba 24,81 m e Pomerode são leituras suspeitas -> vão para `suspeitas`, não para `leituras`.
     CORREÇÃO (03/09/2026, ver docs/API-DCSC-CAMPOS-NOVOS.md): a investigação dos campos `type` e
     `filter.relacao.tem_nivel_do_rio` da API confirma que as DUAS são estações Hidro reais que DECLARAM
     medir nível de rio — o problema é datum/escala do valor bruto, não sensor ou grandeza errada. A lista
     SUSPEITAS abaixo foi reescrita para não sugerir mais "sensor errado".
  8. Gaspar (DCSC-00005) e Blumenau (DCSC-00026) NÃO medem nível de rio nesta rede — confirmado pela mesma
     investigação (`tem_nivel_do_rio = false`; Blumenau é `type = "Meteo"`). Antes deste coletor tratava as
     duas como "sensor de rio que às vezes fica mudo" (armadilha 2); estava errado — é ausência estrutural
     da capacidade, não intermitência. Vão para o balde `nao_mede_nivel`, não para `sem_leitura`.
  9. QUERY_CAMPOS_NOVOS (03/09/2026) pede também `type`, `filter.relacao.tem_nivel_do_rio` e
     `data.rio.{rio_nome,rio_area_drenagem}`. A API usa allowlist de query persistida e pode recusar
     qualquer string que não seja a exata do bundle (ver o .md citado) — este ambiente não alcança o
     host para validar isso de antemão. Por isso `buscar()` TENTA a enriquecida primeiro e, se a API
     devolver `errors`, CAI para a QUERY original (validada em 01/09) automaticamente — nunca decide
     às cegas qual string funciona; é a resposta real, na primeira execução na VPS, que decide. Quando
     a enriquecida funciona, `converter()` usa `tem_nivel_do_rio` da própria resposta para classificar
     (substituindo NAO_MEDE_NIVEL); quando não funciona (campo ausente = None), cai para os dicionários
     hardcoded abaixo, que continuam servindo de rede de segurança.

Uso:
    python3 scripts/coleta_nivel_sc.py            # imprime + grava data/tempo-real/ultimo_nivel_sc.json
    python3 scripts/coleta_nivel_sc.py --so-acu   # só as estações mapeadas do Itajaí-Açu/Mirim
Rodar na VPS (o container do assistente não alcança este host). Cron: */15.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

URL = "https://monitoramento.defesacivil.sc.gov.br/graphql"
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
SAIDA = Path(__file__).resolve().parent.parent / "data" / "tempo-real"
LIMITE_M = 30.0          # acima disto não é régua de rio urbano (é altitude / reservatório grande)
BACIA_RE = "Itaja"       # filtro em position.bacia (case-insensitive)

#: Fuso das medições no resto do projeto: `medido_em` é hora de Brasília SEM fuso, e o GraphQL devolve UTC
#: com fuso. Converter errado desloca a idade de toda leitura em três horas — e a idade é o que diz se o
#: número serve. Idêntico ao `coleta_chuva_sc.py`.
FUSO_BRASILIA = timezone(timedelta(hours=-3))

# Estações que interessam à cadeia (código → cidade/slug). Fora daqui ainda é coletado, só sem 'cidade'.
CADEIA = {
    "DCSC-00025": "agrolandia", "DCSC-00039": "ituporanga", "DCSC-00033": "pouso-redondo",
    "DCSC-00041": "taio", "DCSC-00031": "laurentino", "DCSC-00001": "agronomica",
    "DCSC-00013": "rio-do-sul", "DCSC-00032": "lontras", "DCSC-00020": "ibirama",
    "DCSC-00043": "presidente-getulio", "DCSC-00021": "jose-boiteux", "DCSC-00003": "ascurra",
    "DCSC-00006": "indaial", "DCSC-00023": "timbo", "DCSC-00004": "benedito-novo",
    "DCSC-00011": "rio-dos-cedros", "DCSC-00028": "doutor-pedrinho", "DCSC-00007": "pomerode",
    "DCSC-00026": "blumenau", "DCSC-00005": "gaspar", "DCSC-00030": "ilhota",
    "DCSC-00163": "ilhota-arraial-dos-cunhas",
    # Mirim
    "DCSC-00024": "vidal-ramos", "DCSC-00018": "botuvera", "DCSC-00027": "botuvera-2",
    "DCSC-00019": "brusque", "DCSC-00029": "guabiruba",
    # barragens (reservatório, datum próprio — nunca cota urbana)
    "DCSC-00040": "barragem-oeste-taio", "DCSC-00038": "barragem-sul-ituporanga",
}
RESERVATORIOS = {"DCSC-00040", "DCSC-00038"}
# Estações Hidro que a API confirma medir nível de rio (`tem_nivel_do_rio=true`, investigação de
# 03/09/2026, docs/API-DCSC-CAMPOS-NOVOS.md), mas cujo valor bruto é implausível para o rio local —
# problema de DATUM/ESCALA da estação, não sensor ou grandeza errada. Vão para 'suspeitas': o valor
# não é usável cru, mas a estação é real e mede a grandeza certa.
SUSPEITAS = {"DCSC-00029": "Guabiruba ~24,8 m: estação Hidro real (tem_nivel_do_rio=true), mas o valor "
                           "bruto é implausível para o ribeirão — datum/escala própria não calibrada",
             "DCSC-00007": "Pomerode: estação Hidro real (tem_nivel_do_rio=true), mas oscila de forma "
                           "implausível entre leituras — datum/escala própria não calibrada"}
# Estações que a mesma investigação confirma NÃO medirem nível de rio nesta rede
# (`tem_nivel_do_rio=false`; Blumenau é `type="Meteo"`). `value` vem null sempre — não é "sensor mudo
# agora" (armadilha 2), é ausência estrutural. Vão para 'nao_mede_nivel', não para 'sem_leitura'.
NAO_MEDE_NIVEL = {"DCSC-00005": "Gaspar: tem_nivel_do_rio=false na API estadual — não mede nível de rio "
                                 "nesta rede (cota de Gaspar vem da Defesa Civil municipal, não da DCSC)",
                  "DCSC-00026": "Blumenau: type=Meteo, tem_nivel_do_rio=false — estação meteorológica, "
                                 "não mede nível de rio (cota de Blumenau vem do AlertaBlu, não da DCSC)"}

#: Query validada por curl em 01/09/2026. Sempre funciona — é o fallback seguro de `buscar()`.
QUERY = ('query Tags_data { tags_data(clients: ["secretaria-de-defesa-civil"]) { qualle_meteorologia { '
         'codigo name { general local } timestamp position { bacia latitude longitude } '
         'data { rio { rio_nivel { value } } chuva { acumulado { h024 { value } } } } } } }')

#: Tentativa (03/09/2026, docs/API-DCSC-CAMPOS-NOVOS.md) de pedir também `type`,
#: `filter.relacao.tem_nivel_do_rio` e `data.rio.{rio_nome,rio_area_drenagem}`. Não validada contra
#: o host real por este ambiente (allowlist de query persistida — ver armadilha 9 no docstring).
#: `buscar()` tenta esta primeiro e cai para `QUERY` se a API recusar.
QUERY_CAMPOS_NOVOS = (
    'query Tags_data { tags_data(clients: ["secretaria-de-defesa-civil"]) { qualle_meteorologia { '
    'codigo name { general local } timestamp type position { bacia latitude longitude } '
    'filter { relacao { tem_nivel_do_rio tem_vazao_do_rio tem_chuva_acumulada } } '
    'data { rio { rio_nome rio_nivel { value } rio_area_drenagem } '
    'chuva { acumulado { h024 { value } } } } } } }'
)


def e_numero(valor) -> bool:
    """`isinstance(True, int)` é True em Python, e True não é metro."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def hora_local(carimbo: str | None) -> str | None:
    """UTC do GraphQL -> hora de Brasília sem fuso, que é o formato do projeto (ver armadilha 5)."""
    if not carimbo:
        return None
    try:
        t = datetime.fromisoformat(str(carimbo).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds")


def _post(query: str) -> dict:
    r = requests.post(URL, json={"operationName": "Tags_data", "query": query},
                      headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    return r.json()


def buscar() -> list[dict]:
    """
    Tenta QUERY_CAMPOS_NOVOS (type/tem_nivel_do_rio/rio_area_drenagem); se a API recusar
    (`errors` no GraphQL, ou a request falhar), cai para a QUERY original de 01/09 — nunca
    escolhe às cegas qual string funciona, é a resposta real que decide (armadilha 9).
    """
    try:
        j = _post(QUERY_CAMPOS_NOVOS)
        if j.get("errors"):
            raise RuntimeError(j["errors"])
    except Exception as e:
        print(f"aviso: query com campos novos (type/tem_nivel_do_rio/rio_area_drenagem) recusada "
              f"({e}); caindo para a query original de 01/09", file=sys.stderr)
        j = _post(QUERY)
        if j.get("errors"):
            raise RuntimeError(j["errors"])
    return j["data"]["tags_data"]["qualle_meteorologia"]


def converter(
    estacoes: list[dict], so_cadeia: bool = False
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Devolve (leituras, sem_leitura, suspeitas, nao_mede_nivel). Tudo com datum bruto e usar_para_cota=False."""
    leituras, sem_leitura, suspeitas, nao_mede_nivel = [], [], [], []
    for s in estacoes:
        bacia = (s.get("position") or {}).get("bacia") or ""          # armadilha 6
        if BACIA_RE.lower() not in bacia.lower():
            continue
        cod = s.get("codigo", "")
        cidade = CADEIA.get(cod)
        if so_cadeia and not cidade:
            continue
        nome = " ".join(x for x in [(s.get("name") or {}).get("general"), (s.get("name") or {}).get("local")] if x).strip()
        if "(H)" in nome:                                              # armadilha 3
            continue
        rio_bloco = (s.get("data") or {}).get("rio") or {}
        rio = rio_bloco.get("rio_nivel") or {}
        val = rio.get("value")                                         # armadilha 1 (NÃO show.value)
        chuva = (((s.get("data") or {}).get("chuva") or {}).get("acumulado") or {}).get("h024") or {}
        # Campos novos (armadilha 9): None quando QUERY_CAMPOS_NOVOS não foi aceita pela API —
        # nesse caso caímos nos dicionários hardcoded abaixo, como antes.
        tipo_estacao = s.get("type")
        declara_nivel = ((s.get("filter") or {}).get("relacao") or {}).get("tem_nivel_do_rio")
        base = {
            "codigo": cod, "estacao": nome, "cidade": cidade,
            "origem": "estadual",
            "datum": "reservatorio" if cod in RESERVATORIOS else "bruto_estadual",
            "offset_datum": None, "usar_para_cota": False,
            "medido_em": hora_local(s.get("timestamp")),                # UTC (+00:00) -> Brasília (armadilha 5)
            "chuva_24h_mm": chuva.get("value") if e_numero(chuva.get("value")) else None,
            "lat": (s.get("position") or {}).get("latitude"),
            "lon": (s.get("position") or {}).get("longitude"),
            "tipo_estacao": tipo_estacao,
            "rio_nome": rio_bloco.get("rio_nome"),
            "rio_area_drenagem_km2": rio_bloco.get("rio_area_drenagem"),
        }
        if declara_nivel is False:                                     # armadilha 9: a API declara
            motivo = "API declara tem_nivel_do_rio=false"
            if tipo_estacao:
                motivo += f" (type={tipo_estacao})"
            nao_mede_nivel.append({**base, "motivo": motivo})
            continue
        if declara_nivel is None and cod in NAO_MEDE_NIVEL:             # armadilha 8: rede de segurança
            nao_mede_nivel.append({**base, "motivo": NAO_MEDE_NIVEL[cod]})
            continue
        if val is None:                                                # armadilha 2
            sem_leitura.append({**base, "motivo": "value null — sensor sem leitura agora (não 'sem sensor')"})
            continue
        if not e_numero(val):                                          # armadilha 1 (booleano/lixo)
            sem_leitura.append({**base, "motivo": f"value não numérico: {val!r}"})
            continue
        v = float(val)
        if cod in SUSPEITAS:                                           # armadilha 7
            suspeitas.append({**base, "nivel_bruto_m": round(v, 2), "motivo": SUSPEITAS[cod]})
            continue
        if v > LIMITE_M and cod not in RESERVATORIOS:                  # armadilha 3 (valor absurdo)
            suspeitas.append({**base, "nivel_bruto_m": round(v, 2), "motivo": f"> {LIMITE_M} m: altitude/grandeza errada"})
            continue
        leituras.append({**base, "nivel_bruto_m": round(v, 2)})
    return leituras, sem_leitura, suspeitas, nao_mede_nivel


def _linha_serie(l: dict) -> dict:
    """O que vai para a série ndjson — só o essencial do nível bruto."""
    return {
        "codigo": l.get("codigo"), "cidade": l.get("cidade"), "estacao": l.get("estacao"),
        "datum": l.get("datum"), "nivel_bruto_m": l.get("nivel_bruto_m"), "medido_em": l.get("medido_em"),
    }


def _chaves_existentes(arquivo: Path) -> set:
    """(codigo, medido_em) já gravados no mês, para não duplicar."""
    vistas: set = set()
    if not arquivo.exists():
        return vistas
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            d = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if d.get("medido_em"):
            vistas.add((d.get("codigo", ""), d["medido_em"]))
    return vistas


def acumular_serie(leituras: list[dict]) -> tuple[int, int]:
    """
    Acrescenta o nível bruto novo em `nivel-sc-AAAA-MM.ndjson` (dedup por codigo+medido_em).

    Devolve (novas, repetidas). É a matéria-prima da tendência confiável e do offset
    calibrado — o `.ndjson` fica fora do git (é série, não fonte de verdade). Igual ao
    `acumular` do `coleta_niveis.py`, só que por `codigo` (a régua estadual não tem nome
    único como as municipais).
    """
    SAIDA.mkdir(parents=True, exist_ok=True)
    novas = repetidas = 0
    por_mes: dict[str, list[dict]] = {}
    for l in leituras:
        m = l.get("medido_em")
        if not m:                       # sem carimbo não dá para deduplicar nem datar o pico
            continue
        por_mes.setdefault(str(m)[:7], []).append(l)
    for mes, do_mes in sorted(por_mes.items()):
        arquivo = SAIDA / f"nivel-sc-{mes}.ndjson"
        vistas = _chaves_existentes(arquivo)
        linhas = []
        for l in do_mes:
            chave = (l.get("codigo", ""), l["medido_em"])
            if chave in vistas:
                repetidas += 1
                continue
            vistas.add(chave)
            linhas.append(json.dumps(_linha_serie(l), ensure_ascii=False))
            novas += 1
        if linhas:
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
    return novas, repetidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-acu", action="store_true", help="só estações mapeadas na CADEIA")
    a = ap.parse_args()
    try:
        est = buscar()
    except Exception as e:
        print(f"ERRO ao buscar a rede estadual: {e}", file=sys.stderr)
        return 1
    leituras, sem, susp, nao_mede = converter(est, so_cadeia=a.so_acu)
    saida = {
        "fonte": URL, "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aviso": "NÍVEL BRUTO (datum da estação). usar_para_cota=False em todas. Não comparar com cotas municipais sem offset calibrado.",
        "leituras": leituras, "sem_leitura": sem, "suspeitas": susp, "nao_mede_nivel": nao_mede,
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "ultimo_nivel_sc.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    novas, repetidas = acumular_serie(leituras)
    for l in sorted(leituras, key=lambda x: x["cidade"] or "zz"):
        print(f"{l['nivel_bruto_m']:6.2f} m bruto  {l['codigo']}  {l['estacao'][:32]:32s}  [{l['cidade'] or '-'}]")
    print(f"\n{len(leituras)} com nível · {len(sem)} sem leitura agora · {len(susp)} suspeitas · "
          f"{len(nao_mede)} não medem nível → data/tempo-real/ultimo_nivel_sc.json")
    print(f"série: +{novas} leitura(s) nova(s), {repetidas} repetida(s) em nivel-sc-AAAA-MM.ndjson")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
