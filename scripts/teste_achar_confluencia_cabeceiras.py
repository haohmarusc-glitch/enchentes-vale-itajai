#!/usr/bin/env python3
"""
Testes da confluência das cabeceiras: o achado real e, sobretudo, as RECUSAS.

O valor deste script não é achar o ponto — é não gravar ponto nenhum quando a
premissa cai. Por isso os testes de recusa são a maior parte: traçado ausente,
vértice que deixou de ser compartilhado, e cabeceira chegando pelo rumo errado
(que significaria arquivo com nomes trocados OU topologia nossa errada — em
qualquer dos dois casos, gravar seria afirmar geografia falsa na tela).
"""
import json
import math
import unittest
from unittest import mock

import achar_confluencia_cabeceiras as ac


def _tracados(sul_fim=None, oeste_fim=None, sul_ini=None, oeste_ini=None):
    """Traçados sintéticos com a mesma topologia da fonte: os três num só vértice."""
    junta = (-49.6483391, -27.2160314)
    return {
        ac.TRONCO: [junta, (-49.55, -27.15)],
        # Itajaí do Sul vem do SUL (latitude menor), Oeste vem do OESTE (longitude menor).
        "Rio Itajaí do Sul": [sul_ini or (-49.6469, -27.2974), sul_fim or junta],
        "Rio Itajaí do Oeste": [oeste_ini or (-49.7177, -27.2284), oeste_fim or junta],
    }


class Confluencia(unittest.TestCase):
    def test_arquivo_real_da_o_ponto_e_os_rumos_conferem(self):
        r = ac.analisar()
        self.assertEqual(r["status"], "ok")
        # O ponto que a fonte declara, em Rio do Sul.
        self.assertAlmostEqual(r["lat"], -27.2160314, places=6)
        self.assertAlmostEqual(r["lon"], -49.6483391, places=6)
        # A conferência independente: Sul pelo sul, Oeste pelo oeste.
        self.assertEqual(r["rumos"]["Rio Itajaí do Sul"], "S")
        self.assertEqual(r["rumos"]["Rio Itajaí do Oeste"], "O")

    def test_os_tres_tracados_compartilham_o_vertice_ao_digito(self):
        # A afirmação forte do script: não é "perto", é o MESMO ponto. Se algum
        # dia a fonte parar de snapar, este teste cai antes de a tela mentir.
        rios = ac.carregar()
        junta = rios[ac.TRONCO][0]
        for nome in ac.CABECEIRAS:
            self.assertLess(ac.metros(rios[nome][-1], junta), ac.LIMITE_VERTICE_M)

    def test_sem_o_tracado_no_arquivo_recusa(self):
        with mock.patch.object(ac, "carregar", lambda: {ac.TRONCO: [(0, 0)]}):
            r = ac.analisar()
        self.assertEqual(r["status"], "sem_tracado")
        self.assertIn("Itajaí do Sul", r["texto"])

    def test_vertice_que_deixou_de_ser_compartilhado_recusa(self):
        # 2 km de folga: traçados que "quase" se encontram não valem — devolver
        # o ponto mais próximo seria inventar precisão que a fonte não deu.
        longe = (-49.6483391 + 0.02, -27.2160314)
        with mock.patch.object(ac, "carregar", lambda: _tracados(sul_fim=longe)):
            r = ac.analisar()
        self.assertEqual(r["status"], "nao_compartilham")
        self.assertIn("Itajaí do Sul", r["texto"])

    def test_cabeceira_chegando_pelo_rumo_errado_recusa(self):
        # Itajaí do Sul vindo do NORTE: ou o arquivo trocou os nomes, ou a nossa
        # topologia está errada. Gravar seria afirmar geografia falsa.
        do_norte = (-49.6483391, -27.2160314 + 0.05)
        with mock.patch.object(ac, "carregar", lambda: _tracados(sul_ini=do_norte)):
            r = ac.analisar()
        self.assertEqual(r["status"], "rumo_inesperado")
        self.assertIn("esperado S", r["texto"])

    def test_cabeceira_gravada_ao_contrario_nao_passa_despercebida(self):
        # Traçado invertido (começa na junção e termina longe): é a ponta FINAL
        # que tem de coincidir, então isto tem de cair como "não compartilham" —
        # aceitar a ponta mais próxima esconderia o arquivo invertido.
        junta = (-49.6483391, -27.2160314)
        invertido = {**_tracados(), "Rio Itajaí do Sul": [junta, (-49.6469, -27.2974)]}
        with mock.patch.object(ac, "carregar", lambda: invertido):
            r = ac.analisar()
        self.assertEqual(r["status"], "nao_compartilham")

    def test_rumo_corrige_o_encurtamento_da_longitude(self):
        # Na latitude 27, um grau de longitude vale ~0,89 grau de latitude.
        # 1,0° de longitude = ~99,2 km; 0,92° de latitude = ~101,7 km. Em
        # distância REAL o deslocamento é norte-sul — mas comparando os graus
        # crus (1,0 > 0,92) sairia "O". É este caso que a correção acerta.
        origem = (-49.0, -27.0)
        self.assertEqual(ac.rumo((-49.0 - 1.0, -27.0 - 0.92), origem), "S")
        # E um leste-oeste de verdade continua leste-oeste.
        self.assertEqual(ac.rumo((-49.0 - 1.0, -27.0 - 0.5), origem), "O")

    def test_gravar_é_idempotente_e_nunca_deixa_json_invalido(self):
        original = ac.ESTACOES.read_text(encoding="utf-8")
        try:
            r = ac.analisar()
            self.assertTrue(ac.gravar(r))
            primeira = ac.ESTACOES.read_text(encoding="utf-8")
            d = json.loads(primeira)
            bloco = d["rios"]["itajai-acu"]["_topologia"]["confluencia_cabeceiras"]
            self.assertAlmostEqual(bloco["lat"], -27.2160314, places=6)
            self.assertEqual(bloco["nasce"], "rio-do-sul")
            # Rodar de novo não duplica o bloco nem muda o arquivo.
            self.assertTrue(ac.gravar(r))
            self.assertEqual(ac.ESTACOES.read_text(encoding="utf-8"), primeira)
            self.assertEqual(primeira.count('"confluencia_cabeceiras"'), 1)
        finally:
            ac.ESTACOES.write_text(original, encoding="utf-8")

    def test_ponto_bate_com_a_cidade_que_a_topologia_afirma(self):
        # O Açu nasce EM Rio do Sul: o ponto tem de cair perto da cidade, não
        # numa cidade vizinha. Confere o achado contra o cadastro do projeto.
        r = ac.analisar()
        d = json.loads(ac.ESTACOES.read_text(encoding="utf-8"))
        rds = next(c for c in d["rios"]["itajai-acu"]["cidades"] if c["id"] == "rio-do-sul")
        lat, lon = rds["coordenadas"]
        self.assertLess(ac.metros((r["lon"], r["lat"]), (lon, lat)), 5000)


if __name__ == "__main__":
    unittest.main()
