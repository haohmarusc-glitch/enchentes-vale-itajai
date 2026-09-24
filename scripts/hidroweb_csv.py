#!/usr/bin/env python3
"""
HidroWeb (ANA/SNIRH), exportação CSV: leitor do formato largo, e a conferência do Mirim.

O QUE É A FONTE
---------------
Em 22/09/2026 o Jefferson exportou do HidroWeb (portal, pelo navegador dele; o
domínio não responde deste ambiente) as estações convencionais da ANA no
Itajaí-Mirim: quatro de cota (83892990 Salseiro, 83892998 Botuverá-Montante,
83893000 Botuverá, 83900000 Brusque PCD; 83905000 só tem qualidade de água) e
seis de chuva (2748000 Brusque PCD, 2748014 Brusque/INMET, 2749033 Vidal Ramos,
2749038 Botuverá, 2749045 Botuverá-Montante; 2749107 Rio das Pacas veio vazia).
Os zips estão como vieram em `data/brutos/hidroweb-mirim-2026-09-22/`, junto
com três derivados dele: cotas e chuva em formato longo, e um JSON de picos de
Brusque com o pico a montante e a antecedência (1997–2021).

O FORMATO LARGO DO HIDROWEB
---------------------------
Cabeçalho institucional em latin-1, uma linha de legenda por código, e uma
tabela `;` com UMA LINHA POR MÊS e uma coluna por dia (`Cota01..Cota31`,
`Chuva01..Chuva31`), cada uma com a coluna de status ao lado (`Cota01Status`).
Cotas em CENTÍMETROS inteiros; chuva em mm com vírgula decimal, entre aspas.
Para cota, o mesmo mês aparece em até quatro linhas: `NivelConsistencia` 1
(bruto) com `hora` 07:00, 17:00 e média diária, e `NivelConsistencia` 2
(consistido) só com a média diária. Para chuva, uma linha por nível de
consistência. Status: 0 branco, 1 real, 2 estimado, 3 duvidoso, 4 régua seca /
acumulado.

O QUE ESTE SCRIPT FAZ, E O QUE NÃO FAZ
--------------------------------------
* `ler_cotas` / `ler_chuvas`: do zip ou do CSV para registros longos.
* `conferir_cotas` / `conferir_chuvas`: reproduzem os derivados do Jefferson a
  partir do bruto — leitura instantânea vem do nível 1; média diária e chuva
  vêm do nível 2 quando o dia tem valor consistido, senão do 1.
* `implausiveis`: leitura das 07h/17h que destoa da média consistida do dia.
  O bruto do HidroWeb tem erros de digitação que a consistência da ANA corrige
  na média e deixa na instantânea: 1140 por 140, 3145 por 145, 1444 por 144.
  Os "recordes" de Brusque de 1941, 1944, 1958 e 1978 são desse tipo — a média
  consistida do dia fica em 1,2–1,5 m. Duas dessas leituras (Salseiro,
  03/10/2020 e 15/04/2023) foram conferidas contra a série de 15 min da Defesa
  Civil de Brusque, que dá 1,49 m nos dois dias.
* `picos` / `pico_a_montante`: reproduz o JSON de picos (Brusque ≥ limiar,
  eventos separados por mais de N dias, pico a montante = maior leitura nas
  72 h anteriores; antecedência em horas, com resolução de 10/14 h).
* NÃO escreve em `enchentes.json`, `estacoes.json` nem `transito.json`. Cota da
  ANA está no zero da ANA; a régua municipal de Brusque coincide com a 83900000
  em 2019–2021 ao centímetro, e ainda assim ninguém transplanta valor — o que
  se compara é horário.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "brutos" / "hidroweb-mirim-2026-09-22"
DERIVADO_COTAS = DIR / "ana_cotas_itajai_mirim.csv.gz"
DERIVADO_CHUVA = DIR / "ana_chuva_diaria_itajai_mirim.csv.gz"
PICOS_JSON = DIR / "picos_itajai_mirim_1997_2021.json"

# Inventário público da ANA (data/brutos/ana-inventario-api-2026-09-08.json), lido em 22/09/2026.
ESTACOES = {
    "83892990": {"nome": "Salseiro", "municipio": "Vidal Ramos", "tipo": "cota", "lat": -27.33, "lon": -49.33},
    "83892998": {"nome": "Botuverá-Montante", "municipio": "Botuverá", "tipo": "cota", "lat": -27.1972, "lon": -49.0878},
    "83893000": {"nome": "Botuverá", "municipio": "Botuverá", "tipo": "cota", "lat": -27.1908, "lon": -49.0653},
    "83900000": {"nome": "Brusque (PCD)", "municipio": "Brusque", "tipo": "cota", "lat": -27.1006, "lon": -48.9167},
    "83905000": {"nome": "Brusque", "municipio": "Brusque", "tipo": "cota", "lat": -27.0331, "lon": -48.8611},
    "2748000": {"nome": "Brusque (PCD)", "municipio": "Brusque", "tipo": "chuva", "lat": -27.1008, "lon": -48.9181},
    "2748014": {"nome": "Brusque", "municipio": "Brusque", "tipo": "chuva", "lat": -27.0833, "lon": -48.9333},
    "2749033": {"nome": "Vidal Ramos", "municipio": "Vidal Ramos", "tipo": "chuva", "lat": -27.3925, "lon": -49.3656},
    "2749038": {"nome": "Botuverá", "municipio": "Botuverá", "tipo": "chuva", "lat": -27.1833, "lon": -49.0667},
    "2749045": {"nome": "Botuverá-Montante", "municipio": "Botuverá", "tipo": "chuva", "lat": -27.1967, "lon": -49.0872},
    "2749107": {"nome": "Vidal Ramos - Rio das Pacas", "municipio": "Vidal Ramos", "tipo": "chuva", "lat": -27.415, "lon": -49.4512},
}
HORAS = {"07:00": 7, "17:00": 17}


@dataclass(frozen=True)
class Leitura:
    codigo: str
    data: date
    leitura: str          # "07:00", "17:00" ou "media_diaria"
    nivel: int            # 1 bruto, 2 consistido
    valor: float | None   # cm (cota) ou mm (chuva); None = branco
    status: int           # 0 branco, 1 real, 2 estimado, 3 duvidoso, 4 régua seca/acumulado


def numero(texto: str) -> float | None:
    t = texto.strip().strip('"').replace(",", ".")
    return float(t) if t else None


def _tabela(texto: str) -> tuple[list[str], list[list[str]]]:
    linhas = texto.splitlines()
    i = next(i for i, linha in enumerate(linhas) if linha.startswith("EstacaoCodigo;"))
    cab = linhas[i].split(";")
    corpo = [linha.split(";") for linha in linhas[i + 1:] if linha.count(";") >= 10]
    return cab, corpo


def _texto(caminho: Path, sufixo: str) -> str:
    """Lê o CSV de dentro do zip do HidroWeb (ou um CSV solto). latin-1 sempre."""
    if caminho.suffix == ".zip":
        with zipfile.ZipFile(caminho) as z:
            nome = next((n for n in z.namelist() if n.endswith(sufixo)), None)
            if nome is None:
                return ""
            return z.read(nome).decode("latin-1")
    return caminho.read_text(encoding="latin-1")


def _dias(ano: int, mes: int) -> int:
    prox = date(ano + (mes == 12), mes % 12 + 1, 1)
    return (prox - date(ano, mes, 1)).days


def ler_cotas(caminho: Path, sufixo: str = "_Cotas.csv") -> list[Leitura]:
    """`sufixo="_Cotas.txt"` para a exportação TXT do HidroWeb: mesmo miolo, outra extensão."""
    texto = _texto(caminho, sufixo)
    if not texto:
        return []
    cab, corpo = _tabela(texto)
    ix = {c: i for i, c in enumerate(cab)}
    saida: list[Leitura] = []
    for p in corpo:
        cod = p[ix["EstacaoCodigo"]]
        nivel = int(p[ix["NivelConsistencia"]])
        d, m, a = (int(x) for x in p[ix["Data"]].split("/"))
        hora = p[ix["hora"]].strip()
        leitura = hora if p[ix["MediaDiaria"]].strip() == "0" and hora else "media_diaria"
        for dia in range(1, _dias(a, m) + 1):
            v = numero(p[ix[f"Cota{dia:02d}"]])
            st = p[ix[f"Cota{dia:02d}Status"]].strip() or "0"
            saida.append(Leitura(cod, date(a, m, dia), leitura, nivel, v, int(st)))
    return saida


def ler_chuvas(caminho: Path) -> list[Leitura]:
    texto = _texto(caminho, "_Chuvas.csv")
    if not texto:
        return []
    cab, corpo = _tabela(texto)
    ix = {c: i for i, c in enumerate(cab)}
    saida: list[Leitura] = []
    for p in corpo:
        cod = p[ix["EstacaoCodigo"]]
        nivel = int(p[ix["NivelConsistencia"]])
        d, m, a = (int(x) for x in p[ix["Data"]].split("/"))
        for dia in range(1, _dias(a, m) + 1):
            v = numero(p[ix[f"Chuva{dia:02d}"]])
            st = p[ix[f"Chuva{dia:02d}Status"]].strip() or "0"
            saida.append(Leitura(cod, date(a, m, dia), "diaria", nivel, v, int(st)))
    return saida


def indice(leituras: list[Leitura]) -> dict[tuple[str, date, str, int], Leitura]:
    return {(x.codigo, x.data, x.leitura, x.nivel): x for x in leituras}


def meses_consistidos(leituras: list[Leitura]) -> set[tuple[str, int, int]]:
    return {(x.codigo, x.data.year, x.data.month) for x in leituras if x.nivel == 2}


def _abre(caminho: Path):
    if caminho.suffix == ".gz":
        return gzip.open(caminho, "rt", encoding="utf-8", newline="")
    return open(caminho, encoding="utf-8", newline="")


def _derivado_esperado(idx, meses2, cod, d, leitura):
    """Regra do derivado: instantânea = nível 1; média diária e chuva = nível 2 quando o DIA
    tem valor consistido, senão nível 1 (o consistido tem dias em branco que o bruto preenche)."""
    if leitura in HORAS:
        return idx.get((cod, d, leitura, 1))
    x2 = idx.get((cod, d, leitura, 2))
    if x2 is not None and x2.valor is not None:
        return x2
    return idx.get((cod, d, leitura, 1))


def conferir_cotas(leituras: list[Leitura], derivado: Path = DERIVADO_COTAS) -> dict:
    idx, meses2 = indice(leituras), meses_consistidos(leituras)
    iguais = 0
    difs: list[tuple] = []
    with _abre(derivado) as f:
        for r in csv.DictReader(f):
            d = date.fromisoformat(r["data"])
            x = _derivado_esperado(idx, meses2, r["codigo"], d, r["leitura"])
            v = numero(r["cota_cm"])
            ok = x is not None and x.valor == v and str(x.status) == (r["status"] or "0") \
                and (x.nivel == 2) == (r["consistido"] == "1")
            if ok:
                iguais += 1
            else:
                difs.append((r["codigo"], r["data"], r["leitura"], r["cota_cm"], r["status"], r["consistido"], x))
    return {"iguais": iguais, "diferentes": len(difs), "exemplos": difs[:10]}


def conferir_chuvas(leituras: list[Leitura], derivado: Path = DERIVADO_CHUVA) -> dict:
    idx, meses2 = indice(leituras), meses_consistidos(leituras)
    iguais = 0
    difs: list[tuple] = []
    with _abre(derivado) as f:
        for r in csv.DictReader(f):
            d = date.fromisoformat(r["data"])
            x = _derivado_esperado(idx, meses2, r["codigo"], d, "diaria")
            v = numero(r["prec_mm"])
            ok = x is not None and x.valor == v and str(x.status) == (r["status"] or "0") \
                and (x.nivel == 2) == (r["consistido"] == "1")
            if ok:
                iguais += 1
            else:
                difs.append((r["codigo"], r["data"], r["prec_mm"], r["status"], r["consistido"], x))
    return {"iguais": iguais, "diferentes": len(difs), "exemplos": difs[:10]}


def implausiveis(leituras: list[Leitura], fator: float = 2.0, folga_cm: float = 100.0) -> list[tuple]:
    """Leitura das 07h/17h maior que `fator` × média consistida do dia + folga.

    Pega o dedo do digitador (1140 por 140), não a cheia: uma crista real
    das 17h fica perto da média do dia, nunca no dobro mais um metro.
    """
    idx = indice(leituras)
    saida = []
    for x in leituras:
        if x.leitura not in HORAS or x.valor is None:
            continue
        media = idx.get((x.codigo, x.data, "media_diaria", 2))
        if media is None or media.valor is None:
            continue
        if x.valor > fator * media.valor + folga_cm:
            saida.append((x.codigo, x.data.isoformat(), x.leitura, x.valor, media.valor))
    return sorted(saida)


def serie_instantanea(leituras: list[Leitura], codigo: str, excluir_status=(3,),
                      excluir: set[tuple[date, str]] | None = None) -> dict[datetime, float]:
    """`{carimbo local: cm}` das leituras 07h/17h brutas, sem as duvidosas e sem `excluir`."""
    s = {}
    for x in leituras:
        if x.codigo != codigo or x.nivel != 1 or x.leitura not in HORAS or x.valor is None:
            continue
        if x.status in excluir_status or (excluir and (x.data, x.leitura) in excluir):
            continue
        s[datetime(x.data.year, x.data.month, x.data.day, HORAS[x.leitura])] = x.valor
    return s


def picos(serie: dict[datetime, float], limiar: float, separacao: timedelta = timedelta(days=5),
          desde: int | None = None) -> list[tuple[datetime, float]]:
    """Maior leitura de cada corrida de leituras ≥ limiar; corridas separadas por mais de `separacao`.

    Empate de valor fica com a leitura mais cedo.
    """
    cand = sorted((t, v) for t, v in serie.items() if v >= limiar and (desde is None or t.year >= desde))
    grupos: list[list[tuple[datetime, float]]] = []
    for t, v in cand:
        if grupos and t - grupos[-1][-1][0] <= separacao:
            grupos[-1].append((t, v))
        else:
            grupos.append([(t, v)])
    return [max(g, key=lambda x: (x[1], -x[0].timestamp())) for g in grupos]


def pico_a_montante(serie: dict[datetime, float], t: datetime,
                    janela: timedelta = timedelta(hours=72)) -> tuple[datetime, float, int] | None:
    """Maior leitura em [t − janela, t]; devolve (quando, cm, antecedência em horas)."""
    dentro = {u: v for u, v in serie.items() if t - janela <= u <= t}
    if not dentro:
        return None
    u = max(dentro, key=lambda u: (dentro[u], -u.timestamp()))
    return u, dentro[u], int((t - u).total_seconds() // 3600)


def conferir_picos(leituras: list[Leitura], caminho: Path = PICOS_JSON) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    b = serie_instantanea(leituras, "83900000")
    sa = serie_instantanea(leituras, "83892990")
    bm = serie_instantanea(leituras, "83892998")
    meus = {t.strftime("%Y-%m-%dT%H:%M"): (t, v) for t, v in picos(b, 450, desde=1997)}
    iguais = 0
    difs: list = []
    for e in dados["eventos"]:
        chave = e["pico_brusque"][:16]
        if chave not in meus:
            difs.append(("só no JSON", chave, e["cota_brusque_cm"]))
            continue
        t, v = meus[chave]
        ok = v == e["cota_brusque_cm"]
        for nome, s in (("salseiro", sa), ("botuvera_mont", bm)):
            m = pico_a_montante(s, t)
            ok = ok and m is not None and m[1] == e[nome]["cota_cm"] and m[2] == e[nome]["antecedencia_h"]
        if ok:
            iguais += 1
        else:
            difs.append(("difere", chave, e))
    so_meus = [k for k in meus if k not in {e["pico_brusque"][:16] for e in dados["eventos"]}]
    return {"iguais": iguais, "diferentes": len(difs), "so_no_reproduzido": so_meus, "exemplos": difs[:5]}


def carregar_tudo(pasta: Path = DIR) -> tuple[list[Leitura], list[Leitura]]:
    cotas: list[Leitura] = []
    chuvas: list[Leitura] = []
    for z in sorted(pasta.glob("*_csv.zip")):
        cotas += ler_cotas(z)
        chuvas += ler_chuvas(z)
    return cotas, chuvas


def _cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--conferir", action="store_true", help="reproduz os três derivados a partir dos zips")
    p.add_argument("--implausiveis", action="store_true")
    p.add_argument("--antecedencias", action="store_true", help="distribuição da antecedência dos picos")
    a = p.parse_args(argv)
    if not (a.conferir or a.implausiveis or a.antecedencias):
        p.print_help()
        return 2
    cotas, chuvas = carregar_tudo()
    if a.conferir:
        for nome, r in (("cotas", conferir_cotas(cotas)), ("chuva", conferir_chuvas(chuvas)),
                        ("picos", conferir_picos(cotas))):
            print(f"{nome}: {r['iguais']} iguais, {r['diferentes']} diferentes"
                  + (f", só no reproduzido: {r['so_no_reproduzido']}" if "so_no_reproduzido" in r else ""))
            for ex in r["exemplos"]:
                print("   ", ex)
    if a.implausiveis:
        for x in implausiveis(cotas):
            print("  ", x)
    if a.antecedencias:
        b = serie_instantanea(cotas, "83900000")
        for cod in ("83892990", "83892998"):
            s = serie_instantanea(cotas, cod)
            cont: dict[int, int] = defaultdict(int)
            for t, _v in picos(b, 450, desde=1997):
                m = pico_a_montante(s, t)
                if m:
                    cont[m[2]] += 1
            print(ESTACOES[cod]["nome"], "→ Brusque, antecedência (h): contagem", dict(sorted(cont.items())))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
