"""Os dois formatos de KML do My Maps, e a falha silenciosa que este parser recusa.

Brusque vem com <ExtendedData> e ponto decimal; Gaspar vem com os campos
soltos no <description>, vírgula decimal e o campo `longitu` truncado. Um
parser que conhece só um dos dois devolve o outro com tudo vazio — 1.615
pontos, contagem certa, conteúdo nenhum.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from kml_para_json import campos_da_descricao, main, montar, numero, pontos_do_kml, resumo

KML_GASPAR = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Cotas de enchente</name>
<Folder><name>cotas_enchente_gaspar_01042020</name>
<Placemark><name>8,246</name>
<description><![CDATA[FID: 0<br>sequencia: 1<br>cota: 8,25<br>refer_1: Rua Adriano Kormann<br>refer_2: Rua Nilton Cardoso<br>bairro: Bela Vista<br>coord_x: 698098,862749<br>coord_y: 7023033,51756<br>latitude: -26,90042<br>longitu: -49,005335]]></description>
<Point><coordinates>-49.005335,-26.90042,0</coordinates></Point></Placemark>
<Placemark><name>7,9</name>
<description><![CDATA[FID: 1<br>sequencia: 2<br>cota: 7,90<br>refer_1: Rua B<br>refer_2: <br>bairro: Centro]]></description>
<Point><coordinates>-49.0,-26.9,0</coordinates></Point></Placemark>
</Folder></Document></kml>"""

# O export REAL de Gaspar, verbatim de um Placemark lido na VPS em 10/09/2026:
# sem dois-pontos, nome e valor separados por corrida de espaços, rua no topo.
KML_GASPAR_REAL = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Folder><name>cotas_enchente_gaspar_01042020</name>
<Placemark>
        <name>8,246</name>
        <description><![CDATA[Rua Adriano Kormann    <br>
   <br>   FID   0    <br>   sequencia   1    <br>   cota   8,25    <br>   refer_1   Rua Adriano Kormann    <br>   refer_2
  Rua Nilton Cardoso    <br>   bairro   Bela Vista    <br>
coord_x   698098,862749    <br>   coord_y   7023033,51756
<br>   latitude   -26,90042    <br>   longitu   -49,005335]]></description>
        <styleUrl>#icon-1899-DB4436</styleUrl>
        <Point>
          <coordinates>
            -49.005335,-26.90042,0
          </coordinates>
        </Point>
      </Placemark>
</Folder></Document></kml>"""

KML_BRUSQUE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Folder><name>Cotas de Cheia 2011</name>
<Placemark><name>Luiz Moreli</name>
<ExtendedData><Data name="descrição"><value>ponto 12</value></Data><Data name="cota"><value>15.55</value></Data>
<Data name="obs"><value>esquina com a Rua X</value></Data><Data name="bairro"><value>Dom Joaquim</value></Data>
<Data name="coord_x"><value>703000.5</value></Data><Data name="coord_y"><value>6995000.1</value></Data>
<Data name="ruas"><value>Luiz Moreli</value></Data><Data name="esquina"><value>Rua X</value></Data><Data name="esquina_co"><value>12</value></Data></ExtendedData>
<Point><coordinates>-48.959923,-27.15305,0</coordinates></Point></Placemark>
</Folder></Document></kml>"""

#: Camada "Cotas de cheia 2023" de Brusque — o primeiro Placemark do KML
#: original, VERBATIM (VPS, 10/09/2026), sem a foto (gx_media_links encurtado).
#: O <name> (7,65) é a cota da rua; "Nível registrado no local" (1,31) é a
#: lâmina medida no ponto: 7,65 + 1,31 = 8,96, o pico de 17/11/2023.
KML_BRUSQUE_2023 = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Folder><name>Cotas de cheia 2023</name>
<Placemark>
        <name>7,65</name>
        <description><![CDATA[<img src="https://lh3.googleusercontent.com/umsh/AN6v0v7z" height="200" width="auto" /><br><br>descrição: <br><br>Bairro: Jardim Maluche<br>Rua: Bartolomeu Pruner<br>Esquina: <br>Nível registrado no local: 1,31<br>Conferência: Correta<br>Bairro: Jardim Maluche<br>Rua: Bartolomeu Pruner<br>Esquina: <br>Nível registrado no local: 1,31<br>Conferência: Correta]]></description>
        <styleUrl>#icon-1697-0288D1-labelson</styleUrl>
        <ExtendedData>
          <Data name="descrição">
            <value>
Bairro: Jardim Maluche
Rua: Bartolomeu Pruner
Esquina:
Nível registrado no local: 1,31
Conferência: Correta</value>
          </Data>
          <Data name="Bairro">
            <value>Jardim Maluche</value>
          </Data>
          <Data name="Rua">
            <value>Bartolomeu Pruner</value>
          </Data>
          <Data name="Esquina">
            <value/>
          </Data>
          <Data name="Nível registrado no local">
            <value>1,31</value>
          </Data>
          <Data name="Conferência">
            <value>Correta</value>
          </Data>
          <Data name="gx_media_links">
            <value>https://lh3.googleusercontent.com/umsh/AN6v0v7z</value>
          </Data>
        </ExtendedData>
        <Point>
          <coordinates>
            -48.93,-27.11,0
          </coordinates>
        </Point>
      </Placemark>
</Folder></Document></kml>"""

#: Ruas de Ituporanga — o primeiro Placemark do KML, VERBATIM (VPS, 10/09/2026):
#: o <name> É a cota ("3,38 metros") e o <description> é só a rua.
KML_ITUPORANGA_RUAS = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Folder><name>Cotas de Cheias Ituporanga</name>
<Placemark>
        <name>3,38 metros</name>
        <description>Rua João Back / Galpão Recuperauto</description>
        <styleUrl>#icon-1899-DB4436</styleUrl>
        <Point>
          <coordinates>
            -49.596143,-27.431991,0
          </coordinates>
        </Point>
      </Placemark>
</Folder></Document></kml>"""

KML_SEM_COTA = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Folder><name>x</name>
<Placemark><name>ponto</name><description>só texto, sem campo</description>
<Point><coordinates>-49,-27,0</coordinates></Point></Placemark></Folder></Document></kml>"""


class Numero(unittest.TestCase):
    def test_virgula_e_ponto(self):
        self.assertEqual(numero("8,25"), 8.25)
        self.assertEqual(numero("15.55"), 15.55)
        self.assertEqual(numero("698098,862749"), 698098.862749)

    def test_lixo_vira_none(self):
        self.assertIsNone(numero(""))
        self.assertIsNone(numero("n/d"))
        self.assertIsNone(numero(None))


class Gaspar(unittest.TestCase):
    def setUp(self):
        self.pontos = pontos_do_kml(KML_GASPAR)

    def test_le_os_campos_soltos_do_description(self):
        p = self.pontos[0]
        self.assertEqual(p["formato"], "description")
        self.assertEqual(p["cota_rotulo"], "8,25")
        self.assertEqual(p["cota"], 8.25)
        self.assertEqual(p["rua"], "Rua Adriano Kormann")
        self.assertEqual(p["esquina"], "Rua Nilton Cardoso")
        self.assertEqual(p["bairro"], "Bela Vista")
        self.assertEqual(p["sequencia"], "1")
        self.assertEqual(p["coord_x"], "698098,862749")
        self.assertEqual((p["lon"], p["lat"]), (-49.005335, -26.90042))
        self.assertEqual(p["pasta"], "cotas_enchente_gaspar_01042020")

    def test_o_nome_do_marcador_nao_e_a_cota_rotulo(self):
        """<name> tem três casas (8,246); o campo cota tem duas (8,25)."""
        p = self.pontos[0]
        self.assertEqual(p["nome_marcador"], "8,246")
        self.assertNotEqual(p["nome_marcador"], p["cota_rotulo"])

    def test_longitu_truncado_vira_longitude(self):
        self.assertEqual(self.pontos[0]["longitude"], "-49,005335")

    def test_campo_vazio_vira_none_nao_string_vazia(self):
        self.assertIsNone(self.pontos[1]["esquina"])

    def test_description_com_html_escapado(self):
        campos = campos_da_descricao("cota: 8,25&lt;br&gt;refer_1: Rua A")
        self.assertEqual(campos, {"cota": "8,25", "refer_1": "Rua A"})


class GasparReal(unittest.TestCase):
    """
    A primeira rodada na VPS deu 1.615 pontos com `campos=[]`: o formato dos
    documentos de sessão (campo: valor) não era o do arquivo. O guarda recusou
    gravar — este é o formato de verdade, e o parser tem de lê-lo inteiro.
    """

    def setUp(self):
        self.p = pontos_do_kml(KML_GASPAR_REAL)[0]

    def test_le_todos_os_campos_sem_dois_pontos(self):
        c = self.p["campos"]
        self.assertEqual(c["FID"], "0")
        self.assertEqual(c["sequencia"], "1")
        self.assertEqual(c["cota"], "8,25")
        self.assertEqual(c["refer_1"], "Rua Adriano Kormann")
        self.assertEqual(c["refer_2"], "Rua Nilton Cardoso")   # quebra de linha depois da chave
        self.assertEqual(c["bairro"], "Bela Vista")
        self.assertEqual(c["coord_x"], "698098,862749")
        self.assertEqual(c["coord_y"], "7023033,51756")
        self.assertEqual(c["latitude"], "-26,90042")
        self.assertEqual(c["longitu"], "-49,005335")

    def test_a_rua_do_topo_nao_vira_chave_falsa(self):
        self.assertEqual(self.p["campos"]["_titulo"], "Rua Adriano Kormann")
        self.assertNotIn("Rua", self.p["campos"])

    def test_chaves_normalizadas_como_o_importador_le(self):
        self.assertEqual(self.p["cota"], 8.25)
        self.assertEqual(self.p["cota_rotulo"], "8,25")
        self.assertEqual(self.p["rua"], "Rua Adriano Kormann")
        self.assertEqual(self.p["esquina"], "Rua Nilton Cardoso")
        self.assertEqual(self.p["longitude"], "-49,005335")
        self.assertEqual((self.p["lon"], self.p["lat"]), (-49.005335, -26.90042))

    def test_o_kml_real_grava(self):
        self.assertEqual(resumo(pontos_do_kml(KML_GASPAR_REAL))["com_cota"], 1)


class Brusque(unittest.TestCase):
    def test_le_o_extended_data_com_ponto_decimal(self):
        p = pontos_do_kml(KML_BRUSQUE)[0]
        self.assertEqual(p["formato"], "extended_data")
        self.assertEqual(p["cota"], 15.55)
        self.assertEqual(p["rua"], "Luiz Moreli")
        self.assertEqual(p["esquina"], "Rua X")
        self.assertEqual(p["obs"], "esquina com a Rua X")
        self.assertEqual(p["coord_x"], "703000.5")
        self.assertEqual(p["pasta"], "Cotas de Cheia 2011")
        # nada se perde: os nove campos ficam em `campos`
        self.assertEqual(len(p["campos"]), 9)


class Brusque2023(unittest.TestCase):
    def setUp(self):
        self.p = pontos_do_kml(KML_BRUSQUE_2023)[0]

    def test_a_cota_e_o_nome_e_o_nivel_registrado_e_lamina(self):
        self.assertEqual(self.p["cota"], 7.65)
        self.assertEqual(self.p["cota_rotulo"], "7,65")
        self.assertEqual(self.p["cota_campo"], "nome_marcador")
        self.assertEqual(self.p["lamina_local_m"], 1.31)
        self.assertEqual(self.p["lamina_local_rotulo"], "1,31")
        # a prova de que o nome é a cota: cota + lâmina = pico de 17/11/2023
        self.assertAlmostEqual(self.p["cota"] + self.p["lamina_local_m"], 8.96)

    def test_sinonimos_ignoram_maiusculas_e_acentos(self):
        self.assertEqual(self.p["rua"], "Bartolomeu Pruner")
        self.assertIsNone(self.p["esquina"])          # <value/> vazio vira None
        self.assertEqual(self.p["bairro"], "Jardim Maluche")
        self.assertEqual(self.p["conferencia"], "Correta")
        # os nomes originais ficam intactos em `campos`, foto incluída
        self.assertIn("Nível registrado no local", self.p["campos"])
        self.assertIn("gx_media_links", self.p["campos"])
        self.assertEqual(self.p["formato"], "extended_data")

    def test_lamina_com_unidade_colada_e_lida(self):
        kml = KML_BRUSQUE_2023.replace("<value>1,31</value>", "<value>0,40 m</value>")
        p = pontos_do_kml(kml)[0]
        self.assertEqual(p["lamina_local_m"], 0.40)
        self.assertEqual(p["lamina_local_rotulo"], "0,40 m")

    def test_o_campo_cota_tem_preferencia_sobre_o_nome(self):
        p = pontos_do_kml(KML_BRUSQUE)[0]
        self.assertEqual(p["cota_campo"], "cota")
        self.assertNotIn("lamina_local_m", p)


class IturangaNomeEhCota(unittest.TestCase):
    def test_o_nome_vale_como_cota_so_quando_nao_ha_campo(self):
        p = pontos_do_kml(KML_ITUPORANGA_RUAS)[0]
        self.assertEqual(p["cota"], 3.38)
        self.assertEqual(p["cota_rotulo"], "3,38 metros")
        self.assertEqual(p["cota_campo"], "nome_marcador")
        self.assertEqual(p["_titulo"], "Rua João Back / Galpão Recuperauto")
        self.assertEqual(resumo(pontos_do_kml(KML_ITUPORANGA_RUAS))["com_cota"], 1)

    def test_em_gaspar_o_nome_nao_substitui_o_campo_cota(self):
        p = pontos_do_kml(KML_GASPAR_REAL)[0]
        self.assertEqual(p["cota_campo"], "cota")
        self.assertNotEqual(p["cota_rotulo"], p["nome_marcador"])

    def test_nome_que_nao_e_numero_nao_vira_cota(self):
        self.assertEqual(resumo(pontos_do_kml(KML_SEM_COTA))["com_cota"], 0)
        self.assertIsNone(pontos_do_kml(KML_SEM_COTA)[0]["cota_campo"])


class FalhaSilenciosa(unittest.TestCase):
    def test_ponto_sem_cota_e_contado(self):
        r = resumo(pontos_do_kml(KML_SEM_COTA))
        self.assertEqual((r["total"], r["com_cota"], r["sem_cota"]), (1, 0, 1))

    def test_kml_sem_nenhuma_cota_nao_grava(self):
        with tempfile.TemporaryDirectory() as d:
            kml = Path(d) / "x.kml"
            kml.write_text(KML_SEM_COTA, encoding="utf-8")
            saida = Path(d) / "x.json"
            argv = sys.argv
            sys.argv = ["x", str(kml), "--saida", str(saida)]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 2)
            finally:
                sys.argv = argv
            self.assertFalse(saida.exists())

    def test_nao_sobrescreve_sem_forcar(self):
        with tempfile.TemporaryDirectory() as d:
            kml = Path(d) / "g.kml"
            kml.write_text(KML_GASPAR, encoding="utf-8")
            saida = Path(d) / "g.json"
            saida.write_text("{}", encoding="utf-8")
            argv = sys.argv
            sys.argv = ["x", str(kml), "--saida", str(saida)]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 3)
                sys.argv = ["x", str(kml), "--saida", str(saida), "--forcar"]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 0)
            finally:
                sys.argv = argv
            corpo = json.loads(saida.read_text(encoding="utf-8"))
            self.assertEqual(corpo["_meta"]["total"], 2)
            self.assertEqual(len(corpo["_meta"]["sha256_do_kml"]), 64)


class SaidaCompativelComOImportador(unittest.TestCase):
    def test_tem_as_chaves_que_importar_cotas_gaspar_le(self):
        corpo = montar(pontos_do_kml(KML_GASPAR), Path("g.kml"), KML_GASPAR)
        p = corpo["pontos"][0]
        for chave in ("cota_rotulo", "rua", "esquina", "bairro", "sequencia", "coord_x", "coord_y", "lon", "lat"):
            self.assertIn(chave, p)


if __name__ == "__main__":
    unittest.main()
