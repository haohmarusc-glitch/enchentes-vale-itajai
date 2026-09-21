#!/usr/bin/env python3
"""
Eventos de inundação, enxurrada e alagamento no Vale do Itajaí (1991–2025).

Fonte: Atlas Digital de Desastres no Brasil (Sedec/MIDR + Ceped/UFSC), base
consolidada do S2ID — https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml

O QUE ISTO É, E O QUE NÃO É
---------------------------
É um **roteiro de datas**: diz em que dias houve desastre reconhecido em cada
cidade da bacia, com os danos declarados. Serve para saber onde procurar nível
de rio, e para não deixar passar um evento que o projeto nunca registrou.

**Não é série de nível, e não vira registro de cheia.** Um decreto municipal não
mede régua. Nada daqui entra em `enchentes.json` — pico entra por decisão do
Jefferson, com fonte que traga estação, unidade e referência. Há teste travando
que este script não escreve nos três JSONs do projeto.

O QUE A PRÓPRIA FONTE LIMITA
-----------------------------
* **A tipologia não separa cheia de rio.** A enchente de nov/2008 em Itajaí está
  registrada como *Enxurrada* (12200), e a cheia de out/2023 (Blumenau, Taió,
  Lontras…) foi registrada quase toda como *Chuvas intensas* (13214). Por isso
  13214 entra POR PADRÃO e quem confirma se houve cheia é o nível do rio, não o
  código. `--sem-chuvas` exclui.
* **Cobertura antiga é subnotificada.** A adesão dos municípios ao S2ID foi de
  29% em 2013 e 88% em 2024. Ausência aqui não é ausência de desastre.
* **Começa em 1991.** 1983 e 1984, as duas maiores do vale, não aparecem — e
  esse é justamente o buraco que a série de Rio do Sul e a de Blumenau cobrem.
* Valores monetários já vêm corrigidos pelo IGP-DI para dez/2022.

O CSV vem em **latin-1**, separador `;`, decimal `.`, e os campos de descrição
têm **quebra de linha dentro de aspas** — por isso a leitura é pelo módulo `csv`,
que respeita aspas, e nunca linha a linha.

POR QUE SEM `pandas`
---------------------
O script chegou em 19/09/2026 escrito com `pandas`. Foi portado para a
biblioteca padrão, com o mesmo comportamento e a mesma linha de comando, por
dois motivos medidos: **nenhum outro script deste repositório importa `pandas`**
(o `importar_rede_cemaden.py`, que lê planilha, também é só stdlib), e a
conversão automática de números é uma armadilha conhecida AQUI — foi
`pandas.read_html` lendo `2,09` como `209` que custou a leitura do portal de
Brusque. `csv` + `float()` explícito falha alto em vez de converter errado.

Uso:
    python3 scripts/atlas_desastres.py                  # baixa (cache) e processa
    python3 scripts/atlas_desastres.py --force          # rebaixa
    python3 scripts/atlas_desastres.py --arquivo X.csv  # usa um CSV já baixado
    python3 scripts/atlas_desastres.py --sem-chuvas     # exclui COBRADE 13214

Saídas em `data/desastres/`:
    eventos.csv / eventos.json      um registro S2ID por linha
    episodios.csv / episodios.json  registros agrupados em episódios regionais
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

from comum import USER_AGENT, baixar as baixar_pagina, espera_turno

RAIZ = Path(__file__).resolve().parent.parent
DIR_BRUTOS = RAIZ / "data" / "brutos"
DIR_SAIDA = RAIZ / "data" / "desastres"

PAGINA_DOWNLOADS = "https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml"
#: Link vigente em set/2026. Muda a cada versão; o script tenta descobrir o novo
#: pela página de downloads e só cai neste se não achar.
URL_PADRAO = (
    "https://atlasdigital.mdr.gov.br/arquivos/2026/"
    "BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv"
)

COBRADE_HIDRO = {"12100": "Inundação", "12200": "Enxurrada", "12300": "Alagamento"}
COBRADE_CHUVA = {"13214": "Chuvas intensas"}

#: Código IBGE -> (nome, bacia). `acu` = bacia do Itajaí-Açu (inclui afluentes),
#: `mirim` = Itajaí-Mirim, `ambos` = Itajaí, que recebe os dois.
#:
#: CONFERIDOS em 19/09/2026 contra `data/cemaden-rede-observacional-sc.json`,
#: que não veio daqui: o código de estação do Cemaden começa pelos sete dígitos
#: do IBGE, então cada nome de município do cadastro carrega o código de novo.
#: Vinte de vinte batem. Isso prova o CÓDIGO, não a cobertura — ver o teste.
MUNICIPIOS: dict[str, tuple[str, str]] = {
    "4208203": ("Itajaí", "ambos"),
    # Itajaí-Mirim
    "4202909": ("Brusque", "mirim"),
    "4206306": ("Guabiruba", "mirim"),
    "4202701": ("Botuverá", "mirim"),
    "4219200": ("Vidal Ramos", "mirim"),
    # Itajaí-Açu — baixo e médio vale
    "4211306": ("Navegantes", "acu"),
    "4207106": ("Ilhota", "acu"),
    "4205902": ("Gaspar", "acu"),
    "4202404": ("Blumenau", "acu"),
    "4213203": ("Pomerode", "acu"),
    "4207502": ("Indaial", "acu"),
    "4218202": ("Timbó", "acu"),
    "4202206": ("Benedito Novo", "acu"),
    "4215109": ("Rodeio", "acu"),
    "4201703": ("Ascurra", "acu"),
    "4201257": ("Apiúna", "acu"),
    # Itajaí-Açu — alto vale
    "4209904": ("Lontras", "acu"),
    "4214805": ("Rio do Sul", "acu"),
    "4217808": ("Taió", "acu"),
    "4208500": ("Ituporanga", "acu"),
}

#: Cidades do cadastro do projeto que NÃO estão em MUNICIPIOS, com o motivo.
#: Sem esta lista a ausência delas na saída pareceria "não houve desastre", que
#: é a leitura errada — é recorte, não dado. Entram quando o código IBGE for
#: conferido do mesmo jeito que os vinte acima.
FORA_DO_RECORTE = {
    "Ibirama": "afluente lateral (Rio Hercílio); código IBGE ainda não conferido aqui",
    "Rio dos Cedros": "afluente lateral; código IBGE ainda não conferido aqui",
    "Trombudo Central": "entrou no cadastro sem posição na árvore; idem",
}

#: nome normalizado da coluna no CSV -> nome na saída
COLUNAS = {
    "protocolo_s2id": "protocolo",
    "data_evento": "data_evento",
    "data_registro": "data_registro",
    "cod_ibge_mun": "cod_ibge",
    "sigla_uf": "uf",
    "cod_cobrade": "cobrade",
    "status": "status",
    "dh_mortos": "mortos",
    "dh_feridos": "feridos",
    "dh_desabrigados": "desabrigados",
    "dh_desalojados": "desalojados",
    "dh_desaparecidos": "desaparecidos",
    "dh_total_danos_humanos_diretos": "danos_humanos_total",
    "dh_outros_afetados": "outros_afetados",
    "dm_uni_habita_danificadas": "casas_danificadas",
    "dm_uni_habita_destruidas": "casas_destruidas",
    "dm_total_danos_materiais": "danos_materiais_rs",
    "pe_plepr": "prejuizos_rs",
}
INTEIRAS = ["mortos", "feridos", "desabrigados", "desalojados", "desaparecidos",
            "danos_humanos_total", "outros_afetados", "casas_danificadas",
            "casas_destruidas"]
REAIS = ["danos_materiais_rs", "prejuizos_rs"]
NUMERICAS = INTEIRAS + REAIS

#: registros a menos de N dias do anterior (em qualquer cidade) caem no mesmo episódio
JANELA_EPISODIO_DIAS = 7


def normalizar(nome: str) -> str:
    s = unicodedata.normalize("NFD", nome)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def numero(bruto: str) -> float:
    """
    Converte o que o CSV traz, e devolve 0 só para vazio.

    Vazio é ausência declarada e vira 0, como a fonte trata. Texto que não é
    número NÃO vira 0 em silêncio: isso transformaria dano desconhecido em
    "nenhum dano", que é exatamente a mentira que este projeto não comete.
    """
    bruto = (bruto or "").strip()
    if not bruto:
        return 0.0
    return float(bruto.replace(",", "."))


def data_br(bruto: str) -> date | None:
    bruto = (bruto or "").strip()
    try:
        return datetime.strptime(bruto, "%d/%m/%Y").date()
    except ValueError:
        return None


def descobrir_url() -> str:
    """O nome do arquivo muda a cada versão do Atlas; tenta ler o atual."""
    try:
        html = baixar_pagina(PAGINA_DOWNLOADS)
    except Exception as exc:  # noqa: BLE001 — qualquer falha aqui cai no padrão
        print(f"[aviso] não consegui ler a página de downloads: {exc}", file=sys.stderr)
        return URL_PADRAO
    achados = re.findall(r'href="([^"]*Consolidado\.csv)"', html or "")
    if not achados:
        print("[aviso] a página de downloads não expôs nenhum *Consolidado.csv",
              file=sys.stderr)
        return URL_PADRAO
    from urllib.parse import urljoin
    return urljoin(PAGINA_DOWNLOADS, achados[0])


#: O que o firewall do Atlas devolve no lugar do CSV, com HTTP 200. Visto na
#: VPS em 21/09/2026: "The requested URL was rejected. Please consult with your
#: administrator." — 0 bytes de dado, e o script de então guardou ISSO como se
#: fosse a base e passaria a dizer "Usando cache" em cima de lixo.
MARCAS_DE_BLOQUEIO = ("<html", "<!doctype", "requested url was rejected", "support id")


def parece_a_base(caminho: Path) -> str | None:
    """Por que este arquivo NÃO é o CSV do Atlas — ou None quando é.

    Um download com HTTP 200 não prova nada: o firewall responde 200 com uma
    página de bloqueio. A prova é o CONTEÚDO: nada de HTML no começo e o
    cabeçalho com as colunas que o dicionário COLUNAS espera.
    """
    try:
        tamanho = caminho.stat().st_size
    except OSError as exc:
        return f"não deu para ler: {exc}"
    if tamanho == 0:
        return "arquivo vazio"
    with open(caminho, encoding="latin-1", newline="") as f:
        inicio = f.read(4096)
    baixo = inicio.lower()
    for marca in MARCAS_DE_BLOQUEIO:
        if marca in baixo:
            return f"é HTML, não CSV — contém {marca!r}; parece a página de bloqueio do firewall"
    cabecalho = [normalizar(c) for c in inicio.splitlines()[0].split(";")] if inicio else []
    faltando = [c for c in COLUNAS if c not in cabecalho]
    if faltando:
        return f"o cabeçalho não tem as colunas esperadas: {faltando[:4]}…"
    return None


COMO_BAIXAR_A_MAO = (
    "O Atlas recusou este cliente. Baixe o CSV no NAVEGADOR (a página de downloads é\n"
    f"  {PAGINA_DOWNLOADS}\n"
    "  e o arquivo é o *Consolidado.csv), copie-o para data/brutos/ e rode:\n"
    "  python3 scripts/atlas_desastres.py --arquivo data/brutos/<nome>.csv"
)


def _nome(caminho: Path) -> str:
    """Caminho relativo à raiz do projeto quando está dentro dela; absoluto se não."""
    try:
        return str(caminho.relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def baixar(force: bool) -> Path:
    import requests

    url = descobrir_url()
    destino = DIR_BRUTOS / Path(url).name
    if destino.exists() and not force:
        motivo = parece_a_base(destino)
        if motivo:
            # Cache envenenado: um bloqueio guardado como base. Recusar é o
            # mínimo; apagar sem avisar esconderia que aconteceu.
            sys.exit(f"{_nome(destino)} está em cache mas NÃO é a base do Atlas "
                     f"({motivo}). Apague o arquivo ou rode com --force.\n{COMO_BAIXAR_A_MAO}")
        print(f"Usando cache: {_nome(destino)}")
        return destino
    DIR_BRUTOS.mkdir(parents=True, exist_ok=True)
    print(f"Baixando {url}")
    espera_turno()
    parcial = destino.with_suffix(destino.suffix + ".part")
    with requests.get(url, stream=True, timeout=120,
                      headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        with open(parcial, "wb") as f:
            for bloco in r.iter_content(1 << 20):
                f.write(bloco)
    motivo = parece_a_base(parcial)
    if motivo:
        parcial.unlink(missing_ok=True)
        sys.exit(f"O download veio com HTTP {r.status_code}, mas o corpo não é a base do Atlas "
                 f"({motivo}). Nada foi guardado.\n{COMO_BAIXAR_A_MAO}")
    parcial.rename(destino)
    print(f"  {destino.stat().st_size / 1e6:.1f} MB")
    return destino


def carregar(caminho: Path) -> list[dict[str, str]]:
    """
    Lê o CSV inteiro pelo módulo `csv`, que respeita aspas.

    Ler linha a linha quebraria: os campos de descrição do S2ID têm quebra de
    linha DENTRO das aspas.
    """
    with open(caminho, encoding="latin-1", newline="") as f:
        leitor = csv.reader(f, delimiter=";", quotechar='"')
        try:
            cabecalho = [normalizar(c) for c in next(leitor)]
        except StopIteration:
            sys.exit(f"{caminho}: arquivo vazio")
        faltando = [c for c in COLUNAS if c not in cabecalho]
        if faltando:
            sys.exit(
                f"Colunas esperadas não encontradas: {faltando}\n"
                f"Colunas do arquivo: {cabecalho}\n"
                "O layout do Atlas mudou; ajuste o dicionário COLUNAS."
            )
        onde = {c: i for i, c in enumerate(cabecalho)}
        linhas = []
        for campos in leitor:
            if not campos:
                continue
            linhas.append({
                destino: (campos[onde[origem]].strip() if onde[origem] < len(campos) else "")
                for origem, destino in COLUNAS.items()
            })
    return linhas


def filtrar(linhas: list[dict[str, str]], incluir_chuvas: bool) -> list[dict]:
    codigos = dict(COBRADE_HIDRO)
    if incluir_chuvas:
        codigos.update(COBRADE_CHUVA)

    eventos: list[dict] = []
    vistos: set[str] = set()
    sem_data = 0
    for linha in linhas:
        cobrade = re.sub(r"\.0$", "", linha["cobrade"])
        if linha["uf"] != "SC" or linha["cod_ibge"] not in MUNICIPIOS:
            continue
        if cobrade not in codigos:
            continue
        quando = data_br(linha["data_evento"])
        if quando is None:
            sem_data += 1
            continue
        if linha["protocolo"] in vistos:
            continue
        vistos.add(linha["protocolo"])

        nome, bacia = MUNICIPIOS[linha["cod_ibge"]]
        registro = {
            "protocolo": linha["protocolo"],
            "data_evento": quando.isoformat(),
            "data_registro": (d.isoformat() if (d := data_br(linha["data_registro"])) else None),
            "ano": quando.year,
            "municipio": nome,
            "cod_ibge": linha["cod_ibge"],
            "bacia": bacia,
            "cobrade": cobrade,
            "tipo": codigos[cobrade],
            "status": linha["status"],
        }
        for col in INTEIRAS:
            registro[col] = round(numero(linha[col]))
        for col in REAIS:
            registro[col] = round(numero(linha[col]), 2)
        eventos.append(registro)

    if sem_data:
        print(f"[aviso] {sem_data} registro(s) sem data_evento válida foram descartados",
              file=sys.stderr)
    eventos.sort(key=lambda r: (r["data_evento"], r["municipio"]))
    return eventos


def agrupar_episodios(eventos: list[dict]) -> list[dict]:
    """
    Junta registros próximos no tempo, de qualquer cidade, num episódio.

    O corte é de mais de sete dias sem NENHUM registro na bacia. Não é uma
    afirmação de que os municípios de um episódio viveram a mesma cheia: é um
    agrupamento por proximidade, para orientar a busca de nível.
    """
    episodios: list[dict] = []
    grupo: list[dict] = []

    def fecha(g: list[dict]) -> dict:
        bacias = {r["bacia"] for r in g}
        return {
            "id": g[0]["data_evento"],
            "inicio": g[0]["data_evento"],
            "fim": max(r["data_evento"] for r in g),
            "n_cidades": len({r["cod_ibge"] for r in g}),
            "cidades": ", ".join(sorted({r["municipio"] for r in g})),
            "atinge_acu": bool(bacias & {"acu", "ambos"}),
            "atinge_mirim": bool(bacias & {"mirim", "ambos"}),
            "tipos": ", ".join(sorted({r["tipo"] for r in g})),
            "desabrigados": sum(r["desabrigados"] for r in g),
            "desalojados": sum(r["desalojados"] for r in g),
            "mortos": sum(r["mortos"] for r in g),
            "prejuizos_rs": round(sum(r["prejuizos_rs"] for r in g), 2),
            "protocolos": ", ".join(r["protocolo"] for r in g),
        }

    for r in sorted(eventos, key=lambda r: r["data_evento"]):
        atual = date.fromisoformat(r["data_evento"])
        if grupo and (atual - date.fromisoformat(grupo[-1]["data_evento"])).days > JANELA_EPISODIO_DIAS:
            episodios.append(fecha(grupo))
            grupo = []
        grupo.append(r)
    if grupo:
        episodios.append(fecha(grupo))
    return episodios


#: O nome do arquivo do Atlas carrega a versão: BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv
RE_NOME_ATLAS = re.compile(
    r"BD_Atlas_(?P<inicio>\d{4})_(?P<fim>\d{4})_v(?P<versao>[\d.]+?)_(?P<pub>\d{4}\.\d{2}\.\d{2})")


def ficha_da_fonte(caminho: Path) -> dict:
    """Versão, cobertura, publicação, nome original, sha256 e data da importação.

    Fica junto dos dados (`data/desastres/fonte.json`) porque o Atlas troca de
    versão e o arquivo muda de nome; sem isto ninguém sabe de qual base saiu
    o recorte. Decisão do Jefferson de 21/09/2026.
    """
    import hashlib
    m = RE_NOME_ATLAS.search(caminho.name)
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return {
        "fonte": "Atlas Digital de Desastres no Brasil (Sedec/MIDR + Ceped/UFSC), base consolidada do S2ID",
        "arquivo_original": caminho.name,
        "versao": m.group("versao") if m else None,
        "cobertura": f"{m.group('inicio')}–{m.group('fim')}" if m else None,
        "publicacao": m.group("pub").replace(".", "-") if m else None,
        "sha256": h.hexdigest(),
        "bytes": caminho.stat().st_size,
        "importado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cobrades": sorted({**COBRADE_HIDRO, **COBRADE_CHUVA}),
        "camada": "ocorrências oficiais — não é série de cotas e não altera enchentes.json",
    }


def salvar_fonte(caminho: Path) -> None:
    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    with open(DIR_SAIDA / "fonte.json", "w", encoding="utf-8") as f:
        json.dump(ficha_da_fonte(caminho), f, ensure_ascii=False, indent=1)
        f.write("\n")


def salvar(registros: list[dict], nome: str) -> None:
    if not registros:
        return
    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    campos = list(registros[0])
    with open(DIR_SAIDA / f"{nome}.csv", "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(registros)
    with open(DIR_SAIDA / f"{nome}.json", "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arquivo", type=Path, help="CSV do Atlas já baixado")
    ap.add_argument("--force", action="store_true", help="rebaixar mesmo com cache")
    ap.add_argument("--sem-chuvas", action="store_true",
                    help="excluir COBRADE 13214 (chuvas intensas)")
    args = ap.parse_args()

    caminho = args.arquivo or baixar(args.force)
    eventos = filtrar(carregar(caminho), not args.sem_chuvas)
    if not eventos:
        sys.exit("Nenhum evento encontrado — confira o arquivo e os filtros.")
    episodios = agrupar_episodios(eventos)

    salvar(eventos, "eventos")
    salvar(episodios, "episodios")
    salvar_fonte(caminho)

    cidades = {r["cod_ibge"] for r in eventos}
    anos = [r["ano"] for r in eventos]
    print(f"\n{len(eventos)} registros em {len(cidades)} cidades, "
          f"{min(anos)}–{max(anos)} -> {len(episodios)} episódios")
    por_tipo: dict[str, int] = {}
    for r in eventos:
        por_tipo[r["tipo"]] = por_tipo.get(r["tipo"], 0) + 1
    for tipo, n in sorted(por_tipo.items()):
        print(f"  {tipo:<16} {n}")
    print("\nMaiores episódios (desabrigados + desalojados):")
    for ep in sorted(episodios, key=lambda e: e["desabrigados"] + e["desalojados"],
                     reverse=True)[:10]:
        total = ep["desabrigados"] + ep["desalojados"]
        print(f"  {ep['id']}  {ep['n_cidades']:>2} cidades  {total:>8,} pessoas  "
              f"{ep['cidades'][:70]}")
    if FORA_DO_RECORTE:
        print("\nFora do recorte (não é ausência de desastre, é recorte): "
              + ", ".join(sorted(FORA_DO_RECORTE)))
    print(f"\nArquivos em {DIR_SAIDA.relative_to(RAIZ)}/")


if __name__ == "__main__":
    main()
