#!/usr/bin/env python3
"""
As escadas de cota deste repositório concordam entre si?

POR QUE ESTE ARQUIVO EXISTE (08/09/2026). Emprestado do repo Premercado, que
aprendeu isto em produção: o mesmo indicador tinha duas contas com o mesmo
nome e elas divergiam em silêncio — "RSI 64,6" num painel e "RSI 67,2" no
outro, mesmo ticker, mesmo instante. A lição que o playbook de lá tira é
direta: *indicador com mais de uma implementação é um bug esperando para
acontecer, e quando a duplicação for inevitável, amarre as cópias com um
teste.*

Aqui a grandeza duplicada é **a faixa de aviso**, que é o que pinta a cor da
tela e o que decide se o bot toca. Ela é calculada em QUATRO lugares:

    scripts/alerta_cotas.py   FAIXAS               decide se o bot AVISA
    scripts/bot.py            ORDEM_COTAS          ordem em que o bot LISTA
    scripts/validar_dados.py  ORDEM_DAS_FAIXAS     ordem que o validador COBRA
    web/.../tempoReal.ts      CHAVES_QUE_PINTAM    o que a tela PINTA

E elas não concordavam. Duas divergências, achadas ao escrever este arquivo:

1. VIVA — `alerta_cotas.FAIXAS` não tem `monitoramento`. Taió tem
   `monitoramento: 5,00 m`, então entre 5,00 e 7,00 m a TELA acende o pino e o
   BOT fica calado. Taió estava em 4,54 m quando isto foi escrito: 46 cm
   abaixo do limiar. Se é para o bot calar ali, é decisão legítima — mas
   estava implícita, e implícito não se revisa.

2. LATENTE — `validar_dados` cobra `inundacao` ANTES de `emergencia`;
   `bot.ORDEM_COTAS` lista `emergencia` antes de `inundacao`. Nenhuma cidade
   tem as duas hoje, então ninguém viu. No dia em que tiver, o validador exige
   uma ordem e o bot mostra a outra — a escada que sobe e desce que o próprio
   comentário do bot diz ser "pior que não mostrar".

Este arquivo não decide qual está certa. Ele impede que a discordância volte a
ser invisível.
"""
import json
import re
import unittest
from pathlib import Path

import alerta_cotas
import bot
import validar_dados as vd
from comum import DADOS

RAIZ = Path(__file__).resolve().parent.parent
TEMPO_REAL_TS = RAIZ / "web" / "src" / "logica" / "tempoReal.ts"


def chaves_que_pintam_do_site() -> set[str]:
    """Lê o conjunto do TypeScript. Sem isto, o lado do site fica de fora."""
    texto = TEMPO_REAL_TS.read_text(encoding="utf-8")
    bloco = re.search(r"CHAVES_QUE_PINTAM\s*=\s*new Set\(\[(.*?)\]\)", texto, re.S)
    assert bloco, "CHAVES_QUE_PINTAM sumiu ou mudou de forma em tempoReal.ts"
    return set(re.findall(r"'([^']+)'", bloco.group(1)))


class AsQuatroEscadas(unittest.TestCase):
    def test_o_site_e_o_validador_pintam_o_mesmo_conjunto(self):
        self.assertEqual(chaves_que_pintam_do_site(), set(vd.ORDEM_DAS_FAIXAS))

    def test_o_bot_conhece_toda_faixa_que_a_tela_pinta(self):
        """
        O bot pode conhecer MAIS (tem `observacao_cota` e `inundacao_historica`,
        que não pintam). O que não pode é a tela pintar algo que o bot não sabe
        nomear — aí a régua acende e a resposta do /cotas não a lista.
        """
        faltam = set(vd.ORDEM_DAS_FAIXAS) - set(bot.ORDEM_COTAS)
        self.assertEqual(faltam, set(), f"a tela pinta e o bot não conhece: {faltam}")

    #: `inundacao` e `emergencia` são O MESMO DEGRAU com nomes municipais
    #: diferentes — o topo, logo acima de `alerta`. Rio do Sul (alerta 5,50 →
    #: inundação 6,50) e Blumenau (6,50 → 7,40) usam um nome; Taió, Indaial,
    #: Gaspar, Ilhota, Ibirama, Brusque, Rio dos Cedros e as onze réguas DC de
    #: Itajaí usam o outro. NENHUMA cidade usa os dois.
    #:
    #: Foi isto que resolveu a discordância aparente entre as escadas do bot e
    #: do validador: elas ordenam os dois nomes de formas opostas, e a pergunta
    #: "qual vem primeiro" é MAL FORMADA, porque eles não convivem. Rebatizar
    #: um para caber no outro é o que o comentário de `bot.ROTULO_COTA` proíbe:
    #: a tela passaria a chamar de "emergência" o que a COMPDEC chama de
    #: inundação.
    TOPO_COM_DOIS_NOMES = {"inundacao", "emergencia"}

    def test_bot_e_validador_concordam_na_ordem_das_faixas_que_convivem(self):
        """
        Fora do topo de dois nomes, as duas escadas têm de dar a mesma ordem.
        """
        def sem_o_topo(seq):
            return [f for f in seq if f in vd.ORDEM_DAS_FAIXAS and f not in self.TOPO_COM_DOIS_NOMES]
        self.assertEqual(
            sem_o_topo(bot.ORDEM_COTAS), sem_o_topo(vd.ORDEM_DAS_FAIXAS),
            "bot.ORDEM_COTAS e validar_dados.ORDEM_DAS_FAIXAS discordam da ordem em que a "
            "água sobe. A tela e o bot mostrariam escadas diferentes para a mesma cidade.")

    def test_os_dois_nomes_do_topo_ficam_NO_topo_das_duas_escadas(self):
        """A ordem entre eles é indiferente; a posição, não."""
        for nome, escada in (("bot", bot.ORDEM_COTAS), ("validador", vd.ORDEM_DAS_FAIXAS)):
            conhecidas = [f for f in escada if f in vd.ORDEM_DAS_FAIXAS]
            topo = [f for f in conhecidas if f in self.TOPO_COM_DOIS_NOMES]
            with self.subTest(escada=nome):
                self.assertEqual(conhecidas[-len(topo):], topo,
                                 f"em {nome}, algo do topo ficou abaixo de outra faixa")

    def test_nenhuma_cidade_usa_os_DOIS_nomes_do_topo(self):
        """
        O tripwire. Enquanto nenhuma cidade publicar os dois como degraus
        distintos, a pergunta "qual é mais alto" não precisa de resposta. No dia
        em que alguma publicar, este teste cai e alguém decide COM a fonte na
        mão, em vez de descobrir a discordância durante uma cheia.
        """
        est = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        conjuntos = []
        for rio in est["rios"].values():
            for c in rio["cidades"]:
                conjuntos.append((c["nome"], c.get("cotas_m") or {}))
        for e in est["estacoes_tempo_real"]:
            conjuntos.append((e.get("codigo") or e.get("titulo", "?"), e.get("cotas_m") or {}))
        com_os_dois = [n for n, c in conjuntos if self.TOPO_COM_DOIS_NOMES <= set(c)]
        self.assertEqual(com_os_dois, [], f"agora convivem em {com_os_dois} — decidir a ordem")

    def test_o_bot_de_aviso_cobre_toda_faixa_que_a_tela_pinta(self):
        """
        A divergência VIVA. `alerta_cotas.FAIXAS` decide se o aviso sai; se a
        tela pinta uma faixa que não está lá, o pino acende sem o bot tocar.

        Se a decisão for que `monitoramento` não deve disparar aviso — o que é
        defensável, é a fase que a COMPDEC observa sem anunciar —, então ela
        precisa estar ESCRITA, num conjunto próprio com o motivo, e este teste
        passa a conferir contra ele. O que não pode é a ausência parecer
        esquecimento.
        """
        pinta = set(vd.ORDEM_DAS_FAIXAS)
        avisa = set(alerta_cotas.FAIXAS) - {"normal"}
        nao_dispara = set(getattr(alerta_cotas, "NAO_DISPARAM_AVISO", ()))
        descobertas = pinta - avisa - nao_dispara
        self.assertEqual(
            descobertas, set(),
            f"a tela pinta {sorted(descobertas)} e o bot não avisa nesta faixa. Se for "
            "de propósito, declare em alerta_cotas.NAO_DISPARAM_AVISO com o motivo.")


class AEscadaContraODadoReal(unittest.TestCase):
    """
    Escada consistente no código não basta: o cadastro tem de caber nela.
    """

    @classmethod
    def setUpClass(cls):
        est = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
        cls.conjuntos = []
        for rio in est["rios"].values():
            for c in rio["cidades"]:
                if c.get("cotas_m"):
                    cls.conjuntos.append((c["nome"], c["cotas_m"]))
        for e in est["estacoes_tempo_real"]:
            if e.get("cotas_m"):
                cls.conjuntos.append((e.get("codigo") or e.get("titulo", "?"), e["cotas_m"]))

    def test_bot_e_site_dao_a_MESMA_faixa_para_todo_nivel(self):
        """
        A conta do bot escolhe pela POSIÇÃO na escada; a do site escolhe pelo
        MAIOR VALOR. Só coincidem enquanto o cadastro for monotônico — e é o
        validador que garante isso, num terceiro arquivo. Este teste é o que
        liga as três pontas.
        """
        pintam = list(vd.ORDEM_DAS_FAIXAS)
        for nome, cotas in self.conjuntos:
            valores = sorted(v for v in cotas.values() if isinstance(v, (int, float)))
            if not valores:
                continue
            # Um centímetro abaixo, em cima e acima de cada degrau: é onde as
            # duas contas se separariam se fossem separar.
            niveis = [valores[0] - 0.01, valores[-1] + 5]
            niveis += valores + [v + 0.01 for v in valores]
            for n in niveis:
                pelo_site = self._faixa_do_site(pintam, cotas, n)
                pelo_bot = alerta_cotas.faixa_de(n, cotas)
                if pelo_bot == "normal" and pelo_site not in ("normal",) and \
                        pelo_site not in set(alerta_cotas.FAIXAS):
                    # Faixa que o bot não conhece: coberto pelo teste de cima,
                    # e repetir aqui só duplicaria a mesma falha.
                    continue
                with self.subTest(regua=nome, nivel=n):
                    self.assertEqual(pelo_bot, pelo_site)

    @staticmethod
    def _faixa_do_site(pintam, cotas, nivel):
        """Reproduz `cotaAlcancadaEntre`: a de MAIOR VALOR entre as alcançadas."""
        maior = None
        for chave in pintam:
            valor = cotas.get(chave)
            if not isinstance(valor, (int, float)) or nivel < valor:
                continue
            if maior is None or valor > maior[1]:
                maior = (chave, valor)
        return maior[0] if maior else "normal"


if __name__ == "__main__":
    unittest.main(verbosity=2)
