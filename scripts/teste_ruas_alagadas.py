"""Trava o registro na mão das ruas alagadas (scripts/ruas_alagadas.py, decisão do Jefferson de 05/10/2026)."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import ruas_alagadas as ra
from nivel_antes import carregar, secao_registros

HOJE = date(2026, 10, 5)
CONHECIDAS = set(ra.cidades().values())


def linha(**campos):
    base = {"cidade": "Itajaí", "rua": "R. José Domingos Machado", "ponto": "", "bairro": "São Vicente", "data": "12/09/2026",
            "hora": "6h30", "situacao": "alagada", "quando_e": "hora do fato", "precisao": "", "lamina": "",
            "fonte_tipo": "Defesa Civil", "fonte": "Boletim da Defesa Civil de Itajaí", "confianca": "", "nota": ""}
    return base | campos


def registro(**campos):
    r, problemas = ra.da_linha(linha(), ra.cidades(), HOJE)
    assert not problemas, problemas
    return r | campos


class Leitura(unittest.TestCase):
    def test_formatos_de_data_e_hora(self):
        self.assertEqual(ra.ler_quando("12/09/2026", "6h30"), "2026-09-12T06:30")
        self.assertEqual(ra.ler_quando("2026-09-12", "14:05"), "2026-09-12T14:05")
        self.assertEqual(ra.ler_quando("12/09/2026", "14h"), "2026-09-12T14:00")
        for d, h in (("12/09", "14:00"), ("31/02/2026", "10:00"), ("12/09/2026", "25:00"), ("12/09/2026", ""), ("", "10:00")):
            self.assertIsNone(ra.ler_quando(d, h), (d, h))

    def test_linha_da_planilha_vira_registro_com_rotulos_e_padroes(self):
        r = registro()
        self.assertEqual((r["cidade"], r["quando"], r["situacao"], r["quando_e"]), ("itajai", "2026-09-12T06:30", "alagada", "hora_do_fato"))
        self.assertEqual((r["precisao"], r["fonte_tipo"], r["confianca"], r["registrado_em"]), ("exata", "defesa_civil", "alta", "2026-10-05"))
        self.assertNotIn("ponto", r)  # vazio não entra
        r, _ = ra.da_linha(linha(situacao="Começou a alagar", quando_e="Hora da publicação", fonte_tipo="foto/vídeo"), ra.cidades(), HOJE)
        self.assertEqual((r["situacao"], r["quando_e"], r["fonte_tipo"], r["confianca"]), ("comecou_a_alagar", "hora_da_publicacao", "foto_video", "baixa"))

    def test_planilha_com_virgula_ou_ponto_e_virgula(self):
        cab = ",".join(ra.COLUNAS)
        self.assertEqual(ra.MODELO.read_text(encoding="utf-8").strip(), cab)  # o modelo é o que a importação lê
        um = "Itajaí,R. A,,,12/09/2026,10:00,alagada,hora do fato,,,imprensa,\"ND+, 10h20\",,"
        dois = "Itajaí;R. A;;;12/09/2026;10:00;alagada;hora do fato;;;imprensa;ND+, 10h20;;"
        for texto in (f"{cab}\n{um}\n", f"{cab.replace(',', ';')}\n{dois}\n"):
            linhas = ra.ler_planilha(texto)
            self.assertEqual((linhas[0]["rua"], linhas[0]["fonte"]), ("R. A", "ND+, 10h20"))


class Regras(unittest.TestCase):
    def erros(self, *regs):
        return ra.validar(list(regs), CONHECIDAS, HOJE)

    def test_registro_bom_passa(self):
        self.assertEqual(self.erros(registro()), [])

    def test_teto_de_confianca_pelo_tipo_de_fonte(self):
        self.assertEqual(self.erros(registro(fonte_tipo="imprensa", confianca="media")), [])
        self.assertEqual(self.erros(registro(fonte_tipo="foto_video", confianca="media")), [])
        for tipo, conf in (("relato", "media"), ("relato", "alta"), ("foto_video", "alta"), ("imprensa", "alta")):
            self.assertTrue(any("não sustenta" in e for e in self.erros(registro(fonte_tipo=tipo, confianca=conf))), (tipo, conf))

    def test_dado_pessoal_nao_entra(self):
        for campo, texto in (("fonte", "relato de morador (47) 99999-1234"), ("nota", "ligar 99876-5432"),
                             ("fonte", "fulano@gmail.com")):
            self.assertTrue(any("dado pessoal" in e for e in self.erros(registro(**{campo: texto}))), texto)
        # Número de boletim, hora e link não são telefone.
        self.assertEqual(self.erros(registro(fonte="Boletim 12/2026 das 14h45, https://g1.globo.com/sc/noticia/2026/09/12/x-123456789.ghtml")), [])

    def test_hora_campos_cidade_repetido(self):
        self.assertTrue(any("AAAA-MM-DDTHH:MM" in e for e in self.erros(registro(quando="2026-09-12 06:30"))))
        self.assertTrue(any("futuro" in e for e in self.erros(registro(quando="2026-12-01T10:00"))))
        self.assertTrue(any("estacoes.json" in e for e in self.erros(registro(cidade="navegantes"))))
        self.assertTrue(any("quando_e" in e for e in self.erros(registro(quando_e="talvez"))))
        self.assertTrue(any("falta 'fonte'" in e for e in self.erros(registro(fonte=""))))
        self.assertTrue(any("repetido" in e for e in self.erros(registro(), registro(rua="r. jose domingos machado"))))

    def test_arquivo_real_passa(self):
        conteudo = json.loads(ra.ARQUIVO.read_text(encoding="utf-8"))
        self.assertIn("_meta", conteudo)
        self.assertEqual(ra.validar(conteudo["registros"], CONHECIDAS), [])


class Importacao(unittest.TestCase):
    def test_so_acrescenta_ignora_repetida_e_recusa_com_o_motivo(self):
        existente = registro()
        conteudo = {"registros": [existente]}
        linhas = [linha(), linha(hora="8h"), linha(cidade="Gasparzinho"), linha(fonte_tipo="relato", confianca="alta"), {}]
        novos, recusas, repetidos = ra.importar(linhas, conteudo, HOJE)
        self.assertEqual([r["quando"] for r in novos], ["2026-09-12T08:00"])
        self.assertEqual(repetidos, 1)
        self.assertEqual(len(recusas), 2)
        self.assertTrue(recusas[0].startswith("linha 4: cidade 'Gasparzinho'"))
        self.assertIn("linha 5", recusas[1])
        self.assertEqual(conteudo["registros"], [existente])  # importar não grava nem mexe no que existe


class NaConta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.series = carregar()

    def secao(self, *regs):
        p = Path(tempfile.mkdtemp()) / "ruas-alagadas.json"
        p.write_text(json.dumps({"registros": list(regs)}), encoding="utf-8")
        return secao_registros(self.series, (3, 6), p)

    def test_itajai_mostra_as_reguas_da_cidade_a_mare_e_as_de_cima(self):
        texto = self.secao(registro(precisao="aproximada"))
        self.assertIn("R. José Domingos Machado, São Vicente (itajai) — alagada às 12/set/2026 06:30", texto)
        self.assertIn("hora aproximada", texto)
        self.assertIn("tábua da Marinha", texto)
        self.assertIn("**DC-04 Rio Itajaí-Mirim", texto)
        self.assertIn("**Blumenau (AlertaBlu)** (a montante): 3 h antes:", texto)

    def test_hora_da_publicacao_e_limite_e_cota_da_rua_aparece(self):
        r = registro(cidade="blumenau", rua="Rua São Rafael", bairro="", quando="2026-09-12T02:00", situacao="interditada",
                     quando_e="hora_da_publicacao", fonte_tipo="imprensa", confianca="media")
        texto = self.secao(r)
        self.assertIn("a água chegou antes", texto)
        self.assertIn("7,40 m (final da rua)", texto)
        self.assertIn("**Blumenau (AlertaBlu)**: 7,65 m", texto)
        self.assertNotIn("DC-04", texto)

    def test_sem_registro_diz_como_registrar(self):
        self.assertIn("docs/REGISTRO-RUAS-ALAGADAS.md", self.secao())


if __name__ == "__main__":
    unittest.main()
