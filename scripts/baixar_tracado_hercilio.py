#!/usr/bin/env python3
"""
Baixa do OpenStreetMap o traçado do Rio Hercílio — o Itajaí do Norte, que passa por Ibirama.

POR QUE FALTAVA (05/10/2026). O Monitor já pede `data/rios/hercilio.geojson` (MonitorBacia.tsx, traçados
opcionais) e o conversor já tinha a chave `hercilio`, mas o arquivo nunca nasceu: nenhuma consulta do
Overpass pediu esse rio. E pedir só "Hercílio" não bastaria: no OSM o rio está partido em DOIS nomes —
"Rio Itajaí do Norte" a montante (José Boiteux, a barragem Norte) e "Rio Hercílio" a jusante (Ibirama até
a confluência com o Açu). A ANA o cadastra como um rio só, "Rio Itajaí do Norte ou Hercílio" (Hidrografia
do SNIRH), e é por isso que os dois nomes entram no MESMO arquivo — ao contrário do Rio Conceição, que é
outro curso e ficou separado do Canhanduba.

POR QUE IMPORTA. A Defesa Civil de Ibirama confirmou em 05/10/2026 (C26) que as faixas do rio são lidas na
DCSC-00020. Com o traçado, o pino de Ibirama deixa de flutuar e a tela mostra o rio de onde a água vem.

O QUE CONFERE ANTES DE GRAVAR (sem isso, não grava):
  - os DOIS nomes vieram (um só seria o rio pela metade);
  - o traçado chega ao Açu: alguma ponta a menos de CHEGA_AO_ACU_KM do `itajai-acu.geojson`;
  - o traçado passa pela estação de Ibirama: o pino do cadastro a menos de PASSA_EM_IBIRAMA_KM.

Gravado, `converter_tracado_rios.py` gera `data/rios/hercilio.geojson`. Fonte: © OpenStreetMap
contributors, ODbL. Roda onde o Overpass responde: na VPS ou no Actions (`baixar-tracado-hercilio.yml`).

Uso:
    python3 scripts/baixar_tracado_hercilio.py            # baixa e confere, não grava
    python3 scripts/baixar_tracado_hercilio.py --gravar   # grava data/brutos/tracado-hercilio-osm.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from baixar_vao_canhanduba import BACKOFF_BASE_S, ESPELHOS, STATUS_QUE_ESPERAM, TENTATIVAS_POR_ESPELHO  # noqa: E402
from comum import USER_AGENT  # noqa: E402

SAIDA = RAIZ / "data" / "brutos" / "tracado-hercilio-osm.json"
RIOS = RAIZ / "data" / "rios"

#: Os dois nomes do mesmo rio no OSM. Match EXATO (com e sem acento no Hercílio).
NOMES = ("Rio Itajaí do Norte", "Rio Hercílio", "Rio Hercilio")
NOMES_OBRIGATORIOS = (("Rio Itajaí do Norte",), ("Rio Hercílio", "Rio Hercilio"))

#: Caixa da sub-bacia do Itajaí do Norte (sul, oeste, norte, leste): das nascentes em Itaiópolis até a
#: confluência com o Açu. Larga de propósito — quem filtra é o nome.
CAIXA = (-27.35, -50.45, -26.05, -49.25)

CONSULTA = """[out:json][timeout:120];
way["waterway"="river"]["name"~"^Rio (Itajaí do Norte|Hercílio|Hercilio)$"]({sul},{oeste},{norte},{leste});
out geom;"""

CHEGA_AO_ACU_KM = 1.0
PASSA_EM_IBIRAMA_KM = 0.5

K_LON = math.cos(math.radians(27))


def km(a, b) -> float:
    return math.hypot((a[0] - b[0]) * K_LON, a[1] - b[1]) * 111.32


def consulta() -> str:
    s, o, n, l = CAIXA
    return CONSULTA.format(sul=s, oeste=o, norte=n, leste=l)


def buscar(*, transporte=None, dormir=None, avisar=print) -> tuple[dict, str]:
    """A consulta do Hercílio. Ver `buscar_consulta`."""
    return buscar_consulta(consulta(), transporte=transporte, dormir=dormir, avisar=avisar)


def base_osm(resposta: dict) -> str | None:
    """`osm3s.timestamp_osm_base` da resposta, como veio (pode ser inválido), ou None se ela não disse."""
    v = (resposta.get("osm3s") or {}).get("timestamp_osm_base") if isinstance(resposta, dict) else None
    return v if isinstance(v, str) and v else None


def base_do_arquivo(caminho: Path) -> str | None:
    """`base_osm` do bruto já gravado, ou None se ele não existe, não abre ou não guardou a data."""
    try:
        return base_osm(json.loads(caminho.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None


def instante_da_base(base: str | None) -> datetime | None:
    """A data da base como instante UTC, ou None se faltar ou não for ISO 8601 com fuso."""
    if not base:
        return None
    try:
        t = datetime.fromisoformat(base.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


#: Resultado de `comparar_bases` → (grava?, o que acontece com o arquivo, como o rodada.json diz).
#: A data do DOWNLOAD nunca entra: um espelho atrasado responde hoje com dados de meses atrás.
DECISOES = {
    "sem_arquivo": (True, "novo (não havia arquivo)"),
    "mais_nova": (True, "substituído, base recebida mais nova"),
    "igual": (False, "mantido, mesma base"),
    "antiga": (False, "mantido, base existente mais nova"),
    "resposta_sem_data": (False, "mantido, resposta sem data de base válida (incerto)"),
    "arquivo_sem_data": (False, "mantido, arquivo existente sem data de base válida (incerto)"),
}


def comparar_bases(base_recebida: str | None, base_existente: str | None, arquivo_existe: bool) -> str:
    """
    Uma chave de DECISOES. Só substitui o que é COMPROVADAMENTE mais novo: base recebida estritamente
    posterior à do arquivo. Mesma base não reescreve. Sem data válida de um dos lados não dá para provar, e o
    arquivo fica, com a incerteza registrada. Sem arquivo, qualquer resposta conferida serve.
    """
    if not arquivo_existe:
        return "sem_arquivo"
    existente = instante_da_base(base_existente)
    if existente is None:
        return "arquivo_sem_data"
    recebida = instante_da_base(base_recebida)
    if recebida is None:
        return "resposta_sem_data"
    if recebida > existente:
        return "mais_nova"
    return "igual" if recebida == existente else "antiga"


#: Respostas que não servem para ESTE arquivo: a busca tenta o próximo espelho.
NAO_SERVE_NA_BUSCA = ("antiga", "resposta_sem_data")


def buscar_consulta(texto: str, *, transporte=None, dormir=None, avisar=print,
                    registro: list | None = None, arquivo: Path | None = None) -> tuple[dict, str]:
    """
    (resposta do Overpass conferida como JSON, espelho que respondeu). Insiste como o vão do Canhanduba.

    `registro`, se dado, recebe uma linha por tentativa: {espelho, tentativa, resultado} e, quando houve
    resposta, `base_osm`. É o que o relatório da rodada mostra.

    `arquivo` (o bruto já gravado): a resposta é julgada pela data da base OSM contra a dele
    (`comparar_bases`). Base mais antiga, ou resposta sem data válida, não serve — o espelho pode estar
    atrasado (06/10/2026: o kumi.systems serviu o Benedito com a base de 01/06/2026, e ela teria substituído a
    de 06/10 sem aviso). Fica no registro com a decisão, e a busca passa ao próximo espelho; se nenhum servir,
    sai com SystemExit, e quem chamou mantém o arquivo. Mesma base, base mais nova, arquivo sem data e
    arquivo ausente voltam: quem grava decide pela mesma tabela.
    """
    import time

    dormir = dormir or time.sleep
    if transporte is None:
        import requests

        def transporte(url, dados, cabecalhos, timeout):  # noqa: E306
            return requests.post(url, data=dados, headers=cabecalhos, timeout=timeout)

    def anota(espelho: str, tentativa: int, resultado: str, **extra) -> None:
        if registro is not None:
            registro.append({"espelho": espelho, "tentativa": tentativa, "resultado": resultado, **extra})

    existe = arquivo is not None and arquivo.exists()
    base_existente = base_do_arquivo(arquivo) if existe else None

    ultimo = ""
    for espelho in ESPELHOS:
        for tentativa in range(1, TENTATIVAS_POR_ESPELHO + 1):
            onde = f"{espelho} (tentativa {tentativa}/{TENTATIVAS_POR_ESPELHO})"
            try:
                r = transporte(espelho, {"data": texto}, {"User-Agent": USER_AGENT}, 240)
            except OSError as e:
                # Timeout ou queda de conexão (requests.RequestException é OSError) conta como fila: espera e
                # tenta de novo, depois o próximo espelho. Em 06/10/2026, um ReadTimeout do kumi.systems
                # derrubava a rodada inteira, com os rios seguintes sem baixar.
                motivo = f"{type(e).__name__}: {e}"
                anota(espelho, tentativa, motivo)
                ultimo = f"{onde} não respondeu: {motivo}"
                if tentativa == TENTATIVAS_POR_ESPELHO:
                    break
                espera = BACKOFF_BASE_S * 2 ** (tentativa - 1)
                avisar(f"   {onde}: {type(e).__name__} — esperando {espera}s")
                dormir(espera)
                continue
            if r.status_code == 200:
                try:
                    dados = json.loads(r.text)
                except ValueError:
                    anota(espelho, tentativa, "HTTP 200 sem JSON")
                    ultimo = f"{onde} respondeu 200 mas o corpo NÃO é JSON.\n{r.text[:400]}"
                    break
                base = base_osm(dados)
                decisao = comparar_bases(base, base_existente, existe) if arquivo is not None else None
                if decisao in NAO_SERVE_NA_BUSCA:
                    motivo = (f"base OSM {base} mais antiga que a do arquivo ({base_existente})"
                              if decisao == "antiga" else f"resposta sem data de base válida ({base!r})")
                    anota(espelho, tentativa, motivo, base_osm=base, decisao=decisao)
                    ultimo = f"{onde}: {motivo}"
                    avisar(f"   {onde}: {motivo} — tentando o próximo espelho")
                    break
                anota(espelho, tentativa, "ok", base_osm=base, **({"decisao": decisao} if decisao else {}))
                return dados, espelho
            anota(espelho, tentativa, f"HTTP {r.status_code}")
            ultimo = f"{onde} respondeu {r.status_code}.\n{r.text[:400]}"
            if r.status_code not in STATUS_QUE_ESPERAM or tentativa == TENTATIVAS_POR_ESPELHO:
                break
            espera = BACKOFF_BASE_S * 2 ** (tentativa - 1)
            avisar(f"   {onde}: HTTP {r.status_code} — fila do Overpass; esperando {espera}s")
            dormir(espera)
        avisar(f"   {espelho} não serviu; tentando o próximo espelho")
    raise SystemExit(f"Nenhum espelho do Overpass respondeu com JSON. Último retorno:\n{ultimo}")


def linhas(elementos: list[dict]) -> dict[str, list[list[tuple[float, float]]]]:
    """nome → linhas [(lon, lat)], só dos ways com os nomes pedidos e geometria."""
    out: dict[str, list[list[tuple[float, float]]]] = {}
    for e in elementos:
        nome = (e.get("tags") or {}).get("name")
        if e.get("type") != "way" or nome not in NOMES:
            continue
        pts = [(p["lon"], p["lat"]) for p in e.get("geometry") or []
               if isinstance(p.get("lon"), (int, float)) and isinstance(p.get("lat"), (int, float))]
        if len(pts) >= 2:
            out.setdefault(nome, []).append(pts)
    return out


def comprimento_km(ls: list[list[tuple[float, float]]]) -> float:
    return sum(km(a, b) for l in ls for a, b in zip(l, l[1:]))


def tracado(rio_id: str) -> list[tuple[float, float]]:
    caminho = RIOS / f"{rio_id}.geojson"
    if not caminho.exists():
        return []
    d = json.loads(caminho.read_text(encoding="utf-8"))
    return [(c[0], c[1]) for l in d["geometry"]["coordinates"] for c in l]


def pino_de_ibirama() -> tuple[float, float]:
    e = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
    c = next(c for r in e["rios"].values() for c in r["cidades"] if c["id"] == "ibirama")
    lat, lon = c["coordenadas"]
    return (lon, lat)


def conferir(por_nome: dict[str, list], acu: list[tuple[float, float]], ibirama: tuple[float, float]) -> list[str]:
    """Problemas que impedem gravar. Lista vazia = pode gravar."""
    problemas = []
    for alternativas in NOMES_OBRIGATORIOS:
        if not any(por_nome.get(n) for n in alternativas):
            problemas.append(f"não veio nenhum way chamado {' / '.join(alternativas)}: seria o rio pela metade")
    todas = [l for ls in por_nome.values() for l in ls]
    if not todas:
        return problemas or ["nenhum way com os nomes pedidos"]
    if acu:
        pontas = [p for l in todas for p in (l[0], l[-1])]
        d = min(km(p, q) for p in pontas for q in acu)
        if d > CHEGA_AO_ACU_KM:
            problemas.append(f"o traçado não chega ao Açu: a ponta mais próxima fica a {d:.2f} km (limite {CHEGA_AO_ACU_KM} km)")
    else:
        problemas.append("falta data/rios/itajai-acu.geojson para conferir a confluência")
    d = min(km(ibirama, p) for l in todas for p in l)
    if d > PASSA_EM_IBIRAMA_KM:
        problemas.append(f"o traçado não passa pela estação de Ibirama: fica a {d:.2f} km do pino (limite {PASSA_EM_IBIRAMA_KM} km)")
    return problemas


def main() -> int:
    ap = argparse.ArgumentParser(description="Baixa o traçado do Rio Hercílio / Itajaí do Norte (OSM).")
    ap.add_argument("--gravar", action="store_true", help=f"grava {SAIDA.relative_to(RAIZ)} se passar na conferência")
    a = ap.parse_args()
    registro: list[dict] = []
    try:
        resposta, espelho = buscar_consulta(consulta(), registro=registro, arquivo=SAIDA)
    except SystemExit as e:
        # Sem resposta, ou só espelhos atrasados: o arquivo gravado fica como está, e a rodada avisa.
        print(f"AVISO: coleta não realizada; {SAIDA.relative_to(RAIZ)} mantido. {e}", file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS"):
            print("::warning title=Coleta do Hercílio não realizada::último arquivo válido mantido; "
                  + "; ".join(f"{t['espelho']} #{t['tentativa']}: {t['resultado']}" for t in registro))
        return 0
    por_nome = linhas(resposta.get("elements") or [])
    for nome, ls in sorted(por_nome.items()):
        print(f"   {nome}: {len(ls)} way(s), {comprimento_km(ls):.1f} km")
    problemas = conferir(por_nome, tracado("itajai-acu"), pino_de_ibirama())
    if problemas:
        for p in problemas:
            print(f"RECUSADO: {p}", file=sys.stderr)
        return 1
    print(f"conferido: chega ao Açu e passa por Ibirama ({sum(len(v) for v in por_nome.values())} ways)")
    decisao = comparar_bases(base_osm(resposta), base_do_arquivo(SAIDA), SAIDA.exists())
    grava, efeito = DECISOES[decisao]
    print(f"base OSM recebida {base_osm(resposta)} · do arquivo {base_do_arquivo(SAIDA)} → {efeito}")
    if a.gravar and not grava:
        if os.environ.get("GITHUB_ACTIONS") and decisao != "igual":
            print(f"::warning title=Hercílio não substituído::{efeito}")
        return 0
    if a.gravar:
        resposta["_consulta"] = {
            "overpass": consulta(),
            "espelho": espelho,
            "base_osm": base_osm(resposta),
            "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "script": "scripts/baixar_tracado_hercilio.py",
        }
        SAIDA.write_text(json.dumps(resposta, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"gravado: {SAIDA.relative_to(RAIZ)}. Agora: python3 scripts/converter_tracado_rios.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
