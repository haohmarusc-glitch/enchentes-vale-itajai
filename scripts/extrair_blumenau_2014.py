#!/usr/bin/env python3
"""
Tira do PDF de 2014 da Defesa Civil de Blumenau as 2.034 cotas por rua.

O documento é "Cotas das ruas de Blumenau", da Secretaria Municipal de Defesa
Civil, 111 páginas. Cada registro traz quatro coisas, e a quarta é a que a
nossa lista de 2022 não tem:

    R São Rafael ITOUPAVA NORTE                 <- rua e bairro
    E9 Igreja Evangélica Livre de Blumenau -    <- ABRIGO, com o código dele
    . 7,40Cota:Bairro:                          <- a cota
    Abrigo:
    Final da rua (pega só uma casa)Observação:  <- o ponto exato da rua

**O abrigo é informação nova e é a que muda o que a pessoa faz.** Saber que a
rua alaga a 7,40 m diz para sair; saber que o abrigo é a Igreja Evangélica
Livre diz para onde.

Este script só converte PDF em JSON. Quem compara com o que já temos é
`scripts/conferir_blumenau_2014.py`, e quem decide o que entra em
`cotas-ruas.json` é `scripts/importar_cotas_blumenau.py`.

Uso:
    python3 scripts/extrair_blumenau_2014.py            # grava o bruto
    python3 scripts/extrair_blumenau_2014.py --seco     # só mostra o resumo
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter

from comum import DADOS

PDF = "brutos/blumenau-cotas-2014.pdf"
SAIDA = "brutos/blumenau-cotas-2014.json"

#: A linha da cota, que é o âncora de cada registro: as outras quatro são
#: contadas a partir dela.
RE_COTA = re.compile(r"^\.\s*([\d.,]+)Cota:Bairro:\s*$")
RE_ABRIGO = re.compile(r"^(?:([A-Z]{1,2}\d{1,2})\s+)?(.*?)-\s*$")

#: Quantas vezes um sufixo em caixa alta precisa aparecer para ser aceito como
#: bairro. Sem esse piso, "R Do CVV VELHA" viraria bairro "CVV VELHA" — o nome
#: da rua acaba em caixa alta e a regra gulosa o engole junto.
MINIMO_PARA_SER_BAIRRO = 3


def sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()


def ler_pdf(caminho) -> str:
    """O texto de todas as páginas, em ordem."""
    _sem_cryptography_quebrada()
    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    return "\n".join((p.extract_text() or "") for p in leitor.pages)


def _sem_cryptography_quebrada() -> None:
    """
    Deixa o pypdf cair no caminho sem criptografia quando a `cryptography` do
    ambiente está quebrada.

    O pypdf já sabe funcionar sem ela — usa só para PDF CIFRADO, e este não é —,
    mas o `try/except ImportError` dele não segura uma instalação que estoura de
    outro jeito (aqui, um panic do binding em Rust). Um módulo vazio no lugar faz
    o import falhar como ImportError, que é o que o pypdf espera, e ele segue.

    Só age quando a `cryptography` realmente não importa: onde ela está sadia,
    esta função não faz nada.
    """
    import types

    if "cryptography" in sys.modules:
        return
    try:
        import cryptography.exceptions  # noqa: F401
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        # BaseException, e não Exception, de propósito: a instalação quebrada
        # aqui estoura com um PanicException do pyo3, que não herda de
        # Exception e passaria batido por um except comum.
        sys.modules["cryptography"] = types.ModuleType("cryptography")


def bairros_do_texto(linhas: list[str]) -> set[str]:
    """
    O vocabulário de bairros, descoberto do próprio documento.

    Um bairro de verdade aparece dezenas de vezes; um nome de rua terminado em
    caixa alta aparece uma. É o que separa os dois sem lista escrita à mão —
    lista à mão envelhece calada quando a fonte muda.
    """
    candidatos: Counter[str] = Counter()
    for i, linha in enumerate(linhas):
        if not RE_COTA.match(linha) or i < 2:
            continue
        caps = []
        for token in reversed(linhas[i - 2].split()):
            if token == token.upper() and re.search(r"[A-ZÀ-Ü]", token):
                caps.insert(0, token)
            else:
                break
        if caps:
            candidatos[sem_acento(" ".join(caps)).upper()] += 1
    return {b for b, n in candidatos.items() if n >= MINIMO_PARA_SER_BAIRRO}


def separar_rua_e_bairro(cabecalho: str, bairros: set[str]) -> tuple[str, str | None]:
    """
    Parte "R Almirante Tamandaré AGUA VERDE" em rua e bairro.

    Casa o MAIOR bairro conhecido que sirva de sufixo. O maior, e não o
    primeiro, porque "ITOUPAVA NORTE" e "ITOUPAVA CENTRAL" começam igual.
    """
    tokens = cabecalho.split()
    for corte in range(1, len(tokens)):
        candidato = sem_acento(" ".join(tokens[corte:])).upper()
        if candidato in bairros:
            return " ".join(tokens[:corte]).strip(), " ".join(tokens[corte:]).strip()
    return cabecalho.strip(), None


def analisar(texto: str) -> tuple[list[dict], list[str]]:
    """Os registros e as linhas que não deram para ler."""
    linhas = texto.splitlines()
    bairros = bairros_do_texto(linhas)
    registros: list[dict] = []
    recusas: list[str] = []

    for i, linha in enumerate(linhas):
        achou = RE_COTA.match(linha)
        if not achou or i < 2 or i + 2 >= len(linhas):
            continue
        rua, bairro = separar_rua_e_bairro(linhas[i - 2].strip(), bairros)
        if not rua:
            recusas.append(f"linha {i}: registro sem nome de rua")
            continue

        codigo = nome_abrigo = None
        casou = RE_ABRIGO.match(linhas[i - 1].strip())
        if casou:
            codigo, nome_abrigo = casou.group(1), (casou.group(2) or "").strip() or None

        observacao = linhas[i + 2].strip()
        observacao = observacao[: -len("Observação:")].strip() if observacao.endswith(
            "Observação:") else None

        registros.append({
            "rua": rua,
            "bairro": bairro,
            "cota_rotulo": achou.group(1),
            "abrigo_codigo": codigo,
            "abrigo": nome_abrigo,
            "observacao": observacao or None,
        })
    return registros, recusas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="mostra o resumo, sem gravar")
    args = ap.parse_args()

    caminho = DADOS / PDF
    if not caminho.exists():
        print(f"{caminho} não está aqui. O PDF fica em data/brutos/.", file=sys.stderr)
        return 1

    registros, recusas = analisar(ler_pdf(caminho))
    print(f"{len(registros)} registros lidos do PDF")
    for r in recusas[:5]:
        print(f"  recusado — {r}")
    com_abrigo = sum(1 for r in registros if r["abrigo"])
    sem_bairro = [r for r in registros if not r["bairro"]]
    print(f"{com_abrigo} com abrigo · {len(set(r['bairro'] for r in registros if r['bairro']))} bairros")
    if sem_bairro:
        print(f"{len(sem_bairro)} sem bairro: " + ", ".join(r["rua"] for r in sem_bairro[:5]))

    if args.seco:
        for r in registros[:5]:
            print(f"  {r['cota_rotulo']:>6} m  {r['rua'][:30]:32} {r['bairro'] or '':18} "
                  f"{(r['abrigo'] or '')[:34]}")
        return 0

    saida = {
        "_meta": {
            "descricao": "Cotas das ruas de Blumenau — PDF da Secretaria Municipal de "
                         "Defesa Civil, 111 páginas, 2.034 registros.",
            "origem": "https://farolblumenau.com/wp-content/uploads/2014/06/"
                      "Cotas-de-enchente-das-ruas-Blumenau.pdf — PDF em "
                      "data/brutos/blumenau-cotas-2014.pdf",
            "data_fonte": "2014-06",
            "total": len(registros),
            "o_que_tem_de_novo": "o ABRIGO de cada rua, com código, que a relação de "
                                 "2022 reproduzida pela imprensa não traz",
            "referencia": "Não declarada no documento. É a pergunta que "
                          "scripts/conferir_blumenau_2014.py responde, cruzando com a "
                          "relação de 2022 que já está em cotas-ruas.json.",
        },
        "registros": registros,
    }
    (DADOS / SAIDA).write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(f"\ngravado em {DADOS / SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
