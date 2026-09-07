#!/usr/bin/env python3
"""
Testes do leitor do inventário da ANA.

O script existe para responder UMA pergunta: esta estação mede nível de rio, e
fica onde? Errar qualquer das duas metades escreve um `codigo_ana` que aponta
para um pluviômetro ou para a estação de outro município — e ninguém veria,
porque o código, o nome e o município estariam certos. Os dois modos de errar
estão travados aqui, junto com o de falhar em silêncio.

⚠️ Os nomes dos campos do XML NÃO foram conferidos contra o serviço real (o
ambiente bloqueia *.ana.gov.br). Estes testes provam que o parser aguenta a
variação de grafia e que ele DENUNCIA o campo que não achou — não que a ANA
use exatamente estes nomes.
"""
import unittest

import ana_inventario as ai

FLUVIOMETRICA = """<?xml version="1.0"?>
<DataSet><diffgram><DocumentElement>
  <Table>
    <Codigo>83250000</Codigo><Nome>ITUPORANGA</Nome>
    <Latitude>-27,4167</Latitude><Longitude>-49,6000</Longitude>
    <Altitude>380</Altitude><AreaDrenagem>1650</AreaDrenagem>
    <TipoEstacao>1</TipoEstacao><nmRio>RIO ITAJAI DO SUL</nmRio>
    <nmMunicipio>ITUPORANGA</nmMunicipio>
    <PeriodoEscalaInicio>1929-01-01</PeriodoEscalaInicio>
    <PeriodoEscalaFim></PeriodoEscalaFim>
  </Table>
</DocumentElement></diffgram></DataSet>"""

PLUVIOMETRICA = FLUVIOMETRICA.replace(
    "<TipoEstacao>1</TipoEstacao>", "<TipoEstacao>2</TipoEstacao>")

GRAFIA_DIFERENTE = """<?xml version="1.0"?>
<DataSet><DocumentElement><Table>
  <codigo_estacao>83520000</codigo_estacao><estacao_nome>WARNOW</estacao_nome>
  <lat>-26.9500</lat><long>-49.2000</long><tipo_estacao>1</tipo_estacao>
</Table></DocumentElement></DataSet>"""

SEM_COORDENADA = """<?xml version="1.0"?>
<DataSet><DocumentElement><Table>
  <Codigo>83440000</Codigo><Nome>IBIRAMA</Nome><TipoEstacao>1</TipoEstacao>
  <UmCampoQueNaoConhecemos>42</UmCampoQueNaoConhecemos>
</Table></DocumentElement></DataSet>"""


class LeituraDoXml(unittest.TestCase):
    def uma(self, xml):
        achadas = [ai.estacao(r) for r in ai.registros_do_xml(xml)]
        self.assertEqual(len(achadas), 1, "devia ler exatamente um registro")
        return achadas[0]

    def test_le_os_campos_da_fluviometrica(self):
        e = self.uma(FLUVIOMETRICA)
        self.assertEqual(e["codigo"], "83250000")
        self.assertEqual(e["nome"], "ITUPORANGA")
        self.assertEqual(e["tipo"], "fluviometrica")
        self.assertAlmostEqual(e["lat"], -27.4167)
        self.assertAlmostEqual(e["lon"], -49.6)
        self.assertEqual(e["area_drenagem_km2"], 1650)

    def test_virgula_decimal_da_ana_vira_numero(self):
        """`-27,4167` é como a ANA publica. Ler como texto quebra a distância."""
        self.assertAlmostEqual(self.uma(FLUVIOMETRICA)["lat"], -27.4167)

    def test_ponto_decimal_tambem(self):
        self.assertAlmostEqual(self.uma(GRAFIA_DIFERENTE)["lat"], -26.95)

    def test_pluviometrica_nao_se_disfarca_de_fluviometrica(self):
        """É o erro que a regra emendada existe para impedir."""
        self.assertEqual(self.uma(PLUVIOMETRICA)["tipo"], "pluviometrica")

    def test_grafia_diferente_do_campo_ainda_e_lida(self):
        e = self.uma(GRAFIA_DIFERENTE)
        self.assertEqual(e["codigo"], "83520000")
        self.assertEqual(e["tipo"], "fluviometrica")

    def test_campo_ausente_vira_None_e_o_registro_denuncia_o_que_veio(self):
        """Falhar em silêncio é o modo de erro caro: sem coordenada, sem vínculo."""
        e = self.uma(SEM_COORDENADA)
        self.assertIsNone(e["lat"])
        self.assertIsNone(e["lon"])
        self.assertIn("umcampoquenaoconhecemos", e["campos_no_xml"])

    def test_xml_sem_registro_devolve_lista_vazia(self):
        self.assertEqual(ai.registros_do_xml("<DataSet><Vazio/></DataSet>"), [])


class Distancia(unittest.TestCase):
    def test_mede_em_metros_na_latitude_da_bacia(self):
        """Um grau de latitude ~111 km; a longitude encolhe com o cosseno."""
        d = ai.metros((-27.0, -49.0), (-27.0, -49.01))
        self.assertAlmostEqual(d, 111320 * 0.01 * 0.891, delta=15)

    def test_mesmo_ponto_da_zero(self):
        self.assertEqual(ai.metros((-27.1, -48.9), (-27.1, -48.9)), 0.0)


class ListaDePendentes(unittest.TestCase):
    def test_brusque_saiu_da_lista(self):
        """Fechou em 07/09/2026 pelo codigo_dcsc; deixar aqui pediria de novo."""
        self.assertNotIn("83900000", ai.PENDENTES)

    def test_toda_pendente_aponta_uma_cidade_do_eixo(self):
        ids = {c["id"] for rio in ai.le_json("estacoes.json")["rios"].values()
               for c in rio["cidades"]}
        for codigo, (cidade, _) in ai.PENDENTES.items():
            self.assertIn(cidade, ids, f"{codigo} aponta cidade que não existe")


if __name__ == "__main__":
    unittest.main()
