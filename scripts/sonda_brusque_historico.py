#!/usr/bin/env python3
"""Sonda o download de histórico da Defesa Civil de Brusque — sem gravar dado.

ORIGEM (08/09/2026): o Jefferson leu o formulário da página de estação e
extraiu o endpoint sem disparar nada:

    POST /estacao/baixar-historico   (form-urlencoded)
    codest=<id>&inicio=AAAA-MM-DD&fim=AAAA-MM-DD

O `codest` é o mesmo número de `/estacao/ver/<id>`. **O formato da resposta é
DESCONHECIDO** — CSV, XLS ou HTML —, e é justamente por isso que isto é sonda e
não coletor: no mesmo dia, a série da ANA ensinou que o formato da resposta
decide tudo, e a de rótulo melhor apagava uma cheia de 4 m
(docs/ANA-API-2026-09-08.md).

⚠️ O QUE ESTA SONDA PODE E NÃO PODE AFIRMAR
Ela mede o que chega. **Não vincula estação a cidade.** As quatro conhecidas:

    31 SALSEIRO           — RECUSADA como régua de Vidal Ramos: 6,8 km da sede,
                            e a diferença foi MEDIDA em 0,70 m (08/09/2026).
    18 BOTUVERÁ           — a conferir; a 83892998 BOTUVERA-MONTANTE também é
                            recusa, e nome parecido já enganou este projeto.
     4 PONTE ESTAIADA     — repasse do DCSC; par PROVADO com a nossa leitura de
                            Brusque em 07/09/2026 (1,27 / 1,27 / 1,28 m).
    23 GUARANI            — a conferir.

⚠️ ROBOTS.TXT PRIMEIRO. Fonte nova só entra com o robots conferido — foi por
isso que o AlertaBlu ficou de fora. Sem robots legível, a sonda RECUSA.

⚠️ NÃO RODA DESTE AMBIENTE: `defesacivil.*.sc.gov.br` é bloqueado no proxy
(HTTP 000 no CONNECT, medido em 08/09/2026). Rode na VPS.

Uso:
    python3 scripts/sonda_brusque_historico.py --seco        # mostra o que faria
    python3 scripts/sonda_brusque_historico.py               # Salseiro, 18 dias
    python3 scripts/sonda_brusque_historico.py --codest 4 --inicio 2026-08-31 --fim 2026-09-02
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover - ambiente sem dependências
    print("Falta a dependência: pip install -r scripts/requirements.txt", file=sys.stderr)
    raise SystemExit(2)

from comum import DADOS, USER_AGENT, espera_turno
from importar_cotas_rio_do_sul import robots_permite

BASE = "https://defesacivil.brusque.sc.gov.br"
ROBOTS = f"{BASE}/robots.txt"
PAGINA = BASE + "/estacao/ver/{codest}"
BAIXAR = f"{BASE}/estacao/baixar-historico"
#: O botão faz um POST AJAX aqui antes de submeter o form; sem ele o
#: servidor pode recusar. Descoberto pelo Jefferson lendo o JS (08/09/2026).
VALIDAR = f"{BASE}/estacao/baixar-historico?validar"
#: O servidor recusa janelas maiores que um ano — por isso os dez arquivos
#: da Salseiro vieram em fatias anuais.
JANELA_MAXIMA = timedelta(days=366)

#: Estação por id, com o papel que ela JÁ TEM no projeto. Recusa é papel: o
#: rótulo viaja com o número para a saída nunca sugerir que sondar é vincular.
ESTACOES = {
    # ids lidos pelo Jefferson no portal em 08/09/2026 (scripts dele). O PAPEL
    # viaja com o id: a saída nunca pode sugerir que sondar é vincular.
    "31": "SALSEIRO — RECUSADA como régua de Vidal Ramos (6,8 km, 0,70 m medidos)",
    "3":  "VIDAL RAMOS — CANDIDATA a ser a NOSSA régua (DCSC-00024): a conferir pelo par "
          "de leituras simultâneas, como se fez com a 79",
    "18": "BOTUVERÁ — a conferir (DCSC-00018?)",
    "2":  "CEOPS - BOTUVERÁ — a conferir; nome parecido já enganou este projeto",
    "32": "BOTUVERÁ - PREFEITURA — a conferir",
    "79": "PONTE ESTAIADA – DCSC — par PROVADO com a leitura de Brusque em 07/09/2026 "
          "(1,27 / 1,27 / 1,28 m). É a DCSC-00019",
    "4":  "PONTE ESTAIADA – ANA — OUTRA RÉGUA, mesmo nome. Provavelmente a 83900000 "
          "(BRUSQUE PCD). ⚠️ no #241 eu a rotulei como 'par provado': era a 79",
    "23": "GUARANI — a conferir",
    "19": "CEDRO ALTO — a conferir", "24": "LIMEIRA ALTA — a conferir",
    "25": "LIMEIRA BAIXA — a conferir", "21": "DOM JOAQUIM — a conferir (⚠️ o ver/21 "
          "citado no cadastro é do portal de GASPAR, não deste)",
    "20": "ZANTÃO — a conferir", "17": "PAQUETÁ — a conferir",
    "22": "RES. FELIPE HECKERT — a conferir",
}

#: Os dois formatos que o campo `<input type="date">` e um backend PHP antigo
#: podem esperar. A sonda tenta o nativo primeiro e só cai no outro se o
#: primeiro voltar vazio ou com erro — sem insistir além disso.
FORMATOS_DE_DATA = ("%Y-%m-%d", "%d/%m/%Y")

#: Quantos bytes do corpo mostrar. O suficiente para reconhecer CSV, XLS ou
#: HTML de erro sem despejar a resposta inteira na tela.
ESPIADA = 600


def permitido(sessao: requests.Session) -> bool:
    """Host sem robots.txt é liberado por omissão; erro de rede NÃO é."""
    try:
        r = sessao.get(ROBOTS, timeout=30)
    except requests.RequestException as erro:
        print(f"não deu para ler {ROBOTS}: {erro}", file=sys.stderr)
        return False
    if r.status_code == 404:
        return True
    if r.status_code != 200:
        print(f"{ROBOTS}: HTTP {r.status_code} — não dá para saber", file=sys.stderr)
        return False
    return robots_permite(r.text, urlparse(BAIXAR).path)


def descreve(resposta: requests.Response) -> str:
    tipo = resposta.headers.get("Content-Type", "?")
    disp = resposta.headers.get("Content-Disposition", "")
    return (f"HTTP {resposta.status_code} · {tipo} · {len(resposta.content)} bytes"
            + (f" · {disp}" if disp else ""))


def tenta(sessao, codest: str, inicio: date, fim: date, formato: str):
    dados = {"codest": codest, "inicio": inicio.strftime(formato), "fim": fim.strftime(formato)}
    espera_turno()
    v = sessao.post(VALIDAR, timeout=30, data=dados)
    print(f"   validar: HTTP {v.status_code} · {len(v.content)} bytes · "
          f"{v.text[:80].replace(chr(10), ' ')!r}")
    espera_turno()
    return sessao.post(BAIXAR, timeout=120, data=dados)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codest", default="31", choices=sorted(ESTACOES))
    ap.add_argument("--inicio", type=date.fromisoformat,
                    default=date.today() - timedelta(days=17))
    ap.add_argument("--fim", type=date.fromisoformat, default=date.today())
    ap.add_argument("--seco", action="store_true", help="mostra o que faria, sem rede")
    args = ap.parse_args()

    print(f"estação {args.codest}: {ESTACOES[args.codest]}")
    print(f"janela: {args.inicio} a {args.fim}")
    if args.fim - args.inicio > JANELA_MAXIMA:
        print("RECUSADO antes de chamar: o servidor não aceita mais de um ano por "
              "pedido. Fatie por ano, como os dez arquivos da Salseiro.", file=sys.stderr)
        return 2
    if args.seco:
        print(f"\nGET  {PAGINA.format(codest=args.codest)}   (cookie de sessão)")
        print(f"POST {BAIXAR}   codest, inicio, fim")
        print(f"antes de tudo: {ROBOTS}")
        print(f"User-Agent: {USER_AGENT}")
        return 0

    sessao = requests.Session()
    sessao.headers["User-Agent"] = USER_AGENT

    if not permitido(sessao):
        print("\nRECUSADO: o robots.txt de defesacivil.brusque.sc.gov.br não libera "
              "este caminho, ou não deu para lê-lo. Fonte nova só entra com o robots "
              "conferido — foi por isso que o AlertaBlu ficou de fora.", file=sys.stderr)
        return 2

    # O GET antes do POST é precaução do Jefferson: este tipo de site costuma
    # amarrar o POST à sessão. Se o POST voltar 302 para a home, era isso.
    espera_turno()
    pagina = sessao.get(PAGINA.format(codest=args.codest), timeout=30)
    print(f"\npágina da estação: {descreve(pagina)} · cookies: {list(sessao.cookies)}")

    for formato in FORMATOS_DE_DATA:
        r = tenta(sessao, args.codest, args.inicio, args.fim, formato)
        print(f"\nPOST com datas em {formato}: {descreve(r)}")
        if r.history:
            print(f"   ⚠️ redirecionou: {[h.status_code for h in r.history]} -> {r.url}")
        corpo = r.content[:ESPIADA]
        print("   espiada:", corpo.decode("utf-8", "replace").replace("\n", "⏎")[:ESPIADA])

        util = r.status_code == 200 and r.content and not r.history
        if not util:
            continue

        destino = (DADOS / "brutos" /
                   f"brusque-historico-{args.codest}-{date.today().isoformat()}.bruto")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(r.content)
        print(f"\n   bruto gravado em {destino.relative_to(DADOS.parent)} — "
              "a extensão é `.bruto` DE PROPÓSITO: o formato ainda não foi "
              "identificado, e nomear de .csv o que pode ser HTML é o primeiro "
              "passo para tratar erro como dado.")
        return 0

    print("\nnenhum dos dois formatos de data trouxe corpo útil. NÃO insistir com "
          "mais variações: registrar o negativo, como se fez com a telemetria da ANA.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
