"""Testes do motor de classificação estadual × municipal (`classificar_reguas.py`, PR 1 de 07/10/2026).

O gabarito `data/classificacao-esperada.json` é dividido com o site: aqui se exige que o motor dê o
`esperado` de cada caso; `web/src/logica/classificacaoParidade.test.ts` exige que o site de hoje dê o
`site`. Os demais testes cobrem a lista do §11 do plano que cabe neste PR (conversão entre réguas não
existe ainda: nenhuma está cadastrada, e o motor não converte).
"""

from __future__ import annotations

import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import classificar_reguas as cr  # noqa: E402
from comum import le_json  # noqa: E402

ESTACOES = le_json("estacoes.json")
GABARITO = le_json("classificacao-esperada.json")
AGORA = cr.de_brasilia("2026-10-07T13:05:00")


def brusque() -> dict:
    return copy.deepcopy(cr.cidade_do_piloto(ESTACOES, "brusque"))


def leitura(nivel=2.29, quando="2026-10-07T13:00:00", codigo="DCSC-00019", estacao="Brusque — Ponte Estaiada (DCSC-00019)"):
    l = {"estacao": estacao, "cidade": "brusque", "rio": "itajai-mirim", "nivel_m": nivel, "medido_em": quando,
         "fonte": "teste"}
    if codigo:
        l["codigo"] = codigo
    return l


def estadual(faixa="normal", quando="2026-10-07T13:00:00", nivel=2.3):
    return {"leituras": [{"codigo": "DCSC-00019", "estacao": "SDC-SC Brusque", "cidade": "brusque",
                          "nivel_bruto_m": nivel, "medido_em": quando,
                          "classificacao_estadual": {"faixa": faixa, "fonte": "DCSC rio_alarmes", "motivo": None}}]}


class TesteGabaritoCompartilhadoComOSite(unittest.TestCase):
    def test_o_motor_reproduz_o_gabarito(self):
        self.assertGreaterEqual(len(GABARITO["casos"]), 15, "gabarito pequeno demais para provar algo")
        for caso in GABARITO["casos"]:
            with self.subTest(caso["id"]):
                agora = cr.de_brasilia(caso["agora_brasilia"])
                cidade = cr.cidade_do_piloto(ESTACOES, caso["cidade"])
                r = cr.classificar_cidade(cidade, caso["leituras"], caso["nivel_sc"], agora)
                esp = caso["esperado"]
                self.assertEqual(r["classificacoes"]["municipal"]["faixa"], esp["municipal"])
                self.assertEqual(r["classificacoes"]["estadual"]["faixa"], esp["estadual"])
                ap = r["classificacao_aplicada"]
                self.assertEqual({"tipo": ap["tipo"], "faixa": ap["faixa"]}, esp["aplicada"])
                estado = {"cidades": {caso["cidade"]: r}}
                self.assertEqual(cr.validar_estado(estado, agora), [], "a saída do motor passa no próprio validador")

    def test_a_saida_do_motor_no_gabarito_esta_em_dia(self):
        """O site é testado com o `motor` guardado em cada caso (PR 2): ele tem de ser o que o motor dá hoje."""
        for caso in GABARITO["casos"]:
            with self.subTest(caso["id"]):
                self.assertIn("motor", caso, "rode: python3 scripts/classificar_reguas.py --gabarito")
                self.assertEqual(caso["motor"], cr.motor_do_caso(ESTACOES, caso),
                                 "motor mudou sem regerar: python3 scripts/classificar_reguas.py --gabarito")

    def test_sem_divergencia_declarada_o_site_pinta_o_mesmo(self):
        """O lado `site` do gabarito, lido como o motor lê: quem pinta e com que faixa."""
        for caso in GABARITO["casos"]:
            with self.subTest(caso["id"]):
                s = caso["site"]
                if s["faixa"] not in ("sem-dado", "varias"):
                    pelo_site = {"tipo": "municipal", "faixa": s["faixa"]}
                elif s["faixaEstadual"]:
                    pelo_site = {"tipo": "estadual", "faixa": s["faixaEstadual"]}
                else:
                    pelo_site = {"tipo": "nenhuma", "faixa": None}
                if caso.get("diverge_do_site"):
                    self.assertNotEqual(pelo_site, caso["esperado"]["aplicada"],
                                        "divergência declarada que não diverge: tirar o campo")
                else:
                    self.assertEqual(pelo_site, caso["esperado"]["aplicada"])


class TesteFaixasMunicipais(unittest.TestCase):
    """Brusque: atenção 3,00 · emergência 5,00 (sem alerta)."""

    def faixa(self, nivel):
        return cr.classificar_municipal(brusque(), [leitura(nivel)], AGORA)["faixa"]

    def test_limites(self):
        self.assertEqual(self.faixa(2.99), "normal")
        self.assertEqual(self.faixa(3.0), "atencao")
        self.assertEqual(self.faixa(4.99), "atencao")
        self.assertEqual(self.faixa(5.0), "emergencia")
        self.assertEqual(self.faixa(7.5), "emergencia")

    def test_alerta_entre_atencao_e_emergencia_quando_a_cidade_tem(self):
        c = brusque()
        c["cotas_m"] = {"atencao": 3.0, "alerta": 4.0, "emergencia": 5.0}
        f = lambda n: cr.classificar_municipal(c, [leitura(n)], AGORA)["faixa"]  # noqa: E731
        self.assertEqual(f(3.5), "atencao")
        self.assertEqual(f(4.0), "alerta")
        self.assertEqual(f(4.5), "alerta")

    def test_marca_que_nao_e_fase_nao_pinta(self):
        c = brusque()
        c["cotas_m"] = {"atencao": 3.0, "emergencia": 5.0, "referencia_historica": 1.0}
        self.assertEqual(cr.classificar_municipal(c, [leitura(2.0)], AGORA)["faixa"], "normal")

    def test_sem_cotas_de_acionamento(self):
        c = brusque()
        c["cotas_m"] = {"referencia_historica": 4.8}
        r = cr.classificar_municipal(c, [leitura(5.0)], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("sem fase de acionamento", r["motivo"])

    def test_faixas_nao_confirmadas_nao_pintam(self):
        c = brusque()
        c["cotas_verificado"] = False
        r = cr.classificar_municipal(c, [leitura(3.5)], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("cotas não confirmadas", r["motivo"])

    def test_fonte_das_faixas_ausente_nao_pinta(self):
        c = brusque()
        c["fonte_cotas"] = ""
        r = cr.classificar_municipal(c, [leitura(3.5)], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("fonte das faixas ausente", r["motivo"])

    def test_cotas_fora_de_ordem(self):
        c = brusque()
        c["cotas_m"] = {"atencao": 5.0, "emergencia": 3.0}
        self.assertIn("fora de ordem", cr.classificar_municipal(c, [leitura(4.0)], AGORA)["motivo"])

    def test_regua_diferente_nao_compara(self):
        r = cr.classificar_municipal(brusque(), [leitura(3.5, codigo=None, estacao="Brusque")], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("réguas diferentes", r["motivo"])
        self.assertTrue(r["de_agora"], "a leitura é de agora: segura a estadual, como o site")

    def test_codigo_dcsc_e_lista_da_cota_propria_precisam_concordar(self):
        c = brusque()
        c["codigo_dcsc"] = "DCSC-00099"
        r = cr.classificar_municipal(c, [leitura(3.5)], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("não concordam", r["motivo"])

    def test_sem_regua_das_cotas_id_nao_compara(self):
        c = brusque()
        del c["regua_das_cotas_id"]
        r = cr.classificar_municipal(c, [leitura(3.5)], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("falta `regua_das_cotas_id`", r["motivo"], "a lista ainda aponta a DCSC-00019: discordância")

    def test_regua_das_cotas_id_sem_fonte_nao_vale(self):
        c = brusque()
        c["regua_das_cotas_id"] = {"codigo": "DCSC-00019", "fonte": " "}
        self.assertIsNone(cr.regua_das_cotas_id(c))
        self.assertIsNone(cr.classificar_municipal(c, [leitura(3.5)], AGORA)["faixa"])

    def test_regua_das_cotas_id_e_lista_da_cota_propria_precisam_concordar(self):
        c = brusque()
        c["regua_das_cotas_id"] = {"codigo": "DCSC-00003", "fonte": "teste"}  # a de Ascurra
        regua, motivo = cr.regua_das_cotas(c)
        self.assertIsNone(regua)
        self.assertIn("não concordam", motivo)

    def test_regua_por_titulo_casa_com_a_publicacao_e_o_resgate(self):
        """Blumenau: sem código, a identidade é o título que `comum.regua_de` devolve (o resgate cola na primária)."""
        blu = copy.deepcopy(cr.cidade_do_piloto(ESTACOES, "blumenau"))
        self.assertEqual(cr.regua_das_cotas(blu), ("Blumenau", None))
        resgate = {"estacao": "Blumenau (PADKND)", "resgate_de": "Blumenau", "cidade": "blumenau",
                   "rio": "itajai-acu", "nivel_m": 4.5, "medido_em": "2026-10-07T13:00:00", "fonte": "teste"}
        r = cr.classificar_municipal(blu, [resgate], AGORA)
        self.assertEqual(r["regua_da_leitura"], "Blumenau")
        self.assertEqual(r["faixa"], "atencao")  # Blumenau: atenção 4,00 · alerta 6,00
        outra = {**resgate, "estacao": "Blumenau", "resgate_de": None}
        self.assertEqual(cr.classificar_municipal(blu, [{**outra, "estacao": "Outra régua"}], AGORA)["faixa"], None)

    def test_comparador_especial_e_recusado(self):
        cidade = cr.cidade_do_piloto(ESTACOES, "ascurra")
        problemas = cr.problemas_do_cadastro(cidade)
        self.assertTrue(any("comparador especial" in p for p in problemas))


class TesteLeitura(unittest.TestCase):
    def status(self, quando, cidade="brusque", nivel=3.0):
        medido = cr.de_brasilia(quando)
        return cr.status_da_leitura(nivel, medido, AGORA, cidade, cr.nivel_plausivel)[0]

    def test_frescor(self):
        self.assertEqual(self.status("2026-10-07T11:35:00"), "valida")      # 90 min
        self.assertEqual(self.status("2026-10-07T11:34:00"), "atrasada")    # 91 min
        self.assertEqual(self.status("2026-10-07T10:05:00"), "atrasada")    # 180 min
        self.assertEqual(self.status("2026-10-07T10:04:00"), "antiga")      # 181 min
        self.assertEqual(self.status("2026-10-07T13:15:00"), "valida")      # 10 min adiantado: relógio
        self.assertEqual(self.status("2026-10-07T13:25:00"), "carimbo_no_futuro")

    def test_blumenau_envelhece_em_2_h(self):
        self.assertEqual(self.status("2026-10-07T11:05:00", "blumenau"), "atrasada")  # 120 min
        self.assertEqual(self.status("2026-10-07T11:04:00", "blumenau"), "antiga")

    def test_valor_impossivel_e_sem_carimbo(self):
        self.assertEqual(self.status("2026-10-07T13:00:00", nivel=0), "valor_impossivel")
        self.assertEqual(self.status("2026-10-07T13:00:00", nivel=25.0), "valor_impossivel")
        self.assertEqual(self.status("2026-10-07T13:00:00", nivel=True), "valor_impossivel")
        self.assertEqual(cr.status_da_leitura(3.0, None, AGORA, "brusque", cr.nivel_plausivel)[0], "sem_carimbo")

    def test_carimbo_com_fuso_nao_e_o_contrato(self):
        self.assertIsNone(cr.de_brasilia("2026-10-07T13:00:00-03:00"))
        self.assertIsNone(cr.de_brasilia("2026-10-07 13:00:00"))
        self.assertEqual(cr.de_brasilia("2026-10-07T13:00"), datetime(2026, 10, 7, 16, 0, tzinfo=timezone.utc))

    def test_arredondamento_igual_ao_do_site(self):
        medido = cr.de_brasilia("2026-10-07T13:00:00")
        self.assertEqual(cr.idade_min(medido, medido.replace(second=30)), 1)  # Math.round(0,5) = 1
        self.assertEqual(cr.idade_min(medido, medido.replace(second=29)), 0)

    def test_a_mais_recente_com_carimbo_vence(self):
        a = leitura(2.0, "2026-10-07T12:00:00")
        b = leitura(3.5, "2026-10-07T13:00:00")
        sem = leitura(9.0, None)
        self.assertIs(cr.escolher_leitura([sem, a, b]), b)
        self.assertIs(cr.escolher_leitura([sem]), sem)


class TesteEstadual(unittest.TestCase):
    def test_so_a_faixa_publicada_nunca_o_metro(self):
        # 9 m na estadual com faixa publicada "normal": o motor não compara metro com limite nenhum.
        r = cr.classificar_estadual(brusque(), estadual("normal", nivel=9.0), AGORA)
        self.assertEqual(r["faixa"], "normal")
        self.assertEqual(r["nivel_m"], 9.0)

    def test_faixa_fora_do_vocabulario_ou_ausente(self):
        for faixa in (None, "inundacao", "vermelho"):
            with self.subTest(faixa):
                self.assertIsNone(cr.classificar_estadual(brusque(), estadual(faixa), AGORA)["faixa"])

    def test_estadual_velha_nao_pinta(self):
        r = cr.classificar_estadual(brusque(), estadual("alerta", quando="2026-10-07T09:00:00"), AGORA)
        self.assertIsNone(r["faixa"])
        self.assertEqual(r["status_leitura"], "antiga")

    def test_motivo_do_balde_quando_nao_ha_leitura(self):
        sc = {"leituras": [], "suspeitas": [{"cidade": "brusque", "codigo": "DCSC-00019", "motivo": "> 20 m"}]}
        r = cr.classificar_estadual(brusque(), sc, AGORA)
        self.assertIn("> 20 m", r["motivo"])


class TesteEscolhaDaPrincipal(unittest.TestCase):
    def aplicada(self, leituras, sc):
        return cr.classificar_cidade(brusque(), leituras, sc, AGORA)["classificacao_aplicada"]

    def test_municipal_valida_pinta(self):
        ap = self.aplicada([leitura(3.5)], estadual("emergencia"))
        self.assertEqual((ap["tipo"], ap["faixa"], ap["fallback"]), ("municipal", "atencao", False))
        self.assertTrue(ap["rotulo"].startswith("Classificação municipal"))

    def test_duas_validas_e_diferentes_a_municipal_manda(self):
        ap = self.aplicada([leitura(2.0)], estadual("alerta"))
        self.assertEqual((ap["tipo"], ap["faixa"]), ("municipal", "normal"))

    def test_sem_municipal_a_estadual_entra_como_fallback_com_aviso(self):
        ap = self.aplicada([], estadual("alerta"))
        self.assertEqual((ap["tipo"], ap["faixa"], ap["fallback"]), ("estadual", "alerta", True))
        self.assertIn("Não são as cotas do município", ap["aviso"])
        self.assertTrue(ap["rotulo"].startswith("Faixa estadual"))

    def test_nenhuma_valida(self):
        ap = self.aplicada([], {"leituras": []})
        self.assertEqual((ap["tipo"], ap["faixa"]), ("nenhuma", None))
        self.assertTrue(ap["motivo"])

    def test_sempre_diz_quem_pintou(self):
        for leituras, sc in (([leitura(3.5)], estadual()), ([], estadual()), ([], {"leituras": []})):
            r = cr.classificar_cidade(brusque(), leituras, sc, AGORA)
            self.assertIn(r["classificacao_aplicada"]["tipo"], cr.TIPOS_APLICADOS)
            self.assertEqual(r["faixa_do_rio"], r["classificacao_aplicada"]["faixa"])


class TesteValidador(unittest.TestCase):
    def estado(self, leituras=None, sc=None):
        r = cr.classificar_cidade(brusque(), leituras if leituras is not None else [leitura(3.5)],
                                  sc if sc is not None else estadual("atencao"), AGORA)
        return {"cidades": {"brusque": r}}

    def test_saida_boa_passa(self):
        self.assertEqual(cr.validar_estado(self.estado(), AGORA), [])
        self.assertEqual(cr.validar_estado(self.estado([], estadual("alerta")), AGORA), [])

    def assertErro(self, estado, trecho):
        erros = cr.validar_estado(estado, AGORA)
        self.assertTrue(any(trecho in e for e in erros), f"esperava '{trecho}' em {erros}")

    def test_regua_da_leitura_diferente_da_das_faixas(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["municipal"]["regua_da_leitura"] = "Brusque"
        self.assertErro(e, "classificada com as cotas de")

    def test_faixa_nao_confirmada_produzindo_cor(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["municipal"]["status_faixas"] = "nao_confirmada"
        self.assertErro(e, "'nao_confirmada' produzindo cor")

    def test_fonte_ausente(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["municipal"]["fonte_faixas"] = None
        self.assertErro(e, "fonte_faixas ausente")

    def test_data_futura(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["municipal"]["medido_em"] = "2026-10-07T18:00:00"
        self.assertErro(e, "no futuro")

    def test_valor_impossivel(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["municipal"]["nivel_m"] = 31.0
        self.assertErro(e, "nivel_m impossível")

    def test_estadual_rotulada_como_municipal(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["estadual"]["tipo"] = "municipal"
        self.assertErro(e, "guardada como estadual")
        e = self.estado([], estadual("alerta"))
        e["cidades"]["brusque"]["classificacao_aplicada"]["rotulo"] = "Classificação municipal — DCSC-00019"
        self.assertErro(e, "rótulo não diz que é estadual")

    def test_leitura_antiga_pintando(self):
        e = self.estado()
        e["cidades"]["brusque"]["classificacoes"]["municipal"]["status_leitura"] = "antiga"
        self.assertErro(e, "faixa com leitura 'antiga'")

    def test_estadual_sem_aviso(self):
        e = self.estado([], estadual("alerta"))
        e["cidades"]["brusque"]["classificacao_aplicada"]["aviso"] = None
        self.assertErro(e, "estadual pintando sem aviso")

    def test_faixa_do_rio_trocada(self):
        e = self.estado()
        e["cidades"]["brusque"]["faixa_do_rio"] = "emergencia"
        self.assertErro(e, "faixa_do_rio diferente")


class TestePilotoDe07De10(unittest.TestCase):
    """Decisões do Jefferson de 07/10/2026: Blumenau entra; Rio dos Cedros entra SEM classificação municipal."""

    def test_o_piloto(self):
        self.assertEqual(set(cr.CIDADES_PILOTO), {"brusque", "blumenau", "rio-dos-cedros"})
        self.assertEqual(set(cr.PILOTO_SEM_MUNICIPAL), {"rio-dos-cedros"})

    def test_rio_dos_cedros_nunca_tem_faixa_municipal_enquanto_as_cotas_nao_forem_confirmadas(self):
        rdc = cr.cidade_do_piloto(ESTACOES, "rio-dos-cedros")
        self.assertIsNot(rdc["cotas_verificado"], True)
        for nivel in (1.0, 4.8, 5.5, 9.0):
            leitura = {"estacao": "Rio dos Cedros — ponte próxima ao Paço Municipal (DCSC-00011)", "codigo": "DCSC-00011",
                       "cidade": "rio-dos-cedros", "rio": "itajai-acu", "nivel_m": nivel, "medido_em": "2026-10-07T13:00:00"}
            r = cr.classificar_municipal(rdc, [leitura], AGORA)
            self.assertIsNone(r["faixa"], f"{nivel} m")
            self.assertIn("cotas não confirmadas", r["motivo"])
            self.assertFalse(r["segura_estadual"], "sem cota confirmada, a municipal não segura a estadual")

    def test_rio_dos_cedros_no_piloto_nao_reprova_o_validador_e_outra_cidade_reprovaria(self):
        self.assertEqual(cr.validar_cadastro_piloto(ESTACOES), [])
        d = copy.deepcopy(ESTACOES)
        next(c for c in d["rios"]["itajai-mirim"]["cidades"] if c["id"] == "brusque")["cotas_verificado"] = False
        self.assertTrue(any("cotas não confirmadas" in e for e in cr.validar_cadastro_piloto(d)),
                        "a exceção é só de Rio dos Cedros")

    def test_brusque_com_cotas_confirmadas_continua_segurando_a_estadual(self):
        r = cr.classificar_municipal(brusque(), [leitura(2.0)], AGORA)
        self.assertTrue(r["segura_estadual"])

    def test_blumenau_so_pinta_pelas_publicacoes_validadas(self):
        blu = cr.cidade_do_piloto(ESTACOES, "blumenau")
        base = {"cidade": "blumenau", "rio": "itajai-acu", "nivel_m": 4.5, "medido_em": "2026-10-07T13:00:00"}
        for titulo in ("Blumenau (AlertaBlu)", "Blumenau (PADKND)"):
            r = cr.classificar_municipal(blu, [{**base, "estacao": titulo, "resgate_de": "Blumenau"}], AGORA)
            self.assertEqual(r["faixa"], "atencao", titulo)
            self.assertEqual(r["regua_nome"], "régua do AlertaBlu")
        r = cr.classificar_municipal(blu, [{**base, "estacao": "Blumenau"}], AGORA)
        self.assertIsNone(r["faixa"])
        self.assertIn("não foi validada", r["motivo"])

    def test_regua_por_titulo_sem_publicacoes_validadas_fica_no_inventario(self):
        rds = cr.cidade_do_piloto(ESTACOES, "rio-do-sul")
        self.assertTrue(any("PUBLICACOES_VALIDADAS" in p for p in cr.problemas_do_cadastro(rds)))


class TesteCadastro(unittest.TestCase):
    def test_o_piloto_esta_limpo_no_estacoes_json_real(self):
        self.assertEqual(cr.validar_cadastro_piloto(ESTACOES), [])

    def test_o_motor_nao_altera_o_estacoes_json(self):
        antes = copy.deepcopy(ESTACOES)
        cr.montar_estado(ESTACOES, {"leituras": [leitura(3.5)]}, estadual(), AGORA)
        cr.inventario(ESTACOES)
        self.assertEqual(ESTACOES, antes)

    def test_piloto_ausente_falha_alto(self):
        with self.assertRaises(ValueError):
            cr.montar_estado(ESTACOES, {}, {}, AGORA, piloto=("nao-existe",))
        self.assertTrue(cr.validar_cadastro_piloto(ESTACOES, ("nao-existe",)))

    def test_itajai_nos_dois_rios_nao_vira_piloto_por_engano(self):
        self.assertIsNone(cr.cidade_do_piloto(ESTACOES, "itajai"))


class TesteGravacao(unittest.TestCase):
    def test_saida_invalida_apaga_a_anterior_e_nao_grava(self):
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "ultimo_classificacao.json"
            saida.write_text("{}", encoding="utf-8")
            with mock.patch.object(cr, "SAIDA", saida), \
                    mock.patch.object(cr, "validar_estado", return_value=["Brusque: erro de teste"]), \
                    mock.patch.object(cr, "_le", return_value={}), mock.patch("sys.stderr"):
                self.assertEqual(cr.main(["--gravar"]), 1)
            self.assertFalse(saida.exists(), "arquivo de outra coleta não pode ficar passando por atual")

    def test_grava_quando_valida(self):
        import json
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as d:
            saida = Path(d) / "ultimo_classificacao.json"
            entradas = {cr.LEITURAS: {"leituras": [leitura(2.0, quando=None)]}, cr.NIVEL_SC: {"leituras": []}}
            with mock.patch.object(cr, "SAIDA", saida), mock.patch.object(cr, "_le", side_effect=entradas.get), \
                    mock.patch("sys.stdout"):
                self.assertEqual(cr.main(["--gravar"]), 0)
            d = json.loads(saida.read_text(encoding="utf-8"))
            self.assertEqual(d["piloto"], list(cr.CIDADES_PILOTO))
            self.assertEqual(d["cidades"]["brusque"]["classificacao_aplicada"]["tipo"], "nenhuma")


if __name__ == "__main__":
    unittest.main()
