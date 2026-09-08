#!/usr/bin/env python3
"""
Testes da auditoria de lacunas.

O relatório existe para ORDENAR a busca. Errar a topologia inverte o pedido —
mandar ofício a Ascurra por um elo que na verdade falta em Indaial —, e errar a
contagem de cotas apaga um buraco real da lista. Os dois casos estão travados
aqui.
"""
import json
import tempfile
import unittest
from pathlib import Path

import auditar_lacunas as al
from comum import DADOS


def cidade(id_, **campos):
    base = {"id": id_, "nome": id_.title(), "cotas_m": {}, "coordenadas": [-27.0, -49.0]}
    base.update(campos)
    return base


class ProximaAJusante(unittest.TestCase):
    """O Açu é ÁRVORE, não fila: a posição vem de ramo + ordem_no_ramo."""

    def setUp(self):
        self.est = {
            "rios": {
                "itajai-acu": {
                    "_topologia": {
                        "tronco_sequencia": ["rio-do-sul", "indaial", "itajai"],
                        "cabeceiras_paralelas": ["taio", "ituporanga"],
                        "confluencia_cabeceiras": {"nasce": "rio-do-sul"},
                        "afluentes_laterais": [
                            {"id": "timbo", "entra_perto_de": "indaial"}
                        ],
                    },
                    "cidades": [
                        cidade("taio", ramo="oeste", ordem_no_ramo=1),
                        cidade("ituporanga", ramo="sul", ordem_no_ramo=1),
                        cidade("rio-do-sul", ramo="tronco_acu", ordem_no_ramo=1),
                        cidade("indaial", ramo="tronco_acu", ordem_no_ramo=2),
                        cidade("itajai", ramo="tronco_acu", ordem_no_ramo=3),
                        cidade("timbo", ramo="benedito", ordem_no_ramo=1),
                        cidade("solta"),
                    ],
                },
                "itajai-mirim": {
                    "cidades": [
                        cidade("brusque", ordem=1),
                        cidade("itajai", ordem=2),
                    ]
                },
            }
        }

    def jusante(self, rio, id_):
        c = next(x for x in self.est["rios"][rio]["cidades"] if x["id"] == id_)
        return al.proxima_a_jusante(self.est, rio, c)

    def test_tronco_segue_a_sequencia(self):
        self.assertEqual(self.jusante("itajai-acu", "rio-do-sul"), "indaial")

    def test_foz_nao_tem_jusante(self):
        self.assertIsNone(self.jusante("itajai-acu", "itajai"))

    def test_cabeceiras_paralelas_caem_na_confluencia(self):
        """Taió e Ituporanga são PARALELAS: nenhuma é jusante da outra."""
        self.assertEqual(self.jusante("itajai-acu", "taio"), "rio-do-sul")
        self.assertEqual(self.jusante("itajai-acu", "ituporanga"), "rio-do-sul")

    def test_afluente_lateral_entra_onde_a_fonte_declara(self):
        self.assertEqual(self.jusante("itajai-acu", "timbo"), "indaial")

    def test_cidade_sem_posicao_nao_ganha_jusante_inventado(self):
        """Trombudo Central é o caso real: a fonte diz o rio, não a confluência."""
        self.assertIsNone(self.jusante("itajai-acu", "solta"))

    def test_rio_em_fila_usa_ordem(self):
        self.assertEqual(self.jusante("itajai-mirim", "brusque"), "itajai")


class ContagemDeCotas(unittest.TestCase):
    """Cota incompleta não é o mesmo buraco que cota ausente."""

    def test_faixas_essenciais_sao_atencao_e_alerta(self):
        self.assertEqual(al.FAIXAS_ESSENCIAIS, ("atencao", "alerta"))

    def test_cota_so_de_atencao_nao_conta_como_completa(self):
        """Brusque é o caso real: tem atenção e inundação, falta alerta."""
        cotas = {"atencao": 3.0, "inundacao": 5.0}
        self.assertFalse(all(f in cotas for f in al.FAIXAS_ESSENCIAIS))
        self.assertTrue(bool(cotas))


class PorQueFaltaOElo(unittest.TestCase):
    """
    A auditoria imprimia os dez elos ausentes como lista de tarefas. Um deles
    não é: Indaial -> Blumenau tem as duas pontas na JICA e a diferença é ZERO
    ou NEGATIVA, porque o Benedito entra entre as duas e adianta o pico de
    baixo. Preencher um positivo ali daria a quem está em Blumenau horas que
    não existem — que é a única coisa que este projeto não pode fazer.
    """

    FONTE = {
        "cidades_na_tabela": ["taio", "ibirama", "rio-do-sul", "timbo", "ituporanga",
                              "brusque", "indaial", "blumenau", "gaspar", "ilhota", "itajai"],
        "relogio_proprio": ["timbo", "ibirama", "brusque"],
    }
    TABELA = {
        "indaial":  {"5": 10, "10": 9, "25": 8, "50": 8},
        "blumenau": {"5": 10, "10": 9, "25": 7, "50": 7},
        "gaspar":   {"5": 12, "10": 11, "25": 9, "50": 8},
        "timbo":    {"5": 0, "10": 0, "25": 0, "50": 0},
    }

    def classe(self, de, para):
        return al.por_que_falta_o_elo(de, para, self.FONTE, self.TABELA)[0]

    def motivos(self, de, para):
        return al.por_que_falta_o_elo(de, para, self.FONTE, self.TABELA)[1]

    def test_indaial_blumenau_nao_e_tempo_de_transito(self):
        self.assertEqual(self.classe("indaial", "blumenau"), "nao_positivo")
        texto = " ".join(self.motivos("indaial", "blumenau"))
        self.assertIn("-1 h", texto, "tem de MOSTRAR o número negativo, não só dizer que é")
        self.assertIn("Benedito", texto)

    def test_diferenca_positiva_em_todas_as_colunas_nao_vira_nao_positivo(self):
        """Blumenau -> Gaspar é +2/+2/+2/+1: existe e é um trânsito de verdade."""
        self.assertEqual(self.classe("blumenau", "gaspar"), "sem_tempo_de_fonte")

    def test_cidade_fora_da_tabela_vale_procurar(self):
        self.assertEqual(self.classe("rio-do-sul", "lontras"), "sem_tempo_de_fonte")
        self.assertIn("não lista lontras", " ".join(self.motivos("rio-do-sul", "lontras")))

    def test_relogio_proprio_so_vale_no_elo_de_CONFLUENCIA(self):
        """
        `timbo → indaial` é afluente→tronco, e o relógio próprio é exatamente a
        razão de não haver viagem ali. Mas quem sabe que o elo é de confluência
        é `tipo_do_elo`, olhando a topologia — esta função recebe o veredito.

        Chamada sem o tipo, ela responderia pela FONTE ("a JICA cobre as duas
        pontas"), que é verdade e é irrelevante: o problema não é falta de
        documento, é que a grandeza não existe.
        """
        tipo, motivos = al.por_que_falta_o_elo(
            "timbo", "indaial", self.FONTE, self.TABELA, "confluencia")
        self.assertEqual(tipo, "confluencia")
        self.assertIn("relógio próprio", " ".join(motivos))
        self.assertIn("nem uma cheia medida", " ".join(motivos))

    def test_guabiruba_brusque_nao_e_classificado_por_relogio_proprio_sozinho(self):
        """
        Erro real da primeira versão: olhava `relogio_proprio` sem checar antes
        se a cidade está na tabela, e classificou Guabiruba -> Brusque como
        relógio próprio. O relógio próprio de Brusque vale em relação ao AÇU;
        Guabiruba é vizinha dela no MIRIM. O que falta ali é a JICA não listar
        Guabiruba, e isso tem de aparecer.
        """
        motivos = " ".join(self.motivos("guabiruba", "brusque"))
        self.assertIn("não lista guabiruba", motivos)

    def test_rio_dos_cedros_timbo_tem_um_motivo_so_e_o_certo(self):
        """
        Este teste exigia DOIS motivos — "a de cima não está na tabela E a de
        baixo tem relógio próprio". O segundo estava errado, e o teste guardava
        o erro: Rio dos Cedros e Timbó estão os dois no Benedito/Cedros, então
        a viagem acontece, e o relógio próprio de Timbó é justamente o que ela
        explica. Dar isso como motivo de o trecho faltar inverte a leitura.

        Sobra o motivo verdadeiro, sozinho: a JICA não lista Rio dos Cedros.
        """
        motivos = self.motivos("rio-dos-cedros", "timbo")
        self.assertEqual(motivos, ["a Tabela 7.5.1 da JICA não lista rio-dos-cedros"])

    def test_bate_com_o_transito_real_do_repositorio(self):
        """A classificação tem de rodar sobre o dado de verdade sem estourar."""
        t = al.le("transito.json")["_meta"]["origem_das_faixas"]
        tabela = t["tabela_7_5_1"]["matriz_horas_por_periodo_de_retorno"]
        classe, motivos = al.por_que_falta_o_elo("indaial", "blumenau", t, tabela)
        self.assertEqual(classe, "nao_positivo")
        self.assertTrue(motivos)


class MinimoDaPrevisao(unittest.TestCase):
    def test_bate_com_o_que_o_claude_md_manda(self):
        """< 5 eventos = 'dados insuficientes', não estimativa."""
        self.assertEqual(al.PARES_MINIMOS, 5)


class ColunaNaoMedidaNaoViraAusencia(unittest.TestCase):
    """
    `—` significa "medido e ausente". Coluna não medida sai `?`.

    O auditor só preenche a coluna de leitura ao vivo quando recebe
    `--ao-vivo`. Sem isso ela saía `—` para TODAS as cidades, e o documento
    passava a afirmar que nenhuma delas publica nível. Era falso — sete
    publicavam — e mandava procurar fonte para cidade que já tem: Taió, Rio do
    Sul, Blumenau, Itajaí (nos dois rios), Vidal Ramos e Brusque estavam na
    lista de busca sem precisar estar.

    O aviso existia, mas só no terminal, que rola e some. O documento é o que
    fica no repositório e o que alguém lê meses depois.

    Os relatórios aqui vêm de `auditar()` sobre os dados REAIS, e não de um
    dicionário montado à mão: fixture inventado sai da forma real sem avisar,
    e este teste existe justamente para pegar coluna que mente.
    """

    @classmethod
    def setUpClass(cls):
        cls.sem = al.auditar(None)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as t:
            json.dump({"leituras": [
                {"estacao": "Taió", "cidade": "taio", "rio": "itajai-acu",
                 "nivel_m": 5.15, "medido_em": "2026-09-07T18:35:00"},
            ]}, t, ensure_ascii=False)
            cls.caminho = Path(t.name)
        cls.com = al.auditar(cls.caminho)

    @classmethod
    def tearDownClass(cls):
        cls.caminho.unlink(missing_ok=True)

    def linha_de(self, md: str, nome: str) -> str:
        return next(l for l in md.splitlines() if l.startswith(f"| {nome} |"))

    def test_sem_medicao_a_coluna_sai_interrogacao(self):
        md = al.markdown(self.sem)
        self.assertIn("| ? |", self.linha_de(md, "Taió"))

    def test_sem_medicao_o_documento_avisa(self):
        """O aviso tem de estar no DOCUMENTO, não só no terminal."""
        md = al.markdown(self.sem)
        self.assertIn("não foi medida nesta execução", md)
        self.assertIn("--ao-vivo", md)

    def test_sem_medicao_a_lista_de_busca_nao_acusa_ninguem(self):
        md = al.markdown(self.sem)
        busca = md.split("### 1.")[1].split("###")[0]
        self.assertIn("não medido", busca)
        self.assertNotIn("**Taió**", busca)

    def test_com_medicao_a_coluna_volta_a_valer(self):
        md = al.markdown(self.com)
        self.assertNotIn("| ? |", self.linha_de(md, "Taió"))
        self.assertNotIn("não foi medida nesta execução", md)

    def test_com_medicao_quem_tem_leitura_sai_da_lista_de_busca(self):
        busca = al.markdown(self.com).split("### 1.")[1].split("###")[0]
        self.assertNotIn("**Taió**", busca)
        # e quem não tem continua nela
        self.assertIn("**Ituporanga**", busca)


class TipoDoElo(unittest.TestCase):
    """
    Medir e procurar são perguntas diferentes.

    `por_que_falta_o_elo` responde "adianta procurar na FONTE?". `tipo_do_elo`
    responde "adianta MEDIR?". Elas se separaram quando a série da rede
    estadual passou a permitir datar picos em dez cidades sem régua municipal:
    de repente todos os elos ficaram mensuráveis, e mensurável não é o mesmo
    que significativo.
    """

    @classmethod
    def setUpClass(cls):
        cls.est = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))

    def tipo(self, de, para, rio="itajai-acu"):
        return al.tipo_do_elo(self.est, rio, de, para)[0]

    def test_tronco_para_tronco_e_roteamento(self):
        """A cheia viaja mesmo: o vão entre os picos é a viagem."""
        self.assertEqual(self.tipo("rio-do-sul", "lontras"), "roteamento")
        self.assertEqual(self.tipo("lontras", "ascurra"), "roteamento")
        self.assertEqual(self.tipo("ascurra", "indaial"), "roteamento")

    def test_dentro_do_mesmo_afluente_e_roteamento(self):
        """
        Rio dos Cedros e Timbó estão os dois no Benedito/Cedros. A viagem
        acontece — e o "relógio próprio" de Timbó é justamente o que ela
        explica, não um motivo para o elo não existir.
        """
        self.assertEqual(self.tipo("rio-dos-cedros", "timbo"), "roteamento")

    def test_afluente_para_tronco_e_confluencia(self):
        """
        Aqui não há viagem: o pico do tronco vem da cheia que desce o tronco, o
        do afluente vem da chuva na sub-bacia dele. O vão é coincidência de
        hidrogramas — muda de valor e até de sinal a cada cheia.
        """
        self.assertEqual(self.tipo("ibirama", "rio-do-sul"), "confluencia")
        self.assertEqual(self.tipo("timbo", "indaial"), "confluencia")

    def test_a_explicacao_nomeia_o_afluente_e_o_rio_dele(self):
        _, porque = al.tipo_do_elo(self.est, "itajai-acu", "timbo", "indaial")
        self.assertIn("Benedito", porque)
        self.assertIn("coincidência", porque)

    def test_rio_em_fila_nao_tem_confluencia_a_declarar(self):
        """O Mirim não tem `_topologia`: sem afluente lateral declarado, todo elo é viagem."""
        self.assertEqual(self.tipo("vidal-ramos", "botuvera", rio="itajai-mirim"), "roteamento")
        self.assertEqual(self.tipo("guabiruba", "brusque", rio="itajai-mirim"), "roteamento")


class RelogioProprioNaoEMotivoDeEloDoMesmoCurso(unittest.TestCase):
    """
    `relogio_proprio` é uma afirmação sobre o elo com o TRONCO do Açu. Dentro do
    mesmo curso ela diz o contrário do certo, e chegou a sair impressa assim:

      * `rio-dos-cedros → timbo` ganhava "timbo tem relógio próprio" como
        motivo de o trecho faltar — quando é justamente a viagem pelo Benedito
        que esse relógio representa;
      * `guabiruba → brusque` ganhava "brusque tem relógio próprio" — e Brusque
        está no MIRIM, onde a marca não vale.

    O tipo já tinha sido corrigido antes; o TEXTO do motivo continuava saindo.
    """

    @classmethod
    def setUpClass(cls):
        cls.fonte = json.loads(
            (DADOS / "transito.json").read_text(encoding="utf-8")
        )["_meta"]["origem_das_faixas"]
        cls.tabela = cls.fonte["tabela_7_5_1"]["matriz_horas_por_periodo_de_retorno"]

    def motivos(self, de, para):
        return al.por_que_falta_o_elo(de, para, self.fonte, self.tabela)[1]

    def test_rio_dos_cedros_timbo_so_diz_o_que_e_verdade(self):
        motivos = self.motivos("rio-dos-cedros", "timbo")
        self.assertEqual(len(motivos), 1)
        self.assertIn("não lista rio-dos-cedros", motivos[0])
        self.assertNotIn("relógio próprio", " ".join(motivos))

    def test_guabiruba_brusque_so_diz_o_que_e_verdade(self):
        motivos = self.motivos("guabiruba", "brusque")
        self.assertEqual(len(motivos), 1)
        self.assertIn("não lista guabiruba", motivos[0])
        self.assertNotIn("relógio próprio", " ".join(motivos))

    def test_indaial_blumenau_continua_sendo_pego_pelos_numeros(self):
        """
        Tronco→tronco COM afluente no meio: `tipo_do_elo` não pega (a topologia
        diz `entra_perto_de`, não entre quais duas cidades). Quem pega é o
        `nao_positivo`, olhando a diferença na JICA.
        """
        tipo, motivos = al.por_que_falta_o_elo(
            "indaial", "blumenau", self.fonte, self.tabela)
        self.assertEqual(tipo, "nao_positivo")
        self.assertIn("Benedito", " ".join(motivos))



class EscalaQueMoraNasReguas(unittest.TestCase):
    """
    O auditor dizia **"Itajaí: sem cota nenhuma"** e mandava procurar o PDF do
    PLANCON — de uma cidade cujas ONZE réguas citam esse PDF por URL e cujos
    onze valores foram conferidos, 11 de 11, contra a versão 17.

    O `cotas_m` vazio da cidade está CERTO: Itajaí não tem uma escala, tem onze,
    uma por régua. Errado era ler o vazio como buraco. Buraco falso gasta o tempo
    de quem procura e ensina a desconfiar da lista inteira — que é o oposto do
    que uma lista de busca serve para fazer.
    """

    def monta(self, reguas):
        return {"estacoes_tempo_real": reguas}

    def test_regua_sem_a_escala_completa_nao_conta(self):
        est = self.monta([{"cidade": "x", "cotas_m": {"atencao": 1.0}}])
        self.assertEqual(al.cotas_nas_reguas(est, "x")["com_escala"], 0)

    def test_conta_so_as_reguas_daquela_cidade(self):
        est = self.monta([
            {"cidade": "x", "cotas_m": {"atencao": 1.0, "alerta": 2.0}},
            {"cidade": "y", "cotas_m": {"atencao": 1.0, "alerta": 2.0}},
        ])
        self.assertEqual(al.cotas_nas_reguas(est, "x"),
                         {"total": 1, "com_escala": 1, "conferidas": 0})

    def test_conferida_exige_o_campo_verificado(self):
        est = self.monta([
            {"cidade": "x", "cotas_m": {"atencao": 1.0, "alerta": 2.0}, "verificado": True},
            {"cidade": "x", "cotas_m": {"atencao": 1.0, "alerta": 2.0}},
        ])
        r = al.cotas_nas_reguas(est, "x")
        self.assertEqual((r["com_escala"], r["conferidas"]), (2, 1))

    def test_o_rotulo_tem_TRES_estados(self):
        """
        Achatar "a cidade tem a escala" e "a escala está nas réguas" num `—` só
        foi exatamente o que criou o buraco falso.
        """
        vazio = {"total": 0, "com_escala": 0, "conferidas": 0}
        self.assertEqual(al.rotulo_de_cota({"cotas_essenciais": True, "reguas": vazio}), "sim")
        self.assertEqual(al.rotulo_de_cota({"cotas_essenciais": False, "reguas": vazio}), "—")
        self.assertEqual(
            al.rotulo_de_cota({"cotas_essenciais": False,
                               "reguas": {"total": 12, "com_escala": 11, "conferidas": 11}}),
            "11×")


class ItajaiNaoEBuracoDeCotaNoDadoReal(unittest.TestCase):
    """Sobre o dado de verdade, não sobre fixture — foi o dado real que mentiu."""

    @classmethod
    def setUpClass(cls):
        cls.rel = al.auditar(None)
        cls.itajai = [l for l in cls.rel["linhas"] if l["id"] == "itajai"]

    def test_itajai_aparece_nos_dois_rios(self):
        self.assertEqual(len(self.itajai), 2, "a foz recebe o Açu e o Mirim")

    def test_itajai_nao_conta_como_sem_cota_nenhuma(self):
        for l in self.itajai:
            with self.subTest(rio=l["rio"]):
                self.assertFalse(l["cotas_nenhuma"],
                                 "11 réguas com escala conferida não é 'sem cota nenhuma'")

    def test_a_escala_de_itajai_esta_nas_reguas_e_sao_onze(self):
        for l in self.itajai:
            with self.subTest(rio=l["rio"]):
                self.assertTrue(l["escala_por_regua"])
                self.assertEqual(l["reguas"]["com_escala"], 11)

    def test_as_onze_estao_conferidas_na_fonte(self):
        """
        Conferidas 11 de 11 contra a Tabela 11 da v17 em 08/09/2026. Se alguém
        derrubar o `verificado`, o auditor volta a pedir busca por elas.
        """
        for l in self.itajai:
            with self.subTest(rio=l["rio"]):
                self.assertEqual(l["reguas"]["conferidas"], 11)

    def test_a_cidade_continua_SEM_cota_propria_e_isso_esta_certo(self):
        """
        A correção é no relatório, não no dado. Gravar uma "cota de Itajaí"
        para calar o auditor seria inventar um número que nenhuma régua publica.
        """
        for l in self.itajai:
            with self.subTest(rio=l["rio"]):
                self.assertEqual(l["cotas"], [])
                self.assertFalse(l["cotas_essenciais"])

    def test_nenhuma_outra_cidade_tem_escala_so_na_regua(self):
        """
        Se aparecer uma segunda, o texto do item 2 do Markdown — escrito no
        singular para Itajaí — precisa ser relido antes de valer.
        """
        ids = {l["id"] for l in self.rel["linhas"] if l["escala_por_regua"]}
        self.assertEqual(ids, {"itajai"}, ids)


if __name__ == "__main__":
    unittest.main()
