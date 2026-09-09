# Blumenau — tronco do Itajaí-Açu (Ponte Adolfo Konder)

**Portal / app:** [AlertaBlu](https://alertablu.blumenau.sc.gov.br/) (bloqueia robô; app Android/iOS)  
**SEDECI:** secretaria.defesacivil@blumenau.sc.gov.br · 199  
**Régua:** Ponte Adolfo Konder · ANA 83800002 · DCSC-00026  
**Já no monitor (desde 09/09/2026):** Observação 3 · Atenção 4 · Alerta 6 · Alerta Máximo 8 (+ histórica 8,50)

---

## Faixas da régua do Centro

Fonte: `static/data/nivel_oficial.json`, campo `condicoes` (fonte "AlertaBLU"), lido na VPS
em 09/09/2026 — bruto `data/brutos/blumenau-alertablu-nivel-oficial-sem-serie-2026-09-09.json`.

| Condição na fonte | A partir de | Chave no cadastro |
|---|---|---|
| Normalidade | 0 m | — |
| Observação | **3,00 m** | `monitoramento` |
| Atenção | **4,00 m** | `atencao` |
| Alerta | **6,00 m** | `alerta` |
| Alerta Máximo | **8,00 m** | `emergencia` (a tela escreve "Alerta Máximo", via `cotas_nomes_na_fonte`) |
| Inundação histórica (cadastro) | **8,50 m** | `inundacao_historica` |

Até 09/09/2026 o cadastro trazia **6,00 / 6,50 / 7,40**, rotulados "AlertaBlu" sem bruto —
origem desconhecida (7,40 coincide com a menor cota de rua, Rua São Rafael). A tela pintava
atenção **dois metros tarde**. Ficaram em `cotas_divergencias`.

Cores do AlertaBlu (rio, chuva e encosta **separados**, por região): verde normal · amarelo observação · laranja atenção · vermelho alerta · roxo alerta máximo.

Previsão hidrológica própria da SEDECI (assumiu o CEOPS em 2024): até **6 h** de antecedência. Dados a cada **5 min** (antes 15 min).

Revisão de cotas de rua contratada com a FURB (R$ 580 mil, dez/2024, 8 meses). Última revisão 2011–2012. Mapearam ruas até lâmina de **16 m**.

```json
"cotas_m": {
  "monitoramento": 3.0,
  "atencao": 4.0,
  "alerta": 6.0,
  "emergencia": 8.0,
  "inundacao_historica": 8.5
}
```

---

## Rede e coletor

- 17 pluviômetros + 1 meteo + 1 hidro (Ramiro, integrada à DC-SC).  
- Barragens Taió / Ituporanga / José Boiteux no app.  
- Rotas de fuga no AlertaBlu.  
- Site antigo: `alertablu.cob.sc.gov.br`.  
- Sem API pública estável (WAF). Usar DC-SC / página de Itajaí “Blumenau” como fallback.

Não misturar com Timbó (Benedito) nem com DC-10 de Itajaí.

---

## ✅ 09/09/2026 — conferido: a escala de cinco estágios é a oficial (histórico da decisão)

Levantamento externo (não conferido daqui; host bloqueado) relata, da página
oficial `defesacivil.blumenau.sc.gov.br/d/nivel-do-rio`, uma escala de **cinco
estágios**: Normalidade 0–3 m · Observação 3–4 · Atenção 4–6 · Alerta 6–8 ·
Alerta Máximo acima de 8 m. Os nomes batem com as cinco cores listadas acima; os
números não batem com os três que este arquivo cadastra desde 30/08 (commit
`9ae8f87`, "AlertaBlu", sem bruto). Se a escala de cinco for a vigente, a tela
pinta atenção **2 m tarde**.

Decidir: `python3 scripts/conferir_faixas_blumenau.py` na VPS imprime as faixas
que `static/data/nivel_oficial.json` publica. Enquanto isso a tela avisa em
texto (`cotas_aviso_publico`). Registro em `cotas_divergencias` de Blumenau.
