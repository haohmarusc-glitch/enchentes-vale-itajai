#!/usr/bin/env python3
"""
Toda cidade que o MAPA pode pintar é vigiada pelo ALARME? Sai 0 se sim, 1 se não.

POR QUE EXISTE (04/09/2026)
O mapa e o alarme são caminhos SEPARADOS: a cor sai do `faixaDaCidade` no
navegador, o Telegram sai do `alerta_cotas.py` na VPS. Um pode estar certo com o
outro mudo — e foi o que aconteceu com BLUMENAU, a cidade com 97 registros
históricos desde 1852:

    o mapa pintava a cor certa    (a tela usa o seu próprio caminho)
    o Telegram não disparava NADA (o alarme recusava a cidade inteira)

A causa foi a fonte de resgate: com o AlertaBlu, Blumenau passou a aparecer duas
vezes no `ultimo.json`, o alarme contou LINHAS em vez de RÉGUAS, concluiu "a
cidade tem mais de uma régua" e recusou as duas. Ninguém percebeu porque **cor
na tela parece aviso funcionando**.

Nenhum teste unitário pegaria: cada lado, sozinho, estava coerente. O que pega é
comparar os dois contra o dado PUBLICADO — que é o que este script faz.

A REGRA QUE ELE COBRA
Cidade com cota de acionamento no cadastro E leitura fresca que pode virar faixa
tem de ser VIGIADA pelo alarme. Se for recusada, a recusa precisa estar na lista
fechada de motivos aceitos — e "a cidade tem mais de uma régua" só é aceito
quando as réguas são MESMO distintas, não quando são a mesma vista duas vezes.

Uso:
    python3 scripts/conferir_mapa_e_alarme.py
    python3 scripts/conferir_mapa_e_alarme.py --arquivo /tmp/ultimo.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from comum import DADOS, regua_de  # noqa: E402
import alerta_cotas as ac  # noqa: E402

ULTIMO = DADOS / "tempo-real" / "ultimo.json"
ESTACOES = DADOS / "estacoes.json"

#: As chaves de cota que fazem o mapa pintar cor de faixa. Mesma lista fechada
#: do `web/src/logica/tempoReal.ts` — se as duas divergirem, este script deixa
#: de cobrir o que promete, então a lista está escrita nos dois lugares de
#: propósito, com teste comparando.
CHAVES_QUE_PINTAM = {"monitoramento", "atencao", "alerta", "inundacao", "emergencia"}

#: Motivos de recusa que são DECISÃO, não buraco.
#:
#: Fechada de propósito: motivo novo aparece como falha até alguém decidir que é
#: aceitável e escrevê-lo aqui. É o oposto de uma lista de exceções que cresce
#: sozinha e para de proteger.
RECUSAS_ACEITAS = (
    "não disparar aviso automático",   # réguas de maré, com motivo no cadastro
    "estuário",
    "sem cota de referência",
    "não trouxe número de nível",
    "não é nível de rio desta bacia",
)


def cidades_que_pintam(estacoes: dict) -> dict[tuple[str, str], dict]:
    """(rio, cidade) -> cotas que pintam, para quem tem alguma."""
    saida = {}
    for rio, r in (estacoes.get("rios") or {}).items():
        for c in r.get("cidades") or []:
            cotas = {k: v for k, v in (c.get("cotas_m") or {}).items()
                     if k in CHAVES_QUE_PINTAM and isinstance(v, (int, float))}
            if cotas:
                saida[(rio, c["id"])] = cotas
    return saida


def avaliar(dados: dict, estacoes: dict) -> list[dict]:
    """Uma linha por cidade que PODE pintar e tem leitura — vigiada ou não."""
    pintam = cidades_que_pintam(estacoes)
    vigiadas, recusas = ac.resolver(dados)

    vigiadas_por_cidade = set()
    for v in vigiadas:
        l = v["leitura"]
        vigiadas_por_cidade.add((l.get("rio"), l.get("cidade")))

    # Recusas vêm por TÍTULO; liga cada uma à cidade da leitura correspondente.
    por_titulo = {}
    for l in dados.get("leituras") or []:
        por_titulo[l.get("estacao") or ""] = l
    recusa_da_cidade: dict[tuple, list[str]] = {}
    for r in recusas:
        titulo = r.split(":", 1)[0]
        l = por_titulo.get(titulo)
        if not l:
            continue
        recusa_da_cidade.setdefault((l.get("rio"), l.get("cidade")), []).append(r)

    saida = []
    for chave, cotas in sorted(pintam.items()):
        rio, cidade = chave
        leituras = [l for l in (dados.get("leituras") or [])
                    if (l.get("rio"), l.get("cidade")) == chave
                    and l.get("usar_para_cota") is not False]
        if not leituras:
            continue  # sem leitura que possa virar faixa: o mapa também não pinta
        motivos = recusa_da_cidade.get(chave, [])
        vigiada = chave in vigiadas_por_cidade
        aceita = any(a in m for m in motivos for a in RECUSAS_ACEITAS)
        saida.append({
            "rio": rio,
            "cidade": cidade,
            "reguas": len({regua_de(l) for l in leituras}),
            "leituras": len(leituras),
            "vigiada": vigiada,
            "motivos": motivos,
            "buraco": not vigiada and not aceita,
            "cotas": cotas,
        })
    return saida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", help="outro ultimo.json (padrão: o de data/)")
    args = ap.parse_args()

    caminho = Path(args.arquivo) if args.arquivo else ULTIMO
    if not caminho.exists():
        print(f"ERRO: {caminho} não existe — rode a coleta ou passe --arquivo",
              file=sys.stderr)
        return 1
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    estacoes = json.loads(ESTACOES.read_text(encoding="utf-8"))
    linhas = avaliar(dados, estacoes)

    for r in linhas:
        marca = "  <<< COR SEM ALARME" if r["buraco"] else ""
        estado = "vigiada" if r["vigiada"] else "recusada"
        print(f"{r['cidade']:14} {r['reguas']} régua(s) / {r['leituras']} leitura(s)"
              f"  {estado}{marca}")
        for m in r["motivos"]:
            print(f"                 {m[:96]}")

    buracos = [r for r in linhas if r["buraco"]]
    print()
    if not buracos:
        print(f"as {len(linhas)} cidades que podem pintar estão vigiadas (ou recusadas "
              "por motivo aceito).")
        return 0
    print(f"{len(buracos)} cidade(s) que o MAPA PINTA e o ALARME NÃO VIGIA:")
    for r in buracos:
        print(f"  {r['cidade']} — cotas {r['cotas']}")
        for m in r["motivos"] or ["(nem sequer apareceu nas recusas)"]:
            print(f"      {m[:96]}")
    print("\nCor na tela parece aviso funcionando. Não é.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
