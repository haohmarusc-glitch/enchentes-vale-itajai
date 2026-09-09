# Gaspar — tronco do Itajaí-Açu

**Portal:** https://defesacivil.gaspar.sc.gov.br/  
**App:** Alerta Gaspar (Android/iOS) — reativado ago/2025  
**E-mail:** defesacivil@gaspar.sc.gov.br  
**199** / (47) 3091-2020  
**Já no monitor:** atenção 5,00 / alerta 6,00 / emergência 7,00

---

## Régua e faixas

Fonte no site: **DC. Gaspar**. Estudo FURB/CEOPS (2019, R$ 278 mil) + carta de enchente.

| Uso | Cota |
|---|---|
| Atenção (cadastro do monitor) | **5,00 m** |
| Primeiras vias (boletim 2023) | **~6,20 m** |
| Alerta / inundação no monitor | **6,00 m** |
| Emergência no monitor | **7,00 m** |
| Pico 2023 | **7,45 m** |
| Pico 2011 | **9,42 m** |
| Pico 2008 | **9,80 m** |
| Máximo histórico listado | **12,00 m** (1852) · **11,50 m** (1983) |

Histórico completo: https://defesacivil.gaspar.sc.gov.br/enchentes

```json
"cotas_m": {
  "atencao": 5.0,
  "alerta": 6.0,
  "emergencia": 7.0
}
```

---

## Mapas e API

| Recurso | URL |
|---|---|
| Carta de enchente | https://defesacivil.gaspar.sc.gov.br/mapas/-carta-enchente-municipio-de-gaspar |
| Cotas por endereço | widget “Sua Cota” na home + `/mapas/cotas-de-enchente` |
| Estação | `/estacao/ver/21` |
| Boletins (endpoint interno, às vezes cai) | `http://node.dx.tec.br/api/dcgaspar/extrair-boletin` |

Stack DEXTAK. Nível na home atualiza sozinho (ex.: 2,05–2,60 m em 2–3/09/2026). Monitorar também o **Ribeirão Belchior** (app).

Dique municipal (R$ 14 mi anunciados) altera a mancha — revalidar cotas de rua depois da obra.

---

## 09/09/2026 — a régua não morreu

Confirmado no navegador em 08/09 ~21h: `/estacao/ver/21` continua viva sob o site
novo (DEXTAK) — "Rio Itajaí Açu Gaspar", 1,12 m, FONTE: DC. GASPAR, medição
08/09/2026 08:03. Legenda: normalidade < 5,00 · atenção > 5,00 ou chuva > 6,00 mm
· emergência > 7,00 — os valores do Plano. O que saiu em 07/09 foi a linha de
`/monitoramento/tabela`, não a régua. A página oferece "BAIXAR SÉRIE HISTÓRICA".

Ressalvas: a leitura tinha 13 h de idade às 21h (medir a cadência antes de
reapontar o coletor), e o host segue sem responder à VPS (só `--arquivo`).
Detalhes em `docs/COTAS-11-MUNICIPIOS-2026-09-09.md`.
