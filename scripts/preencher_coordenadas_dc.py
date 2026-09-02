#!/usr/bin/env python3
"""
Preenche as coordenadas das 11 réguas DC de Itajaí em `estacoes_tempo_real`.

As réguas DC (DC-01..DC-11) não tinham coordenada: a camada delas no ArcGIS da
Prefeitura está atrás de token (ver `docs/coordenadas-dc-itajai.md`). As
coordenadas abaixo vieram dos **marcadores Leaflet da página "Mapa" da Defesa
Civil de Itajaí** (`defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php`), lidas
do HTML em 02/09/2026 — cada uma logo após o seu código DC.

Conferência (feita antes de gravar, e travada no teste): a distância à foz cai
com os nomes — DC-01/CEPSUL é a mais próxima do mar (~1,6 km), DC-10/Limoeiro a
mais distante (~26 km). Pareamento código↔coordenada correto.

O DC-00 (só pluviômetro, sem cota) NÃO entra.

Escreve preservando o formato do arquivo (insere `lat`/`lon`/`fonte_coordenada`
logo após a linha `"codigo"`), não reescreve o JSON inteiro. Idempotente: não
sobrescreve coordenada existente sem `--forcar`. Se qualquer uma das 11 não for
encontrada, NÃO grava nada e sai com erro.

Uso:
    python3 scripts/preencher_coordenadas_dc.py --seco   # mostra, não grava
    python3 scripts/preencher_coordenadas_dc.py          # grava
    python3 scripts/preencher_coordenadas_dc.py --forcar # sobrescreve existentes
"""

import argparse
import json
import re
import sys

from comum import DADOS

ESTACOES = DADOS / "estacoes.json"
FONTE = ("defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php "
         "(marcadores Leaflet), 02/09/2026")

#: código DC -> (lat, lon), lidas dos marcadores do Mapa.php da Defesa Civil de
#: Itajaí. São réguas de estuário — coordenada é da régua, não do centro urbano.
COORDENADAS = {
    "DC-01": (-26.909230, -48.651600),
    "DC-02": (-26.875683, -48.710217),
    "DC-03": (-26.911820, -48.719220),
    "DC-04": (-26.894100, -48.688380),
    "DC-05": (-26.933360, -48.747760),
    "DC-06": (-26.924420, -48.685760),
    "DC-07": (-26.892699, -48.735573),
    "DC-08": (-26.979694, -48.711948),
    "DC-09": (-26.879777, -48.700308),
    "DC-10": (-27.033530, -48.861419),
    "DC-11": (-26.879641, -48.761549),
}


def _bloco_do_codigo(raw: str, codigo: str) -> tuple[int, int] | None:
    """Início e fim (aprox.) do objeto que tem `"codigo": "<codigo>"`."""
    m = re.search(r'"codigo":\s*"' + re.escape(codigo) + r'"', raw)
    if not m:
        return None
    # o fim do item é antes do próximo "codigo" (ou o fim da lista)
    prox = re.search(r'"codigo":\s*"', raw[m.end():])
    fim = m.end() + prox.start() if prox else len(raw)
    return m.start(), fim


def preencher(raw: str, forcar: bool) -> tuple[str, list[str], list[str]]:
    """Devolve (texto novo, preenchidas, já-tinham). Erro (faltando) sobe fora."""
    faltando, feitas, ja = [], [], []
    for codigo, (lat, lon) in COORDENADAS.items():
        bloco = _bloco_do_codigo(raw, codigo)
        if bloco is None:
            faltando.append(codigo)
            continue
        ini, fim = bloco
        trecho = raw[ini:fim]
        if '"lat"' in trecho and not forcar:
            ja.append(codigo)
            continue
        feitas.append(codigo)

    if faltando:
        raise SystemExit(f"ERRO: códigos não encontrados em estacoes_tempo_real: "
                         f"{', '.join(faltando)}. Nada foi gravado.")

    # Faz as inserções/atualizações do fim para o início, para os índices não moverem.
    for codigo in sorted(feitas, reverse=True):
        lat, lon = COORDENADAS[codigo]
        # casa a linha do codigo e o recuo da linha seguinte, para alinhar os campos novos
        m = re.search(r'("codigo":\s*"' + re.escape(codigo) + r'",\n)([ \t]*)', raw)
        recuo = m.group(2)
        novos = (f'{recuo}"lat": {lat},\n{recuo}"lon": {lon},\n'
                 f'{recuo}"fonte_coordenada": {json.dumps(FONTE, ensure_ascii=False)},\n')
        ini, fim = _bloco_do_codigo(raw, codigo)
        trecho = raw[ini:fim]
        if forcar and '"lat"' in trecho:
            # remove lat/lon/fonte_coordenada antigos deste bloco antes de reinserir
            trecho = re.sub(r'[ \t]*"lat":.*\n[ \t]*"lon":.*\n(?:[ \t]*"fonte_coordenada":.*\n)?',
                            '', trecho, count=1)
            raw = raw[:ini] + trecho + raw[fim:]
            m = re.search(r'("codigo":\s*"' + re.escape(codigo) + r'",\n)([ \t]*)', raw)
        raw = raw[:m.end(1)] + novos + raw[m.end(1):]

    return raw, feitas, ja


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem gravar")
    ap.add_argument("--forcar", action="store_true", help="sobrescreve coordenada existente")
    args = ap.parse_args()

    raw = ESTACOES.read_text(encoding="utf-8")
    novo, feitas, ja = preencher(raw, args.forcar)

    print(f"{len(feitas)} régua(s) a preencher; {len(ja)} já tinham coordenada.")
    for c in sorted(feitas):
        print(f"  {c}: {COORDENADAS[c][0]}, {COORDENADAS[c][1]}")
    if ja:
        print(f"  (mantidas: {', '.join(sorted(ja))} — use --forcar para sobrescrever)")

    json.loads(novo)  # o resultado tem de continuar JSON válido
    if args.seco:
        print("\n--seco: nada gravado.")
        return 0
    if not feitas:
        print("\nnada a gravar.")
        return 0
    ESTACOES.write_text(novo, encoding="utf-8")
    print(f"\ngravado em {ESTACOES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
