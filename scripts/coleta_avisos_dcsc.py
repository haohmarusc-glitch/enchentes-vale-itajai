#!/usr/bin/env python3
"""Avisos e alertas da Defesa Civil de SC, pelo WordPress do site dela (`wp-json`).

POR QUE EXISTE (varredura de 04/11/2026, `docs/VARREDURA-FONTES-2026-11-04-NAVEGADOR.md`). O site
`www.defesacivil.sc.gov.br` é um WordPress e expõe os posts em JSON: as categorias **7 Alerta** e **6 Aviso** são
os avisos meteorológicos oficiais do Estado ("ATENÇÃO – 04/11 09:34 – TEMPORAIS … nas próximas 4 horas"). É a
única fonte estadual de AVISO (não de nível) que o projeto alcança por máquina.

O QUE ELE DIZ E O QUE NÃO DIZ. O texto de cada aviso nomeia **regiões** em prosa ("Vale do Itajaí", "Foz do
Itajaí", "Litoral Norte", "todo o Estado"), nunca município nem polígono. Por isso a saída marca as regiões
citadas e se alguma delas cobre a bacia (`inclui_bacia`), e o site, se um dia mostrar isto, diz "aviso da Defesa
Civil de SC para a região" — **nunca** "para a sua cidade". Nada daqui pinta faixa, dispara aviso de cota ou
entra em `leituras`: é contexto oficial, com fonte, hora e link.

Fuso: o WordPress publica `date` no fuso do site (sem offset) e `date_gmt` em UTC. Para não depender da
configuração do site, `publicado_em` vem do `date_gmt` convertido para Brasília, sem fuso — o contrato do projeto
(`CLAUDE.md`); `publicado_em_utc` guarda o original.

Uso:
    python3 scripts/coleta_avisos_dcsc.py             # imprime os avisos recentes
    python3 scripts/coleta_avisos_dcsc.py --publicar  # grava data/tempo-real/ultimo_avisos_dcsc.json
    python3 scripts/coleta_avisos_dcsc.py --arquivo resposta.json   # lê um JSON já baixado, sem rede
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum import DADOS, baixar, grava_json  # noqa: E402

#: As categorias do WordPress da DCSC (ids lidos no navegador em 04/11/2026). Só estas duas são avisos.
CATEGORIAS = {7: "Alerta", 6: "Aviso"}
QUANTOS = 20
URL = ("https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts"
       f"?categories={','.join(str(c) for c in CATEGORIAS)}&per_page={QUANTOS}"
       "&_fields=id,date,date_gmt,link,title,content,categories")
ARQUIVO_PUBLICAVEL = "tempo-real/ultimo_avisos_dcsc.json"
FUSO_BRASILIA = timezone(timedelta(hours=-3))
TRECHO_MAX = 400

#: Como a DCSC nomeia as regiões nos avisos (chave sem acento e em minúsculas) → nome na tela. A lista é a das
#: regiões que apareceram nos textos lidos em 04/11/2026; nome fora dela só entra em `regioes` se for acrescentado
#: aqui, nunca por adivinhação.
REGIOES = {
    "vale do itajai": "Vale do Itajaí",
    "alto vale": "Alto Vale",
    "medio vale": "Médio Vale",
    "foz do itajai": "Foz do Itajaí",
    "foz do rio itajai": "Foz do Itajaí",
    "litoral norte": "Litoral Norte",
    "grande florianopolis": "Grande Florianópolis",
    "planalto norte": "Planalto Norte",
    "planalto sul": "Planalto Sul",
    "serra": "Serra",
    "litoral sul": "Litoral Sul",
    "extremo oeste": "Extremo Oeste",
    "meio-oeste": "Meio-Oeste",
    "meio oeste": "Meio-Oeste",
    "grande oeste": "Grande Oeste",
    "oeste": "Oeste",
    "norte": "Norte",
    "sul": "Sul",
}
#: Regiões que cobrem alguma cidade do projeto (Alto Vale → Taió, Rio do Sul…; Médio Vale → Blumenau…;
#: Foz / Litoral Norte → Itajaí, Navegantes). "Litoral Norte" entra porque a DCSC às vezes põe a foz nele.
REGIOES_DA_BACIA = {"Vale do Itajaí", "Alto Vale", "Médio Vale", "Foz do Itajaí", "Litoral Norte"}
#: Frases que querem dizer "o Estado inteiro".
ESTADO_INTEIRO = ("todo o estado", "todas as regioes", "em todo sc", "todo sc", "para sc", "em santa catarina",
                  "todas as regioes do estado")


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()


def texto_de(html_bruto: str) -> str:
    """HTML do WordPress → texto corrido (sem tags, entidades resolvidas, espaços normalizados)."""
    sem_tags = re.sub(r"<[^>]+>", " ", html_bruto or "")
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def regioes_citadas(texto: str) -> tuple[list[str], bool]:
    """(regiões nomeadas no texto, o aviso é para o Estado inteiro?). Ordem: a da primeira menção."""
    plano = _sem_acento(texto)
    estado = any(frase in plano for frase in ESTADO_INTEIRO)
    achadas: dict[str, int] = {}
    for chave, nome in REGIOES.items():
        # "oeste" não pode casar dentro de "extremo oeste"/"meio-oeste"; "norte" não casa em "litoral norte".
        for m in re.finditer(r"(?<![a-z-])" + re.escape(chave) + r"(?![a-z])", plano):
            if chave in ("oeste", "norte", "sul"):
                antes = plano[max(0, m.start() - 12):m.start()]
                if any(antes.endswith(p) for p in ("extremo ", "meio-", "meio ", "grande ", "litoral ", "planalto ")):
                    continue
            achadas.setdefault(nome, m.start())
            break
    return [nome for nome, _ in sorted(achadas.items(), key=lambda kv: kv[1])], estado


def _brasilia(date_gmt: str | None) -> str | None:
    if not date_gmt:
        return None
    try:
        t = datetime.fromisoformat(date_gmt.replace("Z", ""))
    except ValueError:
        return None
    return t.replace(tzinfo=timezone.utc).astimezone(FUSO_BRASILIA).replace(tzinfo=None).isoformat(timespec="seconds")


def converter(posts: list[dict]) -> list[dict]:
    """Posts crus do WordPress → avisos do projeto, só os das categorias de aviso, do mais novo ao mais antigo."""
    avisos = []
    for p in posts:
        if not isinstance(p, dict):
            continue
        cats = [c for c in (p.get("categories") or []) if c in CATEGORIAS]
        if not cats:
            continue
        titulo = texto_de((p.get("title") or {}).get("rendered", "") if isinstance(p.get("title"), dict) else str(p.get("title") or ""))
        corpo = texto_de((p.get("content") or {}).get("rendered", "") if isinstance(p.get("content"), dict) else "")
        regioes, estado = regioes_citadas(titulo + " " + corpo)
        avisos.append({
            "id": p.get("id"),
            "categoria": CATEGORIAS[cats[0]],
            "titulo": titulo,
            "publicado_em": _brasilia(p.get("date_gmt")),
            "publicado_em_utc": p.get("date_gmt"),
            "link": p.get("link"),
            "regioes": regioes,
            "estado_inteiro": estado,
            "inclui_bacia": estado or any(r in REGIOES_DA_BACIA for r in regioes),
            "trecho": corpo[:TRECHO_MAX] + ("…" if len(corpo) > TRECHO_MAX else ""),
        })
    avisos.sort(key=lambda a: a.get("publicado_em_utc") or "", reverse=True)
    return avisos


#: UMA tentativa de até 50 s. A publicação corta este coletor em 60 s (`timeout 60` em publicar_tempo_real.sh);
#: com o padrão de três tentativas de 30 s mais as pausas (~96 s), uma resposta lenta nunca chegava à
#: segunda tentativa: o coletor era morto calado e o arquivo não subia (07/11/2026, na VPS, durante a cheia).
TENTATIVAS = 1
TIMEOUT_S = 50


def buscar() -> list[dict]:
    dados = json.loads(baixar(URL, tentativas=TENTATIVAS, timeout=TIMEOUT_S))
    if not isinstance(dados, list):
        raise ValueError(f"resposta não é lista de posts: {str(dados)[:120]}")
    return dados


def montar(avisos: list[dict], gerado_em: str) -> dict:
    return {
        "versao": 1,
        "fonte": "Defesa Civil de Santa Catarina — www.defesacivil.sc.gov.br (categorias Alerta e Aviso)",
        "fonte_url": URL,
        "gerado_em": gerado_em,
        "aviso": ("Avisos meteorológicos oficiais do Estado, por REGIÃO em texto livre: não nomeiam município nem "
                  "polígono, não são faixa de rio e não disparam aviso de cota. `inclui_bacia` só diz que alguma "
                  "região citada cobre cidades do projeto."),
        "regioes_da_bacia": sorted(REGIOES_DA_BACIA),
        "avisos": avisos,
    }


def publicar(buscador=buscar) -> int:
    """`--publicar`: uma consulta, um arquivo pequeno. Falha APAGA o anterior (um de outra coleta não passa por atual)."""
    destino = DADOS / ARQUIVO_PUBLICAVEL
    gerado = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    try:
        avisos = converter(buscador())
    except Exception as e:  # noqa: BLE001 — avisos nunca seguram a publicação do nível
        destino.unlink(missing_ok=True)
        print(f"aviso: avisos da Defesa Civil de SC indisponíveis ({e}); nada publicado", file=sys.stderr)
        return 1
    grava_json(ARQUIVO_PUBLICAVEL, montar(avisos, gerado))
    bacia = sum(1 for a in avisos if a["inclui_bacia"])
    print(f"{len(avisos)} aviso(s) da DCSC, {bacia} citando a bacia -> data/{ARQUIVO_PUBLICAVEL}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--arquivo", type=Path, help="JSON da API já baixado, para rodar sem rede")
    ap.add_argument("--publicar", action="store_true", help="grava data/tempo-real/ultimo_avisos_dcsc.json")
    a = ap.parse_args(argv)
    if a.publicar:
        return publicar()
    posts = json.loads(a.arquivo.read_text(encoding="utf-8")) if a.arquivo else buscar()
    for av in converter(posts):
        marca = "BACIA" if av["inclui_bacia"] else "     "
        print(f"{av['publicado_em']}  {av['categoria']:6s} {marca}  {av['titulo'][:90]}  [{', '.join(av['regioes']) or 'sem região'}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
