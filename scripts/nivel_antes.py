#!/usr/bin/env python3
"""
"Quando a régua X chegou à crista (ou passou de um nível), como estavam as outras N horas antes?"
Pedido do Jefferson de 05/10/2026: fazer a conta nas datas e cidades em que o repositório tem série
com hora. É SOMENTE LEITURA: não escreve em `enchentes.json`, `transito.json` nem em nenhum dado do site.

SÉRIES QUE ENTRAM (todas já versionadas em `data/brutos/`):
  - réguas do coletor de 2026 (`serie-2026-itajai/`): Itajaí DC-01 a DC-11, Blumenau (AlertaBlu) e Ilhota
    (DCSC-00030). A publicação "Blumenau" da página antiga de Itajaí fica de fora: vinha 3 h atrasada
    (CLAUDE.md, "Fuso dos carimbos");
  - Defesa Civil de SC na cheia de setembro de 2026 (`dcsc-cheia-2026-09-11-12/`, 10 min);
  - Asthon (Rio do Sul e Vidal Ramos, 2026) e o histórico horário de Taió (09–10/09/2026);
  - telemetria da ANA (`ana-telemetria-*.json`, 15 min): janelas de 2020 a 2023.
  Com `--series PASTA`, entra também a série inteira que o coletor guarda na VPS (`data/tempo-real/`, o
  mesmo formato), que tem Brusque e as outras cidades.

REGRAS DA CONTA:
  - Cada régua tem o seu zero: o número de uma régua nunca se compara com o de outra. O relatório põe as
    leituras lado a lado, cada uma na sua régua, com a hora da medição.
  - Fuso: todas as fontes de 2026 gravam hora de Brasília sem fuso (provado para DCSC e Asthon, CLAUDE.md).
    O fuso da telemetria da ANA NÃO foi conferido: por isso séries da ANA só se cruzam com séries da ANA
    (é o caso de 2020–2023, quando não há outra fonte com hora). Duas famílias nunca se misturam.
  - Crista: o máximo da série suavizada (média móvel de 1 h; de 12,42 h, um ciclo de maré, nas réguas de
    Itajaí que sentem a maré, `docs/ANALISE-CHEGADA-ITAJAI-2026.md`), que é o maior valor num raio de 48 h e
    subiu pelo menos 0,5 m nas 48 h antes. Crista na borda dos dados é marcada como "na borda" (piso).
  - "N horas antes": a leitura mais próxima até 10 min, ou a interpolação entre duas leituras com até
    60 min de intervalo. Sem isso, "sem leitura" — nunca se estima.
  - Isto é DESCRITIVO, não previsão nem calibração (a mesma regra de `analisar_chegada_itajai.py`).

Uso:
    python3 scripts/nivel_antes.py --listar
    python3 scripts/nivel_antes.py --alvo DC-04 --data 2026-09-12 --horas 3 6 12
    python3 scripts/nivel_antes.py --alvo DC-04 --data 2026-09-11 --nivel 1.5
    python3 scripts/nivel_antes.py --rua "São Rafael"   # Blumenau: hora em que a régua passou da cota da rua
    python3 scripts/nivel_antes.py --registradas         # ruas alagadas registradas à mão (data/ruas-alagadas.json)
    python3 scripts/nivel_antes.py --relatorio docs/NIVEL-ANTES.md
    python3 scripts/nivel_antes.py --series /opt/enchentes-vale-itajai/data/tempo-real --listar
"""
from __future__ import annotations

import argparse
import bisect
import csv
import functools
import gzip
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "data" / "brutos"

SUAVE_H = 1.0
SUAVE_MARE_H = 12.42
SUBIDA_MIN_M = 0.5
RAIO_CRISTA_H = 48
PERTO = timedelta(minutes=10)
VAO_MAX = timedelta(minutes=60)
HORAS_PADRAO = (3, 6, 12)

# Réguas de Itajaí que sentem a maré (Tabela 1 de docs/ANALISE-CHEGADA-ITAJAI-2026.md) e Ilhota.
SENTE_MARE = ("DC-01", "DC-03", "DC-04", "DC-06", "DC-09", "DC-11", "DCSC-00030")

# Telemetria da ANA: código → (nome, cidade do cadastro, rio).
ANA = {
    "83029900": ("ANA 83029900 Barragem Taió Montante", "taio", "itajai-acu"),
    "83050000": ("ANA 83050000 Taió", "taio", "itajai-acu"),
    "83250000": ("ANA 83250000 Ituporanga", "ituporanga", "itajai-acu"),
    "83300200": ("ANA 83300200 Rio do Sul", "rio-do-sul", "itajai-acu"),
    "83360000": ("ANA 83360000 José Boiteux (Hercílio)", "", "itajai-acu"),
    "83800002": ("ANA 83800002 Blumenau", "blumenau", "itajai-acu"),
    "83892990": ("ANA 83892990 Salseiro (Vidal Ramos)", "vidal-ramos", "itajai-mirim"),
}
# Defesa Civil de SC: código → cidade do cadastro (nome da estação vem do CSV de estações).
DCSC_CIDADE = {
    "DCSC-00003": "ascurra", "DCSC-00006": "indaial", "DCSC-00007": "", "DCSC-00011": "rio-dos-cedros",
    "DCSC-00013": "rio-do-sul", "DCSC-00019": "brusque", "DCSC-00023": "timbo", "DCSC-00030": "ilhota",
    "DCSC-00032": "lontras", "DCSC-00062": "", "DCSC-00163": "",
}
# Régua em que as cotas de rua de `data/cotas-ruas.json` foram publicadas, por cidade. Só entra cidade em
# que a série com hora é COMPROVADAMENTE essa régua: Blumenau, AlertaBlu = régua de hoje (CLAUDE.md). Gaspar,
# Brusque e Rio do Sul têm cotas, mas falta conferir qual estação do coletor é a régua delas.
REGUA_DAS_COTAS = {"blumenau": "Blumenau (AlertaBlu)"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


@dataclass
class Serie:
    id: str
    cidade: str
    rio: str
    fonte: str
    familia: str  # "brasilia" ou "ana" — famílias não se cruzam
    pontos: list[tuple[datetime, float]] = field(default_factory=list)
    _cristas: dict = field(default_factory=dict, repr=False, compare=False)
    # (cidade, rio) de cada leitura do coletor: a série fica com o par da maioria. A DC-11 já foi gravada como
    # Ilhota no começo de setembro; a primeira linha lida não pode decidir de que cidade a régua é.
    _votos: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def mare(self) -> bool:
        return self.id.startswith(SENTE_MARE)

    def arrumar(self) -> "Serie":
        visto: dict[datetime, float] = {}
        for t, v in self.pontos:
            visto[t] = v
        self.pontos = sorted(visto.items())
        return self


# ---------------------------------------------------------------- leitura das fontes

def _abrir(p: Path):
    return gzip.open(p, "rt", encoding="utf-8") if p.suffix == ".gz" else open(p, encoding="utf-8")


def _quando(texto: str) -> datetime | None:
    try:
        return datetime.fromisoformat(texto.replace(" ", "T")[:19])
    except (ValueError, AttributeError):
        return None


def ler_tempo_real(pasta: Path, series: dict[str, Serie]) -> None:
    """O formato do coletor (`AAAA-MM.ndjson[.gz]` e `nivel-sc-AAAA-MM.ndjson[.gz]`), hora de Brasília."""
    for arq in sorted(pasta.glob("*.ndjson*")):
        nome = arq.name
        if nome.startswith("chuva"):
            continue
        estadual = nome.startswith("nivel-sc")
        if not (estadual or nome[:4].isdigit()):
            continue
        with _abrir(arq) as f:
            for linha in f:
                try:
                    d = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                t = _quando(d.get("medido_em", ""))
                if t is None:
                    continue
                if estadual:
                    v, sid = d.get("nivel_bruto_m"), f"{d.get('codigo')} {d.get('estacao')}"
                    cidade, rio = d.get("cidade") or DCSC_CIDADE.get(d.get("codigo", ""), ""), ""
                else:
                    sid = d.get("estacao") or ""
                    if sid == "Blumenau":  # página antiga de Itajaí, 3 h atrasada
                        continue
                    v, cidade, rio = d.get("nivel_m"), d.get("cidade") or "", d.get("rio") or ""
                if not isinstance(v, (int, float)):
                    continue
                s = series.setdefault(sid, Serie(sid, cidade, rio, "coletor", "brasilia"))
                s.pontos.append((t, float(v)))
                s._votos[(cidade, rio)] = s._votos.get((cidade, rio), 0) + 1


def ler_dcsc(pasta: Path, nomes: dict[str, str], series: dict[str, Serie]) -> None:
    for arq in sorted(pasta.glob("DCSC-*.csv")):
        cod = arq.stem
        sid = next((k for k in series if k.startswith(cod + " ")), f"{cod} SDC-SC {nomes.get(cod, cod)}")
        s = series.setdefault(sid, Serie(sid, DCSC_CIDADE.get(cod, ""), "", "dcsc", "brasilia"))
        with open(arq, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                t = _quando(r.get("medido_em", ""))
                try:
                    v = float(r.get("rio_nivel") or "")
                except ValueError:
                    continue
                if t:
                    s.pontos.append((t, v))


def ler_csv_simples(arq: Path, sid: str, cidade: str, rio: str, fonte: str, series: dict[str, Serie]) -> None:
    if not arq.exists():
        return
    s = series.setdefault(sid, Serie(sid, cidade, rio, fonte, "brasilia"))
    with open(arq, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = _quando(r.get("medido_em", ""))
            try:
                v = float(r.get("nivel_m") or "")
            except ValueError:
                continue
            if t:
                s.pontos.append((t, v))


def ler_ana(series: dict[str, Serie]) -> None:
    for arq in sorted(BRUTOS.glob("ana-telemetria-*.json")):
        try:
            itens = json.loads(arq.read_text(encoding="utf-8")).get("items") or []
        except json.JSONDecodeError:
            continue
        for it in itens:
            cod = str(it.get("codigoestacao"))
            if cod not in ANA or it.get("Cota_Adotada") in (None, ""):
                continue
            t = _quando(it.get("Data_Hora_Medicao", ""))
            try:
                v = round(float(it["Cota_Adotada"]) / 100, 2)
            except (TypeError, ValueError):
                continue
            nome, cidade, rio = ANA[cod]
            if t:
                series.setdefault(nome, Serie(nome, cidade, rio, "ana", "ana")).pontos.append((t, v))


def carregar(extras: list[Path] | None = None) -> dict[str, Serie]:
    series: dict[str, Serie] = {}
    ler_tempo_real(BRUTOS / "serie-2026-itajai", series)
    for p in extras or []:
        ler_tempo_real(p, series)
    nomes = {}
    est = BRUTOS / "dcsc-estacoes-vale-2026-09-13.csv"
    if est.exists():
        with open(est, encoding="utf-8") as f:
            nomes = {r["codigo"]: r["nome"] for r in csv.DictReader(f)}
    ler_dcsc(BRUTOS / "dcsc-cheia-2026-09-11-12", nomes, series)
    ler_csv_simples(BRUTOS / "asthon-historico" / "ponte_dom_tito_buss.csv", "Asthon Rio do Sul (Ponte Dom Tito Buss)", "rio-do-sul", "itajai-acu", "asthon", series)
    ler_csv_simples(BRUTOS / "asthon-historico" / "vidal_ramos.csv", "Asthon Vidal Ramos", "vidal-ramos", "itajai-mirim", "asthon", series)
    ler_csv_simples(BRUTOS / "taio-evento-2026-09-10-historico-horario.csv", "Defesa Civil de Taió", "taio", "itajai-acu", "taio", series)
    ler_ana(series)
    # O rio das estações da DCSC vem do cadastro da cidade.
    cad = cadastro()
    for s in series.values():
        if s._votos:
            s.cidade, s.rio = max(s._votos, key=lambda par: (s._votos[par], par))
        if not s.rio and s.cidade in cad:
            s.rio = cad[s.cidade][0]
    return {k: s.arrumar() for k, s in series.items() if len(s.pontos) >= 10}


@functools.lru_cache(maxsize=1)
def cadastro() -> dict[str, tuple[str, int]]:
    """cidade → (rio, posição no tronco; -1 cabeceira; 999 afluente/sem posição)."""
    e = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
    out: dict[str, tuple[str, int]] = {}
    for rid, r in e["rios"].items():
        topo = r.get("_topologia") or {}
        tronco = topo.get("tronco_sequencia") or []
        for c in r["cidades"]:
            cid = c["id"]
            if cid in out:
                continue
            pos = tronco.index(cid) if cid in tronco else (-1 if cid in (topo.get("cabeceiras_paralelas") or []) else 999)
            out[cid] = (rid, pos)
    return out


# ---------------------------------------------------------------- contas

def suavizar(pontos: list[tuple[datetime, float]], janela_h: float) -> list[float]:
    ts = [t for t, _ in pontos]
    vs = [v for _, v in pontos]
    acum = [0.0]
    for v in vs:
        acum.append(acum[-1] + v)
    meia = timedelta(hours=janela_h / 2)
    out = []
    for t in ts:
        i, j = bisect.bisect_left(ts, t - meia), bisect.bisect_right(ts, t + meia)
        out.append((acum[j] - acum[i]) / (j - i))
    return out


@dataclass
class Crista:
    quando: datetime
    nivel: float  # leitura bruta no instante da crista suavizada
    suave: float
    borda: bool


def cristas(s: Serie, subida_min: float = SUBIDA_MIN_M, raio_h: float = RAIO_CRISTA_H) -> list[Crista]:
    chave = (len(s.pontos), subida_min, raio_h)
    if chave not in s._cristas:
        s._cristas[chave] = _cristas(s, subida_min, raio_h)
    return s._cristas[chave]


def _cristas(s: Serie, subida_min: float, raio_h: float) -> list[Crista]:
    sm = suavizar(s.pontos, SUAVE_MARE_H if s.mare else SUAVE_H)
    ts = [t for t, _ in s.pontos]
    raio = timedelta(hours=raio_h)
    achadas: list[Crista] = []
    for k, (t, v) in enumerate(s.pontos):
        i, j = bisect.bisect_left(ts, t - raio), bisect.bisect_right(ts, t + raio)
        janela = sm[i:j]
        if sm[k] < max(janela) or sm.index(sm[k], i, j) != k:
            continue
        antes = sm[i:k + 1]
        if sm[k] - min(antes) < subida_min:
            continue
        borda = (t - ts[0]) < timedelta(hours=6) or (ts[-1] - t) < timedelta(hours=6)
        achadas.append(Crista(t, v, round(sm[k], 2), borda))
    return achadas


def nivel_em(s: Serie, t: datetime) -> tuple[float, datetime] | None:
    """Leitura até 10 min de distância, ou interpolação entre leituras com até 60 min de vão."""
    ts = [x for x, _ in s.pontos]
    i = bisect.bisect_left(ts, t)
    candidatos = [k for k in (i - 1, i) if 0 <= k < len(ts)]
    perto = min(candidatos, key=lambda k: abs(ts[k] - t), default=None)
    if perto is not None and abs(ts[perto] - t) <= PERTO:
        return s.pontos[perto][1], ts[perto]
    if 0 < i < len(ts) and ts[i] - ts[i - 1] <= VAO_MAX:
        (t0, v0), (t1, v1) = s.pontos[i - 1], s.pontos[i]
        f = (t - t0) / (t1 - t0)
        return round(v0 + f * (v1 - v0), 2), t
    return None


def primeira_passagem(s: Serie, nivel: float, desde: datetime) -> datetime | None:
    for t, v in s.pontos:
        if t >= desde and v >= nivel:
            return t
    return None


def montante(alvo: Serie, outra: Serie, cad: dict[str, tuple[str, int]]) -> bool:
    """A outra régua está rio acima do alvo, no mesmo rio (cabeceira conta; afluente lateral não)."""
    rio = alvo.rio
    if outra.rio != rio or outra.cidade == alvo.cidade:
        return False
    pa = cad.get(alvo.cidade, (rio, 999))[1] if alvo.cidade != "itajai" else 10_000
    po = cad.get(outra.cidade, (rio, 999))[1]
    if pa == 999:
        # Afluente lateral ou cidade sem posição: o tronco não está "acima" dela. Sem a régua do próprio
        # afluente rio acima, não há montante para mostrar.
        return False
    return po < pa and po != 999


@functools.lru_cache(maxsize=1)
def extremos_mare() -> tuple[tuple[datetime, float, str], ...]:
    """Tábua da Marinha (hora local, como a série das réguas). A altura é sobre o NR da carta: nunca é régua."""
    try:
        m = json.loads((RAIZ / "data" / "mare-itajai.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    ex = [(datetime.fromisoformat(x["quando"]), x["altura_m"], "preamar") for x in m.get("preamares", [])]
    ex += [(datetime.fromisoformat(x["quando"]), x["altura_m"], "baixa-mar") for x in m.get("baixamares", [])]
    return tuple(sorted(ex))


def mare_perto(t: datetime) -> str:
    extremos = extremos_mare()
    perto = [e for e in extremos if abs(e[0] - t) <= timedelta(hours=7)]
    if not perto:
        return ""
    q, h, tipo = min(perto, key=lambda e: abs(e[0] - t))
    return f"tábua da Marinha: {tipo} às {hora(q)}, {num(h)} m sobre o zero da carta náutica — não é régua de rio"


def num(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def horas_txt(h: float) -> str:
    return f"{h:.1f} h".replace(".", ",")


def hora(t: datetime) -> str:
    return f"{t.day:02d}/{MESES[t.month - 1]} {t.hour:02d}:{t.minute:02d}"


def data_hora(t: datetime) -> str:
    return f"{t.day:02d}/{MESES[t.month - 1]}/{t.year} {t.hour:02d}:{t.minute:02d}"


def linhas_antes(alvo: Serie, t0: datetime, series: dict[str, Serie], horas: tuple[int, ...], so_montante: bool) -> list[str]:
    cad = cadastro()
    out = []
    outras = [s for s in series.values() if s.id != alvo.id and s.familia == alvo.familia]
    outras.sort(key=lambda s: (not montante(alvo, s, cad), s.rio, cad.get(s.cidade, ("", 999))[1], s.id))
    for s in outras:
        mont = montante(alvo, s, cad)
        if so_montante and not mont:
            continue
        valores = []
        for n in horas:
            r = nivel_em(s, t0 - timedelta(hours=n))
            valores.append(f"{n} h antes: {num(r[0])} m" if r else f"{n} h antes: sem leitura")
        if all("sem leitura" in v for v in valores):
            continue
        propria = [c for c in cristas(s) if timedelta(hours=-72) <= c.quando - t0 <= timedelta(hours=24)]
        extra = ""
        if propria:
            c = min(propria, key=lambda c: abs(c.quando - t0))
            dif = (t0 - c.quando).total_seconds() / 3600
            quando = f"{horas_txt(abs(dif))} antes" if dif >= 0 else f"{horas_txt(abs(dif))} depois"
            extra = f"; crista própria {num(c.nivel)} m às {hora(c.quando)} ({quando}){' — na borda dos dados' if c.borda else ''}"
        out.append(f"- **{s.id}**{' (a montante)' if mont else ''}: " + " · ".join(valores) + extra)
    return out


def bloco(alvo: Serie, t0: datetime, titulo: str, series: dict[str, Serie], horas: tuple[int, ...], so_montante: bool) -> str:
    linhas = [f"### {alvo.id} — {titulo}", ""]
    r = nivel_em(alvo, t0)
    linhas.append(f"Referência: **{data_hora(t0)}**" + (f", leitura {num(r[0])} m na régua desta estação" if r else ""))
    if alvo.cidade == "itajai" and (m := mare_perto(t0)):
        linhas.append(f"({m})")
    if alvo.familia == "ana":
        linhas.append("(telemetria da ANA: fuso não conferido; as horas só se comparam entre séries da ANA)")
    linhas.append("")
    corpo = linhas_antes(alvo, t0, series, horas, so_montante)
    linhas += corpo or ["- Nenhuma outra régua com leitura nessas horas."]
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------- saída

def cotas_da_rua(texto: str) -> list[dict]:
    t = texto.lower()
    todas = json.loads((RAIZ / "data" / "cotas-ruas.json").read_text(encoding="utf-8"))["cotas"]
    return [c for c in todas if t in c["rua"].lower() and c.get("cota_m") is not None and c.get("referencia") == "régua"]


def bloco_rua(texto: str, series: dict[str, Serie], horas: tuple[int, ...]) -> str:
    """Hora em que a régua da cidade passou da cota oficial de cada ponto da rua, em cada cheia guardada."""
    cotas = cotas_da_rua(texto)
    if not cotas:
        return f"Nenhuma cota de rua com régua declarada casa com '{texto}' em data/cotas-ruas.json.\n"
    saida = []
    for c in cotas:
        local = ", ".join(x for x in (c["rua"], c.get("ponto"), c.get("bairro")) if x)
        sid = REGUA_DAS_COTAS.get(c["cidade"])
        cab = f"## {local} ({c['cidade']}) — cota {num(c['cota_m'])} m"
        if sid not in series:
            saida.append(f"{cab}\n\nA série com hora da régua desta cidade ainda não está ligada às cotas de rua (ver REGUA_DAS_COTAS).\n")
            continue
        regua = series[sid]
        saida.append(f"{cab}\n\nÉ a cota oficial em que este ponto começa a alagar, na régua da cidade ({sid}). A hora abaixo é a "
                     "da régua passando dela — não é observação na rua.\n")
        achou = False
        for cr in cristas(regua):
            if cr.nivel < c["cota_m"]:
                continue
            t0 = primeira_passagem(regua, c["cota_m"], cr.quando - timedelta(hours=RAIO_CRISTA_H))
            if t0 is None or t0 > cr.quando:
                continue
            achou = True
            k = [t for t, _ in regua.pontos].index(t0)
            entre = ""
            if k > 0 and t0 - regua.pontos[k - 1][0] > PERTO:
                ta, va = regua.pontos[k - 1]
                entre = f" entre {hora(ta)} ({num(va)} m) e {hora(t0)}"
            titulo = f"passou de {num(c['cota_m'])} m{entre} (crista de {num(cr.nivel)} m às {data_hora(cr.quando)})"
            saida.append(bloco(regua, t0, titulo, series, horas, True))
        if not achou:
            fim = regua.pontos[-1][0]
            saida.append(f"Nas cheias guardadas ({data_hora(regua.pontos[0][0])} a {data_hora(fim)}) a régua não chegou a {num(c['cota_m'])} m.\n")
    return "\n".join(saida)


RUAS_ALAGADAS = RAIZ / "data" / "ruas-alagadas.json"
SITUACAO_TXT = {"comecou_a_alagar": "começou a alagar", "alagada": "alagada", "interditada": "interditada", "liberada": "liberada"}


def registros_de_ruas(caminho: Path = RUAS_ALAGADAS) -> list[dict]:
    if not caminho.exists():
        return []
    return json.loads(caminho.read_text(encoding="utf-8")).get("registros", [])


def rios_da_cidade(cidade: str) -> list[str]:
    e = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
    return [rid for rid, r in e["rios"].items() if any(c["id"] == cidade for c in r["cidades"])]


def bloco_registro(reg: dict, series: dict[str, Serie], horas: tuple[int, ...]) -> str:
    """Rua alagada registrada à mão (data/ruas-alagadas.json): as réguas da cidade na hora e as de cima N h antes."""
    t0 = datetime.strptime(reg["quando"], "%Y-%m-%dT%H:%M")
    local = ", ".join(x for x in (reg["rua"], reg.get("ponto"), reg.get("bairro")) if x)
    linhas = [f"### {local} ({reg['cidade']}) — {SITUACAO_TXT.get(reg['situacao'], reg['situacao'])} às {data_hora(t0)}", ""]
    if reg.get("quando_e") == "hora_da_publicacao":
        linhas.append("A hora é a da **publicação**: a água chegou antes. As leituras abaixo são um limite, não o momento.")
    else:
        linhas.append("A hora é a do fato: a água estava lá nessa hora" + (" (hora aproximada)." if reg.get("precisao") == "aproximada" else "."))
    linhas.append(f"Fonte: {reg['fonte']} (confiança {reg['confianca']})" + (f". Lâmina: {reg['lamina']}" if reg.get("lamina") else "") + ".")
    if reg["cidade"] == "itajai" and (m := mare_perto(t0)):
        linhas.append(f"({m})")
    cotas = [c for c in cotas_da_rua(reg["rua"]) if c["cidade"] == reg["cidade"]]
    if cotas:
        linhas.append("Cota oficial de rua com esse nome, na régua da cidade: "
                      + "; ".join(f"{num(c['cota_m'])} m ({c.get('ponto') or 'sem ponto'})" for c in cotas) + ".")
    linhas.append("")
    proprias = []
    for s in sorted(series.values(), key=lambda s: s.id):
        if s.cidade != reg["cidade"] or s.familia != "brasilia":
            continue
        r = nivel_em(s, t0)
        if r:
            exata = any(t == t0 for t, _ in s.pontos)
            obs = f" (leitura das {hora(r[1])})" if r[1] != t0 else ("" if exata else " (entre duas leituras)")
            proprias.append(f"- **{s.id}**: {num(r[0])} m{obs}")
    linhas += ["Réguas da própria cidade nessa hora (cada uma no seu zero):", ""] + (proprias or ["- nenhuma com leitura"]) + [""]
    acima: list[str] = []
    for rio in rios_da_cidade(reg["cidade"]):
        alvo = Serie(f"registro {reg['cidade']}", reg["cidade"], rio, "registro", "brasilia")
        acima += [x for x in linhas_antes(alvo, t0, series, horas, True) if x not in acima]
    linhas += ["Réguas de cima, N horas antes:", ""] + (acima or ["- nenhuma com leitura nessas horas"])
    return "\n".join(linhas) + "\n"


def secao_registros(series: dict[str, Serie], horas: tuple[int, ...], caminho: Path = RUAS_ALAGADAS, filtro: str = "") -> str:
    regs = [r for r in registros_de_ruas(caminho) if filtro.lower() in r["rua"].lower()]
    partes = ["## Ruas alagadas registradas à mão", ""]
    if not regs:
        partes += ["Nenhum registro ainda em `data/ruas-alagadas.json`. Como registrar durante a cheia:",
                   "`docs/REGISTRO-RUAS-ALAGADAS.md`.", ""]
    for r in regs:
        partes.append(bloco_registro(r, series, horas))
    return "\n".join(partes)


def listar(series: dict[str, Serie]) -> str:
    out = ["Séries com hora (cada uma na sua régua):", ""]
    for s in sorted(series.values(), key=lambda s: (s.familia, s.pontos[0][0], s.id)):
        cs = cristas(s)
        out.append(f"- {s.id} [{s.fonte}, {s.cidade or '—'}, {s.rio or '—'}]: {hora(s.pontos[0][0])} {s.pontos[0][0].year} → "
                   f"{hora(s.pontos[-1][0])} {s.pontos[-1][0].year}, {len(s.pontos)} leituras; cristas: "
                   + (", ".join(f"{hora(c.quando)} ({num(c.nivel)} m{', borda' if c.borda else ''})" for c in cs) or "nenhuma"))
    return "\n".join(out)


def achar(series: dict[str, Serie], texto: str) -> Serie:
    t = texto.lower()
    cands = [s for s in series.values() if t in s.id.lower() or t == s.cidade]
    if not cands:
        raise SystemExit(f"Nenhuma série casa com '{texto}'. Veja --listar.")
    if len(cands) > 1 and not any(s.id.lower().startswith(t) for s in cands):
        raise SystemExit("Mais de uma série casa: " + "; ".join(s.id for s in cands))
    return next((s for s in cands if s.id.lower().startswith(t)), cands[0])


def relatorio(series: dict[str, Serie], horas: tuple[int, ...], origem: str = "") -> str:
    partes = [
        "# Nível das réguas N horas antes de cada crista e de cada rua alagada registrada",
        "",
        "Gerado por `scripts/nivel_antes.py --relatorio` (somente leitura). **Descritivo, não previsão nem",
        "calibração.** Cada régua tem o seu zero: os números estão lado a lado, cada um na sua régua, e não se",
        "comparam entre si. Só aparecem as réguas **a montante** no mesmo rio. Séries da ANA (2020–2023) só se",
        "cruzam com séries da ANA, porque o fuso delas não foi conferido. Crista de réguas de Itajaí que sentem a",
        "maré: máximo da média de 12,42 h (um ciclo de maré); a leitura mostrada é a do instante. Só entram como",
        "alvo as réguas de cidades cadastradas em `data/estacoes.json`.",
        "",
    ]
    if origem:
        partes += [origem, ""]
    partes.append(secao_registros(series, horas))
    partes += ["## Cristas das réguas", ""]
    cad = cadastro()
    todas = sorted(((c, s) for s in series.values() if s.cidade in cad for c in cristas(s)), key=lambda x: (x[0].quando, x[1].id))
    sozinhas = []
    for c, alvo in todas:
        titulo = f"crista de {num(c.nivel)} m{' (na borda dos dados: piso)' if c.borda else ''}"
        if linhas_antes(alvo, c.quando, series, horas, True):
            partes.append(bloco(alvo, c.quando, titulo, series, horas, True))
        else:
            sozinhas.append(f"- {alvo.id}: {titulo}, {data_hora(c.quando)}")
    if sozinhas:
        partes += ["## Cristas sem régua a montante com leitura nessas horas", "",
                   "A conta não dá para fazer nelas com as séries do repositório (com `--series`, a série inteira da VPS",
                   "pode cobrir algumas, como Brusque para as réguas do Itajaí-Mirim em Itajaí).", "", *sozinhas, ""]
    return "\n".join(partes)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--series", type=Path, action="append", default=[], help="pasta com a série do coletor (data/tempo-real)")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--alvo", help="parte do nome da régua (ex.: DC-04, AlertaBlu, DCSC-00003) ou id da cidade")
    ap.add_argument("--data", help="AAAA-MM-DD: a crista desse dia (ou, com --nivel, a partir desse dia)")
    ap.add_argument("--nivel", type=float, help="usar a primeira passagem desse nível (m, na régua do alvo) em vez da crista")
    ap.add_argument("--horas", type=int, nargs="+", default=list(HORAS_PADRAO))
    ap.add_argument("--rua", help="parte do nome da rua em data/cotas-ruas.json: hora em que a régua passou da cota dela")
    ap.add_argument("--registradas", nargs="?", const="", help="ruas alagadas registradas à mão (opcional: parte do nome da rua)")
    ap.add_argument("--todas", action="store_true", help="mostrar também réguas que não estão a montante")
    ap.add_argument("--relatorio", type=Path, help="gravar o relatório de todas as cristas neste arquivo .md")
    ap.add_argument("--origem", default="", help="parágrafo sobre a série usada, no topo do relatório (ex.: o commit do arquivo-series)")
    a = ap.parse_args()
    series = carregar(a.series)
    horas = tuple(a.horas)
    if a.listar:
        print(listar(series))
    if a.relatorio:
        a.relatorio.write_text(relatorio(series, horas, a.origem), encoding="utf-8")
        print(f"relatório: {a.relatorio}")
    if a.registradas is not None:
        print(secao_registros(series, horas, filtro=a.registradas))
    if a.rua:
        print(bloco_rua(a.rua, series, horas))
    if a.alvo:
        alvo = achar(series, a.alvo)
        dia = datetime.fromisoformat(a.data) if a.data else alvo.pontos[0][0]
        if a.nivel is not None:
            t0 = primeira_passagem(alvo, a.nivel, dia)
            if t0 is None:
                raise SystemExit(f"{alvo.id} não passou de {num(a.nivel)} m a partir de {a.data}.")
            titulo = f"passou de {num(a.nivel)} m"
        else:
            cs = [c for c in cristas(alvo) if c.quando.date() == dia.date()] if a.data else cristas(alvo)
            if not cs:
                raise SystemExit(f"{alvo.id} não tem crista em {a.data}. Cristas: " + ", ".join(hora(c.quando) for c in cristas(alvo)))
            c = max(cs, key=lambda c: c.suave)
            t0, titulo = c.quando, f"crista de {num(c.nivel)} m"
        print(bloco(alvo, t0, titulo, series, horas, not a.todas))


if __name__ == "__main__":
    main()
