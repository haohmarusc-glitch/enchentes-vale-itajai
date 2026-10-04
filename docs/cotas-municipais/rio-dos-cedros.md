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
  Gravadas em `data/hidraulica.json` em 05/09/2026 com `tipo: "local"`, o que as separa das três de
  contenção da bacia (Oeste, Sul, Norte) em toda a interface. Sem área, volume, ano ou comportas: esta
  página não os traz, e não se inventa. Sem `a_montante_de` também — dizer que ficam logo acima da régua
  da Praça Matriz seria afirmar posição que o PLANCON não dá; usam `no_municipio`.

---

## 04/10/2026 — escala no plano vigente; vínculo com a estação estadual pendente

- **Tabela e vigência:** o Plano de Contingência v10.9 (abr/2026), p. 9, traz "De zero a 4,80 metros … estado
  normal. De 4,80 a 5,30 metros … ESTADO DE ATENÇÃO" e a tabela "5,70 Alarme / 5,30 Alerta / 4,80 Atenção / Abaixo
  Normal". ✅ Conferido em `data/brutos/varredura-pintar-2026-10-03/RioCedros_Plano-de-Contingencia-versao-10.9_2026-04.pdf`.
  A escala é a mesma do cadastro; o "Alarme" fica "Alarme".
- **Régua:** a p. 4 escolhe o Paço Municipal como sede "pela proximidade da régua de medição". A tabela não
  nomeia a régua. 🟡
- **Notícia 235108 da prefeitura** (data original 13/03/2014; a página também mostra 05/07/2024, que não é nova
  homologação): ≥ 4,80 / ≥ 5,30 / ≥ 5,70 m, e cita o acompanhamento pela régua eletrônica do CEOPS a partir de
  5,30 m. Fonte: handoff de 03/10/2026. **Não conferida daqui.**
- **Equivalência com a DCSC-00011:** ❌. A estação fica a 0,24 km do pino, viva (1,56 m em 03/10). Não há leitura
  municipal para parear.
