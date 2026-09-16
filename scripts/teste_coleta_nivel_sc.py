#!/usr/bin/env python3
"""
Testes do coletor de NÍVEL BRUTO da rede estadual (Defesa Civil de SC).

A chamada de rede não roda aqui (o host não é alcançável do container); o que se
testa é o `converter`, onde moram os riscos: o fuso (errar desloca a idade em
três horas), a separação em baldes (leitura / sem_leitura / suspeita) e a regra
de fundo — nível BRUTO, `usar_para_cota` SEMPRE False, nunca comparado com cota
municipal sem offset calibrado.

    python3 scripts/teste_coleta_nivel_sc.py
"""

import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import coleta_nivel_sc
from coleta_nivel_sc import acumular_serie, buscar, converter, e_numero, hora_local


def estacao(codigo="DCSC-00006", nome="SDC-SC Indaial", local="",
            bacia="SC - Rio Itajaí-Açu", nivel=6.86, chuva24=13.5,
            carimbo="2026-09-01T23:42:54+00:00",
            tipo=None, tem_nivel_do_rio=None, rio_nome=None, rio_area_drenagem=None,
            alarmes=None):
    d = {
        "codigo": codigo,
        "name": {"general": nome, "local": local},
        "timestamp": carimbo,
        "position": {"bacia": bacia, "latitude": -26.9, "longitude": -49.2},
        "data": {
            "rio": {"rio_nivel": {"value": nivel}, "rio_nome": rio_nome,
                    "rio_area_drenagem": rio_area_drenagem},
            "chuva": {"acumulado": {"h024": None if chuva24 is None else {"value": chuva24}}},
        },
    }
    if tipo is not None:
        d["type"] = tipo
    if tem_nivel_do_rio is not None:
        d["filter"] = {"relacao": {"tem_nivel_do_rio": tem_nivel_do_rio}}
    if alarmes is not None:
        d["data"]["rio"]["rio_alarmes"] = {"inundacao": alarmes}
    return d


def alarme(ativo=1, atencao=0, alerta=0, emergencia=0, status=None):
    """O bloco `rio_alarmes.inundacao` como a API o publica: cada campo em {value}."""
    return {"ativo": {"value": ativo}, "status": {"value": status},
            "atencao": {"value": atencao}, "alerta": {"value": alerta}, "emergencia": {"value": emergencia}}


class TestFuso(unittest.TestCase):
    """UTC do GraphQL -> hora de Brasília sem fuso, o formato do projeto (CLAUDE.md)."""

    def test_converte_utc_para_brasilia(self):
        self.assertEqual(hora_local("2026-09-01T23:42:54+00:00"), "2026-09-01T20:42:54")

    def test_a_diferenca_e_de_tres_horas(self):
        # Se isto quebrar, a idade de toda leitura sai errada em 3 h.
        self.assertEqual(hora_local("2026-08-31T12:00:00+00:00"), "2026-08-31T09:00:00")

    def test_vira_o_dia_para_tras(self):
        self.assertEqual(hora_local("2026-08-31T01:00:00+00:00"), "2026-08-30T22:00:00")

    def test_a_leitura_sai_em_horario_de_brasilia(self):
        leituras, _, _, _ = converter([estacao()])
        self.assertEqual(leituras[0]["medido_em"], "2026-09-01T20:42:54",
                         "medido_em é Brasília sem fuso, não o UTC cru do GraphQL")

    def test_carimbo_ilegivel_nao_vira_hora(self):
        self.assertIsNone(hora_local(None))
        self.assertIsNone(hora_local("ontem"))


class TestBaldes(unittest.TestCase):
    def test_indaial_vira_leitura(self):
        leituras, sem, susp, nao_mede = converter([estacao()])
        self.assertEqual(len(leituras), 1)
        self.assertEqual((sem, susp, nao_mede), ([], [], []))
        l = leituras[0]
        self.assertEqual(l["cidade"], "indaial")
        self.assertEqual(l["nivel_bruto_m"], 6.86)

    def test_value_null_de_estacao_comum_vai_para_sem_leitura(self):
        """Estação comum com sensor que às vezes vem null: é 'sem leitura agora', não some."""
        leituras, sem, susp, nao_mede = converter([estacao(nivel=None)])  # Indaial, fora de NAO_MEDE_NIVEL
        self.assertEqual(leituras, [])
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0]["cidade"], "indaial")

    def test_gaspar_vai_para_nao_mede_nivel_nao_para_sem_leitura(self):
        """Gaspar: tem_nivel_do_rio=false na API (03/09/2026) — não é 'sensor mudo agora', é
        ausência estrutural. Não deve mais cair em sem_leitura mesmo com value null."""
        leituras, sem, susp, nao_mede = converter([estacao(codigo="DCSC-00005", nome="SDC-SC Gaspar", nivel=None)])
        self.assertEqual(leituras, [])
        self.assertEqual(sem, [])
        self.assertEqual(len(nao_mede), 1)
        self.assertEqual(nao_mede[0]["cidade"], "gaspar")
        self.assertIn("tem_nivel_do_rio", nao_mede[0]["motivo"])

    def test_blumenau_vai_para_nao_mede_nivel(self):
        """Blumenau: type=Meteo, tem_nivel_do_rio=false — estação meteorológica, não de rio."""
        leituras, sem, susp, nao_mede = converter([estacao(codigo="DCSC-00026", nome="SDC-SC Blumenau", nivel=None)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(nao_mede), 1)
        self.assertEqual(nao_mede[0]["cidade"], "blumenau")

    def test_estacao_H_e_descartada(self):
        """'(H)' reporta altitude, não rio: não entra em balde nenhum."""
        leituras, sem, susp, nao_mede = converter([estacao(nome="SDC-SC Salete (H)", nivel=399.0)])
        self.assertEqual((leituras, sem, susp, nao_mede), ([], [], [], []))

    def test_guabiruba_e_suspeita_por_datum_nao_por_sensor_errado(self):
        leituras, sem, susp, nao_mede = converter([estacao(codigo="DCSC-00029", nome="SDC-SC Guabiruba", nivel=24.91)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(susp), 1)
        self.assertEqual(susp[0]["cidade"], "guabiruba")
        # Correção de 03/09: é estação Hidro real (tem_nivel_do_rio=true) — problema é datum, não sensor.
        self.assertIn("datum", susp[0]["motivo"])
        self.assertNotIn("grandeza errada", susp[0]["motivo"])

    def test_barragem_tem_datum_reservatorio(self):
        leituras, _, _, _ = converter([estacao(codigo="DCSC-00040", nome="SDC-SC Barragem Oeste", nivel=12.0)])
        self.assertEqual(leituras[0]["datum"], "reservatorio")

    def test_bacia_null_nao_quebra_e_estacao_de_fora_fica_de_fora(self):
        """position.bacia null não estoura; e sem 'Itaja' a estação não entra."""
        leituras, sem, susp, nao_mede = converter([estacao(bacia=None)])
        self.assertEqual((leituras, sem, susp, nao_mede), ([], [], [], []))

    def test_valor_absurdo_vai_para_suspeita(self):
        leituras, sem, susp, nao_mede = converter([estacao(nivel=50.0)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(susp), 1)

    def test_booleano_nao_e_metro(self):
        """rio_nivel.value booleano (armadilha 1) não vira 1,00 m — vai para sem_leitura."""
        leituras, sem, susp, nao_mede = converter([estacao(nivel=True)])
        self.assertEqual(leituras, [])
        self.assertEqual(len(sem), 1)


class TestCamposNovosDaAPI(unittest.TestCase):
    """
    Quando QUERY_CAMPOS_NOVOS é aceita, a API DECLARA tem_nivel_do_rio — e isso
    tem prioridade sobre os dicionários hardcoded (NAO_MEDE_NIVEL/SUSPEITAS),
    inclusive para estações que os dicionários ainda não conhecem.
    """

    def test_tem_nivel_do_rio_false_vai_para_nao_mede_nivel_mesmo_fora_do_dicionario(self):
        # Um código qualquer, não cadastrado em NAO_MEDE_NIVEL: a declaração da API basta.
        leituras, sem, susp, nao_mede = converter(
            [estacao(codigo="DCSC-99998", nome="SDC-SC Nova", tipo="Meteo", tem_nivel_do_rio=False)]
        )
        self.assertEqual(leituras, [])
        self.assertEqual(sem, [])
        self.assertEqual(len(nao_mede), 1)
        self.assertIn("tem_nivel_do_rio=false", nao_mede[0]["motivo"])
        self.assertIn("Meteo", nao_mede[0]["motivo"])
        self.assertEqual(nao_mede[0]["tipo_estacao"], "Meteo")

    def test_declaracao_da_api_vence_o_dicionario_hardcoded_quando_diverge(self):
        # Gaspar está em NAO_MEDE_NIVEL, mas se a API agora declarar tem_nivel_do_rio=true
        # (ex.: sensor reativado), a leitura deve valer — a fonte viva manda, não o hardcode.
        leituras, sem, susp, nao_mede = converter(
            [estacao(codigo="DCSC-00005", nome="SDC-SC Gaspar", nivel=3.5,
                      tipo="Hidro", tem_nivel_do_rio=True)]
        )
        self.assertEqual(nao_mede, [])
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0]["nivel_bruto_m"], 3.5)

    def test_sem_campos_novos_cai_no_dicionario_hardcoded(self):
        # Sem type/filter na resposta (QUERY original), o comportamento é o de sempre.
        leituras, sem, susp, nao_mede = converter([estacao(codigo="DCSC-00005", nome="SDC-SC Gaspar", nivel=None)])
        self.assertEqual(len(nao_mede), 1)
        self.assertIsNone(nao_mede[0]["tipo_estacao"])

    def test_rio_nome_e_area_drenagem_passam_para_a_leitura(self):
        leituras, _, _, _ = converter([estacao(rio_nome="Itajaí do Sul", rio_area_drenagem=1164.0)])
        self.assertEqual(leituras[0]["rio_nome"], "Itajaí do Sul")
        self.assertEqual(leituras[0]["rio_area_drenagem_km2"], 1164.0)


class TestBuscarFallback(unittest.TestCase):
    """
    buscar() tenta QUERY_CAMPOS_NOVOS primeiro; se a API recusar (GraphQL 'errors' —
    a allowlist de query persistida pode rejeitar qualquer string que não seja a exata
    do bundle), cai para a QUERY original de 01/09. Nunca escolhe às cegas: é a resposta
    real, na primeira execução contra o host de verdade, que decide.
    """

    @staticmethod
    def _resposta(ok=True):
        m = unittest.mock.Mock()
        m.raise_for_status = unittest.mock.Mock()
        corpo = (
            {"data": {"tags_data": {"qualle_meteorologia": [{"codigo": "X"}]}}}
            if ok else {"errors": ["allowlist recusou a query"]}
        )
        m.json = unittest.mock.Mock(return_value=corpo)
        return m

    def test_usa_a_enriquecida_direto_quando_aceita(self):
        with unittest.mock.patch.object(coleta_nivel_sc.requests, "post",
                                         return_value=self._resposta(ok=True)) as m:
            est = buscar()
        self.assertEqual(est, [{"codigo": "X"}])
        self.assertEqual(m.call_count, 1, "aceitou de primeira, não devia tentar a original")
        self.assertIn("rio_alarmes", m.call_args.kwargs["json"]["query"])

    def test_cai_para_a_original_quando_a_api_recusa_a_enriquecida(self):
        with unittest.mock.patch.object(
            coleta_nivel_sc.requests, "post",
            side_effect=[self._resposta(ok=False), self._resposta(ok=True)],
        ) as m:
            est = buscar()
        self.assertEqual(est, [{"codigo": "X"}])
        self.assertEqual(m.call_count, 2)
        primeira, segunda = m.call_args_list
        self.assertIn("rio_alarmes", primeira.kwargs["json"]["query"])
        self.assertNotIn("tem_nivel_do_rio", segunda.kwargs["json"]["query"])

    def test_propaga_erro_se_as_duas_falharem(self):
        with unittest.mock.patch.object(coleta_nivel_sc.requests, "post",
                                         return_value=self._resposta(ok=False)):
            with self.assertRaises(RuntimeError):
                buscar()


class TestRegraDeFundo(unittest.TestCase):
    def test_toda_leitura_e_bruta_e_nao_serve_para_cota(self):
        leituras, _, _, _ = converter([estacao(), estacao(codigo="DCSC-00040", nome="SDC-SC Barragem", nivel=9.0)])
        self.assertTrue(leituras)
        for l in leituras:
            self.assertFalse(l["usar_para_cota"], "nível estadual nunca vira cota sem offset calibrado")
            self.assertEqual(l["origem"], "estadual")
            self.assertIsNone(l["offset_datum"])
            self.assertIn(l["datum"], ("bruto_estadual", "reservatorio"))


class TestCadeia(unittest.TestCase):
    def test_estacao_fora_da_cadeia_entra_sem_cidade(self):
        leituras, _, _, _ = converter([estacao(codigo="DCSC-99999", nome="SDC-SC Outra")])
        self.assertEqual(len(leituras), 1)
        self.assertIsNone(leituras[0]["cidade"])

    def test_so_cadeia_recusa_estacao_fora_do_mapa(self):
        leituras, _, _, _ = converter([estacao(codigo="DCSC-99999", nome="SDC-SC Outra")], so_cadeia=True)
        self.assertEqual(leituras, [])


class TestSerie(unittest.TestCase):
    """A série ndjson acumula sem duplicar — é a matéria-prima do offset."""

    def test_acumula_uma_vez_e_deduplica_na_segunda(self):
        leituras, _, _, _ = converter([estacao()])
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(coleta_nivel_sc, "SAIDA", Path(d)):
                self.assertEqual(acumular_serie(leituras), (1, 0))
                self.assertEqual(acumular_serie(leituras), (0, 1))   # mesma leitura: repetida
                arq = Path(d) / "nivel-sc-2026-09.ndjson"            # mês de medido_em (Brasília)
                self.assertTrue(arq.exists())
                linhas = [x for x in arq.read_text(encoding="utf-8").splitlines() if x.strip()]
                self.assertEqual(len(linhas), 1)

    def test_leitura_sem_carimbo_nao_entra(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(coleta_nivel_sc, "SAIDA", Path(d)):
                self.assertEqual(acumular_serie([{"codigo": "X", "nivel_bruto_m": 1.0, "medido_em": None}]),
                                 (0, 0))


class TestENumero(unittest.TestCase):
    def test_booleano_nao_e_numero(self):
        self.assertFalse(e_numero(True))
        self.assertTrue(e_numero(0))
        self.assertTrue(e_numero(6.86))
        self.assertFalse(e_numero(None))
        self.assertFalse(e_numero("6.86"))




class TestChuvaSemanal(unittest.TestCase):
    def test_semana_publicada_nao_e_soma_de_janelas(self):
        s = estacao()
        for valor, esperado in [(127.84, 127.84), (0, 0), (None, None), (-1, None), (True, None), (float('nan'), None), (float('inf'), None)]:
            s['data']['chuva']['acumulado']['h168'] = {'value': valor}
            leituras, *_ = converter([s])
            self.assertEqual(leituras[0]['chuva_168h_mm'], esperado)
    def test_arquivo_antigo_nao_inventa_semana(self):
        leituras, *_ = converter([estacao()])
        self.assertIsNone(leituras[0]['chuva_168h_mm'])



class TestClassificacaoEstadual(unittest.TestCase):
    """C7: a faixa que a Defesa Civil de SC publica, com as condições do Jefferson (14/09/2026)."""

    def leitura(self, **alarmes):
        leituras, *_ = converter([estacao(codigo="DCSC-00013", nome="SDC-SC Rio do Sul",
                                          nivel=5.46, alarmes=alarme(**alarmes))])
        self.assertEqual(len(leituras), 1)
        return leituras[0]["classificacao_estadual"]

    def test_uma_flag_ligada_e_ativo_vira_faixa(self):
        for nome, kw in (("atencao", {"atencao": 1, "status": 2}),
                         ("alerta", {"alerta": 1, "status": 1}),
                         ("emergencia", {"emergencia": 1})):
            with self.subTest(nome):
                c = self.leitura(**kw)
                self.assertEqual(c["faixa"], nome)
                self.assertTrue(c["ativo"] and c["coerente"])
                self.assertIsNone(c["motivo"])
                self.assertIn("Defesa Civil de SC", c["fonte"])

    def test_sem_faixas_configuradas_fica_cinza_mesmo_com_flag(self):
        c = self.leitura(ativo=0, alerta=1)
        self.assertIsNone(c["faixa"])
        self.assertFalse(c["ativo"])
        self.assertIn("sem faixas configuradas", c["motivo"])

    def test_duas_flags_e_contraditorio_e_fica_cinza(self):
        c = self.leitura(atencao=1, emergencia=1)
        self.assertIsNone(c["faixa"])
        self.assertFalse(c["coerente"])
        self.assertIn("contraditório", c["motivo"])

    def test_ativo_sem_flag_e_normal(self):
        """Validado na VPS em 14/09/2026: Brusque 1,73 m veio ativo=true sem flag, status 0."""
        c = self.leitura(status=0)
        self.assertEqual(c["faixa"], "normal")
        self.assertIsNone(c["motivo"])

    def test_ascurra_sem_faixas_do_estado_e_o_que_a_compdec_disse(self):
        """Ascurra 8,26 m veio ativo=false: o estado não tem faixas para ela — bate com o C18."""
        leituras, *_ = converter([estacao(codigo="DCSC-00003", nome="SDC-SC Ascurra", nivel=8.26,
                                          alarmes=alarme(ativo=0, status=0))])
        c = leituras[0]["classificacao_estadual"]
        self.assertIsNone(c["faixa"])
        self.assertIn("ativo=false", c["motivo"])

    def test_sem_rio_alarmes_na_resposta_fica_none(self):
        leituras, *_ = converter([estacao(codigo="DCSC-00013", nivel=5.46)])
        self.assertIsNone(leituras[0]["classificacao_estadual"], "query antiga (fallback) não traz alarmes")

    def test_status_so_registrado_nunca_decide(self):
        c = self.leitura(alerta=1, status=99)
        self.assertEqual(c["faixa"], "alerta")
        self.assertEqual(c["status"], 99)

    def test_serie_guarda_a_faixa(self):
        leituras, *_ = converter([estacao(codigo="DCSC-00013", nivel=5.46, alarmes=alarme(atencao=1))])
        self.assertEqual(coleta_nivel_sc._linha_serie(leituras[0])["faixa_estadual"], "atencao")

    def test_query_enriquecida_pede_alarmes_e_a_antiga_nao(self):
        self.assertIn("rio_alarmes", coleta_nivel_sc.QUERY_CAMPOS_NOVOS)
        self.assertNotIn("rio_alarmes", coleta_nivel_sc.QUERY, "o fallback validado em 01/09 não muda")

    def test_query_enriquecida_tem_a_forma_que_passou_no_host_em_13_09(self):
        """HTTP 400 em 14/09: `rio_nome`/`rio_area_drenagem` são objetos e exigem `{ value }`;
        `filter { relacao }` não existe no levantamento por introspecção."""
        q = coleta_nivel_sc.QUERY_CAMPOS_NOVOS
        self.assertIn("rio_nome { value }", q)
        self.assertIn("rio_area_drenagem { value }", q)
        self.assertNotIn("filter", q)
        self.assertIn("rio_alarmes { inundacao { ativo { value } status { value } "
                      "atencao { value } alerta { value } emergencia { value } } }", q)

    def test_rio_nome_como_objeto_ou_cru(self):
        leituras, *_ = converter([estacao(codigo="DCSC-00013", nivel=5.0, rio_nome={"value": "Rio Itajaí-Açu"},
                                          rio_area_drenagem={"value": 5100})])
        self.assertEqual(leituras[0]["rio_nome"], "Rio Itajaí-Açu")
        self.assertEqual(leituras[0]["rio_area_drenagem_km2"], 5100)
        leituras, *_ = converter([estacao(codigo="DCSC-00013", nivel=5.0, rio_nome="cru")])
        self.assertEqual(leituras[0]["rio_nome"], "cru")

    def test_nada_disto_entra_em_leituras_do_site(self):
        """O bot só lê `leituras` do ultimo.json; a classificação vive no ultimo_nivel_sc.json."""
        import coleta_estadual_com_cota as cec
        leituras, *_ = converter([estacao(codigo="DCSC-00013", nivel=5.46, alarmes=alarme(emergencia=1))])
        self.assertEqual(cec.montar(leituras), [], "Rio do Sul não tem cota na própria régua estadual")

if __name__ == "__main__":
    unittest.main(verbosity=2)
