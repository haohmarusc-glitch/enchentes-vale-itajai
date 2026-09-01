#!/usr/bin/env python3
"""
Lê a tabela de monitoramento da Defesa Civil de Gaspar.

Fonte: https://defesacivil.gaspar.sc.gov.br/monitoramento/tabela — HTML simples.
Traz a estação do Itajaí-Açu em Gaspar, as barragens e pluviômetros.

POR QUE GASPAR
--------------
Gaspar tem **1.618 cotas de rua** e **nenhuma cota de régua** em `estacoes.json`.
Os números dizem a partir de quanto cada rua alaga; falta o "o rio está chegando
lá". Enquanto a cidade não tiver cota de referência, **nada que este script
colete dispara aviso** — ele mostra, e é só.

O QUE ESTE SCRIPT SE RECUSA A FAZER
-----------------------------------
Uma versão anterior deduzia as faixas de cota varrendo o texto da página atrás
de "atenção", "alerta" e "emergência" seguidos de um número. Numa página de
monitoramento, "ATENÇÃO — nível 3,25 m" quer dizer que o rio ESTÁ em 3,25 m, não
que a cota de atenção é 3,25 m. O deduzido iria para `estacoes.json` e viraria o
limiar que dispara o aviso de Gaspar — no nível errado, para sempre, sem nada na
tela denunciando.

Então: **faixa só sai daqui se vier rotulada numa célula própria da tabela**, e
mesmo assim ela é PROPOSTA, nunca gravada. E uma candidata que seja igual ao
nível atual é recusada, porque quase certamente é o nível ecoado.

Uso:
    python3 scripts/coleta_gaspar.py            # lê, mostra e grava a última leitura
    python3 scripts/coleta_gaspar.py --seco     # lê e mostra, sem gravar
    python3 scripts/coleta_gaspar.py --cotas    # propõe as faixas, se houver, sem gravar
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse

from comum import DADOS, USER_AGENT, baixar, espera_turno, nivel_plausivel
from importar_cotas_rio_do_sul import robots_permite

URL = "https://defesacivil.gaspar.sc.gov.br/monitoramento/tabela"
ROBOTS = "https://defesacivil.gaspar.sc.gov.br/robots.txt"
SAIDA = "tempo-real/ultimo_gaspar.json"

#: Um nível: número com vírgula ou ponto seguido de "m". A unidade é obrigatória
#: — é ela que separa "3,25 m" de "85,4 %" e de "01/09/2026".
RE_NIVEL = re.compile(r"(\d{1,3}[,.]\d{1,2})\s*m\b", re.IGNORECASE)
RE_PORCENTAGEM = re.compile(r"(\d{1,3}(?:[,.]\d{1,2})?)\s*%")
RE_QUANDO = re.compile(r"(\d{2}/\d{2}/\d{4})\D{0,6}(\d{2}:\d{2})")

#: Os rótulos de faixa que a tabela pode trazer, e o nome que usamos.
FAIXAS = {"atencao": "atencao", "alerta": "alerta", "emergencia": "emergencia",
          "inundacao": "inundacao", "observacao": "observacao"}

#: Uma candidata a faixa que fique a menos disto do nível atual é descartada: é
#: o nível ecoado no rótulo, não um limiar.
MARGEM_DO_NIVEL_M = 0.02


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower())
                   if unicodedata.category(c) != "Mn")


def numero(texto) -> float | None:
    achado = RE_NIVEL.search(str(texto or ""))
    return float(achado.group(1).replace(",", ".")) if achado else None


def celulas(linha_html) -> list[str]:
    return [c.get_text(" ", strip=True) for c in linha_html.find_all(["td", "th"])]


def ler_linha(cels: list[str]) -> dict | None:
    """
    Uma linha da tabela vira uma leitura — ou nada.

    Cada grandeza sai da SUA célula. Juntar a linha inteira e pegar o primeiro
    número faria a ocupação de uma barragem ("85,4 %") virar nível de rio, que é
    o que acontecia antes.
    """
    if not cels or len(cels) < 2:
        return None
    rotulo = cels[0].strip()
    if not rotulo:
        return None

    nivel = porcentagem = quando = None
    for celula in cels[1:]:
        if nivel is None and (achado := RE_NIVEL.search(celula)):
            nivel = float(achado.group(1).replace(",", "."))
        if porcentagem is None and (achado := RE_PORCENTAGEM.search(celula)):
            porcentagem = float(achado.group(1).replace(",", "."))
        if quando is None and (achado := RE_QUANDO.search(celula)):
            quando = f"{achado.group(1)} {achado.group(2)}"

    if nivel is None and porcentagem is None:
        return None
    return {
        "rotulo": rotulo,
        "nivel_m": nivel,
        # A régua de plausibilidade que a coleta inteira usa. Fora dela o número
        # aparece na linha bruta e não no campo, para não ser lido como nível.
        "nivel_plausivel": nivel is not None and nivel_plausivel(nivel),
        "ocupacao_pct": porcentagem,
        "medido_em": quando,
        # A linha crua fica para quem for ajustar o parser contra o HTML real.
        "linha_bruta": " | ".join(cels)[:220],
    }


def e_barragem(rotulo: str) -> bool:
    return any(p in sem_acento(rotulo) for p in ("barragem", "represa"))


def faixas_da_linha(cels: list[str], nivel_atual: float | None) -> dict[str, float]:
    """
    Faixas rotuladas em células próprias — e só assim.

    Uma célula precisa ser o rótulo ("Atenção") e a seguinte o número. Não se
    varre texto corrido: numa página de monitoramento, "ATENÇÃO — nível 3,25 m"
    é o nível atual, e capturá-lo como limiar poria o aviso de Gaspar no nível
    errado.
    """
    achadas: dict[str, float] = {}
    for i, celula in enumerate(cels[:-1]):
        chave = FAIXAS.get(sem_acento(celula).strip(" :"))
        if not chave:
            continue
        valor = numero(cels[i + 1])
        if valor is None or not nivel_plausivel(valor):
            continue
        if nivel_atual is not None and abs(valor - nivel_atual) <= MARGEM_DO_NIVEL_M:
            continue
        achadas.setdefault(chave, valor)
    return achadas


def analisar(html: str) -> dict:
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(html, "html.parser")
    leitura = {"fonte": URL, "coletado_em": datetime.now(timezone.utc).isoformat(),
               "estacoes": [], "barragens": [], "faixas_propostas": {}}

    linhas = [celulas(tr) for tabela in sopa.find_all("table")
              for tr in tabela.find_all("tr")]
    for cels in linhas:
        item = ler_linha(cels)
        if item is None:
            continue
        (leitura["barragens"] if e_barragem(item["rotulo"])
         else leitura["estacoes"]).append(item)

    nivel_gaspar = next((e["nivel_m"] for e in leitura["estacoes"]
                         if "gaspar" in sem_acento(e["rotulo"]) and e["nivel_plausivel"]), None)
    for cels in linhas:
        leitura["faixas_propostas"].update(faixas_da_linha(cels, nivel_gaspar))
    return leitura


def permitido(buscar=baixar) -> bool:
    """Fonte nova, mesma régua de sempre: o robots.txt antes de qualquer coisa."""
    try:
        texto = buscar(ROBOTS)
    except Exception as erro:
        if "404" in str(erro) or "Not Found" in str(erro):
            return True
        print(f"não deu para ler {ROBOTS}: {erro}", file=sys.stderr)
        return False
    return robots_permite(texto, urlparse(URL).path)


def propor_cotas(leitura: dict) -> None:
    faixas = leitura.get("faixas_propostas") or {}
    if not faixas:
        print("\n[--cotas] a tabela não traz faixa de cota rotulada.")
        print("  Isso é resposta, não falha: a página pode publicar só o nível atual.")
        print("  As cotas de régua de Gaspar teriam então de vir por ofício à Defesa")
        print("  Civil ou do Plano de Contingência do município — foi assim que as")
        print("  onze estações de Itajaí entraram.")
        return
    print("\n[--cotas] proposta para data/estacoes.json → itajai-acu → gaspar (REVISAR):")
    # Sem o campo `referencia`: ele tem conjunto fechado (régua, IBGE, null) e
    # hipótese vai em `nota`. Ver a REGRA BLOQUEANTE no CLAUDE.md.
    print(json.dumps({
        "cotas_m": faixas,
        "cotas_verificado": False,
        "observacao": (f"Faixas lidas de {URL} em {leitura['coletado_em']}. Falta "
                       "confirmar a que régua se referem — a de rua de Gaspar é a da "
                       "ANA na empresa Círculo, e isso NÃO foi verificado para estas."),
    }, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra sem gravar")
    ap.add_argument("--cotas", action="store_true", help="propõe as faixas, se houver")
    args = ap.parse_args()

    if not permitido():
        print("\nRECUSADO: o robots.txt de defesacivil.gaspar.sc.gov.br não libera "
              "esta página, ou não deu para lê-lo.", file=sys.stderr)
        return 2

    espera_turno()
    try:
        leitura = analisar(baixar(URL))
    except Exception as erro:
        print(f"não deu para ler {URL}: {erro}", file=sys.stderr)
        return 1

    print(f"{len(leitura['estacoes'])} estações · {len(leitura['barragens'])} barragens "
          f"· faixas rotuladas: {sorted(leitura['faixas_propostas']) or 'nenhuma'}")
    for e in leitura["estacoes"][:10]:
        marca = "" if e["nivel_plausivel"] or e["nivel_m"] is None else "  <- fora de faixa"
        print(f"  {str(e['nivel_m']):>7} m  {e['medido_em'] or '-':<17} "
              f"{e['rotulo'][:44]}{marca}")
    for b in leitura["barragens"]:
        print(f"  [barragem] {str(b['nivel_m']):>7} m · ocupação "
              f"{b['ocupacao_pct'] if b['ocupacao_pct'] is not None else '-'}%  {b['rotulo'][:40]}")
    print(f"\nUser-Agent: {USER_AGENT}")
    print("Enquanto Gaspar não tiver cota em estacoes.json, nada disto dispara aviso.")

    if args.cotas:
        propor_cotas(leitura)
    if not args.seco and not args.cotas:
        # Só a última leitura. A série é trabalho do coleta_niveis.py, que já
        # compacta por mês; um arquivo por execução num cron de 15 min viraria
        # milhares de arquivos aqui dentro.
        (DADOS / SAIDA).write_text(json.dumps(leitura, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
        print(f"gravado em data/{SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
