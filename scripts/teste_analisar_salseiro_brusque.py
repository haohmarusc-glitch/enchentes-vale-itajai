"""A armadilha do zero, e o que a Salseiro pode e não pode dizer — travados.

O histórico do portal da Defesa Civil de Brusque grava `cota = 0,00` quando a
leitura falta. Entre 40% e 57% das linhas são assim. Um `min()` ingênuo diria
que o Mirim seca toda semana. Estes testes usam os valores REAIS de dezembro
de 2020, o único evento que o projeto conseguiu parear com hora nas duas
pontas.
"""

from __future__ import annotations

import io
import tarfile
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import analisar_salseiro_brusque as s

FONTE = (Path(__file__).resolve().parent / "analisar_salseiro_brusque.py").read_text(encoding="utf-8")


def _html(linhas: list[tuple[str, str]]) -> str:
    corpo = "".join(f"<tr><td>{d}</td><td>0</td><td>0,00</td><td>{c}</td><td>0</td></tr>"
                    for d, c in linhas)
    return ("<table><tr><td colspan=\"5\"><b>Salseiro - Vidal Ramos</b></td></tr>"
            "<tr><td><b>data</b></td><td><b>historico</b></td><td><b>chuva</b></td>"
            f"<td><b>cota</b></td><td><b>manual</b></td></tr>{corpo}</table>")


def _tar(arquivos: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "t.tar.gz"
    with tarfile.open(tmp, "w:gz") as tar:
        for nome, html in arquivos.items():
            dados = html.encode()
            info = tarfile.TarInfo(nome)
            info.size = len(dados)
            tar.addfile(info, io.BytesIO(dados))
    return tmp


class ZeroEhAusenteNaoNivel(unittest.TestCase):
    def test_zero_vira_none(self):
        self.assertIsNone(s.cota_ou_nada("0,00"))
        self.assertIsNone(s.cota_ou_nada("0"))

    def test_valor_real_passa(self):
        self.assertEqual(s.cota_ou_nada("1,20"), 1.20)
        self.assertEqual(s.cota_ou_nada("4,83"), 4.83)

    def test_lixo_vira_none_e_nao_explode(self):
        for ruim in ("", "N/A", None):
            self.assertIsNone(s.cota_ou_nada(ruim))

    def test_o_caso_da_primeira_linha_real(self):
        """1,20 → 0,00 → 0,00 → 1,19: o rio não secou entre as duas."""
        serie = s.linhas_do_html(_html([("09/09/2019 00:00:00", "1,20"),
                                        ("09/09/2019 00:15:00", "0,00"),
                                        ("09/09/2019 00:30:00", "0,00"),
                                        ("09/09/2019 01:15:00", "1,19")]))
        cotas = [c for _, c in serie]
        self.assertEqual(cotas, [1.20, None, None, 1.19])
        self.assertEqual(min(c for c in cotas if c is not None), 1.19,
                         "um mínimo ingênuo daria 0,00")


class ATabelaEhLidaInteira(unittest.TestCase):
    def test_duplicata_entre_arquivos_fica_com_o_valor(self):
        """As janelas anuais se sobrepõem um dia; se um lado tem 0,00 e o outro tem valor, fica o valor."""
        tar = _tar({"a.xls": _html([("09/09/2020 00:00:00", "0,00")]),
                    "b.xls": _html([("09/09/2020 00:00:00", "1,50")])})
        serie = s.serie_do_tar(tar)
        self.assertEqual(serie, [(datetime(2020, 9, 9), 1.50)])

    def test_arquivo_vazio_nao_derruba(self):
        """O _2 real tem 233 bytes: só cabeçalho."""
        tar = _tar({"vazio.xls": _html([]), "cheio.xls": _html([("01/01/2021 00:00:00", "2,00")])})
        self.assertEqual(len(s.serie_do_tar(tar)), 1)


class PicosEBuracos(unittest.TestCase):
    def test_pico_por_evento_com_hora(self):
        serie = [(datetime(2020, 12, 15, 12, 0), 2.50), (datetime(2020, 12, 15, 13, 15), 2.73),
                 (datetime(2020, 12, 15, 15, 15), 2.48), (datetime(2020, 12, 25, 0, 0), 2.60)]
        ps = s.picos(serie, limiar=2.4)
        self.assertEqual(len(ps), 2, "dois eventos separados por 10 dias")
        self.assertEqual(ps[0][:2], (datetime(2020, 12, 15, 13, 15), 2.73))

    def test_buraco_conta_so_ausentes_seguidos(self):
        base = datetime(2020, 5, 1)
        serie = [(base + i * s.PASSO, None) for i in range(96)] + [(base + 96 * s.PASSO, 1.0)]
        bs = s.buracos(serie)
        self.assertEqual(len(bs), 1)
        self.assertEqual(bs[0][2], 96)


class OPareamentoDizQuandoNaoPode(unittest.TestCase):
    BRUSQUE = [(datetime(2020, 12, 15, 20, 45), 4.95), (datetime(2022, 6, 23, 0, 45), 5.46)]

    def test_o_evento_real_de_dezembro_de_2020(self):
        serie = [(datetime(2020, 12, 15, 13, 15), 2.73), (datetime(2020, 12, 15, 15, 15), 2.48)]
        p = s.parear(serie, self.BRUSQUE[:1])[0]
        self.assertEqual(p["horas"], 7.5)
        self.assertEqual(p["salseiro_em"], datetime(2020, 12, 15, 13, 15))

    def test_janela_sem_leitura_e_recusa_e_nao_zero(self):
        p = s.parear([], self.BRUSQUE[1:])[0]
        self.assertIn("recusa", p)
        self.assertNotIn("horas", p, "sem par não pode sair número")

    def test_janela_so_com_ausentes_e_recusa(self):
        serie = [(datetime(2022, 6, 22, 10, 0), None), (datetime(2022, 6, 22, 11, 0), None)]
        p = s.parear(serie, self.BRUSQUE[1:])[0]
        self.assertIn("0,00", p["recusa"])

    def test_a_cobertura_da_janela_viaja_junto(self):
        """57% ausente é o que faz 7,5 h ser teto, não medida."""
        serie = [(datetime(2020, 12, 15, 13, 15), 2.73), (datetime(2020, 12, 15, 13, 30), None)]
        p = s.parear(serie, self.BRUSQUE[:1])[0]
        self.assertEqual((p["leituras"], p["ausentes"]), (2, 1))


class SondarNaoEhVincular(unittest.TestCase):
    def test_nao_escreve_nos_jsons(self):
        for arq in ("estacoes.json", "transito.json"):
            self.assertNotIn(f'"{arq}"', FONTE)
        self.assertNotIn("grava_json", FONTE)

    def test_o_aviso_da_regua_esta_no_arquivo(self):
        self.assertIn("NÃO SERVE COMO NÍVEL DE VIDAL RAMOS", FONTE.upper())
        self.assertIn("0,70 m", FONTE)

    def test_a_atencao_e_da_salseiro_nao_de_vidal_ramos(self):
        self.assertEqual(s.ATENCAO_SALSEIRO_M, 3.0)
        self.assertIn("nunca a de Vidal Ramos", FONTE)


class ORegistroEmTransitoEhMedicaoNaoFaixa(unittest.TestCase):
    """O _meta.medicoes de transito.json guarda o evento sem virar horas_min/max."""

    def test_o_evento_esta_registrado_com_as_ressalvas(self):
        from comum import le_json
        med = le_json("transito.json")["_meta"]["medicoes"]["salseiro_para_brusque"]
        self.assertEqual(len(med), 1)
        self.assertEqual(med[0]["horas"], 7.5)
        texto = " ".join(med[0]["ressalvas"])
        for marca in ("UM evento", "57%", "NÃO É A RÉGUA DE VIDAL RAMOS", "23/06/2022"):
            self.assertIn(marca, texto, f"a ressalva perdeu {marca!r}")

    def test_o_elo_brusque_itajai_nao_mudou_por_causa_disto(self):
        from comum import le_json
        for tr in le_json("transito.json")["trechos"]:
            if tr["rio"] == "itajai-mirim":
                self.assertEqual((tr["de"], tr["para"]), ("brusque", "itajai"))
                self.assertEqual((tr["horas_min"], tr["horas_max"]), (6, 6))


if __name__ == "__main__":
    unittest.main()
