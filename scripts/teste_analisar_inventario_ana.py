"""O crash que truncou a análise do inventário, travado por teste.

Em 08/09/2026 a primeira análise do inventário da ANA foi um heredoc colado no
terminal. Ela quebrou no meio da lista, num `i.get(chave, "")[:7]`: quando a
chave EXISTE com valor None, o `.get` devolve None e o default nunca entra.

A saída ficou truncada ANTES de chegar às estações do Itajaí, e parecia dizer
que a bacia não tem estação de nível. Análise que morre no meio mente por
omissão — e o dado real da ANA está cheio de campos nulos, então isto ia
acontecer de qualquer jeito.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from analisar_inventario_ana import (
    NOSSAS,
    e_da_bacia,
    main,
    mede_nivel,
    numero,
    relatorio,
    texto,
    uf_incoerente,
)


def _estacao(**campos) -> dict:
    base = {
        "codigoestacao": "83800002", "Estacao_Nome": "BLUMENAU", "Rio_Nome": "RIO ITAJAI-ACU",
        "Municipio_Nome": "BLUMENAU", "UF_Estacao": "SC",
        "Latitude": "-26.9186", "Longitude": "-49.0656",
        "Tipo_Estacao_Escala": "1", "Tipo_Estacao_Registrador_Nivel": "0",
        "Tipo_Estacao_Telemetrica": "0", "Operando": "1",
        "Data_Periodo_Escala_Inicio": None, "Data_Periodo_Escala_Fim": None,
        "Data_Periodo_Telemetrica_Inicio": None, "Data_Periodo_Telemetrica_Fim": None,
    }
    base.update(campos)
    return base


class NuncaFatiaNone(unittest.TestCase):
    """O bug exato que truncou a saída."""

    def test_none_vira_travessao(self):
        self.assertEqual(texto(None), "—")
        self.assertEqual(texto(None, 7), "—")
        self.assertEqual(texto(""), "—")

    def test_corta_sem_explodir(self):
        self.assertEqual(texto("2011-09-01 00:00:00.0", 7), "2011-09")

    def test_o_relatorio_atravessa_uma_estacao_toda_nula(self):
        """
        A prova real: uma estação com TODOS os campos de período nulos não pode
        derrubar o relatório. Antes, ela o matava na primeira linha.
        """
        nulas = [_estacao(codigoestacao=str(i), Data_Periodo_Escala_Inicio=None)
                 for i in range(5)]
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            relatorio(nulas)  # não levanta
        self.assertIn("RIO ITAJAI-ACU", saida.getvalue(),
                      "o relatório parou antes de listar a bacia")


class SeparaOItajaiDasBaciasVizinhas(unittest.TestCase):
    def test_coordenada_sozinha_nao_basta(self):
        """
        Foi assim que Tijucas, Itapocu e Cubatão entraram na primeira lista: a
        caixa pega as bacias vizinhas, e só o nome do rio as separa.
        """
        vizinha = _estacao(Rio_Nome="RIO TIJUCAS", Latitude="-27.30", Longitude="-48.95")
        self.assertFalse(e_da_bacia(vizinha), "uma estação do Tijucas passou por Itajaí")

    def test_o_acu_entra(self):
        self.assertTrue(e_da_bacia(_estacao()))

    def test_afluentes_da_bacia_entram(self):
        for rio in ("RIO HERCILIO", "RIO BENEDITO", "RIO ITAJAI-MIRIM"):
            with self.subTest(rio=rio):
                self.assertTrue(e_da_bacia(_estacao(Rio_Nome=rio)))

    def test_fora_da_caixa_nao_entra_mesmo_com_o_nome_certo(self):
        longe = _estacao(Rio_Nome="RIO ITAJAI-ACU", Latitude="-20.82", Longitude="-45.06")
        self.assertFalse(e_da_bacia(longe))


class MedeNivelEhPorTipo(unittest.TestCase):
    def test_escala_conta(self):
        self.assertTrue(mede_nivel(_estacao(Tipo_Estacao_Escala="1")))

    def test_registrador_conta(self):
        self.assertTrue(mede_nivel(_estacao(Tipo_Estacao_Escala="0",
                                            Tipo_Estacao_Registrador_Nivel="1")))

    def test_pluviometro_puro_nao_conta(self):
        """
        A regra emendada do projeto: o vínculo é por coordenada E POR TIPO.
        Quatro pluviômetros caem a menos de 750 m de uma régua nossa.
        """
        chuva = _estacao(Tipo_Estacao_Escala="0", Tipo_Estacao_Registrador_Nivel="0")
        self.assertFalse(mede_nivel(chuva))


class UfIncoerenteEhMedidoNaoSuposto(unittest.TestCase):
    def test_acha_a_estacao_de_minas(self):
        """O caso real: CGH ANIL JUSANTE, UF_Estacao SC, coordenada em MG."""
        mg = _estacao(codigoestacao="2045036", Latitude="-20.8242", Longitude="-45.0639")
        self.assertEqual(len(uf_incoerente([mg, _estacao()])), 1)

    def test_sem_coordenada_nao_e_acusado(self):
        """Sem coordenada não se pode afirmar incoerência — só ausência."""
        self.assertEqual(uf_incoerente([_estacao(Latitude=None, Longitude=None)]), [])


class OsRotulosNaoConfundemSondaComVinculo(unittest.TestCase):
    def test_as_recusadas_estao_marcadas(self):
        """
        Quatro das estações que o projeto nomeia são RECUSAS escritas em
        `codigo_ana_nao_e`. Se a saída as listasse sem esse rótulo, ela
        convidaria ao pareamento que o Salseiro quase fez em Vidal Ramos.
        """
        for codigo in ("83250000", "83520000", "83870001", "83892990", "83892998"):
            with self.subTest(codigo=codigo):
                self.assertIn("RECUSADA", NOSSAS[codigo])

    def test_ibirama_e_candidata_com_decisao_aberta(self):
        self.assertIn("decisão aberta", NOSSAS["83440000"])


class ArquivoRuimFalhaComRecado(unittest.TestCase):
    def _roda(self, conteudo) -> int:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "inv.json"
            p.write_text(json.dumps(conteudo), encoding="utf-8")
            return main.__wrapped__(p) if hasattr(main, "__wrapped__") else self._via_argv(p)

    def _via_argv(self, p: Path) -> int:
        import sys
        argv = sys.argv
        sys.argv = ["analisar_inventario_ana.py", str(p)]
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                return main()
        finally:
            sys.argv = argv

    def test_sem_items_sai_com_erro(self):
        self.assertEqual(self._roda({"status": "OK"}), 1)

    def test_com_items_passa(self):
        self.assertEqual(self._roda({"items": [_estacao()]}), 0)


class NumeroToleraLixo(unittest.TestCase):
    def test_converte_e_recusa(self):
        self.assertEqual(numero("-26.9186"), -26.9186)
        for ruim in (None, "", "N/A", "sul"):
            self.assertIsNone(numero(ruim))


if __name__ == "__main__":
    unittest.main()
