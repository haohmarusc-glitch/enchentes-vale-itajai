#!/usr/bin/env python3
"""Testes do autorizar_email.py, contra uma Cloudflare de mentira — sem rede, sem token."""
from __future__ import annotations

import contextlib
import copy
import io
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import autorizar_email as ae  # noqa: E402

CONTA = "conta123"


def politica(nome: str = "Só eu", emails: tuple[str, ...] = ("dono@gmail.com",), pid: str = "p1") -> dict[str, Any]:
    return {"id": pid, "uid": pid, "name": nome, "decision": "allow", "reusable": True, "app_count": 1,
            "created_at": "2026-09-06T00:00:00Z", "updated_at": "2026-09-06T00:00:00Z",
            "include": [{"email": {"email": e}} for e in emails], "exclude": [], "require": [],
            "session_duration": "24h"}


class CloudflareFalsa:
    """Guarda políticas e registra as chamadas. `mentir=True` aceita o PUT e não grava."""

    def __init__(self, *pols: dict[str, Any], mentir: bool = False, da_app: bool = False) -> None:
        self.pols = {p["id"]: copy.deepcopy(p) for p in pols}
        self.chamadas: list[tuple[str, str, Any]] = []
        self.mentir = mentir
        #: `da_app`: as políticas são antigas, da aplicação — não aparecem entre as reutilizáveis.
        self.da_app = da_app

    def __call__(self, metodo: str, caminho: str, corpo: dict[str, Any] | None = None) -> dict[str, Any]:
        self.chamadas.append((metodo, caminho, copy.deepcopy(corpo)))
        apps = f"/accounts/{CONTA}/access/apps"
        reutilizaveis = f"/accounts/{CONTA}/access/policies"
        if caminho == apps:
            return {"success": True, "result": [{"id": "outra", "name": "outro site"},
                                                {"id": "app1", "name": "enchentes"}]}
        if caminho == f"{apps}/outra/policies":
            return {"success": True, "result": []}
        if (caminho == reutilizaveis and self.da_app) or (caminho == f"{apps}/app1/policies" and not self.da_app):
            return {"success": True, "result": []}
        base = f"{apps}/app1/policies" if self.da_app else reutilizaveis
        assert caminho.startswith(base), f"caminho errado para esta política: {caminho}"
        pid = caminho[len(base) + 1:]
        if metodo == "GET" and not pid:
            return {"success": True, "result": copy.deepcopy(list(self.pols.values()))}
        if metodo == "GET":
            return {"success": True, "result": copy.deepcopy(self.pols[pid])}
        assert metodo == "PUT" and corpo is not None
        if not self.mentir:
            self.pols[pid] = {**self.pols[pid], **copy.deepcopy(corpo)}
        return {"success": True, "result": {}}

    def puts(self) -> list[Any]:
        return [c for c in self.chamadas if c[0] == "PUT"]


def roda(cf: CloudflareFalsa, *argv: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    ambiente = {"CLOUDFLARE_ACCOUNT_ID": CONTA, **(env or {})}
    with mock.patch.dict(os.environ, ambiente, clear=True), mock.patch.object(ae, "carrega_env"), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        cod = ae.principal(list(argv), chamar=cf)
    return cod, out.getvalue(), err.getvalue()


class Autorizar(unittest.TestCase):
    def test_acrescenta_e_confere_relendo(self):
        cf = CloudflareFalsa(politica())
        cod, out, _ = roda(cf, "Nova.Pessoa@Gmail.com")
        self.assertEqual(cod, 0)
        self.assertIn("nova.pessoa@gmail.com autorizado", out)
        self.assertEqual(ae.emails_da_politica(cf.pols["p1"]), ["dono@gmail.com", "nova.pessoa@gmail.com"])
        self.assertEqual(cf.chamadas[-1][0], "GET", "a última chamada é a releitura que confere")

    def test_put_nao_leva_campo_so_de_leitura_e_preserva_o_resto(self):
        cf = CloudflareFalsa(politica())
        roda(cf, "x@y.com")
        corpo = cf.puts()[0][2]
        self.assertFalse(ae.SO_LEITURA & corpo.keys())
        self.assertEqual((corpo["name"], corpo["decision"], corpo["session_duration"]), ("Só eu", "allow", "24h"))

    def test_quem_ja_esta_nao_gera_put(self):
        cf = CloudflareFalsa(politica())
        cod, out, _ = roda(cf, "DONO@gmail.com")
        self.assertEqual(cod, 0)
        self.assertIn("já estava autorizado", out)
        self.assertEqual(cf.puts(), [])

    def test_email_invalido_recusa_sem_tocar(self):
        cf = CloudflareFalsa(politica())
        cod, _, err = roda(cf, "fulano")
        self.assertEqual(cod, 1)
        self.assertIn("não parece um e-mail", err)
        self.assertEqual(cf.puts(), [])

    def test_put_aceito_mas_nao_gravado_e_erro(self):
        """200 no PUT não é prova: se a releitura não mostra o e-mail, falha alto."""
        cf = CloudflareFalsa(politica(), mentir=True)
        cod, _, err = roda(cf, "x@y.com")
        self.assertEqual(cod, 1)
        self.assertIn("não aparece na política ao reler", err)


class Revogar(unittest.TestCase):
    def test_tira_so_o_pedido(self):
        cf = CloudflareFalsa(politica(emails=("dono@gmail.com", "outra@x.com")))
        cod, out, _ = roda(cf, "--revogar", "OUTRA@x.com")
        self.assertEqual(cod, 0)
        self.assertIn("revogado", out)
        self.assertEqual(ae.emails_da_politica(cf.pols["p1"]), ["dono@gmail.com"])

    def test_nao_tira_o_ultimo(self):
        cf = CloudflareFalsa(politica())
        cod, _, err = roda(cf, "--revogar", "dono@gmail.com")
        self.assertEqual(cod, 1)
        self.assertIn("último e-mail", err)
        self.assertEqual(cf.puts(), [])

    def test_quem_nao_esta_nao_gera_put(self):
        cf = CloudflareFalsa(politica())
        cod, out, _ = roda(cf, "--revogar", "ninguem@x.com")
        self.assertEqual(cod, 0)
        self.assertIn("não estava na lista", out)
        self.assertEqual(cf.puts(), [])

    def test_regra_que_nao_e_email_fica_intacta(self):
        pol = politica(emails=("dono@gmail.com", "outra@x.com"))
        pol["include"].append({"email_domain": {"domain": "defesacivil.sc.gov.br"}})
        cf = CloudflareFalsa(pol)
        roda(cf, "--revogar", "outra@x.com")
        self.assertIn({"email_domain": {"domain": "defesacivil.sc.gov.br"}}, cf.pols["p1"]["include"])


class AchaERenomeia(unittest.TestCase):
    def test_acha_pelo_nome_antigo_e_renomeia(self):
        cf = CloudflareFalsa(politica(pid="outra", nome="Outra coisa"), politica())
        cod, out, _ = roda(cf, "--renomear", "Autorizados")
        self.assertEqual(cod, 0)
        self.assertIn("'Só eu' → 'Autorizados'", out)
        self.assertEqual(cf.pols["p1"]["name"], "Autorizados")
        self.assertEqual(cf.pols["outra"]["name"], "Outra coisa")
        self.assertEqual(ae.emails_da_politica(cf.pols["p1"]), ["dono@gmail.com"], "renomear não mexe em quem entra")

    def test_depois_de_renomear_continua_achando(self):
        cf = CloudflareFalsa(politica(nome="Autorizados"))
        cod, out, _ = roda(cf, "--listar")
        self.assertEqual(cod, 0)
        self.assertIn("'Autorizados' (allow): 1 e-mail(s)", out)

    def test_nome_ambiguo_pede_o_id(self):
        cf = CloudflareFalsa(politica(pid="a"), politica(pid="b"))
        cod, _, err = roda(cf, "--listar")
        self.assertEqual(cod, 1)
        self.assertIn("CLOUDFLARE_ACCESS_POLICY_ID", err)

    def test_id_no_env_vence_o_nome(self):
        cf = CloudflareFalsa(politica(pid="a"), politica(pid="b", nome="Qualquer"))
        cod, out, _ = roda(cf, "--listar", env={"CLOUDFLARE_ACCESS_POLICY_ID": "b"})
        self.assertEqual(cod, 0)
        self.assertIn("'Qualquer'", out)

    def test_nenhuma_politica_conhecida_diz_quais_existem(self):
        cf = CloudflareFalsa(politica(nome="Outra coisa"))
        cod, _, err = roda(cf, "--listar")
        self.assertEqual(cod, 1)
        self.assertIn("'Outra coisa'", err)


class PoliticaDaAplicacao(unittest.TestCase):
    """Política antiga, criada dentro da aplicação: não está na lista das reutilizáveis."""

    def test_acha_na_aplicacao_e_grava_pelo_caminho_dela(self):
        cf = CloudflareFalsa(politica(), da_app=True)
        cod, out, _ = roda(cf, "x@y.com")
        self.assertEqual(cod, 0, out)
        self.assertEqual(cf.puts()[0][1], f"/accounts/{CONTA}/access/apps/app1/policies/p1")
        self.assertEqual(ae.emails_da_politica(cf.pols["p1"]), ["dono@gmail.com", "x@y.com"])
        self.assertNotIn("_caminho", cf.puts()[0][2])


class Credenciais(unittest.TestCase):
    def test_sem_conta_nao_chama_nada(self):
        cf = CloudflareFalsa(politica())
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(ae, "carrega_env"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            cod = ae.principal(["--listar"], chamar=cf)
        self.assertEqual(cod, 2)
        self.assertIn("CLOUDFLARE_ACCOUNT_ID", err.getvalue())
        self.assertEqual(cf.chamadas, [])

    def test_erro_da_api_nao_vaza_o_token(self):
        resp = mock.Mock(ok=False, status_code=403)
        resp.json.return_value = {"success": False, "errors": [{"code": 10000, "message": "Authentication error"}]}
        with mock.patch.object(ae.requests, "request", return_value=resp) as req:
            with self.assertRaises(ae.ErroAcesso) as ctx:
                ae.chamada_http("SEGREDO-123")("GET", "/accounts/x/access/policies", None)
        self.assertIn("403", str(ctx.exception))
        self.assertIn("Authentication error", str(ctx.exception))
        self.assertNotIn("SEGREDO-123", str(ctx.exception))
        self.assertEqual(req.call_args.kwargs["headers"]["Authorization"], "Bearer SEGREDO-123")


if __name__ == "__main__":
    unittest.main()
