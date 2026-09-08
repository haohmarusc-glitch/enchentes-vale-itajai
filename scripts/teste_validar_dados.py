#!/usr/bin/env python3
"""Testes do portão de qualidade: as regras da topologia em árvore têm de ABORTAR.

Documentar a topologia não impediu o JSON de ficar errado por versões seguidas;
o que impediu foi o validador passar a falhar. Estes testes travam esse "falhar":
cada um estraga UM ponto dos dados reais e exige que `valida_estacoes` acuse.
"""

import copy
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

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

    #: Os desalinhamentos que o cadastro REAL tem hoje, cada um com o motivo.
    #: Enumerar em vez de contar é o que faz um desalinhamento NOVO reprovar:
    #: "pelo menos N" aceitaria qualquer coisa que entrasse depois.
    DESALINHADOS_CONHECIDOS = {
        # A data de 1911 de Rio do Sul (05) não bate com nenhuma de jusante no
        # mesmo mês. Pendência antiga, anterior a Indaial.
        ("rio-do-sul 1911-05", "indaial"),
        ("rio-do-sul 1911-05", "blumenau"),
        # Entraram com os 16 picos de Indaial em 06/09/2026, do PDF da COMPDEC.
        # São sinal para conferir na fonte, NÃO para trocar a data: corrigir por
        # plausibilidade seria inventar medição.
        ("indaial 1927-11-09", "blumenau"),
        # Esta é a que a própria fonte pediu para conferir. Mantida literal.
        ("indaial 2014-09-08", "blumenau"),
    }

    def test_os_desalinhados_dos_dados_reais_sao_EXATAMENTE_os_conhecidos(self):
        avisos = _meses(*self.base())
        achados = set()
        for a in avisos:
            for montante, jusante in self.DESALINHADOS_CONHECIDOS:
                if montante in a and f"evento de {jusante}" in a:
                    achados.add((montante, jusante))
        novos = [a for a in avisos if not any(
            m in a and f"evento de {j}" in a for m, j in self.DESALINHADOS_CONHECIDOS)]
        self.assertEqual(novos, [], "desalinhamento NOVO: conferir na fonte antes de aceitar")
        self.assertEqual(
            achados, self.DESALINHADOS_CONHECIDOS,
            "um desalinhamento conhecido sumiu — se foi resolvido, tirar daqui com a fonte que resolveu")

    def test_a_excecao_de_lista_esparsa_e_estreita_e_tem_motivo(self):
        """
        `LISTAS_SO_COM_CHEIA_GRANDE` é uma porta na trava, e porta sem tranca
        vira corredor. Duas coisas a seguram: cada entrada precisa de MOTIVO
        escrito, e a lista precisa continuar curta — se um dia meia bacia
        estiver aqui, a trava não protege mais nada.
        """
        self.assertIn("gaspar", vd.LISTAS_SO_COM_CHEIA_GRANDE)
        self.assertLessEqual(len(vd.LISTAS_SO_COM_CHEIA_GRANDE), 3,
                             "excecoes demais: a trava deixou de valer")
        for cidade, motivo in vd.LISTAS_SO_COM_CHEIA_GRANDE.items():
            self.assertGreater(len(motivo), 60, f"{cidade} sem motivo escrito")

    def test_a_esparsidade_de_gaspar_continua_verdadeira_NO_DADO(self):
        """
        A exceção vale por uma MEDIÇÃO, não por opinião: nenhum evento de
        Blumenau abaixo de 8,50 m tem par em Gaspar no mesmo mês. Se alguém
        importar as cheias pequenas de Gaspar um dia, a premissa cai e a
        exceção tem de sair junto — este teste é quem avisa.
        """
        ev = self.enchentes["eventos"]
        g_meses = {e["data"][:7] for e in ev if e["cidade"] == "gaspar"}
        bl = [e for e in ev
              if e["cidade"] == "blumenau" and len(e["data"]) >= 7 and e.get("pico_m")]
        com_par = [e["pico_m"] for e in bl if e["data"][:7] in g_meses]
        self.assertTrue(com_par, "Gaspar sumiu da base")
        self.assertGreaterEqual(
            min(com_par), 8.0,
            "a lista de Gaspar deixou de ter limiar — reveja LISTAS_SO_COM_CHEIA_GRANDE")

    def test_a_excecao_nao_desliga_a_trava_para_quem_nao_esta_nela(self):
        """Blumenau como jusante continua sendo cobrada."""
        est, enc = self.base()
        enc["eventos"] = [
            {"rio": "itajai-acu", "cidade": "rio-do-sul", "data": "1954-10", "pico_m": 10.7},
            {"rio": "itajai-acu", "cidade": "blumenau", "data": "1954-12-01", "pico_m": 9.0},
        ]
        self.assertTrue([a for a in _meses(est, enc) if "evento de blumenau" in a])

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


class CodigoAnaEhReguaDeRio(unittest.TestCase):
    """
    A emenda à regra nº 1: o vínculo é por coordenada E POR TIPO.

    O cruzamento com o inventário da ANA (06/09/2026) mediu a distância entre as
    réguas do projeto e todas as estações da ANA em SC. Cinco caíram a menos de
    750 m de uma régua nossa — e QUATRO são PLUVIÔMETROS. A `2750017 TAIÓ` fica
    a 53 m da nossa régua e não mede rio nenhum: município certo, nome certo,
    coordenada certa, grandeza errada.

    Sem estes testes a trava seria só prosa dentro de uma função — e prosa não
    reprova ninguém.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def erros(self, estacoes):
        vd.erros.clear()
        vd.avisos.clear()
        orig = vd.le_json
        vd.le_json = lambda nome: estacoes if nome == "estacoes.json" else orig(nome)
        try:
            vd.valida_codigo_ana()
        finally:
            vd.le_json = orig
        return list(vd.erros), list(vd.avisos)

    def test_dados_reais_passam(self):
        self.assertEqual(self.erros(copy.deepcopy(self.real))[0], [])

    def test_pluviometro_como_codigo_ana_aborta(self):
        d = copy.deepcopy(self.real)
        _cidade(d, "itajai-acu", "taio")["codigo_ana"] = "2750017"
        erros, _ = self.erros(d)
        self.assertTrue(any("PLUVIOMETRICA" in e for e in erros),
                        "a 2750017 fica a 53 m da régua de Taió e mede CHUVA")

    def test_pluviometro_com_zero_a_esquerda_tambem_aborta(self):
        """
        O caso que escapa: com o zero à esquerda o código tem os oito dígitos do
        HidroWeb e passa na trava de formato. É a forma em que a 02648008 de
        Itajaí circula.
        """
        d = copy.deepcopy(self.real)
        _cidade(d, "itajai-acu", "itajai")["codigo_ana"] = "02648008"
        erros, _ = self.erros(d)
        self.assertTrue(any("PLUVIOMETRICA" in e for e in erros))

    def test_estacao_fluviometrica_fora_do_tracado_aborta(self):
        """A estação de rio fica NO rio. Coordenada longe = coordenada errada."""
        d = copy.deepcopy(self.real)
        original = vd.ESTACOES_ANA_CONHECIDAS["83800002"]
        vd.ESTACOES_ANA_CONHECIDAS["83800002"] = original[:3] + (-49.20,) + original[4:]
        try:
            erros, _ = self.erros(d)
        finally:
            vd.ESTACOES_ANA_CONHECIDAS["83800002"] = original
        self.assertTrue(any("do traçado" in e for e in erros))

    def test_escala_encerrada_sem_sucessora_avisa(self):
        """
        Quatro réguas da bacia morreram em 12/2021 (Blumenau, Indaial, Gaspar,
        Ibirama). A série histórica continua valendo; o presente, não.
        """
        d = copy.deepcopy(self.real)
        _cidade(d, "itajai-acu", "blumenau").pop("codigo_ana_sucessor")
        _, avisos = self.erros(d)
        self.assertTrue(any("ENCERROU" in a for a in avisos))

    def test_o_sucessor_de_blumenau_esta_declarado_nos_dados_reais(self):
        blu = _cidade(self.real, "itajai-acu", "blumenau")
        self.assertEqual(blu.get("codigo_ana_sucessor"), "83800003")

    def test_sucessora_nula_COM_motivo_e_resposta_valida(self):
        """
        Gaspar é a única das quatro réguas mortas em 12/2021 sem sucessora na
        ANA. Exigir um código ali faria inventar um; o que não pode é a chave
        faltar sem que ninguém tenha olhado.
        """
        d = copy.deepcopy(self.real)
        gaspar = _cidade(d, "itajai-acu", "gaspar")
        self.assertIsNone(gaspar["codigo_ana_sucessor"])
        self.assertTrue(gaspar["codigo_ana_sucessor_nota"])
        _, avisos = self.erros(d)
        self.assertFalse([a for a in avisos if "ENCERROU" in a and "gaspar" in a])

    def test_sucessora_nula_SEM_motivo_ainda_avisa(self):
        d = copy.deepcopy(self.real)
        gaspar = _cidade(d, "itajai-acu", "gaspar")
        gaspar.pop("codigo_ana_sucessor_nota")
        _, avisos = self.erros(d)
        self.assertTrue([a for a in avisos if "ENCERROU" in a and "gaspar" in a])

    def test_ituporanga_fechou_pelo_TIPO_e_a_serie_e_curta(self):
        """
        Os dois candidatos de Ituporanga eram complementares: a 83145140 tinha
        coordenada sem tipo, a 83250000 tinha tipo sem coordenada. A execução de
        07/09/2026 resolveu os dois de uma vez — e a resposta foi cruzada: quem
        fecha é a 83145140 (fluviométrica, 45 m do pino), e a 83250000, que tem
        a série de 1929, fica a 9,59 km e NÃO é esta régua.

        A série que ficou é curta de propósito: 10/2020. Um teste que só
        conferisse o código deixaria alguém supor 97 anos de histórico aqui.
        """
        c = _cidade(self.real, "itajai-acu", "ituporanga")
        self.assertEqual(c["codigo_ana"], "83145140")
        self.assertEqual(c["codigo_ana_escala"]["inicio"], "2020-10")
        self.assertNotIn("codigo_ana_candidatos", c)
        self.assertIn("JUSANTE DA BARRAGEM SUL", c["codigo_ana_verificacao"])

    def test_brusque_so_fechou_porque_o_elo_do_nosso_lado_apareceu(self):
        """
        O que faltava em Brusque nunca foi prova da ANA — a 83900000 sempre
        teve tipo (fluviométrica) e vizinhança (51 m da DCSC-00019). Faltava o
        NOSSO lado: `codigo_dcsc` era null, então os 51 m mediam até uma
        estação que este repositório nunca tinha afirmado ser este pino.

        Escrever o `codigo_ana` sem o `codigo_dcsc` reabriria exatamente o
        buraco que o candidato descrevia, então os dois andam juntos aqui.
        """
        c = _cidade(self.real, "itajai-mirim", "brusque")
        self.assertEqual(c["codigo_ana"], "83900000")
        self.assertEqual(c["codigo_dcsc"], "DCSC-00019")
        self.assertNotIn("codigo_ana_candidatos", c)
        self.assertIn("DCSC-00019", c["codigo_ana_verificacao"])

    def test_o_pino_de_cada_cidade_com_codigo_dcsc_cai_em_cima_da_estacao(self):
        """
        `codigo_dcsc` é ligação POR COORDENADA — é o que a convenção promete.
        As quatro do Mirim foram escritas em 07/09/2026 e precisam passar pela
        mesma régua das nove do Açu, senão a promessa vale só para metade.
        """
        import math as _math
        bruto = DADOS / "brutos" / "dcsc-estacoes-coordenadas-bacia-itajai.json"
        dcsc = {e["codigo"]: e for e in json.loads(bruto.read_text(encoding="utf-8"))["estacoes"]}
        vistas = 0
        for rio in self.real["rios"].values():
            for c in rio["cidades"]:
                cod = c.get("codigo_dcsc")
                if not cod or cod not in dcsc:
                    continue
                la, lo = c["coordenadas"]
                dy = (dcsc[cod]["lat"] - la) * 111320
                dx = (dcsc[cod]["lon"] - lo) * 111320 * _math.cos(_math.radians(la))
                d = _math.hypot(dx, dy)
                self.assertLess(d, 50, f"{c['id']} está a {d:.0f} m da {cod}")
                vistas += 1
        self.assertGreaterEqual(vistas, 13, "o cruzamento deixou de olhar cidades")

    def test_estacao_longe_do_tracado_mas_colada_no_pino_passa(self):
        """
        Ituporanga, caso real de 07/09/2026: a 83145140 fica a 45 m do pino e a
        21,4 km do traçado do Itajaí do Sul — que só cobre 10,5 km perto de Rio
        do Sul. A estação não está em outro rio; o rio é que não está desenhado.
        Medir só contra o traçado reprovaria a estação certa.
        """
        d = copy.deepcopy(self.real)
        c = _cidade(d, "itajai-acu", "ituporanga")
        self.assertEqual(c["codigo_ana"], "83145140")
        self.assertEqual(self.erros(d)[0], [])

    def test_estacao_longe_do_pino_mas_colada_no_tracado_passa(self):
        """
        Blumenau é o caso oposto, e a primeira versão da guarda reprovou ele: o
        PINO é que não é régua de nível (DCSC-00026 mede chuva, a 3 km do
        talvegue). A 83800002 está a 6,94 km desse pino e a 49 m do traçado —
        e é a régua certa.
        """
        d = copy.deepcopy(self.real)
        c = _cidade(d, "itajai-acu", "blumenau")
        self.assertEqual(c["codigo_ana"], "83800002")
        self.assertEqual(self.erros(d)[0], [])

    def test_estacao_longe_das_DUAS_referencias_reprova(self):
        """
        A regra do mínimo não pode virar 'passa qualquer coisa'. Estação longe
        do traçado E longe do pino continua sendo de outro curso d'água.
        """
        d = copy.deepcopy(self.real)
        c = _cidade(d, "itajai-acu", "ituporanga")
        # 83250000 é real, fluviométrica, chama-se ITUPORANGA — e fica a 9,59 km
        # do pino. É a armadilha desta cidade.
        c["codigo_ana"] = "83250000"
        erros, _ = self.erros(d)
        self.assertTrue([e for e in erros if "83250000" in e and "ituporanga" in e],
                        f"a 83250000 devia reprovar; erros: {erros}")

    def test_o_nao_e_da_83250000_esta_gravado_no_dado(self):
        """
        Um 'não' que mora só no documento volta como proposta na próxima rodada:
        a 83250000 se chama ITUPORANGA, é fluviométrica e tem a série mais longa
        do ramo (1929). O que a desmente é a coordenada, e isso fica no JSON.
        """
        c = _cidade(self.real, "itajai-acu", "ituporanga")
        nao_e = c["codigo_ana_nao_e"]
        self.assertEqual(nao_e["codigo"], "83250000")
        self.assertIn("9,59 km", nao_e["por_que_nao"])

    def test_a_quebra_de_12_2021_esta_registrada(self):
        """
        Uma série de 90 anos que para em 12/2021 não PARECE quebrada — parece
        que o rio parou de subir. Quem calcular 'o maior nível dos últimos anos'
        acha um número baixo e não sabe por quê.
        """
        nota = self.real["_meta"]["notas"].get("quebra_de_12_2021", "")
        for codigo in ("83800002", "83690000", "83840000", "83440000"):
            self.assertIn(codigo, nota)

    def test_salseiro_continua_fora_de_vidal_ramos(self):
        """
        A ANA respondeu o que o ofício C9 pedia à EPAGRI: a SALSEIRO (83892990)
        fica a 6,8 km da nossa régua e drena 286 km². Mesmo município não é
        mesma estação — e o registro do porquê tem de ficar no dado, senão o
        boletim da EPAGRI convida ao mesmo vínculo de novo no mês que vem.
        """
        vr = _cidade(self.real, "itajai-mirim", "vidal-ramos")
        self.assertIsNone(vr["codigo_ana"])
        self.assertEqual(vr["codigo_ana_nao_e"]["codigo"], "83892990")



class TestaCoberturaDaMare(unittest.TestCase):
    """
    A tábua de maré acaba, e o painel da foz fica MUDO sem avisar.

    Em 06/09/2026 a base tinha preamares e baixamares de 01/09 a 30/09 e mais
    nada: 24 dias de tábua restantes, e no dia 1º de outubro o painel de maré
    de Itajaí ficaria vazio. Maré alta trava a saída da água do rio — é metade
    da explicação da cheia na foz.
    """

    def _com_mare(self, ultimo_dia):
        """Roda o validador contra uma tábua que termina no dia dado."""
        orig = vd.le_json
        tabua = {
            "preamares": [{"quando": f"{ultimo_dia}T04:28", "altura_m": 1.1}],
            "baixamares": [{"quando": f"{ultimo_dia}T09:49", "altura_m": 0.2}],
        }
        vd.le_json = lambda nome: tabua if nome == "mare-itajai.json" else orig(nome)
        vd.erros.clear()
        vd.avisos.clear()
        try:
            vd.valida_cobertura_da_mare()
            return list(vd.erros), list(vd.avisos)
        finally:
            vd.le_json = orig
            vd.erros.clear()
            vd.avisos.clear()

    def test_tabua_que_ja_acabou_e_ERRO(self):
        erros, _ = self._com_mare((date.today() - timedelta(days=3)).isoformat())
        self.assertTrue(erros, "tábua vencida tem de reprovar, não só avisar")
        self.assertIn("JÁ está sem tábua", " ".join(erros))

    def test_tabua_acabando_avisa_com_semanas_de_folga(self):
        erros, avisos = self._com_mare((date.today() + timedelta(days=10)).isoformat())
        self.assertFalse(erros, "ainda há tábua: avisa, não reprova")
        self.assertTrue(avisos)
        self.assertIn("restam 10 dia(s)", " ".join(avisos))

    def test_tabua_farta_nao_reclama(self):
        erros, avisos = self._com_mare((date.today() + timedelta(days=200)).isoformat())
        self.assertFalse(erros)
        self.assertFalse(avisos, "tábua do ano inteiro não pode virar ruído")

    def test_lista_vazia_e_ERRO(self):
        # Sem preamar não há painel de maré nenhum — e isso não é "sem dado
        # hoje", é a tela da foz perdendo metade do que ela explica.
        orig = vd.le_json
        vd.le_json = lambda nome: {"preamares": [], "baixamares": []} if nome == "mare-itajai.json" else orig(nome)
        vd.erros.clear()
        vd.avisos.clear()
        try:
            vd.valida_cobertura_da_mare()
            self.assertEqual(len(vd.erros), 2, "preamares e baixamares vazios, dois erros")
        finally:
            vd.le_json = orig
            vd.erros.clear()
            vd.avisos.clear()



class TestaCotasDeIndaial(unittest.TestCase):
    """
    A escala de Indaial é a que a COMPDEC publica — não um número nosso.

    Até 06/09/2026 o cadastro trazia `atencao: 6,00 m`, e esse nome era NOSSO: a
    leitura anterior achou só a PÁGINA do município, que lista 12 vias com
    alagamento já registrado a 6,00 m, e gravou o único número que existia.

    A COMPDEC publica uma escala, no PDF "Indaial - cotas de enchente" da aba
    ARQUIVOS da mesma página: até 3 m normal, 3 a 4 m atenção, 4 a 5,5 m alerta,
    acima de 5,5 m emergência.

    Os 6,00 m ficavam, portanto, 1,5 m ACIMA da emergência do próprio município.
    A tela chamaria de "abaixo da atenção" um nível que Indaial já trata como
    emergência — o lado perigoso, o único que este projeto não pode errar.
    """

    def setUp(self):
        self.indaial = _cidade(vd.le_json("estacoes.json"), "itajai-acu", "indaial")

    def test_a_escala_e_a_do_PDF(self):
        self.assertEqual(self.indaial["cotas_m"], {"atencao": 3.0, "alerta": 4.0, "emergencia": 5.5})

    def test_a_atencao_nunca_mais_passa_da_emergencia(self):
        c = self.indaial["cotas_m"]
        self.assertLess(c["atencao"], c["emergencia"], "foi exatamente este o erro de 06/09/2026")

    def test_os_6_metros_nao_voltam_como_cota(self):
        # Os 6,00 m são alagamento de rua, que começa meio metro depois da
        # emergência. Continuam valendo como fato; não são degrau da escada.
        self.assertNotIn(6.0, self.indaial["cotas_m"].values())

    def test_a_fonte_aponta_para_o_PDF_e_nao_so_para_a_pagina(self):
        # Foi ler só a página que produziu o erro: a escala está no anexo.
        self.assertIn("PDF", self.indaial["fonte_cotas"])
        self.assertIn("cotas de enchente", self.indaial["fonte_cotas"])

    def test_a_referencia_da_regua_esta_registrada(self):
        # 67 m (o que o PDF diz que 5,5 m equivale) menos 5,5 = 61,5 = o RN.
        # É isso que prova que o zero da régua É o RN, e que não há dois datums.
        self.assertIn("1402-X", self.indaial["regua_das_cotas"])
        self.assertIn("61,49", self.indaial["regua_das_cotas"])


class TestaOrdemDasCotas(unittest.TestCase):
    """As faixas de uma régua sobem na ordem, em todas as cidades."""

    def _erros_com(self, cotas):
        orig = vd.le_json
        falso = {"rios": {"r": {"cidades": [{"id": "x", "cotas_m": cotas}]}}}
        vd.le_json = lambda nome: falso if nome == "estacoes.json" else orig(nome)
        vd.erros.clear()
        vd.avisos.clear()
        try:
            vd.valida_ordem_das_cotas()
            return list(vd.erros), list(vd.avisos)
        finally:
            vd.le_json = orig
            vd.erros.clear()
            vd.avisos.clear()

    def test_atencao_acima_da_emergencia_e_ERRO(self):
        erros, _ = self._erros_com({"atencao": 6.0, "alerta": 4.0, "emergencia": 5.5})
        self.assertTrue(erros)

    def test_escala_certa_passa(self):
        erros, avisos = self._erros_com({"atencao": 3.0, "alerta": 4.0, "emergencia": 5.5})
        self.assertFalse(erros)
        self.assertFalse(avisos)

    def test_cota_igual_a_anterior_e_ERRO(self):
        # Duas faixas no mesmo metro não são duas faixas: uma delas nunca acende.
        erros, _ = self._erros_com({"atencao": 4.0, "alerta": 4.0})
        self.assertTrue(erros)

    def test_anotacao_conhecida_nao_vira_ruido(self):
        _, avisos = self._erros_com({"atencao": 3.0, "inundacao_historica": 8.04})
        self.assertFalse(avisos, "anotação da fonte não é degrau e não deve avisar")

    def test_chave_desconhecida_avisa(self):
        _, avisos = self._erros_com({"atencaoo": 3.0})
        self.assertTrue(avisos, "erro de digitação numa faixa não pinta nada e tem de aparecer")

    def test_o_cadastro_REAL_esta_em_ordem(self):
        vd.erros.clear()
        try:
            vd.valida_ordem_das_cotas()
            self.assertEqual(vd.erros, [])
        finally:
            vd.erros.clear()
            vd.avisos.clear()


def erros_de_cotas(cotas_dict) -> list[str]:
    """Roda só `valida_cota_de_rua_duplicada` sobre um cotas-ruas.json em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json
    vd.le_json = lambda nome: cotas_dict if nome == "cotas-ruas.json" else orig(nome)
    try:
        vd.valida_cota_de_rua_duplicada()
    finally:
        vd.le_json = orig
    return list(vd.erros)


class TestaCotaDeRuaDuplicada(unittest.TestCase):
    """
    A mesma medição entrando duas vezes some da conta — e some uma rua da lista.

    Gaspar teve quatro: Petúnia, Costa Rica, Hilberto Gaertner e Sertão Verde
    chegaram pela consulta rua a rua de 2017 (só nome e cota) e de novo pela
    camada do Google My Maps de 2020 (nome, bairro, ponto e coordenada). Como
    `proximas()` conta LINHAS e as quatro estavam no fundo da escala, a lista
    das "próximas 5 ruas a alagar" mostrava três ruas em cinco lugares e
    empurrava a rua seguinte para fora.
    """

    def cotas(self, *linhas):
        return {"cotas": list(linhas)}

    def linha(self, rua, cota, ponto=None, cidade="gaspar"):
        return {"cidade": cidade, "rua": rua, "cota_m": cota, "ponto": ponto,
                "referencia": "régua"}

    def test_o_arquivo_real_esta_limpo(self):
        vd.erros.clear()
        vd.avisos.clear()
        vd.valida_cota_de_rua_duplicada()
        self.assertEqual(vd.erros, [])

    def test_mesma_rua_e_mesma_cota_com_uma_linha_sem_ponto_e_ERRO(self):
        erros = erros_de_cotas(self.cotas(
            self.linha("Rua Petúnia", 6.2, ponto=None),
            self.linha("Rua Petúnia", 6.2, ponto="Final de rua"),
        ))
        self.assertEqual(len(erros), 1)
        self.assertIn("repetida", erros[0])

    def test_a_abreviacao_do_logradouro_nao_esconde_a_duplicata(self):
        """'Av. Hilberto Gaertner' e 'Avenida Hilberto Gaertner' são a mesma avenida."""
        erros = erros_de_cotas(self.cotas(
            self.linha("Av. Hilberto Gaertner", 6.25, ponto=None),
            self.linha("Avenida Hilberto Gaertner", 6.25, ponto="Final de rua"),
        ))
        self.assertEqual(len(erros), 1)

    def test_rua_comprida_com_DOIS_pontos_na_mesma_cota_PASSA(self):
        """
        A Adolfo Radunz alaga a 9,55 m na esquina da Macaé e depois da casa
        nº 105. São 143 pares assim no arquivo: barrar "mesma rua, mesma cota"
        apagaria todos eles.
        """
        self.assertEqual(erros_de_cotas(self.cotas(
            self.linha("Rua Adolfo Radunz", 9.55, ponto="Esquina - Rua Macaé"),
            self.linha("Rua Adolfo Radunz", 9.55, ponto="Após a casa nº 105"),
        )), [])

    def test_mesma_rua_com_cotas_diferentes_PASSA(self):
        self.assertEqual(erros_de_cotas(self.cotas(
            self.linha("Rua Petúnia", 6.2, ponto=None),
            self.linha("Rua Petúnia", 6.35, ponto="Meio da rua"),
        )), [])

    def test_cidades_diferentes_nunca_se_cruzam(self):
        """7 m em Gaspar não é 7 m em Blumenau — nem para achar duplicata."""
        self.assertEqual(erros_de_cotas(self.cotas(
            self.linha("Rua Sete de Setembro", 7.0, ponto=None, cidade="gaspar"),
            self.linha("Rua Sete de Setembro", 7.0, ponto="Nº 40", cidade="blumenau"),
        )), [])

    def test_cota_nula_fica_de_fora(self):
        """Cota nula não é zero, e não pode virar duplicata de coisa nenhuma."""
        self.assertEqual(erros_de_cotas(self.cotas(
            self.linha("Rua Sem Número", None, ponto=None),
            self.linha("Rua Sem Número", None, ponto="Final"),
        )), [])


class TestaCotasDeBrusque(unittest.TestCase):
    """
    A escala de Brusque é a que o município publica, não a cota de uma rua.

    Até 07/09/2026 `atencao` era 4,80 m — a cota em que a Av. Beira-Rio começa
    a alagar, gravada ali por ser o único número que existia. É o mesmo erro
    que Indaial tinha com 6,00 m (doze vias alagando) no lugar da escala da
    COMPDEC, e com a mesma consequência: entre 3,00 e 4,80 m a tela dizia
    NORMAL enquanto a Defesa Civil já declara ATENÇÃO — 1,80 m de rio errando
    para o lado de quem lê achando que está seguro.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.brusque = _cidade(cls.real, "itajai-mirim", "brusque")

    def test_a_escala_e_a_do_municipio(self):
        self.assertEqual(self.brusque["cotas_m"], {"atencao": 3.0, "emergencia": 5.0})

    def test_os_4_80_nao_voltam_como_faixa(self):
        """Podem voltar como anotação; como degrau de aviso, não."""
        for chave, valor in self.brusque["cotas_m"].items():
            self.assertNotEqual(valor, 4.8, f"{chave} não pode ser a cota da Beira-Rio")
            self.assertNotEqual(valor, 6.0, f"{chave} não pode ser o 6,00 sem procedência")

    def test_a_atencao_nunca_passa_da_emergencia(self):
        self.assertLess(self.brusque["cotas_m"]["atencao"],
                        self.brusque["cotas_m"]["emergencia"])

    def test_o_par_regua_cota_esta_declarado_como_provado(self):
        """Três leituras do mesmo minuto (1,27 · 1,27 · 1,28) provaram a régua."""
        self.assertIn("PAR PROVADO", self.brusque["regua_das_cotas_fonte"])

    def test_a_fonte_da_escala_aponta_para_a_pagina_do_municipio(self):
        self.assertIn("defesacivil.brusque.sc.gov.br", self.brusque["fonte_cotas"])

    def test_o_que_saiu_fica_registrado_com_o_motivo(self):
        # Trocar cota de segurança sem deixar o rastro do que havia antes é
        # como o 4,80 chegou aqui em primeiro lugar.
        saiu = self.brusque["cotas_substituidas_em_2026_09_07"]
        self.assertEqual(saiu["_o_que_saiu"], {"atencao": 4.8, "inundacao": 6.0})
        self.assertIn("Beira-Rio", saiu["_por_que_saiu"])


class TestaVidalRamosNaoHerdaOSalseiro(unittest.TestCase):
    """
    As cotas do Salseiro não podem virar as cotas de Vidal Ramos.

    O portal de Brusque publica 'Salseiro – Vidal Ramos' com uma escala
    completa — justo o que falta nesta cidade. Mas a ANA já respondeu que a
    SALSEIRO fica a 6,8 km desta régua e drena 286 km². É o vínculo por NOME DE
    MUNICÍPIO que `codigo_ana_nao_e` recusou, voltando por outra porta.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.vr = _cidade(cls.real, "itajai-mirim", "vidal-ramos")

    def test_continua_sem_cota(self):
        self.assertEqual(self.vr["cotas_m"], {})

    def test_e_o_motivo_esta_escrito_no_dado(self):
        # Sem isto, o mesmo achado convida ao mesmo erro no mês que vem.
        motivo = self.vr["cotas_m_por_que_vazio"]
        self.assertIn("SALSEIRO", motivo.upper())
        self.assertIn("6,8 km", motivo)

    def test_a_recusa_nao_se_apoia_mais_na_area_de_drenagem(self):
        """
        O motivo gravado era "drena 286 km² — sub-bacia bem menor". Não se
        sustentava: não há área de drenagem cadastrada para a nossa própria
        régua de Vidal Ramos, então a comparação era com nada. E o que dá para
        comparar aponta ao contrário — 286 km² (Salseiro) → 827 km²
        (BOTUVERA-MONTANTE) → 1.240 km² (Brusque) é progressão limpa de
        montante para jusante, própria de pontos do MESMO rio, com códigos
        quase consecutivos (83892990 / 83892998).

        A recusa continua, por motivo mais forte: 6,8 km é outro ponto do rio,
        com outro zero. Este teste existe para o motivo velho não voltar.
        """
        motivo = self.vr["codigo_ana_nao_e"]["por_que_nao"]
        self.assertIn("CORRIGIDO", motivo)
        self.assertIn("6,8 km", motivo)
        self.assertNotIn("sub-bacia bem menor. O Boletim", motivo)

    def test_o_que_a_area_de_drenagem_nao_prova_esta_dito(self):
        motivo = self.vr["codigo_ana_nao_e"]["por_que_nao"]
        self.assertIn("827", motivo, "a comparação que desmente tem de estar no dado")
        self.assertIn("1.240", motivo)

    def test_o_traco_e_o_zero_convivendo_no_mesmo_cartao_estao_registrados(self):
        """
        A captura de 07/09 mostra '---' nas cinco acumuladas e '0,00 mm' na
        chuva atual, no mesmo cartão. A página prova, sozinha, que '---' é o
        'não tenho dado' desta fonte — e que o 0,00 ao lado, numa estação
        parada há 142 dias, é número fabricado. A regra de atenção da legenda
        lê justamente esse campo.
        """
        motivo = self.vr["cotas_m_por_que_vazio"]
        self.assertIn("---", motivo)
        self.assertIn("35,00 mm", motivo)

    def test_as_cotas_do_salseiro_nao_aparecem_em_lugar_nenhum_da_cidade(self):
        texto = json.dumps(self.vr, ensure_ascii=False)
        for chave in ("atencao", "alerta", "emergencia", "inundacao"):
            self.assertNotIn(f'"{chave}": 3.0', texto)
            self.assertNotIn(f'"{chave}": 4.5', texto)


class ConflitoDoPlanconDeItajaiFechado(unittest.TestCase):
    """
    Duas leituras do Plano de Contingência de Itajaí davam valores diferentes.
    Em 08/09/2026 o PDF da versão 17 (22/12/2025) foi aberto e lido: a tabela
    de níveis é a **Tabela 11**, na página 23; o documento tem doze tabelas e
    **não existe Tabela 13 nele**. Os onze valores cadastrados batem
    exatamente com o PDF — 11 de 11.

    A outra leitura é de OUTRA EDIÇÃO. E a diferença não é só de valores: lá a
    DC-09 é "Ribeirão Ariribá — Clube Ariribá"; na v17 é "Ribeirão da Murta –
    Bairro Murta". Rio diferente para o mesmo código. As estações foram
    remanejadas entre edições.

    Estes testes travam o que a resolução comprou: que os valores continuem
    sendo os da v17 inteiros, que a leitura da outra edição fique guardada em
    vez de descartada (ela é a prova do remanejamento), e que ninguém volte a
    tratar as duas como versões da mesma tabela.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.dc = {e["codigo"]: e for e in cls.real["estacoes_tempo_real"]
                  if str(e.get("codigo", "")).startswith("DC-")}

    def test_o_bloco_do_conflito_diz_que_esta_resolvido_e_como(self):
        bloco = self.real["_conflito_plancon_itajai"]
        self.assertIn("RESOLVIDO", bloco["estado"])
        self.assertIn("Tabela 11", bloco["resolucao"])
        self.assertIn("11 de 11", bloco["resolucao"])

    def test_a_regra_que_sobrou_exige_a_versao_do_documento(self):
        """
        O que este episódio ensinou não é "a v17 está certa" — é que sem a
        versão não dá para saber a que estação o número pertencia.
        """
        bloco = self.real["_conflito_plancon_itajai"]
        self.assertIn("VERSÃO", bloco["regra_que_fica"])

    def test_o_erro_de_leitura_anterior_ficou_registrado(self):
        """
        Em 07/09 supus "é a mesma tabela revisada" porque a DC-02 coincidia em
        dois de três valores. Indício fraco lido como forte. Apagar isso
        deixaria só o acerto à vista.
        """
        bloco = self.real["_conflito_plancon_itajai"]
        self.assertIn("indício fraco", bloco["por_que_a_hipotese_anterior_estava_errada"])

    def test_as_nove_reguas_guardam_as_DUAS_leituras(self):
        emconflito = [c for c, e in self.dc.items() if "cotas_divergencia" in e]
        self.assertEqual(len(emconflito), 9, emconflito)
        for cod in emconflito:
            div = self.dc[cod]["cotas_divergencia"]
            with self.subTest(regua=cod):
                self.assertEqual(div["adotado_tabela_11_v17"], self.dc[cod]["cotas_m"],
                                 "o adotado tem de ser igual ao que está valendo")
                for faixa in ("atencao", "alerta", "emergencia"):
                    self.assertIn(faixa, div["outra_leitura_de_outra_edicao"])

    def test_a_leitura_da_outra_edicao_nao_pode_ser_apagada(self):
        """
        A tentação depois de resolver: "o conflito acabou, tira o lixo".
        Mas é justamente a comparação entre as duas que mostra que a DC-09
        mudou de rio. Descartar a outra leitura apaga a prova.
        """
        for cod, e in self.dc.items():
            div = e.get("cotas_divergencia")
            if not div:
                continue
            with self.subTest(regua=cod):
                self.assertIn("remanejadas", div["_o_que_era_a_outra_leitura"])

    def test_nenhuma_regua_ficou_com_escala_misturada(self):
        """
        A tentação antiga: pegar a atenção de uma leitura e a emergência da
        outra, "para errar para o lado seguro". Isso montaria uma escala que
        nenhuma das duas edições publica. Continua valendo depois de resolvido.
        """
        for cod, e in self.dc.items():
            div = e.get("cotas_divergencia")
            if not div:
                continue
            a, b = div["adotado_tabela_11_v17"], div["outra_leitura_de_outra_edicao"]
            atual = e["cotas_m"]
            with self.subTest(regua=cod):
                self.assertTrue(
                    atual == a or atual == b,
                    f"{cod} não bate com nenhuma das duas leituras inteiras: {atual}")

    def test_o_que_vale_e_a_v17_inteira(self):
        """Não é "a nossa ganhou": é que a v17 foi lida na fonte e as onze
        linhas conferem. Se alguém trocar uma cota por um valor da outra
        edição, isto cai."""
        for cod, e in self.dc.items():
            div = e.get("cotas_divergencia")
            if not div:
                continue
            with self.subTest(regua=cod):
                self.assertEqual(e["cotas_m"], div["adotado_tabela_11_v17"])


class ItuporangaTemEscalaOficialDeOutraRegua(unittest.TestCase):
    """
    A SPDC/SC determina que o aviso de Ituporanga saia da 83250000 (ANA/EPAGRI),
    com atenção > 1,40 / alerta > 1,90 / emergência > 2,60 m.

    Isso NÃO reabilita a 83250000 como régua deste pino — ela continua a 9,59 km
    e drenando 1.650 km² contra 1.170 km². As duas coisas são verdadeiras ao
    mesmo tempo, e é isso que o dado passa a dizer.
    """

    @classmethod
    def setUpClass(cls):
        real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.it = _cidade(real, "itajai-acu", "ituporanga")

    def test_continua_sem_cota_cadastrada(self):
        """
        As cotas são da 83250000; a nossa leitura vem da DCSC-00039. Gravar
        1,40/1,90/2,60 aqui criaria o par régua↔cota errado.
        """
        self.assertEqual(self.it["cotas_m"], {})

    def test_a_designacao_oficial_esta_registrada_com_os_valores(self):
        texto = self.it["codigo_ana_nao_e"]["designacao_oficial"]
        for v in ("1,40", "1,90", "2,60"):
            self.assertIn(v, texto)
        self.assertIn("EPAGRI", texto)

    def test_o_vinculo_continua_recusado(self):
        # A cidade TEM código ANA — a 83145140. O que continua recusado é a
        # 83250000 como régua deste pino, apesar de ser a régua do aviso.
        self.assertEqual(self.it["codigo_ana"], "83145140")
        self.assertEqual(self.it["codigo_ana_nao_e"]["codigo"], "83250000")
        self.assertIn("9,59 km", self.it["codigo_ana_nao_e"]["designacao_oficial"])

    def test_o_caminho_que_destrava_esta_dito(self):
        """Coletar a 83250000: com a leitura dela, a cota dela vale."""
        self.assertIn("SIG²A-SPEHC", self.it["cotas_m_por_que_vazio"])



def _dispara(eventos: list[dict]) -> bool:
    """Roda só `valida_divergencia_que_virou_registro` sobre dados em memória."""
    vd.erros.clear()
    vd.avisos.clear()
    orig = vd.le_json
    vd.le_json = lambda nome: ({"eventos": eventos} if nome == "enchentes.json" else orig(nome))
    try:
        vd.valida_divergencia_que_virou_registro()
    finally:
        vd.le_json = orig
    return bool(vd.erros)


class DivergenciaQueVirouRegistro(unittest.TestCase):
    """
    Brusque tinha o 10,30 m de 1984 nos dois lugares: registro solto `1984` e
    divergência dentro do `1984-08` (10,50 m), com a fonte dizendo, ela mesma,
    "valor anterior deste repositório".

    O estrago não é a contagem, é a ORDEM. O evento fantasma empurrava todos os
    de baixo uma posição: a cheia de 2011 aparecia como 3ª maior de Brusque
    quando é a 2ª, e a de 17/11/2023 como 4ª quando é a 3ª — que é exatamente o
    número que a imprensa da cidade usa e que o morador lê.
    """

    def setUp(self):
        self.real = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))
        self.brusque = [e for e in self.real["eventos"] if e["cidade"] == "brusque"]

    def test_o_registro_solto_de_1984_nao_voltou(self):
        soltos = [e for e in self.brusque if e.get("data") == "1984"]
        self.assertEqual(soltos, [], "o 10,30 m de 1984 é divergência, não registro")

    def test_o_valor_continua_guardado_como_divergencia(self):
        """Apagar o registro não podia apagar o número: ele é a leitura antiga."""
        oitenta_e_quatro = next(e for e in self.brusque if e.get("data") == "1984-08")
        valores = [d["pico_m"] for d in oitenta_e_quatro["divergencias"]]
        self.assertIn(10.3, valores)

    def test_a_ordem_das_cheias_de_brusque(self):
        """
        Trava o ranking que o morador lê. Se um evento fantasma voltar, alguma
        destas posições muda e o teste cai antes de a tela mentir.
        """
        ordem = [e["data"] for e in sorted(self.brusque, key=lambda x: -x["pico_m"])]
        self.assertEqual(ordem[:4], ["1984-08", "2011-09", "2023-11-17", "2008-11"])

    def test_a_guarda_pega_o_padrao_em_dado_de_mentira(self):
        eventos = [
            {"cidade": "x", "data": "1990-05", "pico_m": 9.0,
             "divergencias": [{"pico_m": 8.0, "fonte": "compilação"}]},
            {"cidade": "x", "data": "1990", "pico_m": 8.0, "fonte": "compilação"},
        ]
        self.assertTrue(_dispara(eventos))

    def test_a_guarda_NAO_reclama_de_ano_diferente(self):
        """Duas cheias de anos diferentes com o mesmo metro não são duplicata."""
        eventos = [
            {"cidade": "x", "data": "1990-05", "pico_m": 9.0,
             "divergencias": [{"pico_m": 8.0, "fonte": "c"}]},
            {"cidade": "x", "data": "1991", "pico_m": 8.0, "fonte": "c"},
        ]
        self.assertFalse(_dispara(eventos))

    def test_a_guarda_NAO_reclama_de_outra_cidade(self):
        eventos = [
            {"cidade": "x", "data": "1990-05", "pico_m": 9.0,
             "divergencias": [{"pico_m": 8.0, "fonte": "c"}]},
            {"cidade": "y", "data": "1990", "pico_m": 8.0, "fonte": "c"},
        ]
        self.assertFalse(_dispara(eventos))



class SalseiroNaoEARegoaDeVidalRamos(unittest.TestCase):
    """
    Salseiro é localidade RURAL de Vidal Ramos, e a EPAGRI publica a estação sob
    o nome do município. Parecem a mesma régua e não são: em 08/09/2026 elas
    leram 1,72 m e 2,42 m com NOVE minutos de diferença, num dia em que o rio
    variou 1 cm em 38 leituras.

    O que estes testes travam não é a recusa — ela já estava travada. É a
    RESSALVA: que ninguém use os 0,70 m como fator de conversão. Uma medição,
    num nível só, entre réguas a 6,8 km, não descreve a relação entre elas na
    cheia — que é exatamente quando alguém teria a ideia de converter.
    """

    @classmethod
    def setUpClass(cls):
        real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.bloco = _cidade(real, "itajai-mirim", "vidal-ramos")["codigo_ana_nao_e"]

    def test_a_recusa_continua_de_pe(self):
        self.assertEqual(self.bloco["codigo"], "83892990")
        self.assertIn("NÃO vincular", self.bloco["por_que_nao"])

    def test_a_medicao_esta_registrada_com_as_duas_leituras(self):
        m = self.bloco["medicao_que_fecha"]
        for pedaco in ("1,72", "2,42", "0,70", "08:00", "07:51"):
            with self.subTest(pedaco=pedaco):
                self.assertIn(pedaco, m)

    def test_o_rio_parado_esta_dito_porque_e_o_que_torna_a_medicao_valida(self):
        """Sem essa frase, os 0,70 m poderiam ser subida do rio, como em 31/08."""
        self.assertIn("1 cm", self.bloco["medicao_que_fecha"])

    def test_esta_escrito_que_os_070_m_NAO_sao_conversao(self):
        # Sem sensibilidade a maiúscula: a ênfase é escolha de escrita e pode
        # mudar; o que o teste guarda é o ARGUMENTO estar lá.
        naoe = self.bloco["o_que_os_070_m_NAO_sao"].lower()
        self.assertIn("não são um fator de conversão", naoe)
        self.assertIn("muda com a vazão", naoe)

    def test_o_bruto_do_boletim_existe(self):
        """Medição sem a fonte guardada é afirmação, não prova."""
        bruto = DADOS / "brutos" / "epagri-ciram-boletim-155-2026-09-08.pdf"
        self.assertTrue(bruto.exists(), f"{bruto} sumiu")

    def test_vidal_ramos_continua_sem_codigo_ana(self):
        """A medição CONFIRMOU a recusa; ela não pode ter virado preenchimento."""
        real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        self.assertIsNone(_cidade(real, "itajai-mirim", "vidal-ramos")["codigo_ana"])



class ACotaDaSalseiroNaoEDeVidalRamos(unittest.TestCase):
    """
    A página de detalhes da SALSEIRO publica a escala dela: normalidade < 3,00 m,
    atenção > 3,00 m, emergência > 4,50 m. Vidal Ramos está sem cota nenhuma.

    É a tentação perfeita: a escala existe, é oficial, e tem o nome do município
    do lado. E é errada — em 08/09/2026 as duas réguas leram 1,72 m e 2,42 m com
    nove minutos de diferença. Aplicar 3,00 m à nossa leitura pintaria atenção
    num estado do rio que a própria Salseiro ainda chama de normalidade.

    Cota pertence a uma RÉGUA, não a um município.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.cidade = _cidade(cls.real, "itajai-mirim", "vidal-ramos")
        cls.bloco = cls.cidade["codigo_ana_nao_e"]

    def test_vidal_ramos_continua_SEM_cota(self):
        """O teste que mais importa: a escala da Salseiro não virou a da sede."""
        self.assertEqual(self.cidade["cotas_m"], {})

    def test_os_numeros_da_salseiro_estao_registrados_COM_dono(self):
        texto = self.bloco["cotas_DA_SALSEIRO_nao_da_sede"]
        for n in ("3,00", "4,50"):
            with self.subTest(numero=n):
                self.assertIn(n, texto)
        self.assertIn("SÃO DA SALSEIRO", texto)

    def test_o_3_e_o_450_nao_aparecem_como_cota_de_nenhuma_cidade_do_mirim(self):
        """
        Guarda de verdade, não de texto: se alguém gravar 3,00/4,50 como cota de
        Vidal Ramos em qualquer lugar do cadastro, isto cai.
        """
        for rio_id, rio in self.real["rios"].items():
            for c in rio["cidades"]:
                if c["id"] != "vidal-ramos":
                    continue
                with self.subTest(rio=rio_id):
                    self.assertNotIn(3.0, (c.get("cotas_m") or {}).values())
                    self.assertNotIn(4.5, (c.get("cotas_m") or {}).values())

    def test_o_resultado_NEGATIVO_da_serie_esta_guardado(self):
        """
        O bloco registrava 'vale pedir a série histórica'. Foi pedida e veio
        vazia. Resultado negativo não guardado vira a mesma busca daqui a um mês.
        """
        texto = self.bloco["serie_historica_pedida_e_veio_VAZIA"]
        self.assertIn("NENHUMA LINHA", texto)
        bruto = DADOS / "brutos" / "salseiro-83892990-serie-historica-VAZIA-2026-09-08.xls.html"
        self.assertTrue(bruto.exists(), f"{bruto} sumiu")

    def test_o_bruto_vazio_e_mesmo_vazio(self):
        """Se um dia alguém repuser o arquivo com dado, o texto tem de mudar junto."""
        bruto = DADOS / "brutos" / "salseiro-83892990-serie-historica-VAZIA-2026-09-08.xls.html"
        conteudo = bruto.read_text(encoding="utf-8")
        self.assertIn("<b>data</b>", conteudo)
        self.assertEqual(conteudo.count("<tr>"), 2, "passou a ter linha de dado")

    def test_a_armadilha_do_verde_velho_esta_registrada(self):
        """
        A tela mostrava faixa VERDE de 'NORMALIDADE' sobre uma leitura de quase
        cinco meses antes. É o oposto do que este site faz, e por isso fica
        escrito antes de alguém pensar em coletar dali.
        """
        texto = self.bloco["a_pagina_nao_envelhece_o_dado"]
        self.assertIn("18/04/2026", texto)
        self.assertIn("VERDE", texto)


def _brutos(citacao: str, arquivos: list[str], pendentes: dict[str, str]) -> tuple[list[str], list[str]]:
    """Roda `valida_brutos_citados` sobre um repo de mentira, em pasta temporária.

    `citacao` é o texto que um bloco do estacoes.json traria; `arquivos` é o
    que existe de verdade em data/brutos/; `pendentes` é o BRUTOS_PENDENTES.
    """
    vd.erros.clear()
    vd.avisos.clear()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "data" / "brutos").mkdir(parents=True)
        for nome in arquivos:
            (raiz / "data" / "brutos" / nome).write_text("{}", encoding="utf-8")
        (raiz / "data" / "estacoes.json").write_text(
            json.dumps({"rios": {"x": {"cidades": [{"id": "c", "nota": citacao}]}}}),
            encoding="utf-8")
        raiz_orig, pend_orig, le_orig = vd.RAIZ, vd.BRUTOS_PENDENTES, vd.le_json
        vd.RAIZ, vd.BRUTOS_PENDENTES = raiz, pendentes
        vd.le_json = lambda caminho: json.loads(Path(caminho).read_text(encoding="utf-8"))
        try:
            vd.valida_brutos_citados()
        finally:
            vd.RAIZ, vd.BRUTOS_PENDENTES, vd.le_json = raiz_orig, pend_orig, le_orig
        return list(vd.erros), list(vd.avisos)


class BrutoCitadoTemDeExistir(unittest.TestCase):
    """
    Achado da auditoria de 08/09/2026: dos 106 caminhos citados como evidência
    nos JSONs, 105 existiam e um não — o inventário da ANA, que sustenta quatro
    recusas de código e um vínculo. As recusas seguem certas; a frase é que
    prometia uma conferência impossível. Este guarda impede a próxima.
    """

    CITACAO = "Lido no inventário. Bruto: data/brutos/inventario-2026-09-07.json."

    def test_bruto_ausente_e_nao_declarado_e_erro(self):
        erros, _ = _brutos(self.CITACAO, arquivos=[], pendentes={})
        self.assertTrue(erros, "citou bruto que não existe e o validador deixou passar")
        self.assertIn("NÃO existe", erros[0])

    def test_bruto_presente_passa(self):
        erros, _ = _brutos(self.CITACAO, arquivos=["inventario-2026-09-07.json"], pendentes={})
        self.assertEqual(erros, [])

    def test_bruto_ausente_mas_declarado_passa(self):
        erros, _ = _brutos(
            self.CITACAO, arquivos=[],
            pendentes={"data/brutos/inventario-2026-09-07.json": "gerado na VPS"})
        self.assertEqual(erros, [], "a pendência declarada não deveria virar erro")

    def test_a_excecao_vence_quando_o_arquivo_chega(self):
        """Exceção que não vence vira mobília — e passa a mentir ao contrário."""
        erros, _ = _brutos(
            self.CITACAO, arquivos=["inventario-2026-09-07.json"],
            pendentes={"data/brutos/inventario-2026-09-07.json": "gerado na VPS"})
        self.assertTrue(erros, "o arquivo chegou e a exceção continuou de pé, calada")
        self.assertIn("BRUTOS_PENDENTES", erros[0])

    def test_pendencia_sem_dono_vira_aviso(self):
        _, avisos = _brutos("sem citação nenhuma", arquivos=[],
                            pendentes={"data/brutos/orfao.json": "ninguém cita"})
        self.assertTrue(any("perdido o dono" in a for a in avisos))


class OInventarioDaAnaEstaDeclaradoComoAusente(unittest.TestCase):
    """O caso real, travado contra o repositório de verdade."""

    BRUTO = "data/brutos/ana-inventario-2026-09-07.json"

    def test_ou_o_arquivo_existe_ou_a_pendencia_esta_declarada(self):
        existe = (vd.RAIZ / self.BRUTO).exists()
        declarado = self.BRUTO in vd.BRUTOS_PENDENTES
        self.assertNotEqual(existe, declarado,
                            "o inventário da ANA precisa estar OU no repo OU em "
                            "BRUTOS_PENDENTES — nunca nos dois, nunca em nenhum")

    def test_quem_cita_avisa_que_o_arquivo_nao_esta(self):
        """
        Enquanto o bruto não chegar, cada bloco que o cita diz isso na cara.
        Se o arquivo chegar, este teste cai junto com o guarda do validador —
        de propósito: os textos têm de perder o aviso na mesma hora.
        """
        if (vd.RAIZ / self.BRUTO).exists():
            self.skipTest("o bruto chegou; o validador cobra a limpeza dos textos")
        bruto_texto = (vd.RAIZ / "data" / "estacoes.json").read_text(encoding="utf-8")
        citacoes = bruto_texto.count(self.BRUTO)
        self.assertEqual(citacoes, 5, "mudou o número de citações do inventário")
        self.assertEqual(bruto_texto.count("AINDA NÃO ESTÁ NO REPO"), citacoes,
                         "há citação do inventário sem o aviso de que o arquivo não está")


class OutroPontoDoRioCertoNaoEAReguaDaCidade(unittest.TestCase):
    """
    Achado da auditoria de 08/09/2026, e o segundo do mesmo fio.

    Quatro recusas de código ANA invocavam "o limite de 1 km que o projeto usa
    para dizer 'mesma régua'". Esse limite existia com outro trabalho: o
    `LIMITE_PINO_KM` mede a estação contra o MENOR entre o traçado e o pino, e
    reprova coordenada errada ou rio errado. A medida foi constrangedora —
    TRÊS das quatro estações recusadas ficam a menos de 60 m do traçado do
    próprio rio da cidade. Ligadas, o validador aprovaria as três em silêncio:
    a recusa morava só na cabeça de quem leu a distância.

    O erro que este projeto quase comete não é "rio errado", é OUTRO PONTO DO
    RIO CERTO — e cada ponto tem o seu zero.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def roda(self, estacoes, excecoes=None):
        vd.erros.clear()
        vd.avisos.clear()
        orig_le, orig_exc = vd.le_json, vd.PINO_LONGE_DA_REGUA
        vd.le_json = lambda nome: estacoes if nome == "estacoes.json" else orig_le(nome)
        if excecoes is not None:
            vd.PINO_LONGE_DA_REGUA = excecoes
        try:
            vd.valida_codigo_ana()
        finally:
            vd.le_json, vd.PINO_LONGE_DA_REGUA = orig_le, orig_exc
        return list(vd.erros), list(vd.avisos)

    def liga(self, rio, cidade, codigo):
        d = copy.deepcopy(self.real)
        c = _cidade(d, rio, cidade)
        c["codigo_ana"] = codigo
        c["codigo_ana_sucessor"] = None
        c["codigo_ana_sucessor_nota"] = "irrelevante para este teste"
        return d

    def test_dados_reais_passam(self):
        self.assertEqual(self.roda(copy.deepcopy(self.real))[0], [])

    def test_as_tres_estacoes_em_cima_do_tracado_agora_reprovam(self):
        """
        WARNOW (0,06 km do traçado), ILHOTA-JUSANTE (0,04 km) e
        BOTUVERA-MONTANTE (0,04 km): antes deste guarda, as três passavam.
        """
        casos = [("itajai-acu", "indaial", "83520000", "3.93"),
                 ("itajai-acu", "ilhota", "83870001", "1.18"),
                 ("itajai-mirim", "botuvera", "83892998", "3.47")]
        for rio, cidade, codigo, km in casos:
            with self.subTest(cidade=cidade):
                erros, _ = self.roda(self.liga(rio, cidade, codigo))
                doente = [e for e in erros if cidade in e and "do pino desta cidade" in e]
                self.assertTrue(doente, f"{codigo} ligada a {cidade} e o validador calou")
                self.assertIn(km, doente[0], "a distância medida entrou errada no aviso")

    def test_a_excecao_do_blumenau_segura_o_vinculo_real(self):
        """6,94 km, e com motivo escrito: o pino é da estação de CHUVA."""
        erros, _ = self.roda(copy.deepcopy(self.real))
        self.assertFalse([e for e in erros if "blumenau" in e])

    def test_sem_a_excecao_o_blumenau_reprovaria(self):
        """Se o guarda não medisse, este teste passaria por engano."""
        erros, _ = self.roda(copy.deepcopy(self.real), excecoes={})
        self.assertTrue([e for e in erros if "blumenau" in e and "6.94" in e],
                        "o guarda não está medindo o vínculo real de Blumenau")

    def test_excecao_que_nao_e_usada_vira_aviso(self):
        _, avisos = self.roda(copy.deepcopy(self.real),
                              excecoes={**vd.PINO_LONGE_DA_REGUA, "taio": "sem razão"})
        self.assertTrue(any("taio" in a and "mobília" in a for a in avisos))

    def test_ibirama_continua_indecidida_apesar_dos_476_m(self):
        """
        O contraexemplo vivo: 476 m PASSA no guarda e a decisão continua aberta,
        porque falta o traçado do Hercílio para saber se há confluência entre os
        dois pontos. Se alguém ligar a 83440000 tratando o guarda como prova,
        este teste cai — que é exatamente o erro que o guarda existe para achar.
        """
        ibirama = _cidade(copy.deepcopy(self.real), "itajai-acu", "ibirama")
        self.assertIsNone(ibirama.get("codigo_ana"),
                          "Ibirama foi vinculada sem a conferência do Hercílio")
        candidatas = [c["codigo"] for c in ibirama.get("codigo_ana_candidatos") or []]
        self.assertIn("83440000", candidatas, "a candidata sumiu do cadastro")

    def test_o_limite_diz_por_extenso_que_nao_e_prova(self):
        """Passar no guarda é condição necessária, não suficiente — em código."""
        fonte = (vd.RAIZ / "scripts" / "validar_dados.py").read_text(encoding="utf-8")
        trecho = fonte.split("LIMITE_MESMA_REGUA_KM = ")[0][-2200:]
        self.assertIn("NÃO PROVA", trecho)
        self.assertIn("Ibirama", trecho)


class RessalvaDasCotasChegaNaTela(unittest.TestCase):
    """
    Apontamento do Jefferson, 08/09/2026: algumas cidades mudam de estado
    prevendo a DESCIDA da água das cidades de cima, com o nível daqui baixo.

    O projeto já sabia — está em `cotas_ressalva` de Brusque desde 07/09, com o
    evento medido: a Defesa Civil declarou atenção com a régua de Brusque em
    3,49 m, olhando Vidal Ramos e Botuverá. E a TELA não lia esse campo, nem
    nenhum irmão dele: cinco cidades com ressalva, zero chegando à página.
    """

    @classmethod
    def setUpClass(cls):
        cls.real = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def roda(self, estacoes):
        vd.erros.clear()
        vd.avisos.clear()
        orig = vd.le_json
        vd.le_json = lambda nome: estacoes if nome == "estacoes.json" else orig(nome)
        try:
            vd.valida_ressalva_chega_na_tela()
        finally:
            vd.le_json = orig
        return list(vd.erros), list(vd.avisos)

    def test_dados_reais_passam(self):
        self.assertEqual(self.roda(copy.deepcopy(self.real))[0], [])

    def test_ressalva_sem_decisao_aborta(self):
        d = copy.deepcopy(self.real)
        _cidade(d, "itajai-mirim", "brusque").pop("cotas_aviso_publico")
        erros, _ = self.roda(d)
        self.assertTrue(any("brusque" in e and "chega à tela" in e for e in erros))

    def test_dispensa_explicita_passa(self):
        d = copy.deepcopy(self.real)
        c = _cidade(d, "itajai-mirim", "brusque")
        c.pop("cotas_aviso_publico")
        c["cotas_aviso_publico_nao_precisa"] = "porque sim"
        self.assertEqual(self.roda(d)[0], [])

    def test_mostrar_e_dispensar_ao_mesmo_tempo_aborta(self):
        d = copy.deepcopy(self.real)
        _cidade(d, "itajai-mirim", "brusque")["cotas_aviso_publico_nao_precisa"] = "x"
        erros, _ = self.roda(d)
        self.assertTrue(any("se contradizem" in e for e in erros))

    def test_dispensa_orfa_vira_aviso(self):
        """A ressalva saiu e a justificativa ficou."""
        d = copy.deepcopy(self.real)
        c = _cidade(d, "itajai-acu", "ascurra")
        c.pop("cotas_ressalva")
        _, avisos = self.roda(d)
        self.assertTrue(any("ascurra" in a and "dispensar" in a for a in avisos))

    def test_aviso_publico_longo_aborta(self):
        d = copy.deepcopy(self.real)
        _cidade(d, "itajai-mirim", "brusque")["cotas_aviso_publico"] = "x" * 421
        erros, _ = self.roda(d)
        self.assertTrue(any("421 caracteres" in e for e in erros))

    def test_a_ressalva_de_brusque_nao_cita_mais_a_cota_que_saiu(self):
        """
        A versão de 07/09 dizia "a nossa `atencao` de 4,80 m" e que o site
        pintava mais CALMO que a Defesa Civil. As duas coisas venceram no mesmo
        dia: os 4,80 m saíram de cotas_m e entrou a escala municipal de 3,00 m.
        Ficou desatualizada por um dia — este teste é o que impede o retorno.
        """
        brusque = _cidade(copy.deepcopy(self.real), "itajai-mirim", "brusque")
        self.assertEqual(brusque["cotas_m"].get("atencao"), 3.0)
        texto = brusque["cotas_ressalva"]
        self.assertIn("VENCERAM", texto, "a ressalva voltou a afirmar o que já venceu")
        self.assertIn("cotas_substituidas_em_2026_09_07", texto)

    def test_o_que_a_tela_mostra_nao_repete_o_texto_interno(self):
        for rio in self.real["rios"].values():
            for c in rio["cidades"]:
                publico = c.get("cotas_aviso_publico")
                if not publico:
                    continue
                with self.subTest(cidade=c["id"]):
                    for marca in ("cotas_m", ".json", "docs/", "`"):
                        self.assertNotIn(marca, publico,
                                         "prosa de projeto vazou para a tela")


if __name__ == "__main__":
    unittest.main()
