# Timbó — Rio Benedito / Rio dos Cedros

**Prefeitura:** https://www.timbo.sc.gov.br/  
**Cotas de rua:** [geo.timbo.sc.gov.br](https://geo.timbo.sc.gov.br) (camada COTA ENCHENTE) + Instagram  
**Régua:** Rio Benedito, Rua Equador  
**COMPDEC:** Eduardo Senem · 199  
**PLANCON:** PDF dez/2025

---

## Ativação do plano (homologado)

O PLANCON liga o gabinete quando o **Benedito ou o Cedros ≥ 5,00 m** (ou chuva ≥ 200 mm FURB/CENAD).

| Uso | Cota |
|---|---|
| Ativação PLANCON | **5,00 m** |
| Ruas em alerta citado (2024) | **6,00 m** — Beco Guatemala, Rua Arthur Giotti, Rua Haiti |
| Pico operacional visto | 7,62 m (jan/2021) · 6,89 m (alerta máximo, rede social) |

Cotas de rua (2022) seguem a régua da Rua Equador — lista por bairro no Instagram / GEO Timbó. Não extrair número a número aqui; o mapa é a fonte.

```json
"cotas_m": {
  "ativacao_plancon": 5.0,
  "ruas_alerta_citadas": 6.0
}
```

`verificado: false` nas faixas atenção/alerta/emergência clássicas — o plano só fixa o gatilho de 5 m.

Tempo real: DC-SC. Sem API municipal.

---

## 09/09/2026 — escala de quatro faixas, por imprensa

ND Mais (31/08/2026), citando a Defesa Civil de Timbó: até 2,00 m normal ·
2,01–3,00 atenção · 3,01–4,29 alerta · a partir de 4,30 alto risco, no Rio
Benedito. A notícia não nomeia a régua (o município tem três: Benedito, Cedros
e Rua Indaial, após a junção). **Não pinta**; a tela avisa em texto. Entra em
`cotas_m` quando o PLANCON ou a COMPDEC confirmar régua e tabela.
