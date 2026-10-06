#!/usr/bin/env python3
"""
Testes do conversor de traçado — e das GRAFIAS que o OSM realmente usa.

Escrever as chaves de busca é adivinhar como o mapeador nomeou o curso. Adivinhar
errado não quebra nada barulhento: o conversor pula com aviso, o geojson não
nasce, e o rio simplesmente continua faltando no mapa — que é o estado de antes,
e por isso passa despercebido.

Os nomes abaixo NÃO são chute. Vieram da consulta real ao Overpass rodada na VPS
em 04/09/2026, que devolveu exatamente:

    Rio Canhanduba                       11 ways
    Ribeirão da Murta                     5
    Canal Retificado Rio Itajaí Mirim     2
    Canal Retificado Rio Itajaí-Mirim     1

As duas grafias do canal (com e sem hífen) são o MESMO canal partido em ways
diferentes, e por isso caem no mesmo arquivo — o que o teste também trava.
"""
import json
import unittest

import converter_tracado_rios as ct

#: O que o Overpass devolveu de verdade, com a contagem de ways.
NOMES_REAIS_DO_OSM = {
    "Rio Canhanduba": 11,
    "Ribeirão da Murta": 5,
    "Canal Retificado Rio Itajaí Mirim": 2,
    "Canal Retificado Rio Itajaí-Mirim": 1,
}


def way(nome, n=3):
    """Um way com `n` pontos — geometria fake, o que importa aqui é o nome."""
    return {
        "type": "way",
        "tags": {"name": nome, "waterway": "stream"},
        "geometry": [{"lon": -48.7 + i * 0.001, "lat": -26.9 - i * 0.001} for i in range(n)],
    }


class GrafiasReaisDoOSM(unittest.TestCase):
    def test_cada_nome_real_cai_no_rio_certo(self):
        elementos = [way(n) for n, c in NOMES_REAIS_DO_OSM.items() for _ in range(c)]
        achados = {
            rio: ct.linhas_por_substring(elementos, chaves)
            for rio, chaves in ct.RIOS_AFLUENTES.items()
        }
        self.assertEqual(len(achados["ribeirao-canhanduba"]), 11, "Rio Canhanduba não casou")
        self.assertEqual(len(achados["ribeirao-murta"]), 5, "Ribeirão da Murta não casou")
        # As DUAS grafias do canal, juntas: é o mesmo canal partido em ways.
        self.assertEqual(len(achados["mirim-canal-retificado"]), 3,
                         "as duas grafias do canal deviam cair no mesmo arquivo")

    def test_nenhum_nome_real_cai_em_DOIS_rios(self):
        """
        Chave frouxa demais faria o mesmo way virar dois rios, e o mapa
        desenharia o Canhanduba por cima do canal. Cada nome tem um dono só.
        """
        for nome in NOMES_REAIS_DO_OSM:
            donos = [rio for rio, chaves in ct.RIOS_AFLUENTES.items()
                     if ct.linhas_por_substring([way(nome)], chaves)]
            self.assertEqual(len(donos), 1, f"{nome!r} casou com {donos}")

    def test_o_tronco_nao_e_arrastado_pelas_chaves_dos_afluentes(self):
        # "Rio Itajaí-Mirim" contém "itajaí-mirim"; se a chave do canal fosse só
        # isso, o tronco inteiro viraria canal — e o Mirim apareceria duplicado.
        for nome in ("Rio Itajaí-Mirim", "Rio Itajaí-Açu", "Rio Itajaí do Oeste"):
            donos = [rio for rio, chaves in ct.RIOS_AFLUENTES.items()
                     if ct.linhas_por_substring([way(nome)], chaves)]
            self.assertEqual(donos, [], f"{nome!r} foi capturado por {donos}")


class SemBruto(unittest.TestCase):
    def test_way_curto_demais_nao_vira_linha(self):
        # Um ponto só não é traçado; desenhar viraria um risco de nada.
        self.assertEqual(ct.linhas_por_substring([way("Rio Canhanduba", n=1)],
                                                 ["rio canhanduba"]), [])

    def test_way_sem_nome_e_ignorado(self):
        anonimo = {"type": "way", "tags": {"waterway": "stream"},
                   "geometry": [{"lon": -48.7, "lat": -26.9}, {"lon": -48.6, "lat": -26.9}]}
        self.assertEqual(ct.linhas_por_substring([anonimo], ["rio canhanduba"]), [])

    def test_a_geometria_sai_em_lon_lat_ordem_do_geojson(self):
        # O OSM devolve lat/lon; o GeoJSON quer [lon, lat]. Trocar inverteria o
        # mapa inteiro — e o rio apareceria na África.
        linha = ct.linhas_por_substring([way("Rio Canhanduba")], ["rio canhanduba"])[0]
        lon, lat = linha[0]
        self.assertLess(lon, -40, "longitude e latitude trocadas")
        self.assertGreater(lat, -30)
        self.assertLess(lat, -20)


class CabeceiraDoSul(unittest.TestCase):
    """
    O Itajaí do Sul não estava no mapa até 05/09/2026: a consulta do Overpass
    pediu Açu, Mirim e Oeste, e nunca o Sul. Ituporanga flutuava a 28 km, e a
    linha perto dela era o OESTE — o mapa dizendo série onde os dados dizem
    árvore. Estes testes travam a origem, o crédito e a ressalva de cobertura.
    """

    def test_o_bruto_do_osm_realmente_nao_tem_o_sul(self):
        # A causa raiz, medida. Se um dia o bruto passar a ter o Sul, este teste
        # cai e o certo é tirá-lo da Asthon e pô-lo no OSM, com mais cobertura.
        bruto = json.loads(ct.BRUTO.read_text(encoding="utf-8"))
        nomes = {(e.get("tags") or {}).get("name") for e in bruto.get("elements") or []}
        self.assertIn("Rio Itajaí do Oeste", nomes)
        self.assertNotIn("Rio Itajaí do Sul", nomes)

    def test_le_o_sul_do_geojson_da_asthon(self):
        linhas = ct.linhas_do_geojson_asthon(ct.BRUTO_RIO_DO_SUL, "Rio Itajaí do Sul")
        self.assertEqual(len(linhas), 1)
        self.assertGreaterEqual(len(linhas[0]), 30)

    def test_nome_ausente_devolve_vazio_em_vez_de_explodir(self):
        # Traçado opcional: um bruto que mudou não pode derrubar o tronco.
        self.assertEqual(ct.linhas_do_geojson_asthon(ct.BRUTO_RIO_DO_SUL, "Rio Inexistente"), [])

    def test_o_credito_do_sul_NAO_e_o_do_osm(self):
        # Fonte diferente, licença diferente. Herdar a atribuição do OSM daria
        # crédito a quem não levantou este traçado.
        self.assertNotEqual(ct.ATRIBUICAO_ASTHON, ct.ATRIBUICAO)
        self.assertIn("Rio do Sul", ct.ATRIBUICAO_ASTHON)

    def test_o_arquivo_gravado_diz_de_onde_veio(self):
        """Com o bruto do OSM (06/10/2026), o Sul inteiro, recortado na caixa; sem ele, o da Asthon, parcial."""
        caminho = ct.SAIDA / "itajai-do-sul.geojson"
        if not caminho.exists():
            self.skipTest("rode scripts/converter_tracado_rios.py")
        props = json.loads(caminho.read_text(encoding="utf-8"))["properties"]
        if ct.BRUTOS_AFLUENTES["itajai-do-sul"].exists():
            self.assertEqual(props["fonte"], ct.ATRIBUICAO)
            self.assertIn("RECORTADO", props["cobertura"])
        else:
            self.assertIn("PARCIAL", props["cobertura"])
            self.assertIn("Ituporanga", props["cobertura"])
            self.assertEqual(props["fonte"], ct.ATRIBUICAO_ASTHON)


class AfluentesBaixadosEm06De10(unittest.TestCase):
    """Benedito, Rio dos Cedros, Itajaí do Sul e Trombudo: recortados na caixa do mapa, passando pela régua."""

    def test_recorte_na_caixa_parte_a_linha_que_sai_e_volta(self):
        caixa = (-50.0, -27.5, -49.0, -26.8)
        linha = [[-49.5, -27.0], [-49.5, -26.9], [-49.5, -26.7], [-49.5, -26.85], [-49.5, -26.82]]
        self.assertEqual(ct.recortar_na_caixa([linha], caixa),
                         [[[-49.5, -27.0], [-49.5, -26.9]], [[-49.5, -26.85], [-49.5, -26.82]]])

    def test_o_trombudo_nao_pega_outro_rio_e_o_sul_nao_pega_o_oeste(self):
        elementos = [way("Rio Trombudo"), way("Rio Itajaí do Sul"), way("Rio Itajaí do Oeste")]
        self.assertEqual(len(ct.linhas_por_substring(elementos, ct.RIOS_AFLUENTES["trombudo"])), 1)
        self.assertEqual(len(ct.linhas_por_substring(elementos, ct.RIOS_AFLUENTES["itajai-do-sul"])), 1)

    def test_so_o_trecho_ligado_a_regua_fica(self):
        ligada = [[0.0, 0.0], [1.0, 0.0]]
        vizinha = [[1.0, 0.0], [2.0, 0.0]]
        solta = [[5.0, 0.0], [6.0, 0.0]]   # lacuna: não toca as outras
        self.assertEqual(ct.ligadas_ao_ponto([solta, ligada, vizinha], (0.1, 0.0)), [ligada, vizinha])

    def test_o_guabiruba_desenhado_e_uma_cadeia_so_da_estacao_ao_mirim(self):
        arq = ct.SAIDA / "guabiruba.geojson"
        if not arq.exists():
            self.skipTest("sem guabiruba.geojson")
        ls = json.loads(arq.read_text(encoding="utf-8"))["geometry"]["coordinates"]
        self.assertEqual(len(ct.ligadas_ao_ponto(ls, ct.coordenada_da_cidade("guabiruba"))), len(ls))

    def test_guabiruba_pelo_nome_exato_sem_o_sul(self):
        elementos = [way("Rio Guabiruba Norte"), way("Rio Guabiruba"), way("Rio Guabiruba Sul")]
        self.assertEqual(len(ct.linhas_por_nome_exato(elementos, ct.RIOS_AFLUENTES["guabiruba"])), 2)
        self.assertIn("guabiruba", ct.NOMES_EXATOS)

    def test_os_arquivos_gravados_cabem_na_caixa_e_passam_pela_regua(self):
        import math
        k = math.cos(math.radians(27))
        estacoes = json.loads((ct.RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
        cidades = {c["id"]: c for r in estacoes["rios"].values() for c in r["cidades"]}
        tronco = [l for r in ("itajai-acu", "itajai-mirim")
                  for l in json.loads((ct.SAIDA / f"{r}.geojson").read_text(encoding="utf-8"))["geometry"]["coordinates"]]
        oeste, sul, leste, norte = ct.caixa_do_mapa(tronco)
        f = ct.FOLGA_DA_CAIXA_GRAUS
        oeste, sul, leste, norte = oeste - f, sul - f, leste + f, norte + f
        vistos = 0
        for rio, cidade, limite in (("benedito", "timbo", 1.0), ("rio-dos-cedros", "rio-dos-cedros", 1.0),
                                    ("itajai-do-sul", "ituporanga", 0.5), ("trombudo", "trombudo-central", 1.0)):
            if not ct.BRUTOS_AFLUENTES[rio].exists():
                continue
            pts = [p for l in json.loads((ct.SAIDA / f"{rio}.geojson").read_text(encoding="utf-8"))["geometry"]["coordinates"] for p in l]
            self.assertTrue(all(oeste <= p[0] <= leste and sul <= p[1] <= norte for p in pts), f"{rio} sai da caixa do mapa")
            lat, lon = cidades[cidade]["coordenadas"]
            d = min(math.hypot((p[0] - lon) * k, p[1] - lat) * 111.32 for p in pts)
            self.assertLess(d, limite, f"{rio} fica a {d:.2f} km da régua de {cidade}")
            vistos += 1
        if not vistos:
            self.skipTest("sem os brutos: workflow baixar-tracados-afluentes.yml")

    def test_o_rio_dos_cedros_passa_pela_regua_e_segue_alem(self):
        # A régua de Rio dos Cedros é a borda norte do quadro. Sem a folga, o recorte terminava a linha no pino.
        if not ct.BRUTOS_AFLUENTES["rio-dos-cedros"].exists():
            self.skipTest("sem o bruto do Rio dos Cedros")
        estacoes = json.loads((ct.RAIZ / "data/estacoes.json").read_text(encoding="utf-8"))
        lat = next(c for r in estacoes["rios"].values() for c in r["cidades"] if c["id"] == "rio-dos-cedros")["coordenadas"][0]
        pts = [p for l in json.loads((ct.SAIDA / "rio-dos-cedros.geojson").read_text(encoding="utf-8"))["geometry"]["coordinates"] for p in l]
        self.assertGreater(max(p[1] for p in pts), lat + 0.01)


class TesteHercilio(unittest.TestCase):
    """O rio de Ibirama tem dois nomes no OSM e é recortado para não mudar o enquadramento do Monitor."""

    def test_os_dois_nomes_entram_e_o_oeste_nao(self):
        elementos = [way("Rio Itajaí do Norte"), way("Rio Hercílio"), way("Rio Itajaí do Oeste"), way("Rio Itajaí-Açu")]
        self.assertEqual(len(ct.linhas_por_substring(elementos, ct.RIOS_AFLUENTES["hercilio"])), 2)

    def test_recorte_ao_sul_parte_a_linha_que_sai_e_volta(self):
        linha = [[-49.5, -27.0], [-49.5, -26.9], [-49.5, -26.8], [-49.5, -26.7], [-49.5, -26.86], [-49.5, -26.95]]
        self.assertEqual(ct.recortar_ao_sul([linha], -26.84),
                         [[[-49.5, -27.0], [-49.5, -26.9]], [[-49.5, -26.86], [-49.5, -26.95]]])
        self.assertEqual(ct.recortar_ao_sul([[[-49.5, -26.5], [-49.5, -26.6]]], -26.84), [])

    def test_o_corte_fica_na_borda_norte_do_traçado_de_hoje(self):
        # Se o tronco mudar de extensão, o corte tem de ser revisto: o Hercílio não pode alargar o mapa.
        acu = json.loads((ct.SAIDA / "itajai-acu.geojson").read_text(encoding="utf-8"))
        norte_do_acu = max(p[1] for l in acu["geometry"]["coordinates"] for p in l)
        self.assertLessEqual(ct.CORTE_NORTE["hercilio"], norte_do_acu)

    def test_o_arquivo_gravado_nao_passa_do_corte_e_passa_por_ibirama(self):
        caminho = ct.SAIDA / "hercilio.geojson"
        if not caminho.exists():
            self.skipTest("sem o bruto do Hercílio: rode scripts/baixar_tracado_hercilio.py --gravar")
        g = json.loads(caminho.read_text(encoding="utf-8"))
        pts = [p for l in g["geometry"]["coordinates"] for p in l]
        self.assertLessEqual(max(p[1] for p in pts), ct.CORTE_NORTE["hercilio"])
        self.assertIn("RECORTADO", g["properties"]["cobertura"])
        self.assertEqual(g["properties"]["fonte"], ct.ATRIBUICAO)
        import math
        ibirama = (-49.52, -27.057)
        k = math.cos(math.radians(27))
        d = min(math.hypot((p[0] - ibirama[0]) * k, p[1] - ibirama[1]) * 111.32 for p in pts)
        self.assertLess(d, 0.5, f"o traçado fica a {d:.2f} km do pino de Ibirama")

class TesteRiosDeMunicipio(unittest.TestCase):
    """Os cursos com nome que passam por um município (Ibirama, 05/10/2026): um arquivo por nome."""

    def test_slug_e_nomes_ja_desenhados(self):
        self.assertEqual(ct.slug("Rio Rafael Braço Grande"), "rio-rafael-braco-grande")
        self.assertEqual(ct.slug("Ribeirão Taquaras"), "ribeirao-taquaras")
        self.assertTrue(ct.ja_desenhado("Rio Hercílio"))      # afluente
        self.assertTrue(ct.ja_desenhado("Rio Itajaí-Açu"))    # tronco
        self.assertFalse(ct.ja_desenhado("Rio Rafael"))

    def test_os_rios_de_ibirama_chegam_ao_hercilio(self):
        bruto = ct.RAIZ / "data/brutos/rios-ibirama-osm.json"
        if not bruto.exists():
            self.skipTest("sem o bruto de Ibirama: workflow baixar-rios-municipio.yml")
        import math
        k = math.cos(math.radians(27))

        def pts(rio):
            g = json.loads((ct.SAIDA / f"{rio}.geojson").read_text(encoding="utf-8"))
            self.assertEqual(g["properties"]["municipio"], "ibirama")
            return [p for l in g["geometry"]["coordinates"] for p in l]

        def perto(a, b):
            return min(math.hypot((p[0] - q[0]) * k, p[1] - q[1]) * 111.32 for p in a for q in b[::2]) < 0.1

        hercilio = [p for l in json.loads((ct.SAIDA / "hercilio.geojson").read_text(encoding="utf-8"))["geometry"]["coordinates"] for p in l]
        rafael = pts("rio-rafael")
        self.assertTrue(perto(rafael, hercilio))
        self.assertTrue(perto(pts("ribeirao-taquaras"), hercilio))
        for braco in ("rio-rafael-braco-grande", "rio-rafael-braco-pequeno"):
            self.assertTrue(perto(pts(braco), rafael), braco)


if __name__ == "__main__":
    unittest.main()
