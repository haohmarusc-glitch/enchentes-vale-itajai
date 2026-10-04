# Guabiruba — sem cota de régua

**Prefeitura:** https://guabiruba.sc.gov.br/  
**Ramo:** Itajaí-Mirim (afluente / encosta do Vale Europeu; enxurrada mais que calha)  
**Emergência:** 199

Não há tabela de atenção/alerta/emergência da régua. Carta de Enchentes estadual (nov/2025, R$ 412 mil com Apiúna, Botuverá e Doutor Pedrinho) **não publicada**.

O risco local histórico é **enxurrada de encosta** (ex.: 170 mm numa noite, ~2 mil afetados, Lageado Alto), não o mesmo zero de Brusque ou Vidal Ramos.

Nível ao vivo, se existir estação: mapa DC-SC. Sem API municipal.

```json
"cotas_m": {}
```

Pendência: esperar a Carta de Enchentes ou ofício à COMPDEC.

---

## 09/09/2026 — a estação é do ribeirão

Segunda fonte para o que o validador achou sozinho em 05/09 (pino a 4,24 km do
Mirim): TV Brusque e Araguaia FM descrevem a estação de Guabiruba no Rio
Guabiruba, recente, com 3,48 m enquanto o Mirim em Brusque marcava ~4 m. Não se
comparam. Qualquer cota futura daqui é do ribeirão.

---

## 04/10/2026 — canal para encaminhar o C20

- **Ouvidoria da Prefeitura:** https://guabiruba.sc.gov.br/ouvidoria/ · ouvidoria@guabiruba.sc.gov.br ·
  (47) 3308-3100, com protocolo no Atende.net. Fonte: handoff de 03/10/2026. **Página não conferida daqui**
  (host bloqueado). O telefone confere com `data/brutos/varredura-pintar-2026-10-03/Guabiruba_telefones-uteis.html`.
- É canal administrativo: o pedido vai endereçado à COMPDEC de Guabiruba, pedindo encaminhamento ao setor
  técnico. **Não é e-mail direto da COMPDEC** e não comprova régua, rio nem faixas.
- **Leitura de 01/10/2026** (DC de Brusque, Araguaia FM): "Já em Guabiruba, o rio está em 1,02 metro, após pico
  de 1,27 metro." Não está escrito que é a DCSC-00029, nem que é o mesmo curso d'água.
- C20 com o canal da Ouvidoria em `docs/oficios-b1-c15-c22.md`. Não enviado.

---

## 04/10/2026 — afluente lateral e zero local (decisão do Jefferson)

- **Topologia:** Guabiruba saiu da fila do Mirim. A régua fica no ribeirão Guabiruba, que entra no Mirim
  perto de Brusque; o tronco é Vidal Ramos → Botuverá → Brusque → Itajaí. Não há tempo de descida
  Guabiruba → Brusque.
- **DCSC-00029 no zero local:** leitura abaixo de 10 m vale como régua do ribeirão, com zero próprio da
  estação (0,63 m em 03/10). Não é a cota ortométrica (~25–28 m) que a estação publicou de 01/04/2026 até
  a volta, nem a dos boletins de Brusque. Valor ≥ 10 m continua em `suspeitas`.
- **O que não muda:** sem cota, sem faixa, `usar_para_cota: false`. A série anterior a 01/04/2026 não é
  juntada à de depois da volta sem conferir o zero, e a data da volta ainda precisa ser conferida no
  servidor (`docs/PROPOSTAS-AUDITORIA-2026-10-03.md`, item 3). Os picos de 2026 continuam fora de
  `enchentes.json`.
