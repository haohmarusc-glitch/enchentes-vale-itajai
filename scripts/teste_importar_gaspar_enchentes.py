#!/usr/bin/env python3
"""
Testes da importação do histórico de Gaspar.

Seriam 71 registros de uma vez numa cidade que hoje tem ZERO — a maior entrada
única já feita na base. Os três modos de errar estão travados aqui:

* consertar em silêncio a data impossível que a própria fonte publica;
* deixar passar como pico uma data que é de INÍCIO do evento;
* aceitar sem marca uma data que não pareia com evento nenhum.
"""
import unittest
from datetime import date

import importar_gaspar_enchentes as ig

# Amostra com a mesma forma da página, incluindo os oito valores de controle
# conferidos em 07/09/2026 e a linha do 9855, que é real.
PAGINA = """
<html><body>
<table>
  <tr><th>Início</th><th>Término</th><th>Metragem máxima</th></tr>
  <tr><td>12/10/2023</td><td>16/10/2023</td><td>7,45 m</td></tr>
  <tr><td>09/11/2011</td><td>12/11/2011</td><td>9,42 m</td></tr>
  <tr><td>24/11/2008</td><td>28/11/2008</td><td>9,80 m</td></tr>
  <tr><td>07/08/1984</td><td>10/08/1984</td><td>11,40 m</td></tr>
  <tr><td>09/06/1983</td><td>14/06/1983</td><td>11,50 m</td></tr>
  <tr><td>29/05/1911</td><td>02/06/1911</td><td>12,42 m</td></tr>
  <tr><td>23/09/1880</td><td>26/09/1880</td><td>12,56 m</td></tr>
  <tr><td>29/10/1852</td><td>02/11/1852</td><td>12,00 m</td></tr>
  <tr><td>20/11/1855</td><td>24/11/9855</td><td>10,00 m</td></tr>
</table>
</body></html>
"""

OUTRA_GRAFIA = """
<html><body><table>
  <tr><th>Data de início</th><th>Data de término</th><th>Cota máxima</th></tr>
  <tr><td>12/10/2023</td><td>16/10/2023</td><td>7.45</td></tr>
</table></body></html>
"""

SEM_TABELA_UTIL = """
<html><body><table>
  <tr><th>Bairro</th><th>Abrigo</th></tr><tr><td>Centro</td><td>Escola</td></tr>
</table></body></html>
"""


def registros(html=PAGINA):
    crus, _ = ig.linhas_da_tabela(html)
    return ig.monta(crus, ig.le_json("enchentes.json")["eventos"])


class LeituraDaTabela(unittest.TestCase):
    def test_le_as_nove_linhas(self):
        crus, _ = ig.linhas_da_tabela(PAGINA)
        self.assertEqual(len(crus), 9)

    def test_aceita_outra_grafia_de_cabecalho(self):
        crus, _ = ig.linhas_da_tabela(OUTRA_GRAFIA)
        self.assertEqual(len(crus), 1)
        self.assertEqual(ig.numero(crus[0]["pico"]), 7.45)

    def test_tabela_sem_as_colunas_certas_devolve_os_cabecalhos(self):
        """Falhar em silêncio é o modo caro: o conserto tem de ser de uma linha."""
        crus, cabecalhos = ig.linhas_da_tabela(SEM_TABELA_UTIL)
        self.assertEqual(crus, [])
        self.assertIn("Bairro", cabecalhos)


class NumerosEDatas(unittest.TestCase):
    def test_virgula_decimal(self):
        self.assertEqual(ig.numero("9,80 m"), 9.8)

    def test_ponto_decimal_tambem(self):
        self.assertEqual(ig.numero("11.40"), 11.4)

    def test_data_normal(self):
        self.assertEqual(ig.data_iso("24/11/2008"), ("2008-11-24", False))

    def test_o_9855_da_fonte_e_preservado_e_marcado(self):
        """A prova de que a fonte errou não pode ser apagada pelo conserto."""
        valor, anomala = ig.data_iso("24/11/9855")
        self.assertTrue(anomala)
        self.assertEqual(valor, "24/11/9855", "não pode virar 1855")
        self.assertNotIn("1855", valor)

    def test_mes_impossivel_tambem_e_marcado(self):
        self.assertEqual(ig.data_iso("24/13/2008")[1], True)


class RegistrosMontados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs = registros()
        cls.por_data = {r["data"]: r for r in cls.regs}

    def test_toda_data_e_marcada_como_inicio_do_evento(self):
        for r in self.regs:
            self.assertTrue(r["data_e_do_inicio_do_evento"], r["data"])
            self.assertIn("INÍCIO", r["nota"])

    def test_a_nota_avisa_que_nao_calibra_transito(self):
        self.assertIn("trânsito", self.por_data["2008-11-24"]["nota"])

    def test_seis_dos_oito_controles_pareiam(self):
        """Conferido em 07/09/2026 contra a base: 0 ou 1 dia de vão."""
        for d in ("2023-10-12", "2008-11-24", "1984-08-07",
                  "1911-05-29", "1880-09-23", "1852-10-29"):
            self.assertEqual(self.por_data[d]["pareamento"], "confere", d)

    def test_os_dois_que_nao_pareiam_saem_marcados_e_nao_consertados(self):
        """
        09/11/2011 e 09/06/1983: o DIA bate com um pico conhecido de Blumenau e
        o MÊS não. Pode ser erro da fonte, pode ser evento local. Nem conserta
        nem descarta — marca, e diz qual era o candidato.
        """
        for d, pico in (("2011-11-09", 9.42), ("1983-06-09", 11.5)):
            r = self.por_data[d]
            self.assertEqual(r["pareamento"], "sem par", d)
            self.assertEqual(r["pico_m"], pico, "o valor não pode ser mexido")
            self.assertIn("o mais perto é", r["nota"])

    def test_a_linha_do_9855_entra_com_o_inicio_valido_e_a_marca(self):
        r = self.por_data["1855-11-20"]
        self.assertTrue(r["data_anomala"])
        self.assertEqual(r["data_fim"], "24/11/9855")
        self.assertIn("IMPOSSÍVEL", r["nota"])

    def test_campos_que_o_validador_exige(self):
        for r in self.regs:
            self.assertEqual(r["cidade"], "gaspar")
            self.assertEqual(r["rio"], "itajai-acu")
            self.assertIn("referencia", r)
            self.assertTrue(r["fonte"])
            self.assertIn(r["confianca"], ("alta", "media", "baixa"))

    def test_a_referencia_e_regua_e_nao_IBGE(self):
        """As cotas de rua e o tempo real de Gaspar são régua; misturar com o
        datum IBGE de Blumenau é a REGRA_REFERENCIA_BLUMENAU."""
        for r in self.regs:
            self.assertEqual(r["referencia"], "régua")


class ParMaisProximo(unittest.TestCase):
    """
    Defeito real de 07/09/2026, achado ao escrever o ofício: a primeira versão
    media só a distância, e um registro de Gaspar caiu "a zero dias" de um
    `blumenau 2013` — que é granularidade de ANO e cobre o ano inteiro. Entrou
    marcado como `pareamento: "confere"` sem que o site jamais fosse parear os
    dois, porque `datas.ts` diz que ano NUNCA pareia. Um registro afetado,
    retirado da base.
    """

    EVENTOS = [
        {"cidade": "blumenau", "data": "2013", "pico_m": 10.51},
        {"cidade": "blumenau", "data": "2013-09-23", "pico_m": 9.0},
        {"cidade": "gaspar", "data": "2013-11-20", "pico_m": 7.0},
    ]

    def test_granularidade_de_ano_nunca_conta_como_par(self):
        r = ig.par_mais_proximo("2013-11-23", self.EVENTOS)
        self.assertIsNotNone(r)
        self.assertEqual(r[1]["data"], "2013-09-23", "pegou o registro de ano")
        self.assertGreater(r[0], ig.TOLERANCIA_DIAS)

    def test_a_propria_cidade_nao_pareia_consigo(self):
        """Depois da importação Gaspar está na base; parear consigo é circular."""
        r = ig.par_mais_proximo("2013-11-23", self.EVENTOS)
        self.assertNotEqual(r[1]["cidade"], "gaspar")

    def test_o_2013_11_23_nao_esta_na_base(self):
        """Era o registro afetado. Se voltar, o defeito voltou."""
        g = [e for e in ig.le_json("enchentes.json")["eventos"]
             if e["cidade"] == "gaspar" and e["data"] == "2013-11-23"]
        self.assertEqual(g, [], "voltou o registro que só pareava com um ano")


class ReferenciaVertical(unittest.TestCase):
    """
    A fonte NÃO declara referência. A leitura direta da página, em 07/09/2026,
    confirmou isso — e a objeção "cadastrar sem referência resolvida" é justa.

    O que sustenta gravar "régua" é uma MEDIÇÃO: a menor cota de rua de Gaspar
    (6,20 m, estudo CEOPS/FURB, que DECLARA a régua da ANA na empresa Círculo) e
    o menor pico da lista histórica (6,19 m) diferem em **1 cm**. A lista começa
    exatamente onde a primeira rua alaga. Dois conjuntos publicados por caminhos
    diferentes não concordam no piso por acaso.

    Este teste trava o que sustenta a decisão, não a decisão: se os dois pisos
    se afastarem, é a hora de rever.
    """

    def test_o_piso_das_duas_series_bate_em_um_centimetro(self):
        ruas = [c["cota_m"] for c in ig.le_json("cotas-ruas.json")["cotas"]
                if c["cidade"] == "gaspar" and c.get("cota_m")]
        picos = [e["pico_m"] for e in ig.le_json("enchentes.json")["eventos"]
                 if e["cidade"] == "gaspar" and e.get("pico_m")]
        self.assertTrue(ruas and picos, "Gaspar sumiu de um dos dois arquivos")
        distancia_cm = abs(min(ruas) - min(picos)) * 100
        self.assertLessEqual(
            distancia_cm, 5,
            f"os pisos se afastaram para {distancia_cm:.0f} cm — a evidência que "
            "sustenta `referencia: régua` em Gaspar caiu, reveja a decisão")

    def test_a_referencia_gravada_e_regua(self):
        self.assertEqual(ig.REFERENCIA, "régua")
        for r in registros():
            self.assertEqual(r["referencia"], ig.REFERENCIA)


class ToleranciaBateComOSite(unittest.TestCase):
    def test_sete_dias(self):
        """Se `web/src/logica/datas.ts` mudar, isto tem de mudar junto."""
        alvo = ig.RAIZ_WEB.read_text(encoding="utf-8")
        self.assertIn(f"TOLERANCIA_DIAS = {ig.TOLERANCIA_DIAS}", alvo)

    def test_vao_de_mes_contra_dia(self):
        """1911-05 (mês) contra 1911-05-29 (dia): o dia cai dentro do mês."""
        self.assertEqual(ig.vao_em_dias("1911-05-29", "1911-05"), 0)

    def test_vao_entre_meses_distantes(self):
        self.assertGreater(ig.vao_em_dias("2011-11-09", "2011-09"), 7)


if __name__ == "__main__":
    unittest.main()
