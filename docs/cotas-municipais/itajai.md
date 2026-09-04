# Itajaí — foz do Açu e do Mirim (11 réguas)

**Portal:** https://defesacivil.itajai.sc.gov.br/monitoramento/  
**PLANCON inundação:** versão 17, 22/12/2025 — Tabela 11  
**199** · (47) 3228-7700

Cada estação tem **zero próprio**. Não comparar DC-10 (Limoeiro, 8–10 m) com DC-01 (estuário, ~1 m). Nove estações de estuário: `alerta_automatico=false` no monitor — a maré cruza a cota sem enchente.

---

## Tabela 11 (oficial)

| Estação | Local | Atenção | Alerta | Emergência |
|---|---|---|---|---|
| DC-01 | Itajaí-Açu · ICMBio/CEPSUL | 1,16 | 1,36 | 1,56 |
| DC-02 | Itajaí-Açu · Praça Celso Pereira / Murta | 1,60 | 2,00 | 2,50 |
| DC-03 | Mirim canal · Captação SEMASA | 1,48 | 1,85 | 2,50 |
| DC-04 | Mirim · Vitalmar | 1,50 | 1,85 | 2,25 |
| DC-05 | Mirim curso antigo · sítio | 1,60 | 2,20 | 3,00 |
| DC-06 | Mirim curso antigo · Itamirim | 1,50 | 1,85 | 2,55 |
| DC-07 | Ribeirão da Murta · Portal | 1,00 | 1,35 | 1,65 |
| DC-08 | Ribeirão Canhanduba | 1,80 | 2,30 | 2,89 |
| DC-09 | Ribeirão da Murta · ponte Lídia Puel | 1,12 | 1,32 | 1,52 |
| DC-10 | Mirim · Limoeiro | **8,00** | **9,00** | **10,00** |
| DC-11 | Açu · Santa Regina (Volta de Cima) | 3,00 | 4,00 | 5,00 |

PDF: https://defesacivil.itajai.sc.gov.br/wp-content/uploads/2025/12/Plano-de-Contingencia-de-Inundacao-ALTERADO-EM-22-12-25.pdf

Também publica níveis de Brusque, Blumenau e Rio do Sul na mesma página (outras réguas).

---

## Coletor

- HTML `/monitoramento/nivel-rios` a cada ~10 min.  
- Mapa Leaflet: `/monitoramento/Mapa.php`.  
- Maré: `/monitoramento/mares`.  
- Sem API JSON documentada. Título da estação no HTML é a chave do `extrair_picos.py`.
