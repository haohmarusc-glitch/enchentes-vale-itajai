# Rio dos Cedros — Rio dos Cedros (afluente)

**Prefeitura:** https://riodoscedros.sc.gov.br/  
**Painel:** [Looker Studio — Nível Rio](https://lookerstudio.google.com/u/1/reporting/c216f524-2fab-4c1f-80ea-1db2d6d2416b/page/p_y3vysf4ufd)  
**PLANCON municipal** (versão ~10.7, 2022) + nota antiga no site  
**199**

---

## Faixas da régua (Praça Matriz)

Fonte cruzada: escala publicada no site (monitoramento antigo) + cadência do PLANCON.

| Fase | Cota |
|---|---|
| Atenção | **4,80 m** (monitorar a cada 30 min a partir de 4,50) |
| Alerta | **5,30 m** |
| Alarme | **5,70 m** |
| Bocas-de-lobo da praça | **6,02 m** |

O Looker marca “Nível Enchente – Praça Matriz” em **6,00 m** e “Nível Normal” ~0,90 m. Lê a rede estadual a cada 15 min.

```json
"cotas_m": {
  "atencao": 4.8,
  "alerta": 5.3,
  "alarme": 5.7,
  "praca_boca_lobo": 6.02
}
```

Confirmar com a COMPDEC se a escala de 2014 ainda vale depois do desassoreamento (R$ 3,5 mi / 4,92 km, 2026).

---

## Tempo real

- Fonte bruta: https://monitoramento.defesacivil.sc.gov.br/mapa  
- Pluviômetros CEMADEN (centro, out/2025): https://resources.cemaden.gov.br/graficos/interativo/grafico_CEMADEN.php?menu=periodo&idpcd=17662&uf=SC  
- Barragens locais (PLANCON antigo): Pinhal (Alto Cedros) e Rio Bonito (Palmeiras) — **não** são Taió/Ituporanga.
