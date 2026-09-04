# Blumenau — tronco do Itajaí-Açu (Ponte Adolfo Konder)

**Portal / app:** [AlertaBlu](https://alertablu.blumenau.sc.gov.br/) (bloqueia robô; app Android/iOS)  
**SEDECI:** secretaria.defesacivil@blumenau.sc.gov.br · 199  
**Régua:** Ponte Adolfo Konder · ANA 83800002 · DCSC-00026  
**Já no monitor:** 6,00 / 6,50 / 7,40 (+ histórica 8,50)

---

## Faixas da régua do Centro

| Fase no app | Cota |
|---|---|
| Atenção | **6,00 m** |
| Alerta | **6,50 m** |
| Inundação | **7,40 m** |
| Inundação histórica (cadastro) | **8,50 m** |

Cores do AlertaBlu (rio, chuva e encosta **separados**, por região): verde normal · amarelo observação · laranja atenção · vermelho alerta · roxo alerta máximo.

Previsão hidrológica própria da SEDECI (assumiu o CEOPS em 2024): até **6 h** de antecedência. Dados a cada **5 min** (antes 15 min).

Revisão de cotas de rua contratada com a FURB (R$ 580 mil, dez/2024, 8 meses). Última revisão 2011–2012. Mapearam ruas até lâmina de **16 m**.

```json
"cotas_m": {
  "atencao": 6.0,
  "alerta": 6.5,
  "inundacao": 7.4,
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
