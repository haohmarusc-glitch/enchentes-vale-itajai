#!/usr/bin/env python3
"""
Leitura da régua do CENTRO de Ituporanga, do Boletim Diário da Defesa Civil municipal.

Fonte: https://www.ituporanga.sc.gov.br/nivel-rio — página HTML da Prefeitura, com o cabeçalho
"Última leitura: dd/mm/aaaa HH:MM · Nível do Rio (Centro): X,XX m · Nível de Criticidade: <texto>" e,
abaixo, a tabela "Histórico de Leituras" da BARRAGEM SUL (montante, jusante, comportas, canal extravasor).
Leitura manual, duas vezes ao dia (07:00 e 17:00). `robots.txt` da Prefeitura: `Allow: /`.

POR QUE EXISTE (decisão do Jefferson, 08/10/2026)
--------------------------------------------------
A régua da cidade no cadastro é a DCSC-00039, que fica A JUSANTE DA BARRAGEM SUL (ANA 83145140,
"Barragem Sul Ituporanga Jusante"); a coluna "Jusante (m)" desta mesma página bate com ela (4,21 m
às 07:00 de 08/10/2026 contra 4,17 m na DCSC às 09:46). A régua do "Centro" é OUTRA régua, dentro da
cidade, que a fonte não nomeia nem situa, e cujo zero não é informado. O morador do Centro olha para
ela; por isso ela entra no site — **com horário e fonte, e sem cor**: as cotas que a Prefeitura usa para
dizer "Alerta" não foram confirmadas na mesma régua, e sem isso nenhuma faixa deste projeto se aplica.

O QUE ESTE SCRIPT NÃO FAZ
-------------------------
* Não escreve em `ultimo.json` nem em `leituras`: se a leitura do Centro entrasse ali como leitura
  de Ituporanga, ela viraria "a leitura municipal" da cidade e desligaria a classificação estadual
  da DCSC-00039 (a municipal manda). Ela vai num arquivo próprio, `ultimo_ituporanga_centro.json`,
  como a maré do CIRAM.
* Não deduz cota, não calcula faixa, não pinta. A criticidade que a fonte escreve ("Alerta") é
  repassada como TEXTO da fonte, com o nome dela, nunca como cor deste site.
* Não lê o nível da barragem como nível da cidade: "Montante (m)" (~20 m) é o reservatório. A
  separação é estrutural — campos diferentes, nunca misturados (a armadilha de Taió).

Uso:
    python3 scripts/coleta_ituporanga.py                 # busca e mostra
    python3 scripts/coleta_ituporanga.py --arquivo p.html  # lê um HTML salvo, sem rede
    python3 scripts/coleta_ituporanga.py --publicar      # grava data/tempo-real/ultimo_ituporanga_centro.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from comum import DADOS, baixar, grava_json, nivel_plausivel
from importar_cotas_rio_do_sul import robots_permite

URL = "https://www.ituporanga.sc.gov.br/nivel-rio"
URL_ROBOTS = "https://www.ituporanga.sc.gov.br/robots.txt"
ARQUIVO_PUBLICAVEL = "tempo-real/ultimo_ituporanga_centro.json"
FONTE = "Prefeitura de Ituporanga — Defesa Civil, Boletim Diário (Nível do Rio)"

#: A fonte publica hora local, sem fuso. É o contrato do `medido_em` do projeto (CLAUDE.md).
HORARIO = "Brasília, sem fuso; leituras manuais às 07:00 e às 17:00, conforme a própria página"

#: Duas leituras por dia: mais de 18 h sem leitura nova é boletim parado, e a tela não mostra o número
#: como atual (o site refaz a idade no relógio de agora; aqui só se registra).
FRESCA_MIN = 18 * 60

RE_ULTIMA = re.compile(r"Última leitura:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})")
RE_CENTRO = re.compile(r"Nível do Rio \(Centro\):\s*([\d.,]+)\s*m")
RE_CRITICIDADE = re.compile(r"Nível de Criticidade:\s*([A-Za-zÀ-ÿ ]+?)(?:\s{2,}|$|\sBarragem)")
RE_DATA_HORA = re.compile(r"^(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})$")


def _texto(fragmento: str) -> str:
    """HTML -> texto corrido, com entidades resolvidas e espaços colapsados."""
    sem_scripts = re.sub(r"<script.*?</script>|<style.*?</style>", " ", fragmento, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", sem_scripts))).strip()


def numero(bruto: str | None) -> float | None:
    """`"2,04"` -> 2.04. Vírgula é decimal nesta fonte; ponto de milhar não aparece em metro."""
    if bruto is None:
        return None
    s = bruto.strip().replace(".", "").replace(",", ".") if "," in bruto else bruto.strip()
    try:
        return float(s)
    except ValueError:
        return None


def data_hora_para_iso(data: str, hora: str) -> str | None:
    """`"08/10/2026", "07:00"` -> `"2026-10-08T07:00:00"` (Brasília, sem fuso)."""
    m = RE_DATA_HORA.match(f"{data} {hora}")
    if not m:
        return None
    d, mes, a, h, mi = (int(x) for x in m.groups())
    try:
        return datetime(a, mes, d, h, mi).isoformat(timespec="seconds")
    except ValueError:
        return None


def _linhas_da_tabela(pagina: str, cabecalho: str) -> list[list[str]]:
    """As linhas (células em texto) da tabela cujo cabeçalho contém `cabecalho`."""
    for tabela in re.findall(r"<table.*?</table>", pagina, flags=re.S):
        linhas = [
            [_texto(c) for c in re.findall(r"<t[hd].*?</t[hd]>", linha, flags=re.S)]
            for linha in re.findall(r"<tr.*?</tr>", tabela, flags=re.S)
        ]
        if linhas and any(cabecalho in c for c in linhas[0]):
            return linhas
    return []


def extrair(pagina: str) -> dict:
    """
    A página -> o que se publica. Falha alto (ValueError) quando o cabeçalho não traz leitura
    legível: um arquivo sem leitura nunca passa por leitura.
    """
    texto = _texto(pagina)
    m_ultima = RE_ULTIMA.search(texto)
    m_centro = RE_CENTRO.search(texto)
    if not m_ultima or not m_centro:
        raise ValueError("a página não traz 'Última leitura' e 'Nível do Rio (Centro)' legíveis")
    medido_em = data_hora_para_iso(m_ultima.group(1), m_ultima.group(2))
    nivel = numero(m_centro.group(1))
    if medido_em is None:
        raise ValueError(f"horário ilegível: {m_ultima.group(0)!r}")
    if nivel is None or not nivel_plausivel(nivel):
        raise ValueError(f"nível do Centro implausível: {m_centro.group(1)!r}")
    m_crit = RE_CRITICIDADE.search(texto)
    criticidade = m_crit.group(1).strip() if m_crit else None

    barragem = None
    linhas = _linhas_da_tabela(pagina, "Montante (m)")
    if len(linhas) >= 2 and len(linhas[1]) >= 8:
        cab, l = linhas[0], linhas[1]
        col = {c: i for i, c in enumerate(cab)}
        try:
            data, hora = l[col["Data / Hora"]].split()
        except (KeyError, ValueError):
            data = hora = ""
        quando = data_hora_para_iso(data, hora) if data and hora else None
        barragem = {
            "medido_em": quando,
            "montante_m": numero(l[col.get("Montante (m)", 1)]),
            "jusante_m": numero(l[col.get("Jusante (m)", 2)]),
            "comportas_abertas": _inteiro(l[col.get("Comp. Aberta(s)", 3)]),
            "comportas_fechadas": _inteiro(l[col.get("Comp. Fechada(s)", 4)]),
            "canal_extravasor": l[col.get("Canal Extravasor", 5)] or None,
            "lamina_canal_extravasor_m": numero(l[col.get("Lâmina Canal Extravasor", 6)]),
            "lamina_vertedouro_m": numero(l[col.get("Lâmina Vertedouro", 7)]),
        }
    return {
        "medido_em": medido_em,
        "nivel_m": nivel,
        "criticidade_na_fonte": criticidade,
        "barragem_sul": barragem,
    }


def _inteiro(bruto: str) -> int | None:
    try:
        return int(bruto.strip())
    except (ValueError, AttributeError):
        return None


def idade_min(medido_em: str, agora: datetime) -> float:
    """Minutos entre a leitura e agora, os DOIS em horário de Brasília (nunca converter um só)."""
    return (agora - datetime.fromisoformat(medido_em)).total_seconds() / 60


def resumo_publicavel(dados: dict, agora: datetime, gerado_em: str) -> dict:
    idade = round(idade_min(dados["medido_em"], agora))
    return {
        "versao": 1,
        "gerado_em": gerado_em,
        "fonte": FONTE,
        "fonte_url": URL,
        "cidade": "ituporanga",
        "regua": {
            "nome": "Centro",
            "identificada": False,
            "nota": ("A fonte não nomeia a régua, não a situa e não informa o zero. NÃO é a DCSC-00039, que "
                     "fica a jusante da Barragem Sul e dá a cor da cidade no site. Sem cor até a Defesa Civil "
                     "confirmar as cotas na mesma régua (decisão do Jefferson, 08/10/2026)."),
        },
        "unidade": "m",
        "horario": HORARIO,
        "frescor_max_min": FRESCA_MIN,
        "idade_min_na_coleta": idade,
        "situacao": "fresca" if 0 <= idade <= FRESCA_MIN else "antiga",
        "ultima_leitura": {
            "medido_em": dados["medido_em"],
            "nivel_m": dados["nivel_m"],
            "criticidade_na_fonte": dados["criticidade_na_fonte"],
        },
        "barragem_sul": dados["barragem_sul"],
        "aviso": ("Leitura manual da Defesa Civil de Ituporanga, duas vezes ao dia, em régua própria. "
                  "Não é alerta deste site, não pinta o mapa e não se compara com a DCSC-00039."),
    }


def baixar_pagina() -> str:
    """A página, só se o robots.txt da Prefeitura permitir o caminho."""
    if not robots_permite(baixar(URL_ROBOTS), "/nivel-rio"):
        raise RuntimeError("robots.txt da Prefeitura de Ituporanga não permite /nivel-rio")
    return baixar(URL)


def publicar(agora: datetime, buscador=baixar_pagina, raiz: Path | None = None) -> int:
    """
    `--publicar`: uma página, um arquivo pequeno. Falha APAGA o arquivo anterior — uma leitura de
    outra coleta não pode passar por atual (o publicador ainda recusa arquivo com mais de 30 min).
    """
    destino = (raiz or DADOS) / ARQUIVO_PUBLICAVEL
    gerado = datetime.now(tz=ZoneInfo("UTC")).isoformat(timespec="seconds")
    try:
        dados = extrair(buscador())
    except Exception as e:  # noqa: BLE001 — a leitura do Centro nunca segura a publicação do nível
        destino.unlink(missing_ok=True)
        print(f"aviso: leitura do Centro de Ituporanga indisponível ({e}); nada publicado", file=sys.stderr)
        return 1
    saida = resumo_publicavel(dados, agora, gerado)
    if raiz is None:
        grava_json(ARQUIVO_PUBLICAVEL, saida)
    else:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Ituporanga Centro: {saida['ultima_leitura']['nivel_m']} m às {dados['medido_em']} "
          f"({saida['situacao']}) -> data/{ARQUIVO_PUBLICAVEL}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Leitura do Centro de Ituporanga (Boletim Diário da Prefeitura).")
    p.add_argument("--arquivo", help="HTML já salvo da página, para conferir sem rede")
    p.add_argument("--publicar", action="store_true",
                   help=f"grava data/{ARQUIVO_PUBLICAVEL} para o site (uma consulta)")
    args = p.parse_args(argv)
    agora = datetime.now(tz=ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
    if args.publicar:
        return publicar(agora)
    pagina = Path(args.arquivo).read_text(encoding="utf-8", errors="replace") if args.arquivo else baixar_pagina()
    dados = extrair(pagina)
    print(json.dumps(resumo_publicavel(dados, agora, "(não publicado)"), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
