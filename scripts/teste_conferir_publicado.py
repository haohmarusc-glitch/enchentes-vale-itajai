#!/usr/bin/env python3
"""Testes do conferidor do último trecho: VPS → branch → raw → navegador.

O site lê nível de rio por `raw.githubusercontent.com`. Se esse trecho travar,
a coleta segue verde na VPS e o morador vê nível velho sem que ninguém perceba.
Este conferidor precisa separar TRÊS causas que, de uma leitura só, parecem
iguais — e precisa dizer "não sei" quando não consegue.

Cada guarda abaixo é SABOTADA num teste próprio: um guarda que não falha
quando quebrado não é guarda.

    python3 scripts/teste_conferir_publicado.py
"""

import json
import unittest
from datetime import datetime, timedelta, timezone

import conferir_publicado as cp
from conferir_publicado import (
    CARIMBOS,
    JANELA_PUBLICACAO_MIN,
    NORMAL_MIN,
    carimbo,
    medir,
    minutos,
    utc,
    veredito,
)

AGORA = datetime(2026, 9, 4, 22, 30, tzinfo=timezone.utc)


def atras(minutos_atras: float) -> datetime:
    return AGORA - timedelta(minutes=minutos_atras)


def iso(d: datetime) -> str:
    return d.isoformat(timespec="seconds")


def transporte(*, raw: dict | None, topo_min: float | None, campo: str = "gerado_em"):
    """Uma rede de mentira: devolve o que o teste mandar, ou explode como a real."""
    def buscar(url: str, **kw) -> str:
        if url.startswith(cp.API):
            if topo_min is None:
                raise RuntimeError("403 Client Error: Forbidden")
            return json.dumps({"sha": "abc12345",
                               "commit": {"committer": {"date": iso(atras(topo_min))}}})
        if raw is None:
            raise RuntimeError("404 Client Error: Not Found")
        return json.dumps(raw)
    return buscar


class OsQuatroVereditos(unittest.TestCase):
    """Cada causa tem que sair com o nome dela — e o diagnóstico decide onde mexer."""

    def test_caminho_vivo_quando_topo_e_conteudo_batem_e_sao_recentes(self):
        v, _ = veredito(idade_raw=15.0, idade_topo=15.0, entre_topo_e_raw=0.0)
        self.assertEqual(v, "CAMINHO VIVO")

    def test_publicacao_parada_quando_o_topo_do_branch_envelhece(self):
        # A VPS parou de empurrar. O raw serve fielmente o que existe — o culpado
        # é o cron, e mandar consertar o raw seria consertar a coisa errada.
        v, porque = veredito(idade_raw=400.0, idade_topo=400.0, entre_topo_e_raw=0.0)
        self.assertEqual(v, "PUBLICAÇÃO PARADA")
        self.assertIn("VPS", porque)

    def test_cache_do_raw_quando_o_topo_e_novo_e_o_conteudo_e_velho(self):
        # Este é o caso que a outra sessão descreveu: topo fresco, conteúdo de
        # horas atrás. Se acontecer, é dado velho chegando ao MORADOR.
        v, porque = veredito(idade_raw=405.0, idade_topo=5.0, entre_topo_e_raw=400.0)
        self.assertEqual(v, "CACHE DO RAW")
        self.assertIn("morador", porque)

    def test_sem_a_API_o_veredito_e_nao_sei_e_nao_um_palpite(self):
        # Sem o topo do branch, cache e publicação parada são indistinguíveis.
        # Escolher um dos dois mandaria consertar a metade errada do caminho.
        v, porque = veredito(idade_raw=405.0, idade_topo=None, entre_topo_e_raw=None)
        self.assertEqual(v, "NÃO DÁ PARA DIZER")
        self.assertIn("separar", porque)

    def test_conteudo_velho_com_topo_novo_e_batendo_nao_vira_acusacao_de_cache(self):
        # Publicação viva, carimbo antigo dentro do arquivo: é problema de
        # coleta, e o conferidor manda para o vigia em vez de chutar.
        v, porque = veredito(idade_raw=200.0, idade_topo=10.0, entre_topo_e_raw=1.0)
        self.assertEqual(v, "NÃO DÁ PARA DIZER")
        self.assertIn("saude_coleta", porque)


class SabotagemDasGuardas(unittest.TestCase):
    """Quebrar cada limiar e exigir que o veredito mude. Guarda mudo é decoração."""

    def test_sem_o_limite_de_idade_a_publicacao_parada_passaria_por_viva(self):
        parada = 3 * NORMAL_MIN
        self.assertEqual(veredito(parada, parada, 0.0)[0], "PUBLICAÇÃO PARADA")
        # Sabotagem: com o limite no infinito, a mesma medição vira "vivo".
        original = cp.NORMAL_MIN
        try:
            cp.NORMAL_MIN = float("inf")
            self.assertEqual(cp.veredito(parada, parada, 0.0)[0], "CAMINHO VIVO",
                             "o limite de idade não estava sendo usado — a guarda é decorativa")
        finally:
            cp.NORMAL_MIN = original

    def test_sem_a_janela_de_publicacao_uma_publicacao_em_curso_viraria_cache(self):
        # Publicar leva alguns segundos: por um instante o topo é mais novo que
        # o conteúdo servido. Sem a janela isso viraria acusação de cache a cada
        # rodada do cron — o alarme falso que faz o vigia ser ignorado.
        self.assertEqual(veredito(16.0, 15.0, 1.0)[0], "CAMINHO VIVO")
        original = cp.JANELA_PUBLICACAO_MIN
        try:
            cp.JANELA_PUBLICACAO_MIN = 0.0
            self.assertEqual(cp.veredito(16.0, 15.0, 1.0)[0], "CACHE DO RAW",
                             "a janela de publicação não estava sendo usada")
        finally:
            cp.JANELA_PUBLICACAO_MIN = original

    def test_a_ordem_importa_ignorancia_vem_antes_de_diagnostico(self):
        # Topo ausente E conteúdo velho: a tentação é dizer "cache". Não dá.
        self.assertEqual(veredito(500.0, None, None)[0], "NÃO DÁ PARA DIZER")


class OsCarimbosDosTresArquivos(unittest.TestCase):
    """Os três arquivos não usam o mesmo nome de campo — e o certo é UTC."""

    def test_a_serie_usa_gerado_em(self):
        d, campo = carimbo({"gerado_em": "2026-09-04T22:16:21+00:00"})
        self.assertEqual(campo, "gerado_em")
        self.assertEqual(d, datetime(2026, 9, 4, 22, 16, 21, tzinfo=timezone.utc))

    def test_os_ultimo_usam_coletado_em(self):
        d, campo = carimbo({"coletado_em": "2026-09-04T22:16:21+00:00"})
        self.assertEqual(campo, "coletado_em")
        self.assertIsNotNone(d)

    def test_medido_em_NAO_serve_de_carimbo_de_publicacao(self):
        # `medido_em` é horário de Brasília SEM fuso (CLAUDE.md) e diz quando a
        # FONTE mediu, não quando publicamos. Usá-lo aqui daria 3 h de erro e
        # acusaria o caminho de morto com a fonte apenas atrasada.
        self.assertNotIn("medido_em", CARIMBOS)
        d, campo = carimbo({"medido_em": "2026-09-04T19:16:21"})
        self.assertIsNone(d)
        self.assertIsNone(campo)

    def test_arquivo_sem_carimbo_nenhum_nao_vira_data_inventada(self):
        self.assertEqual(carimbo({"leituras": []}), (None, None))

    def test_carimbo_sem_fuso_e_lido_como_UTC(self):
        # `gerado_em` e `coletado_em` são UTC por contrato. Sem fuso, assumir
        # Brasília aqui inverteria o sinal do atraso em 3 h.
        self.assertEqual(utc("2026-09-04T22:16:21"),
                         datetime(2026, 9, 4, 22, 16, 21, tzinfo=timezone.utc))


class MedirComRedeDeMentira(unittest.TestCase):
    """O caminho inteiro, ponta a ponta, sem tocar na rede."""

    def test_rodada_saudavel(self):
        m = medir("serie-recente.json", AGORA,
                  buscar=transporte(raw={"gerado_em": iso(atras(15))}, topo_min=15))
        self.assertEqual(m["veredito"], "CAMINHO VIVO")
        self.assertEqual(m["campo"], "gerado_em")
        self.assertEqual(m["topo_sha"], "abc12345")

    def test_raw_fora_do_ar_nao_vira_diagnostico(self):
        m = medir("ultimo.json", AGORA, buscar=transporte(raw=None, topo_min=15))
        self.assertEqual(m["veredito"], "NÃO DÁ PARA DIZER")
        self.assertIn("erro_raw", m)

    def test_API_fora_do_alcance_nao_vira_diagnostico(self):
        m = medir("ultimo.json", AGORA,
                  buscar=transporte(raw={"coletado_em": iso(atras(15))}, topo_min=None))
        self.assertEqual(m["veredito"], "NÃO DÁ PARA DIZER")
        self.assertIn("erro_api", m)

    def test_o_caso_relatado_pela_outra_sessao_sai_como_cache(self):
        # 15:16 no conteúdo, 22:01 na VPS: 405 min de diferença, topo fresco.
        m = medir("serie-recente.json", AGORA,
                  buscar=transporte(raw={"gerado_em": iso(atras(434))}, topo_min=29))
        self.assertEqual(m["veredito"], "CACHE DO RAW")

    def test_o_mesmo_sintoma_com_o_topo_parado_sai_como_publicacao_parada(self):
        # MESMO conteúdo velho — e o veredito muda, porque a causa é outra.
        # É esta linha que justifica o script existir: uma leitura só não separa.
        m = medir("serie-recente.json", AGORA,
                  buscar=transporte(raw={"gerado_em": iso(atras(434))}, topo_min=434))
        self.assertEqual(m["veredito"], "PUBLICAÇÃO PARADA")


class OScriptNaoGravaNada(unittest.TestCase):
    def test_nao_ha_escrita(self):
        with open(cp.__file__, encoding="utf-8") as f:
            fonte = f.read()
        for proibido in ("write_text(", "json.dump(", ".unlink(", "grava_json("):
            self.assertNotIn(proibido, fonte,
                             f"o conferidor passou a escrever ({proibido}) — ele só mede")


class ATodosOsArquivosQueOSiteLe(unittest.TestCase):
    def test_a_lista_cobre_os_tres_que_o_site_busca(self):
        self.assertEqual(set(cp.PUBLICADOS),
                         {"serie-recente.json", "ultimo.json", "ultimo_nivel_sc.json"})

    def test_minutos_devolve_None_quando_falta_qualquer_ponta(self):
        self.assertIsNone(minutos(AGORA, None))
        self.assertIsNone(minutos(None, AGORA))


if __name__ == "__main__":
    unittest.main()
