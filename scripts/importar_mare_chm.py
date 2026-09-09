#!/usr/bin/env python3
"""
Importa a Tábua de Marés da Marinha (CHM/DHN) do Porto de Itajaí para `data/mare-itajai.json`.

POR QUE EXISTE (09/09/2026). A tábua que o site usava veio de uma planilha da
UNIVALI, cobria só setembro de 2026 e, no dia 1º de outubro, o painel de maré
da foz ficaria mudo — o validador avisava isso todo dia. A tábua oficial da
Marinha cobre o ano inteiro e é a `fonte_oficial` que o JSON já declarava.

O QUE O PDF TRAZ. "PORTO DE ITAJAÍ (ESTADO DE SANTA CATARINA) - 2026",
latitude 26° 54'.3 S, longitude 48° 39'.2 W, fuso UTC−3, CHM 78 componentes,
Nível Médio 0,6 m, Carta 1841. Um bloco por dia (número, dia da semana) e, por
extremo, "HHMM ALT(m)". As duas colunas de meio mês saem intercaladas no texto
(01, 17, 02, 18…) — irrelevante, porque tudo é ordenado por data no fim.

O QUE ENTRA, E COMO. Cada extremo vira preamar se não for menor que os dois
vizinhos e baixa-mar se não for maior — a mesma regra de
`importar_mare_univali.classificar_extremos`. Um ponto que não é nem pico nem
vale em relação aos vizinhos (a tábua traz "plôs", estofos com dois mínimos
seguidos) é DESCARTADO e contado: melhor faltar um ponto do que adivinhar.

A ALTURA ENTRA, com o datum escrito. A UNIVALI estava em datum IBGE e por isso
a altura foi omitida; a Marinha publica em metros sobre o NÍVEL DE REDUÇÃO (NR)
da carta 1841, que é o datum das cartas náuticas. NÃO é a régua de nenhum rio:
0,6 m de "Nível Médio" é a altura do nível médio do mar sobre o NR, não uma
conversão para régua fluvial. Comparar altura de maré com cota de régua continua
proibido — o painel usa o HORÁRIO da preamar, e a altura é contexto.

CRUZAMENTO COM A UNIVALI. Enquanto o arquivo antigo existe, o script pareia
cada preamar de setembro da Marinha com a mais próxima da UNIVALI e imprime a
mediana e o máximo da diferença em minutos. Duas previsões harmônicas
independentes do mesmo porto têm de concordar em minutos; se não concordarem,
uma das duas está em fuso errado, e é isso que este cruzamento denuncia.

Uso:
    python3 scripts/importar_mare_chm.py                  # lê o bruto, cruza, grava
    python3 scripts/importar_mare_chm.py --seco           # tudo menos gravar
    python3 scripts/importar_mare_chm.py --pdf outro.pdf  # outro ano/arquivo
"""

from __future__ import annotations

import argparse
import hashlib
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from comum import DADOS, grava_json, le_json
from importar_mare_univali import classificar_extremos

BRUTO = DADOS / "brutos" / "chm-tabua-mare-itajai-2026.pdf"
DESTINO = "mare-itajai.json"

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
RE_ANO = re.compile(r"PORTO DE ITAJA[ÍI].*?-\s*(\d{4})")
RE_DIA = re.compile(r"^(\d{2})$")
RE_ENTRADA = re.compile(r"^([0-2]\d)([0-5]\d)\s+(-?\d\.\d{2})$")
RE_SEMANA = re.compile(r"^(SEG|TER|QUA|QUI|SEX|S[ÁA]B|DOM)$")


def extrair_texto(caminho: Path) -> str:
    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    return "\n".join((p.extract_text() or "") for p in leitor.pages)


def parse(texto: str) -> tuple[list[tuple[datetime, float]], dict]:
    """
    Todos os extremos, em ordem cronológica, e um relato do que foi ignorado.

    O ano vem do cabeçalho; sem ele, nada é lido — um extremo sem ano não é
    uma data. O mês vem do nome; o dia, da linha só com dois dígitos.
    """
    m = RE_ANO.search(texto)
    if not m:
        raise ValueError("cabeçalho 'PORTO DE ITAJAÍ … - AAAA' não encontrado: não sei o ano")
    ano = int(m.group(1))

    pontos: list[tuple[datetime, float]] = []
    relato = {"ano": ano, "meses": 0, "dias": 0, "ignoradas": []}
    mes = dia = None
    for bruta in texto.splitlines():
        linha = bruta.strip()
        if not linha:
            continue
        chave = linha.lower()
        if chave in MESES:
            mes, dia = MESES[chave], None
            relato["meses"] += 1
            continue
        if mes is None:
            continue
        d = RE_DIA.match(linha)
        if d and 1 <= int(d.group(1)) <= 31:
            dia = int(d.group(1))
            relato["dias"] += 1
            continue
        if RE_SEMANA.match(linha) or linha.startswith("HORA"):
            continue
        e = RE_ENTRADA.match(linha)
        if e and dia is not None:
            hh, mm, alt = int(e.group(1)), int(e.group(2)), float(e.group(3))
            try:
                pontos.append((datetime(ano, mes, dia, hh, mm), alt))
            except ValueError:
                relato["ignoradas"].append(f"{linha!r} (mês {mes}, dia {dia})")
            continue
        relato["ignoradas"].append(linha[:60])

    pontos.sort()
    for a, b in zip(pontos, pontos[1:]):
        if a[0] == b[0]:
            raise ValueError(f"dois extremos no mesmo instante: {a[0]:%d/%m %H:%M} — leitura suspeita")
    return pontos, relato


def formatar(pontos: list[tuple[datetime, float]]) -> list[dict]:
    return [{"quando": q.strftime("%Y-%m-%dT%H:%M"), "altura_m": round(v, 2)} for q, v in pontos]


def cruzar(novos: list[dict], antigos: list[dict], janela_min: int = 180) -> dict | None:
    """
    Para cada ponto novo, o antigo mais próximo (dentro da janela): mediana e
    máximo da diferença, em minutos. Serve para pegar fuso errado, não para
    escolher entre as fontes — a Marinha é a oficial.
    """
    def dt(p):
        return datetime.strptime(p["quando"], "%Y-%m-%dT%H:%M")
    velhos = sorted(dt(p) for p in antigos)
    if not velhos:
        return None
    ini, fim = velhos[0], velhos[-1]
    difs = []
    for p in novos:
        q = dt(p)
        if not (ini <= q <= fim):
            continue
        mais_perto = min(velhos, key=lambda v: abs((v - q).total_seconds()))
        d = abs((mais_perto - q).total_seconds()) / 60
        if d <= janela_min:
            difs.append(d)
    if not difs:
        return None
    return {"pareados": len(difs), "mediana_min": round(statistics.median(difs), 1), "maximo_min": round(max(difs), 1)}


def montar(preamares, baixamares, pdf: Path, relato: dict, descartados: int) -> dict:
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    return {
        "_meta": {
            "descricao": ("Tábua de maré do porto de Itajaí. O site cruza estas preamares com a janela "
                          "de chegada da cheia: maré alta trava o escoamento do rio."),
            "fuso": "Horário local (America/Sao_Paulo, UTC−3), como a tábua publica e o site espera.",
            "fonte": (f"Marinha do Brasil, Centro de Hidrografia da Marinha (CHM/DHN) — Tábua de Marés {relato['ano']}, "
                      "Porto de Itajaí (SC), páginas 166–168; 78 componentes harmônicas, Carta 1841. "
                      f"Bruto: data/brutos/{pdf.name} (sha256 {sha}). Importada por scripts/importar_mare_chm.py."),
            "fonte_oficial": "Tábuas de maré da Marinha do Brasil (DHN) — porto de Itajaí",
            "altura": ("`altura_m` é em metros sobre o NÍVEL DE REDUÇÃO (NR) da carta náutica 1841, o datum da DHN. "
                       "NÃO é régua de rio nenhum, e os 0,6 m de 'Nível Médio' do cabeçalho são a altura do nível médio "
                       "do mar sobre o NR — não uma conversão para régua fluvial. O painel usa o HORÁRIO da preamar; "
                       "a altura é contexto e nunca se compara com cota de régua."),
            "metodo": ("Cada extremo da tábua vira preamar se não for menor que os dois vizinhos e baixa-mar se não "
                       f"for maior; {descartados} ponto(s) que não eram nem pico nem vale (estofos) foram descartados "
                       "de propósito — melhor faltar um ponto do que adivinhar."),
            "fonte_curta": f"Marinha do Brasil (CHM/DHN) — Tábua de Marés {relato['ano']}",
        },
        "porto": "Itajaí",
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pontos_astronomicos": len(preamares) + len(baixamares),
        "pontos_observados": 0,
        "preamares": formatar(preamares),
        "baixamares": formatar(baixamares),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", type=Path, default=BRUTO)
    ap.add_argument("--seco", action="store_true", help="não grava")
    args = ap.parse_args()
    if not args.pdf.exists():
        print(f"não achei {args.pdf}", file=sys.stderr)
        return 1

    pontos, relato = parse(extrair_texto(args.pdf))
    preamares, baixamares = classificar_extremos(pontos)
    descartados = len(pontos) - len(preamares) - len(baixamares)
    print(f"ano {relato['ano']}: {relato['meses']} meses, {relato['dias']} dias, {len(pontos)} extremos "
          f"→ {len(preamares)} preamares, {len(baixamares)} baixa-mares, {descartados} descartados (estofos).")
    if relato["ignoradas"]:
        print(f"linhas ignoradas ({len(relato['ignoradas'])}): {relato['ignoradas'][:8]}")
    print(f"cobre de {pontos[0][0]:%d/%m/%Y} a {pontos[-1][0]:%d/%m/%Y}.")

    novo = montar(preamares, baixamares, args.pdf, relato, descartados)
    try:
        antigo = le_json(DESTINO)
    except FileNotFoundError:
        antigo = None
    if antigo:
        for chave in ("preamares", "baixamares"):
            c = cruzar(novo[chave], antigo.get(chave) or [])
            fonte_antiga = (antigo.get("_meta") or {}).get("fonte_curta", "?")
            if c:
                print(f"cruzamento {chave} com '{fonte_antiga}': {c['pareados']} pareadas, "
                      f"mediana {c['mediana_min']} min, máximo {c['maximo_min']} min.")
            else:
                print(f"cruzamento {chave}: nada a parear com o arquivo anterior.")
    if args.seco:
        print("--seco: nada gravado.")
        return 0
    grava_json(DESTINO, novo)
    print(f"gravado data/{DESTINO}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
