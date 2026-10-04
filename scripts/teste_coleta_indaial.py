import io
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import coleta_indaial
from coleta_indaial import interpretar, coletar


class Indaial(unittest.TestCase):
    agora = datetime(2026, 9, 13, 12, tzinfo=ZoneInfo('America/Sao_Paulo'))

    def ler(self, texto):
        return interpretar('Régua instalada fundos Celesc\n' + texto, self.agora)

    def test_mais_recente_independe_da_ordem_e_preserva_idade(self):
        l = self.ler('1209/2026\n22h - 4,10m\n21h - 4,14m\n11/09/2026\n23h - 5,15m')
        self.assertEqual(l['medido_em'], '2026-09-12T22:00:00')
        self.assertEqual(l['nivel_m'], 4.10)

    def test_nao_aceita_milimetros_ou_data_ambigua(self):
        with self.assertRaises(ValueError):
            self.ler('12/09/2026\n09h - 5,00mm\n13/2026\n10h - 5,01m')

    def test_futuro(self):
        with self.assertRaises(ValueError):
            self.ler('14/09/2026\n10h - 4,10m')

    def test_conflito(self):
        with self.assertRaises(ValueError):
            self.ler('12/09/2026\n22h - 4,10m\n22h - 4,11m')

    def test_referencia_obrigatoria(self):
        with self.assertRaises(ValueError):
            interpretar('12/09/2026\n22h - 4,10m', self.agora)

    def test_falha_isolada(self):
        with patch('coleta_indaial.baixar', side_effect=ValueError('indisponível')):
            self.assertEqual(coletar(), [])


class RobotsDoGoogleDocs(unittest.TestCase):
    """Decisão de 04/10/2026: robots.txt que recusa o caminho = não baixar.

    A captura de 28/09 respeitou o robots.txt de docs.google.com e não pediu o
    documento; o coletor pedia mesmo assim. Sem contorno: nem outro User-Agent,
    nem outro endereço do mesmo documento.
    """

    TEXTO = 'Régua instalada fundos Celesc\n12/09/2026\n22h - 4,10m\n'

    def servidor(self, robots):
        pedidas = []

        def buscar(url):
            pedidas.append(url)
            if url == coleta_indaial.ROBOTS:
                if isinstance(robots, Exception):
                    raise robots
                return robots
            return self.TEXTO
        return buscar, pedidas

    def test_robots_que_proibe_NAO_baixa_e_diz_o_motivo(self):
        buscar, pedidas = self.servidor('User-agent: *\nDisallow: /document/\n')
        with patch('sys.stderr', new_callable=io.StringIO) as erro:
            self.assertEqual(coletar(buscar), [])
        self.assertEqual(pedidas, [coleta_indaial.ROBOTS], 'o documento foi pedido')
        self.assertIn('bloqueado por robots.txt', erro.getvalue())
        self.assertIn('captura manual autorizada ou outra fonte pública', erro.getvalue())

    def test_curinga_e_fim_de_linha_tambem_proibem(self):
        for regra in ['/document/d/*/export', '/*export?format=txt$', '/*?format=']:
            with self.subTest(regra=regra):
                buscar, pedidas = self.servidor(f'User-agent: *\nDisallow: {regra}\n')
                self.assertEqual(coletar(buscar), [])
                self.assertEqual(pedidas, [coleta_indaial.ROBOTS])

    def test_allow_nao_abre_o_que_um_disallow_fecha(self):
        """Ignorar o Allow só pode deixar a resposta mais restritiva."""
        robots = 'User-agent: *\nAllow: /document/d/\nDisallow: /document/\n'
        self.assertTrue(coleta_indaial.robots_proibe(robots))

    def test_robots_sem_resposta_conta_como_recusa(self):
        for exc in [RuntimeError('timeout'), RuntimeError('503 Server Error: x'),
                    RuntimeError('429 Client Error: Too Many Requests')]:
            with self.subTest(exc=str(exc)):
                buscar, pedidas = self.servidor(exc)
                self.assertEqual(coletar(buscar), [])
                self.assertEqual(pedidas, [coleta_indaial.ROBOTS])

    def test_robots_inexistente_e_sem_regras(self):
        buscar, pedidas = self.servidor(RuntimeError('404 Client Error: Not Found'))
        self.assertEqual(coletar(buscar)[0]['nivel_m'], 4.10)
        self.assertEqual(pedidas, [coleta_indaial.ROBOTS, coleta_indaial.URL])

    def test_robots_que_libera_deixa_baixar(self):
        buscar, pedidas = self.servidor('User-agent: *\nDisallow: /admin\n')
        self.assertEqual(coletar(buscar)[0]['medido_em'], '2026-09-12T22:00:00')
        self.assertEqual(pedidas, [coleta_indaial.ROBOTS, coleta_indaial.URL])

    def test_regra_para_outro_robo_nao_vale_para_nos(self):
        robots = 'User-agent: Googlebot\nDisallow: /document/\n\nUser-agent: *\nDisallow: /admin\n'
        self.assertFalse(coleta_indaial.robots_proibe(robots))

    def test_sem_contorno_de_user_agent_ou_endereco(self):
        """O pedido continua com o User-Agent do projeto, pelo `comum.baixar`, e
        a única URL do documento é a de exportação que o robots.txt julga."""
        import ast
        import inspect
        arvore = ast.parse(inspect.getsource(coleta_indaial))
        doc = ast.get_docstring(arvore, clean=False)
        textos = [n.value for n in ast.walk(arvore)
                  if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value != doc]
        enderecos = [t for t in textos if 'google.com' in t and 'robots' not in t]
        self.assertEqual(enderecos, [coleta_indaial.FONTE], 'outro endereço do Google no código')
        argumentos = [k.arg for n in ast.walk(arvore) if isinstance(n, ast.Call) for k in n.keywords]
        self.assertNotIn('headers', argumentos, 'cabeçalho próprio (User-Agent) no pedido')
        self.assertTrue(coleta_indaial.URL.endswith('/export?format=txt'))


if __name__ == '__main__':
    unittest.main()
