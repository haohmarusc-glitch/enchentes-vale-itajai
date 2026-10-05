#!/usr/bin/env python3
"""
Registro na mão das ruas alagadas durante a cheia (decisão do Jefferson, 05/10/2026).

Nenhuma fonte publica, com hora e de forma que um robô possa ler, quando cada rua alagou (docs/GUARDAR-CHEIAS.md,
item 2). Então quem acompanha a cheia anota numa planilha: rua, data e hora, o que se viu e de onde veio. Depois,
este script importa a planilha para `data/ruas-alagadas.json`, conferindo linha por linha, e a conta
"N horas antes" (`nivel_antes.py`) passa a usar essas horas.

AS REGRAS (o validador e a importação aplicam as mesmas, desta função `validar`):
  - Hora de Brasília, sem fuso, como o `medido_em` das réguas (CLAUDE.md, "Fuso").
  - `quando_e` diz de que é a hora: `hora_do_fato` (a água estava lá nessa hora: foto com hora, boletim que diz
    "às 14h") ou `hora_da_publicacao` (só se sabe quando foi publicado: a água chegou ANTES). Não confundir, porque
    na conta uma é o momento e a outra é um limite.
  - Toda linha tem fonte. A confiança segue a da série de picos, com teto pelo tipo de fonte: relato e foto/vídeo
    de morador nunca são `alta`; relato é sempre `baixa`.
  - Nada de dado pessoal: sem telefone nem e-mail na fonte ou na nota. Relato de morador entra como "relato de
    morador", sem nome.
  - A importação só ACRESCENTA. Linha repetida (mesma cidade, rua, ponto, hora e situação) é ignorada; nada é
    apagado nem reescrito. Corrigir um registro é editar o JSON no commit, à vista.
  - Não é alerta, não vai para a tela e não muda faixa nenhuma.

Uso:
    python3 scripts/ruas_alagadas.py --planilha cheia.csv --seco   # confere sem gravar
    python3 scripts/ruas_alagadas.py --planilha cheia.csv          # acrescenta as linhas boas
    python3 scripts/ruas_alagadas.py --cidade Itajaí --rua "R. José Domingos Machado" --data 05/10/2026 \\
        --hora 14:30 --situacao alagada --quando-e "hora do fato" --fonte-tipo "Defesa Civil" \\
        --fonte "Boletim 12 da Defesa Civil de Itajaí, 14h45"
Modelo da planilha: docs/modelos/ruas-alagadas.csv. Passo a passo: docs/REGISTRO-RUAS-ALAGADAS.md.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "data" / "ruas-alagadas.json"
MODELO = RAIZ / "docs" / "modelos" / "ruas-alagadas.csv"

COLUNAS = ["cidade", "rua", "ponto", "bairro", "data", "hora", "situacao", "quando_e", "precisao", "lamina",
           "fonte_tipo", "fonte", "confianca", "nota"]

SITUACOES = {
    "comecou_a_alagar": "começou a alagar",
    "alagada": "alagada",
    "interditada": "interditada",
    "liberada": "liberada",
}
QUANDO_E = {"hora_do_fato": "hora do fato", "hora_da_publicacao": "hora da publicação"}
PRECISOES = {"exata": "exata", "aproximada": "aproximada"}
FONTE_TIPOS = {
    "defesa_civil": "Defesa Civil",
    "prefeitura": "Prefeitura",
    "imprensa": "imprensa",
    "foto_video": "foto/vídeo",
    "relato": "relato",
}
# Confiança padrão e teto por tipo de fonte.
CONFIANCA_PADRAO = {"defesa_civil": "alta", "prefeitura": "alta", "imprensa": "media", "foto_video": "baixa", "relato": "baixa"}
CONFIANCA_TETO = {"defesa_civil": "alta", "prefeitura": "alta", "imprensa": "media", "foto_video": "media", "relato": "baixa"}
NIVEL_CONFIANCA = {"baixa": 0, "media": 1, "alta": 2}

# Com DDD (separadores opcionais) ou sem DDD (com separador entre as metades, para não pegar datas e códigos).
TELEFONE = re.compile(r"(?<![\w/.=-])(?:\(?\d{2}\)?[\s.-]?9?\d{4}[\s.-]?\d{4}|9?\d{4}[\s.-]\d{4})(?![\w/])")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower().strip()


def _chave_rotulo(valor: str, tabela: dict[str, str]) -> str | None:
    """Aceita a chave (`hora_do_fato`) ou o rótulo da planilha ("hora do fato"), com ou sem acento."""
    v = sem_acento(valor).replace("_", " ").replace("/", " ").replace("-", " ")
    v = " ".join(v.split())
    for chave, rotulo in tabela.items():
        if v in (chave.replace("_", " "), " ".join(sem_acento(rotulo).replace("/", " ").split())):
            return chave
    return None


def cidades() -> dict[str, str]:
    """nome ou id (sem acento) → id de data/estacoes.json."""
    e = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
    out = {}
    for r in e["rios"].values():
        for c in r["cidades"]:
            out[sem_acento(c["id"])] = c["id"]
            out[sem_acento(c["nome"])] = c["id"]
    return out


def ler_quando(data: str, hora: str) -> str | None:
    """'05/10/2026' ou '2026-10-05' + '14:30', '14h30' ou '14h' → '2026-10-05T14:30'."""
    data, hora = (data or "").strip(), sem_acento(hora or "").replace(" ", "")
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", data)
    try:
        d = date(int(m[3]), int(m[2]), int(m[1])) if m else date.fromisoformat(data)
    except (ValueError, TypeError):
        return None
    h = re.fullmatch(r"(\d{1,2})(?:[:h](\d{2})?)?", hora)
    if not h or int(h[1]) > 23 or int(h[2] or 0) > 59:
        return None
    return f"{d.isoformat()}T{int(h[1]):02d}:{int(h[2] or 0):02d}"


def chave(r: dict) -> tuple:
    return (r.get("cidade"), sem_acento(r.get("rua") or ""), sem_acento(r.get("ponto") or ""), r.get("quando"), r.get("situacao"))


def validar(registros: list[dict], conhecidas: set[str], hoje: date | None = None) -> list[str]:
    """Erros de `data/ruas-alagadas.json`. Lista vazia = válido."""
    hoje = hoje or date.today()
    erros: list[str] = []
    vistos: dict[tuple, int] = {}
    for i, r in enumerate(registros):
        onde = f"ruas-alagadas.json[{i}] ({r.get('cidade')}, {r.get('rua')}, {r.get('quando')})"
        for campo in ("cidade", "rua", "quando", "situacao", "quando_e", "precisao", "fonte_tipo", "fonte", "confianca", "registrado_em"):
            if r.get(campo) in (None, ""):
                erros.append(f"{onde}: falta '{campo}'")
        if r.get("cidade") and r["cidade"] not in conhecidas:
            erros.append(f"{onde}: cidade {r['cidade']!r} não está em estacoes.json")
        try:
            q = datetime.strptime(str(r.get("quando")), "%Y-%m-%dT%H:%M")
            if q.date() > hoje:
                erros.append(f"{onde}: 'quando' no futuro")
        except ValueError:
            erros.append(f"{onde}: 'quando' tem de ser AAAA-MM-DDTHH:MM, hora de Brasília sem fuso")
        try:
            if date.fromisoformat(str(r.get("registrado_em"))) > hoje:
                erros.append(f"{onde}: 'registrado_em' no futuro")
        except ValueError:
            erros.append(f"{onde}: 'registrado_em' tem de ser AAAA-MM-DD")
        for campo, tabela in (("situacao", SITUACOES), ("quando_e", QUANDO_E), ("precisao", PRECISOES), ("fonte_tipo", FONTE_TIPOS)):
            if r.get(campo) not in tabela:
                erros.append(f"{onde}: {campo} {r.get(campo)!r} fora de {sorted(tabela)}")
        conf, tipo = r.get("confianca"), r.get("fonte_tipo")
        if conf not in NIVEL_CONFIANCA:
            erros.append(f"{onde}: confianca {conf!r} fora de alta/media/baixa")
        elif tipo in CONFIANCA_TETO and NIVEL_CONFIANCA[conf] > NIVEL_CONFIANCA[CONFIANCA_TETO[tipo]]:
            erros.append(f"{onde}: fonte '{FONTE_TIPOS[tipo]}' não sustenta confiança '{conf}' (teto: {CONFIANCA_TETO[tipo]})")
        for campo in ("fonte", "nota", "rua", "ponto", "lamina"):
            texto = str(r.get(campo) or "")
            if TELEFONE.search(texto) or EMAIL.search(texto):
                erros.append(f"{onde}: '{campo}' parece ter telefone ou e-mail — dado pessoal não entra")
        k = chave(r)
        if k in vistos:
            erros.append(f"{onde}: repetido do registro [{vistos[k]}]")
        vistos.setdefault(k, i)
    return erros


def da_linha(linha: dict[str, str], mapa_cidades: dict[str, str], hoje: date) -> tuple[dict | None, list[str]]:
    """Uma linha da planilha → registro, ou os motivos da recusa."""
    problemas = []
    g = {k: (linha.get(k) or "").strip() for k in COLUNAS}
    cidade = mapa_cidades.get(sem_acento(g["cidade"]))
    if not cidade:
        problemas.append(f"cidade {g['cidade']!r} desconhecida")
    quando = ler_quando(g["data"], g["hora"])
    if not quando:
        problemas.append(f"data/hora {g['data']!r} {g['hora']!r} ilegível (use 05/10/2026 e 14:30)")
    campos = {}
    for nome, tabela, padrao in (("situacao", SITUACOES, None), ("quando_e", QUANDO_E, None),
                                 ("precisao", PRECISOES, "exata"), ("fonte_tipo", FONTE_TIPOS, None)):
        if not g[nome] and padrao:
            campos[nome] = padrao
            continue
        campos[nome] = _chave_rotulo(g[nome], tabela)
        if not campos[nome]:
            problemas.append(f"{nome} {g[nome]!r} não é um de: {', '.join(tabela.values())}")
    if not g["rua"]:
        problemas.append("falta a rua")
    if not g["fonte"]:
        problemas.append("falta a fonte")
    if problemas:
        return None, problemas
    conf = sem_acento(g["confianca"]) or CONFIANCA_PADRAO[campos["fonte_tipo"]]
    r = {"cidade": cidade, "rua": g["rua"]}
    for opcional in ("ponto", "bairro"):
        if g[opcional]:
            r[opcional] = g[opcional]
    r |= {"quando": quando, **campos}
    if g["lamina"]:
        r["lamina"] = g["lamina"]
    r |= {"fonte": g["fonte"], "confianca": conf, "registrado_em": hoje.isoformat()}
    if g["nota"]:
        r["nota"] = g["nota"]
    return r, []


def ler_planilha(texto: str) -> list[dict[str, str]]:
    """CSV com vírgula (Google Planilhas) ou ponto e vírgula (Excel em português); cabeçalho do modelo."""
    primeira = texto.splitlines()[0] if texto else ""
    sep = ";" if primeira.count(";") > primeira.count(",") else ","
    return [{(k or "").strip().lower(): (v or "") for k, v in linha.items()} for linha in csv.DictReader(io.StringIO(texto), delimiter=sep)]


def carregar() -> dict:
    if ARQUIVO.exists():
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    return {"_meta": META, "registros": []}


def gravar(conteudo: dict) -> None:
    conteudo["registros"].sort(key=lambda r: (r["quando"], r["cidade"], sem_acento(r["rua"])))
    tmp = ARQUIVO.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(ARQUIVO)


def importar(linhas: list[dict[str, str]], conteudo: dict, hoje: date) -> tuple[list[dict], list[str], int]:
    """(novos, recusas, repetidos). Não grava: quem chama decide."""
    mapa = cidades()
    conhecidas = set(mapa.values())
    existentes = {chave(r) for r in conteudo["registros"]}
    novos, recusas, repetidos = [], [], 0
    for n, linha in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        if not any((v or "").strip() for v in linha.values()):
            continue
        r, problemas = da_linha(linha, mapa, hoje)
        if r is not None:
            problemas = [e.split(": ", 1)[1] for e in validar([r], conhecidas, hoje)]
        if problemas:
            recusas.append(f"linha {n}: " + "; ".join(problemas))
            continue
        if chave(r) in existentes:
            repetidos += 1
            continue
        existentes.add(chave(r))
        novos.append(r)
    return novos, recusas, repetidos


META = {
    "descricao": "Ruas alagadas observadas durante as cheias, com a hora, registradas à mão por quem acompanha. "
                 "Serve para a conta 'como estavam as réguas N horas antes' (scripts/nivel_antes.py).",
    "como_registrar": "Planilha docs/modelos/ruas-alagadas.csv → python3 scripts/ruas_alagadas.py --planilha ARQUIVO. "
                      "Passo a passo em docs/REGISTRO-RUAS-ALAGADAS.md.",
    "fuso": "quando = hora de Brasília (America/Sao_Paulo), sem fuso, como o medido_em das réguas.",
    "campos": {
        "cidade": "id de data/estacoes.json",
        "rua": "nome como a fonte escreve",
        "ponto": "trecho, esquina ou número, quando a fonte diz",
        "bairro": "quando a fonte diz",
        "quando": "AAAA-MM-DDTHH:MM, hora de Brasília",
        "situacao": "comecou_a_alagar | alagada | interditada | liberada",
        "quando_e": "hora_do_fato (a água estava lá nessa hora) | hora_da_publicacao (só se sabe quando saiu: a água chegou antes)",
        "precisao": "exata | aproximada ('por volta de')",
        "lamina": "altura da água como a fonte descreve (texto), quando houver",
        "fonte_tipo": "defesa_civil | prefeitura | imprensa | foto_video | relato",
        "fonte": "boletim, link ou descrição de onde veio; nunca nome, telefone ou e-mail de morador",
        "confianca": "alta (Defesa Civil/Prefeitura) | media (imprensa; foto ou vídeo conferidos) | baixa (relato, foto sem conferência)",
        "registrado_em": "AAAA-MM-DD em que a linha entrou",
        "nota": "opcional",
    },
    "cuidados": [
        "Não é alerta e não vai para a tela; não muda faixa nem cota.",
        "Hora da publicação não é hora em que a água chegou: é o limite (a água chegou antes).",
        "A importação só acrescenta; corrigir é editar este arquivo no commit.",
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Importa ruas alagadas registradas à mão (planilha ou uma linha).")
    ap.add_argument("--planilha", type=Path, help="CSV no formato de docs/modelos/ruas-alagadas.csv")
    ap.add_argument("--seco", action="store_true", help="só confere; não grava")
    for c in COLUNAS:
        ap.add_argument(f"--{c.replace('_', '-')}", dest=c, default="")
    a = ap.parse_args()
    hoje = date.today()
    if a.planilha:
        linhas = ler_planilha(a.planilha.read_text(encoding="utf-8-sig"))
    elif a.rua:
        linhas = [{c: getattr(a, c) for c in COLUNAS}]
    else:
        ap.error("use --planilha ARQUIVO ou os campos de uma linha (--cidade, --rua, --data, --hora…)")
    conteudo = carregar()
    novos, recusas, repetidos = importar(linhas, conteudo, hoje)
    for r in recusas:
        print(f"RECUSADA {r}", file=sys.stderr)
    for r in novos:
        print(f"ok  {r['quando'].replace('T', ' ')}  {r['cidade']}  {r['rua']}  ({SITUACOES[r['situacao']]}, {QUANDO_E[r['quando_e']]})")
    print(f"{len(novos)} nova(s), {repetidos} repetida(s) ignorada(s), {len(recusas)} recusada(s).")
    if novos and not a.seco:
        conteudo["registros"].extend(novos)
        gravar(conteudo)
        print(f"gravado em {ARQUIVO.relative_to(RAIZ)}. Conferir o diff e commitar.")
    elif novos:
        print("(--seco: nada gravado)")
    return 1 if recusas else 0


if __name__ == "__main__":
    raise SystemExit(main())
