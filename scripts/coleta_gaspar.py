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

O HOST NÃO RESPONDE DE FORA
---------------------------
Em 31/08 e 01/09/2026, de uma VPS na Finlândia, `defesacivil.gaspar.sc.gov.br`
resolve no DNS (186.250.184.3, só IPv4) e **dá timeout de conexão** em 15 s — na
raiz e no `robots.txt`. Três tentativas, duas datas. O pacote sai e não volta.

O navegador de quem mora na região alcança. Por isso existe o `--arquivo`: abrir
a página no navegador, salvar o HTML e passar o arquivo. Ler um arquivo que
alguém salvou não é rastejar site, então esse caminho não pede `robots.txt` —
e continua sem pedir nada ao servidor.

Uso:
    python3 scripts/coleta_gaspar.py                      # busca, mostra e grava
    python3 scripts/coleta_gaspar.py --seco               # busca e mostra, sem gravar
    python3 scripts/coleta_gaspar.py --cotas              # propõe as faixas, se houver
    python3 scripts/coleta_gaspar.py --arquivo pagina.html --cotas   # sem rede
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from comum import DADOS, USER_AGENT, baixar, espera_turno, nivel_plausivel
from importar_cotas_rio_do_sul import robots_permite

URL = "https://defesacivil.gaspar.sc.gov.br/monitoramento/tabela"
ROBOTS = "https://defesacivil.gaspar.sc.gov.br/robots.txt"
SAIDA = "tempo-real/ultimo_gaspar.json"

#: Um número solto, com ou sem "m" no fim: "3,85", "265,90", "6,00 m". A tabela
#: de Gaspar não põe unidade nenhuma, e outras põem — aceitar as duas formas é
#: seguro porque quem separa nível de chuva é a COLUNA, não o texto. O que
#: continua fora é "85,4 %", que não casa, e qualquer célula com palavra.
RE_NUMERO = re.compile(r"^-?\d{1,4}[,.]?\d{0,3}\s*m?\.?$", re.IGNORECASE)
#: A data como a página escreve: "31/08 22:59" — dia e mês, SEM ano.
RE_QUANDO = re.compile(r"(\d{2})/(\d{2})(?:/(\d{4}))?\D{1,6}(\d{2}):(\d{2})")

#: Os nomes de coluna que interessam, sem acento e em minúscula. O cabeçalho
#: desta tabela diz "Nível" no topo e "Cota" no rodapé, para a mesma coluna.
COLUNAS = {
    "estacao": "estacao", "fonte": "fonte", "coleta": "coleta",
    "nivel": "nivel", "cota": "nivel",
    "chuva atual": "chuva_atual", "ultima hora": "chuva_1h", "6 horas": "chuva_6h",
    "12 horas": "chuva_12h", "24 horas": "chuva_24h", "48 horas": "chuva_48h",
}

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
    """"3,85" vira 3.85. "-" e vazio viram None, que é o que a fonte quer dizer."""
    limpo = str(texto or "").strip()
    if not RE_NUMERO.match(limpo):
        return None
    try:
        return float(re.sub(r"\s*m\.?$", "", limpo, flags=re.IGNORECASE).replace(",", "."))
    except ValueError:
        return None


def indices_do_cabecalho(cels: list[str]) -> dict[str, int]:
    """
    Onde cada coluna está. É isto que substitui adivinhar pelo texto da célula.

    A primeira versão exigia a unidade "m" para um número virar nível, e a
    tabela real não põe unidade nenhuma: `<td>3,85</td>`. A regra que protegia
    de confundir nível com porcentagem passou a não ler nada. Pela coluna, os
    dois problemas somem juntos — chuva fica na coluna de chuva, nível na de
    nível, e nada é deduzido do formato do número.
    """
    achadas: dict[str, int] = {}
    for i, celula in enumerate(cels):
        nome = COLUNAS.get(sem_acento(celula).strip())
        if nome and nome not in achadas:
            achadas[nome] = i
    return achadas


def quando_de(texto: str, agora: datetime | None = None) -> tuple[str | None, str | None]:
    """
    A data da coleta: o texto como a fonte escreve, e o instante em ISO.

    A página omite o ano ("31/08 22:59"). Inventar um é o tipo de coisa que
    este projeto não faz calado, então: usa-se o ano corrente e, se isso jogar a
    leitura no futuro, o anterior — que é a única leitura possível para uma
    medição já feita. O texto original fica junto para conferência.
    """
    achado = RE_QUANDO.search(str(texto or ""))
    if not achado:
        return None, None
    dia, mes, ano, hora, minuto = achado.groups()
    agora = agora or datetime.now()
    for candidato in ([int(ano)] if ano else [agora.year, agora.year - 1]):
        try:
            quando = datetime(candidato, int(mes), int(dia), int(hora), int(minuto))
        except ValueError:
            continue
        if ano or quando <= agora:
            return achado.group(0), quando.isoformat()
    return achado.group(0), None


def celulas(linha_html) -> list[str]:
    return [c.get_text(" ", strip=True) for c in linha_html.find_all(["td", "th"])]


def ler_linha(cels: list[str], indices: dict[str, int],
              agora: datetime | None = None) -> dict | None:
    """Uma linha da tabela vira uma leitura, lida pelas colunas do cabeçalho."""
    def celula(nome: str) -> str:
        i = indices.get(nome)
        return cels[i].strip() if i is not None and i < len(cels) else ""

    rotulo = celula("estacao") or (cels[0].strip() if cels else "")
    if not rotulo or "nivel" not in indices:
        return None

    nivel = numero(celula("nivel"))
    texto_quando, iso = quando_de(celula("coleta"), agora)
    chuva = {nome: numero(celula(nome)) for nome in
             ("chuva_atual", "chuva_1h", "chuva_6h", "chuva_12h", "chuva_24h", "chuva_48h")
             if nome in indices}
    if nivel is None and not any(v is not None for v in chuva.values()):
        return None
    return {
        "rotulo": rotulo,
        "fonte_da_leitura": celula("fonte") or None,
        "nivel_m": nivel,
        # A régua de plausibilidade que a coleta inteira usa. As barragens desta
        # tabela leem 265 a 392 m — cota do reservatório acima do mar, não nível
        # de rio —, e é isto que impede o número de passar por nível.
        "nivel_plausivel": nivel is not None and nivel_plausivel(nivel),
        "medido_em": texto_quando,
        "medido_em_iso": iso,
        "chuva_mm": chuva or None,
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

    linhas = []
    for tabela in sopa.find_all("table"):
        todas = [celulas(tr) for tr in tabela.find_all("tr")]
        # O cabeçalho é a primeira linha que nomeia a coluna de nível. Sem ela
        # não se lê a tabela: melhor não ler do que ler pela posição chutada.
        indices: dict[str, int] = {}
        for cels in todas:
            candidatos = indices_do_cabecalho(cels)
            if "nivel" in candidatos:
                indices = candidatos
                break
        if not indices:
            continue
        for cels in todas:
            if indices_do_cabecalho(cels).get("nivel") is not None:
                continue  # é o próprio cabeçalho, ou o rodapé que o repete
            linhas.append(cels)
            item = ler_linha(cels, indices)
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
    ap.add_argument("--arquivo", metavar="HTML",
                    help="lê um HTML salvo do navegador, em vez de buscar na rede")
    ap.add_argument("--seco", action="store_true", help="mostra sem gravar")
    ap.add_argument("--cotas", action="store_true", help="propõe as faixas, se houver")
    args = ap.parse_args()

    if args.arquivo:
        # Arquivo salvo por uma pessoa no navegador dela. Não há requisição
        # nenhuma aqui, então não há robots.txt a consultar.
        try:
            leitura = analisar(Path(args.arquivo).read_text(encoding="utf-8", errors="replace"))
        except OSError as erro:
            print(f"não deu para ler {args.arquivo}: {erro}", file=sys.stderr)
            return 1
        leitura["fonte"] = f"{URL} (HTML salvo em {args.arquivo})"
    else:
        if not permitido():
            print("\nRECUSADO: o robots.txt de defesacivil.gaspar.sc.gov.br não libera "
                  "esta página, ou não deu para lê-lo.\n"
                  "Se for timeout de conexão, o host não responde de fora da região: "
                  "abra a página no navegador, salve o HTML e use --arquivo.",
                  file=sys.stderr)
            return 2

        espera_turno()
        try:
            leitura = analisar(baixar(URL))
        except Exception as erro:
            print(f"não deu para ler {URL}: {erro}", file=sys.stderr)
            return 1

    print(f"{len(leitura['estacoes'])} estações · {len(leitura['barragens'])} barragens "
          f"· faixas rotuladas: {sorted(leitura['faixas_propostas']) or 'nenhuma'}")
    for e in leitura["estacoes"] + leitura["barragens"]:
        if e["nivel_m"] is None:
            chuva = (e["chuva_mm"] or {}).get("chuva_24h")
            medida = f"{chuva:>6.1f} mm/24h" if chuva is not None else "        só chuva"
        else:
            medida = f"{e['nivel_m']:>6.2f} m     "
        marca = "" if e["nivel_plausivel"] or e["nivel_m"] is None else \
            "  <- fora da faixa de nível de rio"
        etiqueta = "[barragem] " if e_barragem(e["rotulo"]) else "           "
        print(f"  {etiqueta}{medida}  {e['medido_em'] or '-':<14} {e['rotulo'][:40]}{marca}")
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
