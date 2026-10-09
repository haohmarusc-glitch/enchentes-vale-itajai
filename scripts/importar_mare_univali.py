#!/usr/bin/env python3
"""Importa a previsão de maré do Laboratório de Oceanografia Física da UNIVALI (Itajaí/SC) para `data/mare-itajai.json`.

A FONTE (decisão do Jefferson, 08/10/2026: "ajustar a fonte da maré para UNIVALI, a tábua que o Mauro mandou")
---------------------------------------------------------------------------------------------------------
O Prof. Mauro Michelena Andrade (LOF/UNIVALI, titular da Univali no GRAC da Defesa Civil de Itajaí) e o
oceanógrafo Márcio Piazera mandaram, em 03/09/2026 (setembro) e em 23/09/2026 (o ano de 2026 inteiro), a previsão
harmônica da maré para o **marégrafo UNIVALI / Porto de Itajaí / Cabeçudas Iate Clube** (lat −26,92872, lon
−48,62797, UTC−3). Em 09/09 a tábua do site tinha passado para a da Marinha (CHM/DHN) porque a planilha de
setembro acabaria em 30/09; com a planilha do ano, a tábua da UNIVALI volta a ser A fonte, e a da Marinha fica
como referência de cruzamento (`docs/TABUA-UNIVALI-2026.md`).

DOIS FORMATOS DE PLANILHA
-------------------------
1. **Série de 5 min** (planilha de 23/09/2026, `mare_astronomica_2026.xlsx`): colunas `data | hora | sl_fit`, uma
   linha a cada 5 minutos, 105.120 linhas no ano. Preamar e baixa-mar são os MÁXIMOS e MÍNIMOS locais da curva
   (`extremos_da_serie`). A curva de uma maré mista tem ondulações de poucos centímetros no estofo (um "pico" de
   5 mm dentro de um platô): elas não são maré alta nem maré baixa que alguém reconheça, e a própria Tábua da
   Marinha não as publica. `filtrar_ondulacoes` tira os pares adjacentes de amplitude menor que `ONDULACAO_M`
   (2 cm), sempre aos pares, para a alternância preamar/baixa-mar não quebrar. Em 2026: 897 → 851 preamares,
   contra 876 da Marinha.
2. **Blocos de extremos** (planilha de 03/09/2026): blocos de 3 colunas (Data | Hora | Nível) lado a lado, a data
   só na primeira linha de cada dia. Já vem só com os extremos; `classificar_extremos` separa alto de baixo
   pelos vizinhos. Mantido para a planilha antiga e para quem receber outra assim.

O QUE NÃO ENTRA: A ALTURA EM METROS
------------------------------------
A planilha não declara a referência vertical do `sl_fit`. A de setembro vinha em datum IBGE, e a média anual da
série (0,835 m) fica ~0,25 m acima da da Marinha, que publica sobre o Nível de Redução da carta 1841 — são zeros
diferentes, e nada aqui autoriza converter um no outro (é o problema do datum de Blumenau, REGRA BLOQUEANTE).
Regra do projeto (maré medida do CIRAM, 07/10/2026): número só com referência identificada. Então o registro
traz só o INSTANTE de cada preamar/baixa-mar (`quando`), nunca `altura_m`: a hora do pico não depende de datum.
A tela já sabe viver sem altura ("Sem altura"); a Marinha fica no bruto para quem quiser a altura sobre o NR.

CRUZAMENTO ANTES DE GRAVAR
--------------------------
Enquanto o arquivo anterior existir, cada preamar e baixa-mar nova é pareada com a mais próxima dele (até 3 h),
e o script imprime pareadas, mediana e p90 em minutos. Duas previsões harmônicas do mesmo porto têm de
concordar em minutos (em 2026: mediana −11 min, p90 27 min — a UNIVALI prevê um pouco antes); um desvio
sistemático de 60 min seria erro de fuso, e é isso que o cruzamento denuncia. Com `--gravar`, o relato do
cruzamento vai para `_meta.cruzamento`.

Uso:
    python3 scripts/importar_mare_univali.py --arquivo data/brutos/univali-mare-astronomica-2026.xlsx --verificar
    python3 scripts/importar_mare_univali.py --arquivo data/brutos/univali-mare-astronomica-2026.xlsx
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "mare-itajai.json"

#: Índices de coluna (0-based) de cada bloco (Data, Hora, Nível) da planilha de EXTREMOS. A planilha real tem
#: 3 blocos lado a lado, cada um com uma coluna vazia de separação.
BLOCOS = [(0, 1, 2), (4, 5, 6), (8, 9, 10)]

#: Cabeçalho da planilha de SÉRIE (5 min): data, hora e o nível previsto ("sea level fit").
CABECALHO_SERIE = ("data", "hora", "sl_fit")

#: Par adjacente (pico, vale) com amplitude menor que isto é ondulação de estofo, não preamar e baixa-mar.
ONDULACAO_M = 0.02

#: Pareamento com a tábua anterior: ponto sem par a menos disto fica fora da conta.
PAREAMENTO_MAX_MIN = 180

FONTE_CURTA = "Laboratório de Oceanografia Física da UNIVALI — previsão harmônica, marégrafo de Cabeçudas (porto de Itajaí)"

Ponto = tuple[datetime, float]


# --- planilha de EXTREMOS em blocos (03/09/2026) -------------------------------------------------------------

def extrair_eventos(linhas: list[tuple]) -> list[Ponto]:
    """
    (instante, nível) de cada evento da planilha de blocos, em ordem cronológica.

    `linhas` é a lista de tuplas de célula (uma por linha da planilha, já sem o cabeçalho). Dentro de cada
    bloco, a data só vem na primeira linha do dia — as linhas seguintes carregam a data anterior.
    """
    por_bloco: dict[int, list[tuple[date | None, time, float]]] = {b[0]: [] for b in BLOCOS}
    for linha in linhas:
        for (ci_data, ci_hora, ci_val) in BLOCOS:
            hora = linha[ci_hora] if ci_hora < len(linha) else None
            val = linha[ci_val] if ci_val < len(linha) else None
            if hora is None or val is None:
                continue
            bruta = linha[ci_data] if ci_data < len(linha) else None
            data_da_linha = bruta.date() if isinstance(bruta, datetime) else bruta
            por_bloco[ci_data].append((data_da_linha, hora, float(val)))

    eventos: list[Ponto] = []
    for itens in por_bloco.values():
        dia_atual: date | None = None
        for data_da_linha, hora, val in itens:
            if data_da_linha is not None:
                dia_atual = data_da_linha
            if dia_atual is None:
                continue  # linha antes de qualquer data conhecida: não dá pra datar
            eventos.append((datetime.combine(dia_atual, hora), val))

    eventos.sort(key=lambda e: e[0])
    return eventos


def classificar_extremos(eventos: list[Ponto]) -> tuple[list[Ponto], list[Ponto]]:
    """
    Separa os eventos (já extremos da curva) em preamares e baixa-mares.

    Cada evento é preamar se não for menor que os vizinhos imediatos, e baixa-mar se não for maior. Um evento que
    empata com os dois vizinhos não é classificado — melhor faltar um ponto do que adivinhar se é pico ou vale.
    """
    preamares: list[Ponto] = []
    baixamares: list[Ponto] = []
    for i, (quando, val) in enumerate(eventos):
        esquerda = eventos[i - 1][1] if i > 0 else None
        direita = eventos[i + 1][1] if i < len(eventos) - 1 else None
        eh_alto = (esquerda is None or val >= esquerda) and (direita is None or val >= direita)
        eh_baixo = (esquerda is None or val <= esquerda) and (direita is None or val <= direita)
        if eh_alto and not eh_baixo:
            preamares.append((quando, val))
        elif eh_baixo and not eh_alto:
            baixamares.append((quando, val))
    return preamares, baixamares


# --- planilha de SÉRIE de 5 min (23/09/2026) -----------------------------------------------------------------

def eh_serie(cabecalho: tuple) -> bool:
    """A planilha é a série de 5 min quando o cabeçalho é `data | hora | sl_fit`."""
    nomes = tuple(str(c).strip().lower() if c is not None else "" for c in cabecalho[:3])
    return nomes == CABECALHO_SERIE


def _instante(d, h) -> datetime | None:
    """Data (dd/mm/aaaa ou célula de data) e hora (hh:mm:ss ou célula de hora) → datetime local, sem fuso."""
    if d is None or h is None:
        return None
    dia = d.date() if isinstance(d, datetime) else d if isinstance(d, date) else datetime.strptime(str(d).strip(), "%d/%m/%Y").date()
    if isinstance(h, datetime):
        hora = h.time()
    elif isinstance(h, time):
        hora = h
    else:
        texto = str(h).strip()
        hora = datetime.strptime(texto, "%H:%M:%S" if texto.count(":") == 2 else "%H:%M").time()
    return datetime.combine(dia, hora)


def extrair_serie(linhas: list[tuple]) -> list[Ponto]:
    """(instante, nível) de cada linha da série, em ordem cronológica. Linha sem data, hora ou nível é pulada."""
    serie: list[Ponto] = []
    for linha in linhas:
        if len(linha) < 3:
            continue
        q = _instante(linha[0], linha[1])
        v = linha[2]
        if q is None or v is None:
            continue
        serie.append((q, float(v)))
    serie.sort(key=lambda p: p[0])
    return serie


def extremos_da_serie(serie: list[Ponto]) -> list[tuple[str, datetime, float]]:
    """
    Máximos ("P") e mínimos ("B") locais da curva contínua, em ordem.

    Um ponto é máximo quando sobe do anterior e não é menor que o seguinte (platô de dois iguais fica no primeiro);
    mínimo, o simétrico. Os dois extremos da série não entram: não têm os dois vizinhos.
    """
    ext: list[tuple[str, datetime, float]] = []
    for i in range(1, len(serie) - 1):
        a, (q, b), c = serie[i - 1][1], serie[i], serie[i + 1][1]
        if b > a and b >= c:
            ext.append(("P", q, b))
        elif b < a and b <= c:
            ext.append(("B", q, b))
    return ext


def filtrar_ondulacoes(ext: list[tuple[str, datetime, float]], limiar: float = ONDULACAO_M
                       ) -> tuple[list[tuple[str, datetime, float]], int]:
    """
    Tira, aos pares, as ondulações de estofo: enquanto algum par ADJACENTE tiver amplitude menor que `limiar`,
    o par de menor amplitude sai. Tirar um par (pico, vale) entre um vale e um pico preserva a alternância.
    Devolve (extremos que ficaram, pares removidos).
    """
    ext = list(ext)
    removidos = 0
    while len(ext) >= 3:
        amplitudes = [abs(ext[i + 1][2] - ext[i][2]) for i in range(len(ext) - 1)]
        i = min(range(len(amplitudes)), key=lambda k: amplitudes[k])
        if amplitudes[i] >= limiar:
            break
        del ext[i:i + 2]
        removidos += 1
    return ext, removidos


def separar(ext: list[tuple[str, datetime, float]]) -> tuple[list[Ponto], list[Ponto]]:
    return [(q, v) for t, q, v in ext if t == "P"], [(q, v) for t, q, v in ext if t == "B"]


# --- saída -----------------------------------------------------------------------------------------------------

def formatar(pontos: list[Ponto]) -> list[dict]:
    """Só o instante — nunca a altura (ver o cabeçalho do arquivo: referência vertical não declarada)."""
    return [{"quando": q.strftime("%Y-%m-%dT%H:%M")} for q, _ in pontos]


def cruzar(novos: list[Ponto], antigos: list[dict]) -> dict | None:
    """Pareia cada ponto novo com o mais próximo da tábua anterior (até PAREAMENTO_MAX_MIN) e mede os minutos."""
    refs = []
    for e in antigos:
        try:
            refs.append(datetime.fromisoformat(e["quando"]))
        except (KeyError, TypeError, ValueError):
            continue
    if not refs or not novos:
        return None
    difs = []
    for q, _ in novos:
        perto = min(refs, key=lambda r: abs((r - q).total_seconds()))
        d = (q - perto).total_seconds() / 60
        if abs(d) <= PAREAMENTO_MAX_MIN:
            difs.append(d)
    if not difs:
        return None
    absolutos = sorted(abs(d) for d in difs)
    return {
        "pareados": len(difs),
        "mediana_min": round(statistics.median(difs), 1),
        "p90_abs_min": round(absolutos[min(len(absolutos) - 1, int(len(absolutos) * 0.9))], 1),
        "maximo_abs_min": round(absolutos[-1], 1),
    }


def montar(preamares: list[Ponto], baixamares: list[Ponto], *, bruto: Path | None = None,
           formato: str = "serie", ondulacoes_removidas: int = 0, cruzamento: dict | None = None) -> dict:
    sha = hashlib.sha256(bruto.read_bytes()).hexdigest() if bruto and bruto.exists() else None
    metodo = (
        "Preamares e baixa-mares são os máximos e mínimos locais da curva de 5 min da previsão harmônica; "
        f"{ondulacoes_removidas} par(es) adjacente(s) de amplitude menor que {ONDULACAO_M:.2f} m (ondulação de estofo, "
        "que a Tábua da Marinha também não publica) foram tirados aos pares, preservando a alternância."
        if formato == "serie" else
        "Preamares e baixa-mares são os máximos e mínimos locais que a própria planilha já traz — não recalculados aqui."
    )
    meta = {
        "descricao": (
            "Tábua de maré do porto de Itajaí. O site cruza estas preamares com a janela de chegada da cheia: "
            "maré alta trava o escoamento do rio."
        ),
        "fuso": "Horário local (America/Sao_Paulo, UTC−3), como a planilha publica e o site espera.",
        "fonte": (
            "Previsão harmônica da maré do Laboratório de Oceanografia Física da UNIVALI (Itajaí/SC) — Prof. Mauro "
            "Michelena Andrade e oceanógrafo Márcio Piazera — para o marégrafo UNIVALI / Porto de Itajaí / Cabeçudas "
            "Iate Clube (lat −26,92872, lon −48,62797), recebida por e-mail em 23/09/2026. "
            + (f"Bruto: data/brutos/{bruto.name} (sha256 {sha}). " if bruto and sha else "")
            + "Importada por scripts/importar_mare_univali.py. Decisão do Jefferson de 08/10/2026: esta é a tábua do "
            "site; a Tábua de Marés da Marinha (CHM/DHN, data/brutos/chm-tabua-mare-itajai-2026.pdf) fica como "
            "referência de cruzamento."
        ),
        "estacao": {
            "nome": "Marégrafo UNIVALI / Porto de Itajaí / Cabeçudas Iate Clube",
            "lat": -26.92872,
            "lon": -48.62797,
        },
        "referencia_altura": None,
        "altura": (
            "A ALTURA NÃO ENTRA. A planilha não declara a referência vertical do nível previsto; a planilha de "
            "setembro vinha em datum IBGE, e a média anual desta série (≈0,84 m) fica ≈0,25 m acima da Tábua da "
            "Marinha, que é sobre o Nível de Redução da carta 1841 — zeros diferentes, sem conversão autorizada. "
            "Só o HORÁRIO de cada preamar/baixa-mar entra, que não depende de datum. Número com referência "
            "identificada é regra do projeto (maré medida do CIRAM, 07/10/2026)."
        ),
        "metodo": metodo,
        "fonte_curta": FONTE_CURTA,
    }
    if cruzamento:
        meta["cruzamento"] = cruzamento
    return {
        "_meta": meta,
        "porto": "Itajaí",
        "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pontos_astronomicos": len(preamares) + len(baixamares),
        "pontos_observados": 0,
        "preamares": formatar(preamares),
        "baixamares": formatar(baixamares),
    }


def ler_planilha(caminho: Path) -> tuple[tuple, list[tuple]]:
    """(cabeçalho, linhas) da primeira aba."""
    try:
        import openpyxl
    except ImportError:
        print("Para ler .xlsx é preciso o openpyxl: pip install -r scripts/requirements.txt", file=sys.stderr)
        raise SystemExit(2)
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    linhas = list(ws.iter_rows(values_only=True))
    return (linhas[0] if linhas else ()), linhas[1:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", required=True, help="planilha .xlsx da UNIVALI (série de 5 min ou blocos de extremos)")
    ap.add_argument("--verificar", action="store_true", help="mostra o que veio e não grava")
    args = ap.parse_args()

    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"ERRO: {caminho} não existe", file=sys.stderr)
        return 1

    cabecalho, linhas = ler_planilha(caminho)
    if eh_serie(cabecalho):
        serie = extrair_serie(linhas)
        if len(serie) < 3:
            print("ERRO: série vazia ou curta demais", file=sys.stderr)
            return 1
        passos = {(b[0] - a[0]) for a, b in zip(serie, serie[1:])}
        brutos = extremos_da_serie(serie)
        ext, removidos = filtrar_ondulacoes(brutos)
        preamares, baixamares = separar(ext)
        formato = "serie"
        print(f"série:          {len(serie)} pontos, de {serie[0][0]} a {serie[-1][0]}, "
              f"passo(s) {sorted(int(p.total_seconds() // 60) for p in passos)} min")
        print(f"extremos:       {len(brutos)} na curva, {removidos} par(es) de ondulação < {ONDULACAO_M} m tirados")
        periodo = (serie[0][0].date(), serie[-1][0].date())
    else:
        eventos = extrair_eventos(linhas)
        if not eventos:
            print("ERRO: nenhum evento encontrado na planilha (formato inesperado?)", file=sys.stderr)
            return 1
        preamares, baixamares = classificar_extremos(eventos)
        removidos = 0
        formato = "blocos"
        print(f"eventos lidos:  {len(eventos)}")
        nao = len(eventos) - len(preamares) - len(baixamares)
        if nao:
            print(f"AVISO: {nao} evento(s) não classificado(s) (empate com os vizinhos)")
        periodo = (eventos[0][0].date(), eventos[-1][0].date())

    print(f"preamares:      {len(preamares)}")
    print(f"baixa-mares:    {len(baixamares)}")
    print(f"período:        {periodo[0]} a {periodo[1]}")

    cruzamento: dict | None = None
    if DESTINO.exists():
        antigo = json.loads(DESTINO.read_text(encoding="utf-8"))
        fonte_antiga = (antigo.get("_meta") or {}).get("fonte_curta", "?")
        cruzamento = {"com": fonte_antiga}
        for chave, novos in (("preamares", preamares), ("baixamares", baixamares)):
            c = cruzar(novos, antigo.get(chave) or [])
            cruzamento[chave] = c
            if c:
                print(f"cruzamento {chave} com '{fonte_antiga}': {c['pareados']} pareadas, mediana {c['mediana_min']} min, "
                      f"p90 {c['p90_abs_min']} min, máximo {c['maximo_abs_min']} min.")
            else:
                print(f"cruzamento {chave}: nada a parear com o arquivo anterior.")

    dados = montar(preamares, baixamares, bruto=caminho, formato=formato, ondulacoes_removidas=removidos,
                   cruzamento=cruzamento)
    if args.verificar:
        print("\n--verificar: nada foi gravado.")
        return 0

    temporario = DESTINO.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(DESTINO)
    print(f"\ngravado em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
