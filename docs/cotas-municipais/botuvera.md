# Botuverá — Itajaí-Mirim (sem faixa homologada)

**Prefeitura:** https://www.botuvera.sc.gov.br/  
**COMPDEC:** (47) 98498-9777 · defesacivil@botuvera.sc.gov.br  
**Ordem no ramo:** 2 (depois de Vidal Ramos, antes de Brusque)  
**Emergência:** 199

Não há portal de cotas nem API. Carta de Enchentes estadual anunciada em nov/2025 (R$ 412 mil, junto com Apiúna, Doutor Pedrinho e Guabiruba) — **ainda sem publicação**.

---

## Transbordo observado (não homologado)

Levantamento 2015 (*O Município*), “projeção da prefeitura”: o rio transborda com cerca de **7,50 m** na “parte principal” (ponto em que a Defesa Civil mede).

Tempo de onda: **5–6 h** depois do pico de Vidal Ramos; Brusque revisa a projeção quando a cheia passa por Botuverá.

```json
"cotas_m": {
  "transbordo_observado": 7.5
}
```

`verificado: false`.

---

## Barragem (não é cota da cidade)

Edital da Barragem de Botuverá (Rio Itajaí-Mirim, Barra da Areia): ~R$ 153 milhões, 40,8 m de altura, 20,2 hm³, 2 comportas. Destino: amortecer Brusque e Itajaí. Não cria faixa da régua urbana.

Nível ao vivo: DC-SC / CIRAM. Sem endpoint municipal.

---

## 04/10/2026 — tabela operacional localizada no PLANCON 2026; vínculo com a régua pendente

- **Tabela localizada:** Decreto 3.651/2026, publicado em 15/09/2026, aprova o PLANCON. A seção 4.1, "Critérios
  operacionais de referência" (p. 9 do PDF, impressa 6), traz Normal até 3,0 m; Atenção 3,0 a 4,0 m; Alerta 4,0
  a 6,0 m; Emergência acima de 6,0 m. O plano manda considerar tendência, chuva a montante e impactos, e diz que
  os números não substituem alerta oficial.
  - Fonte: https://www.botuvera.sc.gov.br/wp-content/uploads/2026/09/1789494009_decreto_3651_2026__plancon_assinado_extrato.pdf
  - **Não conferido daqui** (host bloqueado). A transcrição é do handoff de 03/10/2026.
- **A mesma escala já aparecia** no plano de saúde VIGIDESASTRE de ago/2023, sem régua nomeada
  (`data/brutos/varredura-pintar-2026-10-03/VigSanSC_PPR-ESP-Botuvera_VIGIDESASTRE.pdf`).
- **Régua:** a tabela não nomeia régua, estação nem zero. ❌
- **Limites:** a redação sobrepõe 3,0 e 4,0 m. Não escolher `>=` ou `>` sem a COMPDEC dizer.
- **Conflito que continua:** em 31/08/2026 há três escalas.
  - 3,87 m "dentro da normalidade" (DC de Botuverá). Pela tabela de 2026, seria "atenção".
  - 4,86 m "atenção" (DC de Brusque).
  - 3,58 m "Emergência" no SDE (dez/2023, estação da DCSC).
- **Leitura:** DCSC-00018 viva em 03/10 (3,37 m); DCSC-00027 sem leitura.
- O "transbordo observado" de 7,50 m (2015) fica como está. O PLANCON de 2026 cita a ponte do trevo a partir
  de 7,50 m. Não é faixa.
- Complemento ao C17 preparado em `docs/oficios-b1-c15-c22.md`. Quadro geral em
  `docs/COTAS-MUNICIPAIS-2026-10-04.md`.
