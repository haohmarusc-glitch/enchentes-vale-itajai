# Ilhota — cotas, plano e o que entra no monitor

**Página:** [Defesa Civil — Prefeitura de Ilhota](https://ilhota.sc.gov.br/defesa-civil/)  
**Documento:** [Plano de Contingência 2025/2028, versão 016 (PDF)](https://ilhota.sc.gov.br/wp-content/uploads/2025/08/Plano_de_Contingencia_Defesa_Civil_Ilhota.pdf)  
**Estação no monitor:** DCSC-00030 · tronco do Itajaí-Açu, perto da foz  
**Régua citada no plano:** estação hidrometeorológica da **Ponte Cláudio Jeremias Cadorin**  
**Consulta:** 3 de setembro de 2026  
**Emergência:** 199. Este arquivo não substitui aviso oficial.

A página institucional é só apresentação (Elementor). Cotas, faixas e ruas estão no PDF.

Não há API municipal de nível (nada no estilo Taió / Uniparking). Tempo real: rede estadual DCSC-00030.

---

## Faixas da régua do rio (usar no monitor)

Fonte: PLANCON, “Condições sobre o nível do Rio Itajaí”.

| Faixa na régua da ponte | Situação no plano |
|---|---|
| 0 a **9,20 m** | Rio na calha — estado **normal** |
| **9,20 a 10,00 m** | Represamento dos ribeirões — **atenção**. COMPDEC monitora; **não avisa a população** |
| **10,00 a 10,50 m** | Água nas várzeas — **prontidão**. Cautela nos avisos (evitar pânico) |
| acima de **10,50 m** | Sinal oficial de **emergência**; alagamento nas partes mais baixas |

O PDF escreve os valores por extenso (“Nove Metros e Vinte Centímetros”). Um trecho solto fala “10,50 centímetros”; no contexto da tabela é **10,50 m**.

Dois níveis de enchente no mesmo plano:

1. Represamento / transbordo dos **ribeirões** (média proporção) — cabe na faixa 9,20–10,00.  
2. Transbordo da calha do **Itajaí-Açu** (grande proporção) — a partir de 10,00 / 10,50.

Sugestão para `estacoes.json`:

```json
{
  "id": "ilhota",
  "nome": "Ilhota",
  "rio": "Rio Itajaí-Açu",
  "ramo": "tronco_acu",
  "codigo_dcsc": "DCSC-00030",
  "cotas_m": {
    "normal_ate": 9.2,
    "atencao": 9.2,
    "prontidao": 10.0,
    "emergencia": 10.5
  },
  "fonte_cotas": "PLANCON Ilhota 2025/2028 v016 — Ponte Cláudio Jeremias Cadorin — https://ilhota.sc.gov.br/wp-content/uploads/2025/08/Plano_de_Contingencia_Defesa_Civil_Ilhota.pdf",
  "verificado": true
}
```

Conferir se a DCSC-00030 é a mesma ponte. Se não for, cadastrar as faixas só na régua municipal.

---

## Cotas de rua ≠ cota da régua

O plano avisa: cotas de rua são **altitude em relação ao nível do mar**, “Régua Municipal”, começando em **12,00 m**. Não é o zero da ponte.

| Cota municipal (nível do mar) | Onde começa a listagem |
|---|---|
| **12,00 m** | Centro: Manoel Cordeiro Filho (Tabuleiro). Pedra de Amolar: Rua Turquesa |
| **12,15 m** | Pedra de Amolar: Turquesa, Pedra do Sol × Alexandrita, Pedra da Lua × Alexandrita, Alexandrita × Turquesa, Esmeraldas, Berilo, Topázio, Diamantes |
| **13,15 m** | Quase todo Pedra de Amolar + Centro (Felindo Furlani, Milton D. Machado, Modesto Vargas, Estrada Geral Pocinho) + Loteamento Primavera + Ilha Bela |

**Não misturar 12 m de rua com 9,20 m da ponte.** São zeros diferentes.

Não há My Maps / mancha por cota da régua.

---

## Picos observados (quadro do plano)

Amostra do quadro histórico (régua do rio):

| Data | Cota (m) |
|---|---|
| 1927-10-09 | 12,30 |
| 1955-05-20 | 10,61 |
| 1967-02-18 | 10,50 |
| 1976-05-29 | 10,85 |
| 1979-10-09 | 10,45 |
| 2001-10-01 | 11,02 |
| 2023-10-05 | 8,78 |
| 2023-10-09 | 10,19 |
| 2023-10-12 | **10,76** |
| 2023-11-03 | 9,50 |
| 2024-05-19 | 8,67 |

Outubro/2023 passou da emergência (10,50).

---

## Como usar no monitor

1. Pintar a DCSC-00030 com 9,20 / 10,00 / 10,50.  
2. Popup: “atenção 9,20 m ainda sem aviso à população; emergência só acima de 10,50 m”.  
3. Lista de ruas (12,00 / 12,15 / 13,15) só como camada de altitude — nunca como nível do rio.  
4. Sem API municipal; coletor = mapa estadual.  
5. Se a ponte da BR-470 fechar, o plano prevê segundo posto de comando no Braço do Baú — não muda a régua.
