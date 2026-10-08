#!/usr/bin/env python3
"""Testes do importador da tábua de maré do Laboratório de Oceanografia Física da UNIVALI (Itajaí/SC).

O ponto mais delicado: `formatar()` NUNCA emite `altura_m` — a planilha não declara a referência vertical, e o
projeto não mostra número sem referência (mesmo problema que já é REGRA BLOQUEANTE para Blumenau). Um teste trava
isso: se `altura_m` vazar para o JSON, quebra. Os outros fixam a leitura da série de 5 min (08/10/2026): extremos
da curva, ondulação de estofo tirada aos pares, alternância preservada, e a fonte creditada à UNIVALI.

    python3 scripts/teste_importar_mare_univali.py
"""

import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path

from importar_mare_univali import (
    ONDULACAO_M,
    classificar_extremos,
    cruzar,
    eh_serie,
    extrair_eventos,
    extrair_serie,
    extremos_da_serie,
    filtrar_ondulacoes,
    formatar,
    montar,
    separar,
)

BRUTO = Path(__file__).resolve().parent.parent / "data" / "brutos" / "univali-mare-astronomica-2026.xlsx"


def linha(d1=None, h1=None, v1=None, d2=None, h2=None, v2=None, d3=None, h3=None, v3=None):
    """Uma linha da planilha de BLOCOS (Data, Hora, Nível | ... | ...)."""
    d1 = datetime.combine(d1, time()) if d1 else None
    d2 = datetime.combine(d2, time()) if d2 else None
    d3 = datetime.combine(d3, time()) if d3 else None
    return (d1, h1, v1, None, d2, h2, v2, None, d3, h3, v3)


class TesteExtrairEventos(unittest.TestCase):
    def test_data_repete_para_baixo_dentro_do_mesmo_dia(self):
        linhas = [
            linha(d1=date(2026, 9, 1), h1=time(4, 28), v1=1.2),
            linha(h1=time(9, 49), v1=0.5),
            linha(d1=date(2026, 9, 2), h1=time(5, 10), v1=1.1),
        ]
        eventos = extrair_eventos(linhas)
        self.assertEqual([e[0] for e in eventos],
                         [datetime(2026, 9, 1, 4, 28), datetime(2026, 9, 1, 9, 49), datetime(2026, 9, 2, 5, 10)])

    def test_tres_blocos_lado_a_lado_juntam_e_ordenam(self):
        linhas = [
            linha(d1=date(2026, 9, 1), h1=time(4, 0), v1=1.0, d2=date(2026, 9, 10), h2=time(1, 0), v2=1.3),
            linha(h1=time(10, 0), v1=0.3),
        ]
        eventos = extrair_eventos(linhas)
        self.assertEqual([e[0] for e in eventos], sorted(e[0] for e in eventos))
        self.assertEqual(len(eventos), 3)

    def test_linha_sem_data_nenhuma_ainda_e_ignorada(self):
        self.assertEqual(extrair_eventos([linha(h1=time(9, 0), v1=0.5)]), [])


class TesteClassificarExtremos(unittest.TestCase):
    def test_alterna_alta_baixa_alta_baixa(self):
        base = datetime(2026, 9, 1)
        eventos = [(base.replace(hour=4), 1.29), (base.replace(hour=9), 0.50),
                   (base.replace(hour=16), 1.18), (base.replace(hour=20), 0.45)]
        preamares, baixamares = classificar_extremos(eventos)
        self.assertEqual([q.hour for q, _ in preamares], [4, 16])
        self.assertEqual([q.hour for q, _ in baixamares], [9, 20])

    def test_plo_total_nao_classifica_nada(self):
        base = datetime(2026, 9, 1)
        eventos = [(base.replace(hour=h), 1.0) for h in (0, 1, 2)]
        preamares, baixamares = classificar_extremos(eventos)
        self.assertEqual(len(preamares) + len(baixamares), 0)


def curva(inicio: datetime, niveis: list[float], passo_min: int = 5) -> list[tuple[datetime, float]]:
    return [(inicio + timedelta(minutes=passo_min * i), v) for i, v in enumerate(niveis)]


class TesteSerieDe5Min(unittest.TestCase):
    def test_reconhece_o_cabecalho_da_serie_e_nao_o_dos_blocos(self):
        self.assertTrue(eh_serie(("data", "hora", "sl_fit")))
        self.assertTrue(eh_serie((" Data", "HORA ", "sl_fit", None)))
        self.assertFalse(eh_serie(("Data", "Hora", "Nível", None, "Data")))
        self.assertFalse(eh_serie(()))

    def test_le_data_e_hora_como_texto_ou_como_celula(self):
        linhas = [("01/01/2026", "00:05:00", 1.25), (datetime(2026, 1, 1), time(0, 0), 1.24), ("01/01/2026", None, 9.9)]
        serie = extrair_serie(linhas)
        self.assertEqual(serie, [(datetime(2026, 1, 1, 0, 0), 1.24), (datetime(2026, 1, 1, 0, 5), 1.25)])

    def test_extremos_sao_os_maximos_e_minimos_locais(self):
        serie = curva(datetime(2026, 1, 1), [0.5, 0.8, 1.0, 0.9, 0.6, 0.4, 0.5, 0.9])
        ext = extremos_da_serie(serie)
        self.assertEqual([(t, q.minute, v) for t, q, v in ext], [("P", 10, 1.0), ("B", 25, 0.4)])

    def test_ondulacao_de_estofo_sai_aos_pares_e_a_alternancia_fica(self):
        # Vale 0,40 → pico 0,822 → "vale" 0,818 → "pico" 0,830 → vale 0,30: o par (0,818; 0,830) tem 1,2 cm e
        # o par (0,822; 0,818) tem 0,4 cm. Sai primeiro o de 0,4 cm; sobra B 0,40 · P 0,830 · B 0,30.
        base = datetime(2026, 1, 5)
        ext = [("B", base, 0.40), ("P", base.replace(hour=1), 0.822), ("B", base.replace(hour=2), 0.818),
               ("P", base.replace(hour=3), 0.830), ("B", base.replace(hour=4), 0.30)]
        limpo, removidos = filtrar_ondulacoes(ext, ONDULACAO_M)
        self.assertEqual(removidos, 1)
        self.assertEqual([(t, v) for t, _, v in limpo], [("B", 0.40), ("P", 0.830), ("B", 0.30)])
        for a, b in zip(limpo, limpo[1:]):
            self.assertNotEqual(a[0], b[0], "alternância quebrada")

    def test_sem_ondulacao_nada_muda(self):
        base = datetime(2026, 1, 5)
        ext = [("B", base, 0.4), ("P", base.replace(hour=6), 1.2), ("B", base.replace(hour=12), 0.3)]
        self.assertEqual(filtrar_ondulacoes(ext), (ext, 0))

    def test_separar_devolve_preamares_e_baixamares(self):
        base = datetime(2026, 1, 5)
        pre, bai = separar([("B", base, 0.4), ("P", base.replace(hour=6), 1.2)])
        self.assertEqual(pre, [(base.replace(hour=6), 1.2)])
        self.assertEqual(bai, [(base, 0.4)])


class TesteFormatarNuncaEmiteAltura(unittest.TestCase):
    def test_formatar_so_tem_a_chave_quando(self):
        saida = formatar([(datetime(2026, 9, 1, 4, 28), 1.2895471327770707)])
        self.assertEqual(saida, [{"quando": "2026-09-01T04:28"}])

    def test_montar_nao_vaza_altura_em_nenhum_registro(self):
        pontos = [(datetime(2026, 9, 1, 4, 28), 1.29)]
        texto = str(montar(pontos, pontos))
        self.assertNotIn("altura_m", texto)
        self.assertNotIn("1.29", texto)

    def test_meta_credita_a_univali_e_diz_que_a_altura_nao_entra(self):
        dados = montar([], [], ondulacoes_removidas=46)
        meta = dados["_meta"]
        self.assertIn("UNIVALI", meta["fonte_curta"])
        self.assertNotIn("Defesa Civil", meta["fonte_curta"])
        self.assertNotIn("Marinha", meta["fonte_curta"])
        self.assertIsNone(meta["referencia_altura"])
        self.assertIn("NÃO ENTRA", meta["altura"])
        self.assertIn("46 par(es)", meta["metodo"])
        self.assertNotIn("aviso_interino", meta, "a UNIVALI é a fonte decidida (08/10/2026), não uma tábua interina")
        self.assertEqual(dados["porto"], "Itajaí")
        self.assertEqual((meta["estacao"]["lat"], meta["estacao"]["lon"]), (-26.92872, -48.62797))


class TesteCruzamento(unittest.TestCase):
    def test_mede_minutos_contra_a_tabua_anterior(self):
        novos = [(datetime(2026, 9, 1, 4, 30), 1.0), (datetime(2026, 9, 1, 16, 50), 1.0), (datetime(2026, 12, 1), 1.0)]
        antigos = [{"quando": "2026-09-01T04:28"}, {"quando": "2026-09-01T16:45"}, {"quando": "2026-09-02T05:00"}]
        c = cruzar(novos, antigos)
        self.assertEqual(c["pareados"], 2)
        self.assertEqual(c["mediana_min"], 3.5)
        self.assertEqual(c["maximo_abs_min"], 5.0)
        self.assertIsNone(cruzar(novos, []))


class TesteBrutoReal(unittest.TestCase):
    def test_a_planilha_de_2026_cobre_o_ano_e_concorda_com_a_marinha_em_minutos(self):
        if not BRUTO.exists():
            self.skipTest("sem data/brutos/univali-mare-astronomica-2026.xlsx")
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl não instalado")
        wb = openpyxl.load_workbook(BRUTO, read_only=True, data_only=True)
        linhas = list(wb.worksheets[0].iter_rows(values_only=True))
        self.assertTrue(eh_serie(linhas[0]))
        serie = extrair_serie(linhas[1:])
        self.assertEqual(len(serie), 105120, "365 dias × 288 pontos de 5 min")
        self.assertEqual((serie[0][0], serie[-1][0]), (datetime(2026, 1, 1, 0, 0), datetime(2026, 12, 31, 23, 55)))
        ext, removidos = filtrar_ondulacoes(extremos_da_serie(serie))
        pre, bai = separar(ext)
        self.assertEqual((len(pre), len(bai), removidos), (851, 851, 46))
        for a, b in zip(ext, ext[1:]):
            self.assertNotEqual(a[0], b[0])


if __name__ == "__main__":
    unittest.main()
