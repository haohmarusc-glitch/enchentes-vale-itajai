#!/usr/bin/env python3
"""
Trava as cotas de Taió e a regra de NÃO remapear os nomes das fases.

Taió tem CINCO fases no Plano de Contingência da COMPDEC (jan/2026), e o nosso
esquema tem quatro nomes. A tentação óbvia é empurrar tudo um degrau — chamar de
`atencao` a fase que a cidade chama de MONITORAMENTO — e assim "não perder" o
piso de 5,00 m. Isso faria a tela dizer "atenção" onde a própria Defesa Civil de
Taió diz que só está monitorando, e o `faixas.json` é explícito: o site DESCREVE
a faixa da cidade, não inventa uma.

O piso de 5,00 m não se perde: fica em `monitoramento`, chave que o código ainda
não desenha e por isso não muda aviso nenhum — mas está no dado, machine-readable,
para quando a tela souber mostrar a fase.

O que este teste impede: alguém "arrumar" o remapeamento sem ler o Plano, e
alguém mexer nos números sem trocar a fonte junto.
"""
import json
import unittest

from comum import DADOS

#: Piso de cada fase, do Plano de Contingência COMPDEC Taió, jan/2026.
FASES_DO_PLANO = {"monitoramento": 5.0, "atencao": 7.0, "alerta": 8.0, "emergencia": 9.0}


def taio() -> dict:
    d = json.loads((DADOS / "estacoes.json").read_text(encoding="utf-8"))
    return next(c for c in d["rios"]["itajai-acu"]["cidades"] if c["id"] == "taio")


class CotasDeTaio(unittest.TestCase):
    def test_as_quatro_fases_com_os_pisos_do_plano(self):
        self.assertEqual(taio()["cotas_m"], FASES_DO_PLANO)

    def test_os_nomes_nao_foram_remapeados_um_degrau(self):
        # O erro que este teste existe para pegar: atencao virar 5,00 (a fase de
        # MONITORAMENTO da cidade). A tela passaria a dizer "atenção" onde a
        # COMPDEC diz "monitoramento".
        c = taio()["cotas_m"]
        self.assertEqual(c["atencao"], 7.0, "atencao é a fase ATENÇÃO do Plano, não a de monitoramento")
        self.assertEqual(c["monitoramento"], 5.0, "o piso de 5,00 m não pode sumir do dado")

    def test_as_cotas_sobem_na_ordem_das_fases(self):
        c = taio()["cotas_m"]
        ordem = [c["monitoramento"], c["atencao"], c["alerta"], c["emergencia"]]
        self.assertEqual(ordem, sorted(ordem))
        self.assertEqual(len(set(ordem)), 4, "duas fases no mesmo metro não são duas fases")

    def test_a_emergencia_fica_abaixo_do_maior_pico_conhecido(self):
        """
        Sanidade contra transcrição errada: 09/10/2023 marcou 12,40 m em Taió.
        Cota de emergência ACIMA do maior pico registrado significaria que nem a
        maior cheia conhecida teria disparado emergência — sinal de que os
        números vieram de outra régua (a da barragem lê ~17 m).
        """
        enchentes = json.loads((DADOS / "enchentes.json").read_text(encoding="utf-8"))
        picos = [e["pico_m"] for e in enchentes["eventos"]
                 if e["cidade"] == "taio" and isinstance(e.get("pico_m"), (int, float))]
        self.assertTrue(picos, "Taió perdeu os picos históricos do enchentes.json")
        self.assertLess(taio()["cotas_m"]["emergencia"], max(picos))

    def test_a_fonte_nomeia_o_plano_e_o_estado_da_conferencia(self):
        c = taio()
        self.assertIn("Plano de Contingência", c["fonte_cotas"])
        self.assertIn("defesacivil.taio.sc.gov.br", c["fonte_cotas"])
        # NÃO conferido: o PDF não está em data/brutos/ e o domínio é
        # inalcançável daqui. Marcar true sem baixar o PDF seria mentir sobre o
        # nível de evidência — foi exatamente esse tipo de salto que custou
        # sessões neste projeto.
        self.assertFalse(c["cotas_verificado"])


if __name__ == "__main__":
    unittest.main()
