#!/usr/bin/env python3
"""
Testes do importador do Atlas Digital de Desastres.

O CSV de teste é SINTÉTICO e reproduz as armadilhas que a fonte real tem:
latin-1, separador `;`, quebra de linha dentro de aspas, COBRADE com `.0`
pendurado, município de fora do recorte, UF de fora, protocolo repetido e data
inválida. Se o parser passar por ele, passa pela fonte.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atlas_desastres as atlas  # noqa: E402

FONTE = (Path(__file__).resolve().parent / "atlas_desastres.py").read_text(encoding="utf-8")
RAIZ = Path(__file__).resolve().parent.parent

CABECALHO = [
    "Protocolo S2ID", "Data Evento", "Data Registro", "COD IBGE Mun", "Sigla UF",
    "COD COBRADE", "Status", "Descrição", "DH Mortos", "DH Feridos",
    "DH Desabrigados", "DH Desalojados", "DH Desaparecidos",
    "DH Total Danos Humanos Diretos", "DH Outros Afetados",
    "DM Uni Habita Danificadas", "DM Uni Habita Destruídas",
    "DM Total Danos Materiais", "PE PLEPR",
]


def linha(protocolo, data, ibge, uf, cobrade, *, desabrigados="0", desalojados="0",
          mortos="0", prejuizo="0", descricao="chuva forte", registro="02/01/2020"):
    return [protocolo, data, registro, ibge, uf, cobrade, "Reconhecido", descricao,
            mortos, "0", desabrigados, desalojados, "0", "0", "0", "0", "0", "0",
            prejuizo]


LINHAS = [
    # Blumenau, inundação, com dano — e DESCRIÇÃO COM QUEBRA DE LINHA nas aspas.
    linha("SC-2008-01", "23/11/2008", "4202404", "SC", "12100",
          desabrigados="100", desalojados="50", mortos="2", prejuizo="1000.50",
          descricao="enchente do vale\nsegunda linha do campo"),
    # Itajaí, mesma cheia, ENXURRADA — a tipologia não separa cheia de rio.
    linha("SC-2008-02", "24/11/2008", "4208203", "SC", "12200", desabrigados="10"),
    # Taió, out/2023, CHUVAS INTENSAS com `.0` pendurado no código.
    linha("SC-2023-01", "07/10/2023", "4217808", "SC", "13214.0", desalojados="7"),
    # Brusque, nov/2023: outro episódio (mais de 7 dias depois).
    linha("SC-2023-02", "17/11/2023", "4202909", "SC", "12100", desabrigados="3"),
    # Fora do recorte: município de SC que não é da bacia.
    linha("SC-2023-03", "17/11/2023", "4205407", "SC", "12100"),
    # Fora do recorte: outra UF com código da bacia (não deve acontecer, e é recusado).
    linha("RS-2023-01", "17/11/2023", "4202404", "RS", "12100"),
    # Tipo que não interessa: vendaval.
    linha("SC-2023-04", "18/11/2023", "4202404", "SC", "12300", desabrigados="1"),
    # Protocolo REPETIDO — a fonte tem duplicata.
    linha("SC-2008-01", "23/11/2008", "4202404", "SC", "12100", desabrigados="999"),
    # Data inválida — descartada com aviso, não convertida em nada.
    linha("SC-XXXX-01", "sem data", "4202404", "SC", "12100"),
]


def escreve_csv(destino: Path, linhas=LINHAS) -> Path:
    import csv
    with open(destino, "w", encoding="latin-1", newline="") as f:
        e = csv.writer(f, delimiter=";", quotechar='"')
        e.writerow(CABECALHO)
        e.writerows(linhas)
    return destino


class NaoEscreveNoProjeto(unittest.TestCase):
    """Decreto municipal não mede régua. Isto é roteiro de datas, não cheia."""

    def test_nao_toca_nos_jsons_do_projeto(self):
        for arquivo in ("estacoes.json", "enchentes.json", "transito.json"):
            self.assertNotIn(f'"{arquivo}"', FONTE,
                             f"o importador menciona {arquivo} em código")

    def test_so_escreve_em_desastres_e_brutos(self):
        for ln in FONTE.splitlines():
            despido = ln.strip()
            if despido.startswith("#") or "open(" not in ln or '"w"' not in ln:
                continue
            self.assertTrue("DIR_SAIDA" in ln, f"escrita fora de data/desastres: {despido}")


class LeituraDoCsv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv = escreve_csv(Path(self.tmp.name) / "atlas.csv")

    def tearDown(self):
        self.tmp.cleanup()

    def eventos(self, incluir_chuvas=True):
        return atlas.filtrar(atlas.carregar(self.csv), incluir_chuvas)

    def test_a_quebra_de_linha_dentro_das_aspas_nao_parte_o_registro(self):
        """Ler linha a linha partiria este CSV em duas — é a razão de usar `csv`."""
        linhas = atlas.carregar(self.csv)
        self.assertEqual(len(linhas), len(LINHAS))

    def test_pega_so_a_bacia_e_so_sc(self):
        ids = {e["protocolo"] for e in self.eventos()}
        self.assertEqual(ids, {"SC-2008-01", "SC-2008-02", "SC-2023-01",
                               "SC-2023-02", "SC-2023-04"})

    def test_o_cobrade_com_ponto_zero_e_aceito(self):
        taio = [e for e in self.eventos() if e["municipio"] == "Taió"]
        self.assertEqual(len(taio), 1)
        self.assertEqual(taio[0]["cobrade"], "13214")
        self.assertEqual(taio[0]["tipo"], "Chuvas intensas")

    def test_sem_chuvas_tira_out_2023_de_taio(self):
        """A cheia de out/2023 foi registrada como 'chuvas intensas'. Excluir
        13214 apaga o evento inteiro — por isso o padrão é INCLUIR."""
        ids = {e["protocolo"] for e in self.eventos(incluir_chuvas=False)}
        self.assertNotIn("SC-2023-01", ids)

    def test_protocolo_repetido_entra_uma_vez_so(self):
        blumenau = [e for e in self.eventos() if e["protocolo"] == "SC-2008-01"]
        self.assertEqual(len(blumenau), 1)
        # e é o PRIMEIRO, não o de 999 desabrigados
        self.assertEqual(blumenau[0]["desabrigados"], 100)

    def test_data_invalida_e_descartada_e_nao_vira_zero(self):
        ids = {e["protocolo"] for e in self.eventos()}
        self.assertNotIn("SC-XXXX-01", ids)

    def test_numeros_nao_sao_adivinhados(self):
        """Texto que não é número falha alto. Virar 0 transformaria dano
        desconhecido em 'nenhum dano' — a mentira que este projeto não comete."""
        self.assertEqual(atlas.numero(""), 0.0)
        self.assertEqual(atlas.numero("1000.50"), 1000.5)
        with self.assertRaises(ValueError):
            atlas.numero("não informado")

    def test_a_bacia_de_cada_cidade(self):
        por_cidade = {e["municipio"]: e["bacia"] for e in self.eventos()}
        self.assertEqual(por_cidade["Blumenau"], "acu")
        self.assertEqual(por_cidade["Brusque"], "mirim")
        self.assertEqual(por_cidade["Itajaí"], "ambos")

    def test_a_data_sai_em_iso(self):
        blumenau = [e for e in self.eventos() if e["protocolo"] == "SC-2008-01"][0]
        self.assertEqual(blumenau["data_evento"], "2008-11-23")
        self.assertEqual(blumenau["ano"], 2008)


class Episodios(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eventos = atlas.filtrar(
            atlas.carregar(escreve_csv(Path(self.tmp.name) / "atlas.csv")), True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_junta_o_que_esta_perto_e_separa_o_que_esta_longe(self):
        eps = atlas.agrupar_episodios(self.eventos)
        self.assertEqual([e["id"] for e in eps],
                         ["2008-11-23", "2023-10-07", "2023-11-17"])

    def test_nov_2008_junta_blumenau_e_itajai(self):
        ep = atlas.agrupar_episodios(self.eventos)[0]
        self.assertEqual(ep["cidades"], "Blumenau, Itajaí")
        self.assertEqual(ep["n_cidades"], 2)
        self.assertEqual(ep["desabrigados"], 110)
        self.assertTrue(ep["atinge_acu"])
        # Itajaí é "ambos": a foz recebe os dois rios.
        self.assertTrue(ep["atinge_mirim"])

    def test_um_episodio_nao_afirma_a_mesma_cheia(self):
        """Nov/2023 junta Brusque (Mirim) e Blumenau (Açu) por proximidade de
        data. Isso é roteiro de busca, não afirmação hidrológica — e o campo
        que diz a bacia é que sustenta a distinção."""
        ep = [e for e in atlas.agrupar_episodios(self.eventos) if e["id"] == "2023-11-17"][0]
        self.assertTrue(ep["atinge_acu"] and ep["atinge_mirim"])


class CodigosIbge(unittest.TestCase):
    """
    Os vinte códigos foram conferidos contra um cadastro que NÃO veio do Atlas.

    O código de estação do Cemaden começa pelos sete dígitos do IBGE, então
    `data/cemaden-rede-observacional-sc.json` carrega o código de cada município
    de novo, por outro caminho. Vínculo por NOME não prova identidade neste
    projeto — aqui o nome só serve para casar duas fontes que trazem o código.
    """

    @staticmethod
    def sem_acento(x: str) -> str:
        x = unicodedata.normalize("NFD", x)
        return "".join(c for c in x if unicodedata.category(c) != "Mn").lower().strip()

    def test_os_vinte_batem_com_o_cadastro_do_cemaden(self):
        cadastro = json.loads(
            (RAIZ / "data" / "cemaden-rede-observacional-sc.json").read_text(encoding="utf-8"))
        por_municipio: dict[str, set[str]] = {}
        for e in cadastro["estacoes"]:
            por_municipio.setdefault(self.sem_acento(e["municipio"]), set()).add(e["codigo"][:7])
        for codigo, (nome, _) in atlas.MUNICIPIOS.items():
            achados = por_municipio.get(self.sem_acento(nome))
            self.assertIsNotNone(achados, f"{nome} não está no cadastro do Cemaden")
            self.assertIn(codigo, achados, f"{nome}: {codigo} não bate com {sorted(achados)}")

    def test_as_cidades_de_fora_do_recorte_estao_escritas_com_motivo(self):
        """Ausência por recorte pareceria ausência de desastre. As três que o
        cadastro do projeto tem e este recorte não estão nomeadas no código."""
        cidades = set()
        estacoes = json.loads((RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8"))
        for rio in estacoes["rios"].values():
            cidades |= {c["nome"] for c in rio["cidades"]}
        no_script = {nome for nome, _ in atlas.MUNICIPIOS.values()}
        self.assertEqual(cidades - no_script, set(atlas.FORA_DO_RECORTE))
        for motivo in atlas.FORA_DO_RECORTE.values():
            self.assertTrue(motivo.strip())


class Saida(unittest.TestCase):
    def test_salvar_escreve_csv_e_json_iguais(self):
        tmp = tempfile.TemporaryDirectory()
        anterior = atlas.DIR_SAIDA
        try:
            atlas.DIR_SAIDA = Path(tmp.name)
            eventos = atlas.filtrar(
                atlas.carregar(escreve_csv(Path(tmp.name) / "atlas.csv")), True)
            atlas.salvar(eventos, "eventos")
            gravado = json.loads((Path(tmp.name) / "eventos.json").read_text(encoding="utf-8"))
            self.assertEqual(gravado, eventos)
            self.assertTrue((Path(tmp.name) / "eventos.csv").exists())
        finally:
            atlas.DIR_SAIDA = anterior
            tmp.cleanup()


class RespeitaAFonte(unittest.TestCase):
    def test_identifica_o_projeto_no_user_agent(self):
        """CLAUDE.md: todo script identifica o User-Agent com o nome do projeto."""
        self.assertIn("USER_AGENT", FONTE)
        self.assertIn("espera_turno", FONTE)

    def test_o_bruto_vai_para_data_brutos(self):
        self.assertIn('"brutos"', FONTE)
        self.assertNotIn('"raw"', FONTE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
