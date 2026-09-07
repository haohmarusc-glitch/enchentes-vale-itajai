#!/usr/bin/env python3
"""Importa o histórico de enchentes que a Defesa Civil de Gaspar publica.

POR QUE EXISTE (07/09/2026)
Gaspar tem **zero picos** em `enchentes.json` e 1.619 cotas de rua: sabe-se em
que nível cada rua alaga e não se sabe em que nível o rio esteve. A página
`/enchentes` do município traz **71 registros de 1852 a 2023**, cada um com
data de início, data de término e metragem máxima. Seria a maior entrada única
já feita na base — razão de sobra para a importação ser conferida, e não
automática.

TRÊS ARMADILHAS, e o script existe por causa delas:

1. **A data publicada é do INÍCIO do evento, não do pico.** Vai para `data`
   assim mesmo, mas marcada: `data_e_do_inicio_do_evento: true`, com `data_fim`
   ao lado. Isso NÃO atrapalha o pareamento da previsão, que tolera sete dias
   (`web/src/logica/datas.ts`) — atrapalharia qualquer cálculo de HORÁRIO, e
   por isso o registro diz o que é em vez de deixar adivinharem.

2. **A fonte tem data impossível.** O registro de 20/11/1855 traz término
   `24/11/9855`. O importador **preserva o original** e marca `data_anomala`;
   virar 9855 em 1855 em silêncio apagaria a prova de que a fonte errou, que é
   exatamente a classe de erro que este projeto persegue.

3. **Data que não pareia com evento nenhum é suspeita, não é fato.** Dos oito
   valores de controle conferidos em 07/09/2026, **seis batem com um evento já
   cadastrado a zero ou um dia** — e dois não: `09/11/2011` (o mais perto é
   Blumenau 09/09/2011, dois meses antes) e `09/06/1983` (Blumenau tem
   09/07/1983). Nos dois o DIA bate com um pico conhecido de Blumenau e o MÊS
   não. Pode ser erro da fonte, pode ser evento local de verdade. **Não se
   conserta nem se descarta**: entra com `pareamento: "sem par"` e a nota
   dizendo qual era o candidato.

O script NÃO grava sem `--gravar`, e nunca sobrescreve registro existente.

⚠️ **DE ONDE ELE NÃO RODA.** Este ambiente tem `defesacivil.gaspar.sc.gov.br`
bloqueado na saída (403 no CONNECT, medido em 07/09/2026). Rode da VPS, ou
salve a página e passe `--arquivo`.

⚠️ **A ESTRUTURA DA TABELA NÃO FOI CONFERIDA** contra a página real, pelo mesmo
motivo. O parser acha a tabela pelos CABEÇALHOS, aceita várias grafias e,
quando não encontra, **imprime os cabeçalhos que a página trouxe** — para o
conserto ser de uma linha. Mesma disciplina de `ana_inventario.py`.

Uso:
    python3 scripts/importar_gaspar_enchentes.py --arquivo pagina.html
    python3 scripts/importar_gaspar_enchentes.py --gravar
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from comum import DADOS, baixar, espera_turno, le_json

URL = "https://defesacivil.gaspar.sc.gov.br/enchentes"

#: POR QUE ESTES REGISTROS ENTRAM COMO `referencia: "régua"` (07/09/2026).
#:
#: A página `/enchentes` **não declara referência vertical nenhuma** — a leitura
#: direta da fonte confirmou isso, e a objeção é justa: cadastrar "régua" sem a
#: fonte dizer seria supor. O que sustenta a decisão é uma MEDIÇÃO, não a
#: suposição:
#:
#:     menor cota de rua de Gaspar  : 6,20 m   (1.619 pontos)
#:     menor pico da lista histórica: 6,19 m   (70 registros)
#:     diferença                    : 1 cm
#:
#: As cotas de rua vêm do estudo CEOPS/FURB (coord. Ademar Cordeiro), que
#: DECLARA a referência: "régua da ANA na empresa Círculo". A lista histórica
#: começa exatamente onde a primeira rua alaga, a um centímetro. Dois conjuntos
#: publicados por caminhos diferentes não concordam no piso por acaso: é a mesma
#: escala, e a lista é de cheias QUE ALAGARAM.
#:
#: É EVIDÊNCIA FORTE, NÃO PROVA. A fonte continua sem declarar, e se a
#: Superintendência disser que são pontos diferentes, isto aqui é o que muda.
#: `teste_importar_gaspar_enchentes.py` trava o 1 cm: se os dois pisos se
#: afastarem, a decisão precisa ser revista.
REFERENCIA = "régua"

#: Tolerância de pareamento do site, em dias (`web/src/logica/datas.ts`).
#: Repetida aqui porque as duas implementações divergirem em silêncio já custou
#: caro neste projeto — se mudar lá, muda aqui, e o teste cobra lendo o arquivo
#: do site. O mesmo cuidado que `comum.NIVEL_MAXIMO_M` tem com a faixa de nível.
TOLERANCIA_DIAS = 7

#: O arquivo do site de onde a tolerância vem — lido pelo teste, não pelo script.
RAIZ_WEB = DADOS.parent / "web" / "src" / "logica" / "datas.ts"

#: Faixa em que um ano pode ser um evento desta bacia. O 9855 do término de
#: 20/11/1855 é o caso real que esta faixa existe para pegar.
ANO_MINIMO, ANO_MAXIMO = 1800, date.today().year

#: Cabeçalhos que valem para cada coluna, sem acento e em minúscula.
COLUNAS = {
    "inicio": ("inicio", "datainicio", "datadeinicio", "iniciodaenchente", "data"),
    "fim": ("termino", "fim", "datatermino", "datadetermino", "fimdaenchente"),
    "pico": ("metragem", "metragemmaxima", "cota", "cotamaxima", "nivel",
             "nivelmaximo", "maxima", "altura"),
}


def chave(texto: str) -> str:
    sem = unicodedata.normalize("NFKD", texto or "")
    sem = "".join(c for c in sem if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", sem.lower())


def numero(texto: str) -> float | None:
    """'9,80 m' -> 9.8. Vírgula é decimal em português; ponto também aparece."""
    if not texto:
        return None
    m = re.search(r"(\d+)[.,](\d+)", texto)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m = re.search(r"\b(\d{1,2})\b", texto)
    return float(m.group(1)) if m else None


def data_iso(texto: str) -> tuple[str | None, bool]:
    """
    `dd/mm/aaaa` -> `aaaa-mm-dd`, e um sinal de que o valor é impossível.

    Devolve `(None, True)` para o que não é data nenhuma e
    `(texto_original, True)` para data cujo ano sai da faixa da bacia — o caso
    real é o término `24/11/9855`. **Nunca conserta**: quem lê o JSON precisa
    ver que a fonte publicou aquilo.
    """
    if not texto:
        return None, False
    m = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,5})", texto.strip())
    if not m:
        return None, True
    d, mes, a = (int(x) for x in m.groups())
    if not (ANO_MINIMO <= a <= ANO_MAXIMO) or not (1 <= mes <= 12) or not (1 <= d <= 31):
        return texto.strip(), True
    try:
        return date(a, mes, d).isoformat(), False
    except ValueError:
        return texto.strip(), True


def intervalo(s: str) -> tuple[date, date]:
    """Mesma granularidade de `web/src/logica/datas.ts`: ano, mês ou dia."""
    p = s.split("-")
    if len(p) == 3:
        d = date(int(p[0]), int(p[1]), int(p[2]))
        return d, d
    if len(p) == 2:
        ano, mes = int(p[0]), int(p[1])
        inicio = date(ano, mes, 1)
        fim = date(ano + (mes == 12), mes % 12 + 1, 1) - timedelta(days=1)
        return inicio, fim
    return date(int(p[0]), 1, 1), date(int(p[0]), 12, 31)


def vao_em_dias(a: str, b: str) -> int:
    ia, fa = intervalo(a)
    ib, fb = intervalo(b)
    return max(0, (max(ia, ib) - min(fa, fb)).days)


def par_mais_proximo(data: str, eventos: list[dict]) -> tuple[int, dict] | None:
    """O evento já cadastrado mais próximo desta data, em qualquer cidade."""
    candidatos = []
    for e in eventos:
        try:
            candidatos.append((vao_em_dias(data, e["data"]), e))
        except ValueError:
            continue
    return min(candidatos, key=lambda x: x[0]) if candidatos else None


def linhas_da_tabela(html: str) -> tuple[list[dict], list[str]]:
    """Devolve (registros crus, cabeçalhos vistos) — o segundo para diagnóstico."""
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(html, "html.parser")
    vistos: list[str] = []
    for tabela in sopa.find_all("table"):
        linhas = tabela.find_all("tr")
        if not linhas:
            continue
        cabecalhos = [c.get_text(" ", strip=True) for c in linhas[0].find_all(["th", "td"])]
        vistos.extend(cabecalhos)
        posicao = {}
        for i, cab in enumerate(cabecalhos):
            k = chave(cab)
            for campo, aceitos in COLUNAS.items():
                if campo not in posicao and any(k.startswith(a) for a in aceitos):
                    posicao[campo] = i
        if "inicio" not in posicao or "pico" not in posicao:
            continue
        saida = []
        for linha in linhas[1:]:
            celulas = [c.get_text(" ", strip=True) for c in linha.find_all(["td", "th"])]
            if len(celulas) <= max(posicao.values()):
                continue
            saida.append({campo: celulas[i] for campo, i in posicao.items()})
        if saida:
            return saida, cabecalhos
    return [], vistos


#: Uma data `dd/mm/aaaa` — o ano vai até cinco dígitos de propósito, para o
#: `9855` da fonte ser CAPTURADO e marcado, em vez de ignorado pelo regex.
RE_DATA = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,5})\b")

#: Um número com decimal: `7,45 metros`, `11.40`.
RE_METROS = re.compile(r"\b\d+[.,]\d+\b")


def linhas_do_texto(texto: str) -> tuple[list[dict], list[str]]:
    """
    Lê a tabela COLADA, não o HTML.

    POR QUE EXISTE (07/09/2026). A página é inalcançável deste ambiente (403 do
    proxy) e da VPS (timeout — provável bloqueio de IP estrangeiro pelo site
    municipal). Quem alcança é o navegador do Jefferson, no celular, e o que um
    celular produz com facilidade é **texto colado**, não arquivo salvo.

    Por isso o parser não depende de coluna nem de separador: em cada linha
    pega as DATAS na ordem em que aparecem (a primeira é início, a segunda é
    término) e o primeiro número com decimal. Sobrevive a tabulação virando
    espaço, que é o que acontece ao colar.

    A coluna "Nome" (todas as linhas dizem "Enchente") e o `-` de término
    ausente caem fora sozinhos, sem precisar de regra para eles.
    """
    saida = []
    for linha in texto.splitlines():
        datas = RE_DATA.findall(linha)
        metros = RE_METROS.search(linha)
        if not datas or not metros:
            continue
        reg = {"inicio": datas[0], "pico": metros.group(0)}
        if len(datas) > 1:
            reg["fim"] = datas[1]
        saida.append(reg)
    return saida, []


def ano_da_linha_de_cima(datas: list[str], i: int) -> str | None:
    """A data da linha `i` com o ANO da linha de cima (a mais nova da lista)."""
    if i == 0:
        return None
    try:
        return date(int(datas[i - 1][:4]), int(datas[i][5:7]), int(datas[i][8:10])).isoformat()
    except (ValueError, IndexError):
        return None


def marca_ano_deslocado(regs: list[dict], eventos: list[dict]) -> None:
    """
    Acha as linhas em que o ANO parece ser o da linha de cima.

    O QUE ISTO DESCOBRIU (07/09/2026), e por que virou código. Dos 70 registros
    publicados, 21 não pareavam com evento nenhum já cadastrado. Testei duas
    hipóteses e as duas foram REFUTADAS no conjunto: "o mês está um a menos"
    conserta 6 e quebra 38; "o ano está deslocado uma linha" conserta 12 e
    quebra 29. Nenhuma vale para a tabela inteira.

    Mas os acertos da segunda não são acaso: **onze deles casam com DIA E MÊS
    IDÊNTICOS** a um evento já cadastrado em outro ano — coincidência de ~1/365
    por caso —, e ficam em DOIS TRECHOS CONTÍGUOS da tabela (as linhas de 1950
    a 1932 e de 1927 a 1911). É a assinatura de uma coluna que escorregou uma
    linha num pedaço da tabela, não de datas imprecisas de registro antigo:
    imprecisão não produz onze igualdades exatas de dia e mês.

    A CONSEQUÊNCIA É GRAVE, e é por isso que estes registros NÃO entram. Se o
    ano está errado, o pico de 8,43 m publicado em 1939 é na verdade o de 1943 —
    e uma correlação montante->jusante que pareie o Gaspar de 1939 com o
    Blumenau de 1939 estaria cruzando águas de cheias diferentes. Pior: não dá
    para saber daqui se escorregou só o ANO ou a data inteira; no segundo caso,
    nem o valor pertence àquela linha.

    NÃO SE CONSERTA. O que este código faz é ANOTAR a evidência em cada
    registro, para o ofício à Defesa Civil de Gaspar poder citar linha por
    linha.
    """
    datas = [r["data"] for r in regs]
    for i, r in enumerate(regs):
        if r.get("pareamento") != "sem par":
            continue
        alternativa = ano_da_linha_de_cima(datas, i)
        if not alternativa:
            continue
        par = par_mais_proximo(alternativa, eventos)
        if not par or par[0] > TOLERANCIA_DIAS:
            continue
        dias, e = par
        r["ano_suspeito_de_deslocamento"] = True
        r["nota"] += (
            f" ⚠️⚠️ SUSPEITA DE ANO DESLOCADO: com o ano da linha de CIMA da tabela "
            f"({alternativa}) este registro pareia com {e['cidade']} {e['data']} "
            f"({e['pico_m']} m), a {dias} dia(s)"
            + (" — DIA E MÊS IDÊNTICOS" if dias == 0 else "") + ". "
            "Onze registros desta tabela têm essa mesma assinatura, em dois trechos "
            "contíguos, o que é sinal de coluna desalinhada e não de data imprecisa. "
            "Não foi corrigido, e não entra na base: se o ano está errado, parear "
            "este pico com o de outra cidade no ano publicado cruzaria cheias "
            "diferentes.")


def monta(crus: list[dict], eventos: list[dict]) -> list[dict]:
    fonte = ("Histórico de enchentes publicado pela Defesa Civil de Gaspar "
             f"({URL}), lido em {date.today().isoformat()} por "
             "scripts/importar_gaspar_enchentes.py. Dados atribuídos ao CEOPS.")
    saida = []
    for cru in crus:
        inicio, inicio_anomala = data_iso(cru.get("inicio", ""))
        fim, fim_anomala = data_iso(cru.get("fim", ""))
        pico = numero(cru.get("pico", ""))
        if inicio is None or pico is None:
            continue

        reg = {
            "rio": "itajai-acu",
            "cidade": "gaspar",
            "data": inicio,
            "pico_m": pico,
            "confianca": "alta",
            "referencia": REFERENCIA,
            "fonte": fonte,
            "data_e_do_inicio_do_evento": True,
        }
        if fim:
            reg["data_fim"] = fim

        notas = ["A data é a de INÍCIO do evento publicada pela fonte, não a do pico. "
                 "Serve para parear eventos (a tolerância do site é de sete dias); "
                 "NÃO serve para calibrar tempo de trânsito."]
        if inicio_anomala or fim_anomala:
            reg["data_anomala"] = True
            qual = "início" if inicio_anomala else "término"
            notas.append(f"⚠️ A fonte publica uma data de {qual} IMPOSSÍVEL, e ela está "
                         "preservada como veio. Não foi consertada de propósito: virar o "
                         "valor em silêncio apagaria a prova de que a fonte errou.")

        if not (inicio_anomala or fim_anomala):
            par = par_mais_proximo(inicio, eventos)
            if par and par[0] <= TOLERANCIA_DIAS:
                reg["pareamento"] = "confere"
            elif par:
                dias, e = par
                reg["pareamento"] = "sem par"
                notas.append(
                    f"⚠️ Não pareia com evento nenhum já cadastrado: o mais perto é "
                    f"{e['cidade']} {e['data']} ({e['pico_m']} m), a {dias} dias — acima da "
                    f"tolerância de {TOLERANCIA_DIAS}. Pode ser erro de data na fonte ou "
                    "evento local de verdade. Conferir antes de usar na previsão.")
        reg["nota"] = " ".join(notas)
        saida.append(reg)
    return saida


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arquivo", type=Path, help="HTML salvo, em vez de baixar")
    p.add_argument("--texto", type=Path,
                   help="tabela COLADA em texto (o que o celular consegue produzir)")
    p.add_argument("--gravar", action="store_true", help="escreve em enchentes.json")
    p.add_argument("--incluir-sem-par", action="store_true",
                   help="importa também os que não pareiam com evento nenhum (NÃO recomendado: "
                        "11 deles têm assinatura de ano deslocado)")
    args = p.parse_args(argv)

    if args.texto:
        crus, cabecalhos = linhas_do_texto(
            args.texto.read_text(encoding="utf-8", errors="replace"))
        html = None
    elif args.arquivo:
        html = args.arquivo.read_text(encoding="utf-8", errors="replace")
    else:
        try:
            espera_turno()
            html = baixar(URL)
        except Exception as erro:
            print(f"⚠️ {type(erro).__name__}: {erro}\nEste ambiente bloqueia "
                  "defesacivil.gaspar.sc.gov.br — rode da VPS ou use --arquivo. "
                  "Nada foi gravado.", file=sys.stderr)
            return 1

    if html is not None:
        crus, cabecalhos = linhas_da_tabela(html)
    if not crus:
        print("Nenhuma linha reconhecida. Cabeçalhos que a página trouxe:\n  "
              + ("\n  ".join(cabecalhos) if cabecalhos else "(nenhuma tabela)"),
              file=sys.stderr)
        return 1

    base = le_json("enchentes.json")
    existentes = {(e["cidade"], e["data"]) for e in base["eventos"]}
    todos = [r for r in monta(crus, base["eventos"])
             if (r["cidade"], r["data"]) not in existentes]
    marca_ano_deslocado(todos, base["eventos"])

    anomalas = [r for r in todos if r.get("data_anomala")]
    sem_par = [r for r in todos if r.get("pareamento") == "sem par"]
    deslocados = [r for r in todos if r.get("ano_suspeito_de_deslocamento")]
    # Registro sem par NÃO entra por padrão. Não é conservadorismo genérico: 11
    # dos 21 têm assinatura de ano deslocado, e um ano errado num pico faz a
    # correlação cruzar cheias diferentes.
    novos = todos if args.incluir_sem_par else [r for r in todos if r not in sem_par]

    print(f"{len(crus)} linhas lidas · {len(todos)} novas · {len(anomalas)} com data "
          f"impossível · {len(sem_par)} sem par ({len(deslocados)} com suspeita de ano "
          f"deslocado) · {len(novos)} a importar")
    for r in anomalas + sem_par:
        print(f"\n  {r['data']} → {r.get('data_fim', '?')}   {r['pico_m']} m")
        print(f"    {r['nota']}")

    if not args.gravar:
        print("\n(nada gravado — use --gravar)")
        return 0

    base["eventos"].extend(novos)
    caminho = DADOS / "enchentes.json"
    caminho.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(novos)} registros acrescentados em {caminho} (ordem preservada)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
