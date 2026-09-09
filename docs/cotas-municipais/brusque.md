# Brusque — Itajaí-Mirim

**Portal:** https://defesacivil.brusque.sc.gov.br/  
**Telemetria:** 6 réguas de nível + 10 pluviômetros (rádio)  
**App / site:** cotas por endereço, manchas, rota segura  
**Emergência:** 199

Já entra no monitor com atenção **4,80 m** / inundação **6,00 m** (incompleto no JSON).

---

## Faixas da régua (ponte estaiada / Beira-Rio)

Fontes cruzadas: COMPDEC + imprensa + PLANCON municipal (Decreto 10.400/2025).

| Evento | Cota |
|---|---|
| Sai da calha (embaixo da estaiada) | **4,75–4,80 m** |
| Primeira casa (histórico 2015) | **7,50 m** |
| Inundação usada no monitor | **6,00 m** |
| Pico 17/11/2023 | **8,96 m** (3ª maior) |
| Pico 2011 | **10,03 m** |

Projeção operacional: pico de **Vidal Ramos** (~12 h) e revisão em **Botuverá**. Beira Rio Lote I/II sem cota depois das obras.

```json
"cotas_m": {
  "atencao": 4.8,
  "inundacao": 6.0,
  "transbordo_calha": 4.75,
  "primeira_casa_2015": 7.5,
  "pico_2023": 8.96,
  "pico_2011": 10.03
}
```

---

## Mapas oficiais

| Camada | URL |
|---|---|
| Cotas de ruas (azul 2023 / laranja 2011; 357 pontos até 8,96 m) | https://defesacivil.brusque.sc.gov.br/mapas/cotas-de-ruas |
| Cartas 7,00–15,00 m | citado no Decreto 10.400/2025 |
| Setorização de risco | https://defesacivil.brusque.sc.gov.br/mapas/setorizacao-de-risco |
| Rota segura / transenchente | https://defesacivil.brusque.sc.gov.br/mapas/rota-segura-transenchente |
| Estudo 2024 (PDF) | https://drive.google.com/file/d/1e6wvdeGW2TIWjiH25g358prD8UBHJuos |

Cotas de rua **podem estar defasadas** após obras (ago/2026). Segunda etapa do levantamento (pontos não atingidos em 2023) prevista e ainda em curso.

---

## Coletor

- Página: `/monitoramento` (estações minuto a minuto).  
- Sem API pública documentada (stack DEXTAK, igual Gaspar).  
- Câmera: ponte estaiada.  
- Não misturar com DC-10 de Itajaí (Limoeiro, outra régua).

---

## 09/09/2026 — 19 cheias de 2019 a 2024, da lista SECOM/Rádio Cidade

Matéria de 21/05/2024 (rc.fm.br, id 981258), crédito SECOM/Prefeitura, dados da Defesa Civil;
transcrita em `data/brutos/brusque-rc-fm-cheias-2019-2024-transcricao.tsv`. Entrou em
`enchentes.json` como `confianca: media` (imprensa citando a prefeitura):

- **14 registros novos** (31/05/2019 a 19/05/2024).
- **2 confirmações** de valor já cadastrado: 13/10/2023 = 6,91 e 17/11/2023 = 8,96.
- **1 divergência**: 15/12/2020, 5,08 na lista contra 4,95 no boletim da Defesa Civil com hora
  (20:45); o boletim fica adotado, a lista fica guardada.
- **29/10/2023 aparece duas vezes na fonte** (5,09 e 5,66): adotado o maior, o outro em `divergencias`.
- **12/12/2020 = 5,30 m** é maior que a crista de 15/12: o evento de dezembro de 2020 teve duas
  cristas, e o pico do evento no gráfico passa a ser o de 12/12. A medição de trânsito Salseiro →
  Brusque (15/12, 7,5 h) continua válida: pareia a segunda crista, que é a que tem hora dos dois lados.

