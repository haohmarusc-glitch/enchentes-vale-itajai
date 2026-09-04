#!/usr/bin/env python3
"""Testes do portão de qualidade: as regras da topologia em árvore têm de ABORTAR.

Documentar a topologia não impediu o JSON de ficar errado por versões seguidas;
o que impediu foi o validador passar a falhar. Estes testes travam esse "falhar":
cada um estraga UM ponto dos dados reais e exige que `valida_estacoes` acuse.
"""

import copy
import json
import unittest

from comum import DADOS
import validar_dados as vd


def _cidade(estacoes, rio, cid):
    return next(c for c in estacoes["rios"][rio]["cidades"] if c["id"] == cid)


def erros_de(estacoes_dict) -> list[str]:
    """Roda só `valida_estacoes` sobre um estacoes.json em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json
    vd.le_json = lambda nome: estacoes_dict if nome == "estacoes.json" else orig(nome)
    try:
        vd.valida_estacoes()
    finally:
        vd.le_json = orig
    return list(vd.erros)


class TopologiaArvore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def base(self):
        return copy.deepcopy(self.real)

    def test_dados_reais_passam(self):
        self.assertEqual(erros_de(self.base()), [], "o estacoes.json real deveria passar limpo")

    def test_ordem_global_em_rio_ramificado_aborta(self):
        d = self.base()
        _cidade(d, "itajai-acu", "taio")["ordem"] = 1  # a bacia é árvore: ordem tem de ser null
        self.assertTrue(any("ordem' global" in e for e in erros_de(d)), "ordem global no Açu deveria falhar")

    def test_ramo_ausente_em_rio_ramificado_aborta(self):
        d = self.base()
        del _cidade(d, "itajai-acu", "rio-do-sul")["ramo"]
        self.assertTrue(any("ramo' ausente" in e for e in erros_de(d)))

    def test_ramo_em_rio_em_fila_aborta(self):
        # Mirim é fila: pôr ramo nele mistura árvore e fila.
        d = self.base()
        _cidade(d, "itajai-mirim", "brusque")["ramo"] = "tronco_acu"
        self.assertTrue(any("não se misturam" in e for e in erros_de(d)))

    def test_codigo_dcsc_trocado_aborta(self):
        d = self.base()
        _cidade(d, "itajai-acu", "taio")["codigo_dcsc"] = "DCSC-99999"
        self.assertTrue(any("codigo_dcsc deveria ser" in e for e in erros_de(d)))

    def test_codigo_dcsc_some_com_a_cidade_aborta(self):
        d = self.base()
        cid = d["rios"]["itajai-acu"]["cidades"]
        d["rios"]["itajai-acu"]["cidades"] = [c for c in cid if c["id"] != "ascurra"]
        self.assertTrue(any("sumiu do eixo" in e for e in erros_de(d)))

    def test_tronco_sequencia_fora_de_ordem_aborta(self):
        d = self.base()
        seq = d["rios"]["itajai-acu"]["_topologia"]["tronco_sequencia"]
        seq[1], seq[2] = seq[2], seq[1]  # troca ascurra <-> indaial
        self.assertTrue(any("não bate" in e for e in erros_de(d)))

    def test_ordem_no_ramo_furada_aborta(self):
        d = self.base()
        _cidade(d, "itajai-acu", "indaial")["ordem_no_ramo"] = 9  # buraco no tronco
        self.assertTrue(any("ordem_no_ramo" in e for e in erros_de(d)))

    def test_regua_sem_aviso_precisa_de_motivo(self):
        d = self.base()
        d["estacoes_tempo_real"].append({
            "titulo": "Régua de teste sem motivo",
            "rio": "itajai-acu", "cidade": "itajai",
            "cotas_m": {"atencao": 1.0}, "verificado": True,
            "alerta_automatico": False,
        })
        self.assertTrue(any("motivo_sem_alerta" in e for e in erros_de(d)))


def _monotonia(estacoes_dict, transito_dict) -> tuple[list[str], list[str]]:
    """Roda só `valida_monotonia_transito` sobre dados em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json

    def falso(nome):
        if nome == "estacoes.json":
            return estacoes_dict
        if nome == "transito.json":
            return transito_dict
        return orig(nome)

    vd.le_json = falso
    try:
        vd.valida_monotonia_transito()
    finally:
        vd.le_json = orig
    return list(vd.erros), list(vd.avisos)


class MonotoniaDaJanela(unittest.TestCase):
    """
    A janela de chegada contra a ordem do rio.

    A distinção que estes testes travam: SOBREPOSIÇÃO não é CONTRADIÇÃO. Tratar
    as duas igual empurraria alguém a "consertar" o dado trocando valor de fonte
    publicada por interpolação — perder dado achando que ganha precisão.
    """

    @classmethod
    def setUpClass(cls):
        cls.estacoes = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.transito = json.loads((DADOS / "transito.json").read_text(encoding="utf-8"))

    def base(self):
        return copy.deepcopy(self.estacoes), copy.deepcopy(self.transito)

    def test_dados_reais_nao_tem_contradicao(self):
        erros, _ = _monotonia(*self.base())
        self.assertEqual(erros, [], "o transito.json real não deveria ter janela impossível")

    def test_a_sobreposicao_conhecida_sai_como_aviso_e_nao_erro(self):
        # Indaial 10-10 h x Blumenau 7-10 h: a de baixo COMEÇA antes, mas
        # 10 <= 10, então existe atribuição consistente. Aviso, nunca erro.
        erros, avisos = _monotonia(*self.base())
        self.assertEqual(erros, [])
        self.assertTrue(
            any("blumenau" in a and "indaial" in a for a in avisos),
            "a sobreposição Blumenau/Indaial deveria aparecer como aviso",
        )

    def test_inversao_forte_avisa_mas_NAO_e_erro(self):
        """
        Corrigido em 04/09/2026 pela Tabela 7.5.1 da JICA (Vol. III-A, p. A-80).

        Este teste exigia ERRO quando o montante passa do máximo do jusante,
        sob a premissa de que "não existe tempo que satisfaça as duas janelas".
        A premissa é falsa: nas colunas de 25 e 50 anos da tabela, Blumenau
        (jusante) pica ANTES de Indaial (montante) — o Rio Benedito entra em
        Indaial e adianta o pico de baixo. Manter como erro rejeitaria dado
        oficial verdadeiro.

        Continua avisando, e o aviso diz que nem chega a encostar — que é a
        informação útil para quem for conferir.
        """
        est, tr = self.base()
        for t in tr["trechos"]:
            if t["de"] == "rio-do-sul" and t["para"] == "indaial":
                t["horas_min"] = t["horas_max"] = 11
        erros, avisos = _monotonia(est, tr)
        self.assertEqual(erros, [], "inversão não pode abortar: a JICA tem uma real")
        self.assertTrue(any("nem chega a encostar" in a for a in avisos))

    def test_o_aviso_nomeia_as_tres_causas_possiveis(self):
        # Quem for arrumar precisa saber se é mistura de coluna, afluente no
        # meio, ou dado errado — sem isso, "consertar" vira trocar fonte por
        # interpolação, que é perder dado.
        _, avisos = _monotonia(*self.base())
        self.assertTrue(avisos)
        for pista in ("COLUNAS diferentes", "afluente", "dado errado"):
            self.assertTrue(any(pista in a for a in avisos), f"o aviso não fala de '{pista}'")

    def test_empate_no_limite_ainda_passa(self):
        # min_montante == max_jusante é o empate que o hidrograma afirma
        # (Indaial e Blumenau na mesma hora). Não pode virar erro.
        est, tr = self.base()
        for t in tr["trechos"]:
            if t["de"] == "rio-do-sul" and t["para"] == "indaial":
                t["horas_min"] = t["horas_max"] = 10
        erros, _ = _monotonia(est, tr)
        self.assertEqual(erros, [])

    def test_segue_a_mesma_busca_do_site(self):
        # Gaspar não tem trecho direto desde Rio do Sul: a janela sai da cadeia
        # rio-do-sul -> blumenau -> gaspar. Se a busca divergir da do site, o
        # validador aprovaria um percurso que a tela não usa.
        _, tr = self.base()
        self.assertEqual(
            vd._janela_ate(tr["trechos"], "itajai-acu", "rio-do-sul", "gaspar"), (9, 12)
        )


def _meses(estacoes_dict, enchentes_dict) -> list[str]:
    """Roda só `valida_meses_pareados` sobre dados em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json

    def falso(nome):
        if nome == "estacoes.json":
            return estacoes_dict
        if nome == "enchentes.json":
            return enchentes_dict
        return orig(nome)

    vd.le_json = falso
    try:
        vd.valida_meses_pareados()
    finally:
        vd.le_json = orig
    return list(vd.avisos)


class MesesPareados(unittest.TestCase):
    """
    Duas cidades do tronco no mesmo evento registram no mesmo mês.

    A cheia desce o Açu em horas (Rio do Sul → Blumenau, 7 a 10 h). Mês
    diferente não é imprecisão: são eventos distintos, ou uma data está errada.
    """

    @classmethod
    def setUpClass(cls):
        cls.estacoes = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.enchentes = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))

    def base(self):
        return copy.deepcopy(self.estacoes), copy.deepcopy(self.enchentes)

    def test_nunca_vira_erro(self):
        # A data pode estar certa e ser evento distinto — quem decide é a fonte.
        _meses(*self.base())
        self.assertEqual(vd.erros, [])

    def test_1911_e_o_unico_desalinhado_nos_dados_reais(self):
        avisos = _meses(*self.base())
        self.assertEqual(len(avisos), 1, f"esperava só 1911 desalinhado, veio: {avisos}")
        self.assertIn("rio-do-sul 1911-05", avisos[0])
        self.assertIn("1911-10-02", avisos[0])

    def test_um_so_evento_de_jusante_no_mesmo_mes_ja_alinha(self):
        # Blumenau tem 113 registros, vários por ano: a cheia de montante casa
        # com UMA delas. Exigir que todas batessem alarmaria sobre dado correto.
        est, enc = self.base()
        enc["eventos"] = [
            {"rio": "itajai-acu", "cidade": "rio-do-sul", "data": "1954-10", "pico_m": 10.7},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1954-05-08", "pico_m": 9.56},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1954-10-22", "pico_m": 12.53},
        ]
        self.assertEqual(_meses(est, enc), [])

    def test_mes_diferente_em_todos_avisa(self):
        est, enc = self.base()
        enc["eventos"] = [
            {"rio": "itajai-acu", "cidade": "rio-do-sul", "data": "1911-05", "pico_m": 12.2},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1911-10-02", "pico_m": 16.9},
        ]
        avisos = _meses(est, enc)
        self.assertEqual(len(avisos), 1)
        self.assertIn("não tem evento de blumenau no mesmo mês", avisos[0])

    def test_ano_sem_registro_a_jusante_nao_conclui_nada(self):
        # Ausência de registro é ausência de dado, não desalinhamento.
        est, enc = self.base()
        enc["eventos"] = [
            {"rio": "itajai-acu", "cidade": "rio-do-sul", "data": "1911-05", "pico_m": 12.2},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1984-08-07", "pico_m": 15.46},
        ]
        self.assertEqual(_meses(est, enc), [])

    def test_data_so_com_ano_e_ignorada(self):
        # Sem mês não há mês para comparar; recusar seria inventar precisão.
        est, enc = self.base()
        enc["eventos"] = [
            {"rio": "itajai-acu", "cidade": "rio-do-sul", "data": "1911", "pico_m": 12.2},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1911-10-02", "pico_m": 16.9},
        ]
        self.assertEqual(_meses(est, enc), [])

    def test_cidade_fora_do_tronco_nao_entra_na_conferencia(self):
        # Taió é cabeceira: o pico dela ENTRA no tronco, e comparar mês com
        # Blumenau afirmaria uma fila que a topologia nega.
        est, enc = self.base()
        enc["eventos"] = [
            {"rio": "itajai-acu", "cidade": "taio", "data": "1911-05", "pico_m": 12.2},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1911-10-02", "pico_m": 16.9},
        ]
        self.assertEqual(_meses(est, enc), [])


def _hidraulica(d) -> tuple[list[str], list[str]]:
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json
    vd.le_json = lambda nome: d if nome == "hidraulica.json" else orig(nome)
    try:
        vd.valida_hidraulica()
    finally:
        vd.le_json = orig
    return list(vd.erros), list(vd.avisos)


class Hidraulica(unittest.TestCase):
    """
    O dado do JICA que explica a bacia — e as travas que o mantêm honesto.

    Não se confere o VALOR aqui (não temos o PDF): confere-se que cada bloco
    continue com fonte, que as duas delimitações de área das barragens sigam
    lado a lado, e que um número recusado pela auditoria não volte como valor.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "hidraulica.json").read_text(encoding="utf-8"))

    def base(self):
        return copy.deepcopy(self.real)

    def test_o_arquivo_real_passa(self):
        erros, _ = _hidraulica(self.base())
        self.assertEqual(erros, [])

    def test_bloco_sem_fonte_aborta(self):
        d = self.base()
        d["capacidade_de_vazao"].pop("_fonte")
        self.assertTrue(any("_fonte" in e for e in _hidraulica(d)[0]))

    def test_as_duas_areas_de_drenagem_tem_de_coexistir(self):
        # JICA diz 1.042 km² para a Oeste; a API estadual diz 851. São
        # delimitações diferentes — fundir seria escolher em silêncio.
        d = self.base()
        d["barragens"]["oeste"].pop("area_drenagem_km2_api_estadual")
        erros, _ = _hidraulica(d)
        self.assertTrue(any("escolher em silêncio" in e for e in erros))

    def test_o_retorno_de_8400_anos_nao_pode_voltar_como_valor(self):
        # A auditoria não achou esse número nas páginas conferidas; o que o
        # Vol. III cita para 1 dia em Blumenau é 270 anos.
        d = self.base()
        d["periodos_de_retorno"]["2008_retorno_anos"] = 8400
        self.assertTrue(any("8.400 aparece como VALOR" in e for e in _hidraulica(d)[0]))

    def test_mas_CITAR_o_numero_no_texto_com_a_ressalva_e_permitido(self):
        """
        O guarda anterior procurava a string e acusava a própria advertência —
        o texto que manda NÃO gravar 8.400 cita 8.400. Falso positivo real,
        pego quando o validador reprovou o arquivo que ele deveria aprovar.
        """
        d = self.base()
        texto = json.dumps(d, ensure_ascii=False)
        self.assertIn("8.400", texto, "a ressalva sobre o número sumiu do arquivo")
        self.assertEqual(_hidraulica(d)[0], [], "citar na prosa não pode ser erro")

    def test_curva_chave_recusa_par_incompleto(self):
        d = self.base()
        d["curva_chave_2008"]["pontos"][0].pop("vazao_m3s")
        self.assertTrue(any("vazao_m3s" in e for e in _hidraulica(d)[0]))

    def test_curva_chave_recusa_nivel_implausivel(self):
        # 115 m não é régua de rio desta bacia — seria vírgula fora do lugar.
        d = self.base()
        d["curva_chave_2008"]["pontos"][0]["nivel_m"] = 115.0
        self.assertTrue(any("fora de faixa plausível" in e for e in _hidraulica(d)[0]))

    def test_a_divisao_do_mirim_NAO_entrou_na_topologia(self):
        """
        Trava a decisão, não só o dado.

        Gravar 2/3–1/3 em `estacoes.json._topologia` do Mirim parece natural e
        quebraria o rio inteiro: é a presença desse campo que faz o validador
        tratar o rio como RAMIFICADO, passando a exigir ramo/ordem_no_ramo em
        todas as cidades — e o Mirim é fila, com `ordem` 1..N.
        """
        est = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        self.assertNotIn("_topologia", est["rios"]["itajai-mirim"],
                         "o Mirim é fila; _topologia o tornaria ramificado")
        self.assertIn("divisao_do_mirim", self.real)

if __name__ == "__main__":
    unittest.main()
