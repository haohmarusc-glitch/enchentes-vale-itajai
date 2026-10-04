# Ibirama — áreas de risco, cotas e o que entra no monitor

**Mapa enviado:** [ÁREAS DE RISCO — IBIRAMA](https://goo.gl/maps/dfcXKigjxcDj9WDS7?g_st=ac)  
**My Maps (mid):** `1AhHZ_XgW2E1Hio97Xshoy1YBsOaRllY`  
**Autor:** José Eduardo do Rosário (coordenador da COMPDEC de Ibirama)  
**Publicado:** 25 de maio · ~480 visualizações  
**KML:** `https://www.google.com/maps/d/kml?mid=1AhHZ_XgW2E1Hio97Xshoy1YBsOaRllY&forcekml=1`  
**Emergência:** 199 · WhatsApp COMPDEC (47) 98838-5645. Este arquivo não substitui aviso oficial.

---

## O que este mapa é (e o que não é)

Não é o formato de Ituporanga (“camada COTA — 3,00 m / 3,50 m…”).  
É o **cadastro municipal de áreas de risco**: 49 polígonos numa única camada (`Camada sem título`), todos com o nome genérico **ÁREA DE RISCO**.

Cores no My Maps:

| Cor | Grau | Quantidade |
|---|---|---|
| Vermelho (`#FF5252`) | Muito Alto | 19 |
| Laranja (`#E65100`) | Alto | 26 |
| Amarelo (`#FFD600`) | Médio | 4 |

Tipos (lidos no KML):

| Tipo | Polígonos |
|---|---|
| Deslizamento (planar / rotacional / misto) | ~35 |
| **Inundação** | 5 |
| **Alagamento** | 3 |
| Solapamento / erosão fluvial (com ou sem inundação) | 2 |
| Queda de blocos | 3 (combinados com deslizamento) |
| Fluxo de detritos / enxurrada | 3 |

Fontes citadas nos balões: CPRM 2016, Geovale 2011, KGEO 2017, Defesa Civil de SC 2019–2021, registros internos da COMPDEC 2020 e 2023, **atualização AMAVI 2025**.

**Para o monitor:** serve como camada de *onde alaga / onde escorrega*. **Não** substitui cota da régua. Nenhum polígono traz “inunda em X,XX m”.

---

## Polígonos hidrológicos (os que importam para enchente)

Centroide aproximado extraído do KML (primeiro vértice). Conferir no mapa antes de desenhar.

| # | Tipo | Grau | Fonte | lat, lon |
|---|---|---|---|---|
| 1 | Inundações | Muito Alto | CPRM 2016 | −27,04819, −49,58652 (oeste / Alto Benedito) |
| 2 | Alagamentos | Alto | COMPDEC 2023 | −27,04398, −49,56668 |
| 7 | Solapamento, erosão fluvial e inundações | Muito Alto | CPRM 2016 + AMAVI 2025 | −27,04327, −49,53776 (setor urbano no rio) |
| 12 | Alagamentos | Muito Alto | DC-SC 2021 | −27,05524, −49,53238 |
| 16 | Erosão fluvial / solapamento | Muito Alto | CPRM 2016 | −27,05766, −49,52277 |
| 17 | Inundações | Muito Alto | CPRM 2016 | −27,05393, −49,51813 |
| 34 | Inundações | Muito Alto | CPRM 2016 | −27,06848, −49,49992 |
| 35 | Inundações | Muito Alto | DC-SC 2020 | −27,08341, −49,48219 (jusante / Distrito) |
| 36 | Inundações | Muito Alto | CPRM 2016 | −27,07934, −49,49821 |
| 38 | Alagamentos | Muito Alto | DC-SC 2021 | −27,05796, −49,51942 |

O restante é encosta (deslizamento, queda de bloco, fluxo de detritos). Útil no app de risco, não na pintura da régua.

---

## Cotas oficiais da régua (plano, não o mapa)

**Estação no monitor:** DCSC-00020 · Rio Hercílio / Itajaí do Norte  
**Documento:** Decreto nº 5.431/2024 — homologa o PLAMCON  
[PDF no DOM/SC](https://s3cache.dom.sc.gov.br/atos/2024/08/1724680743_decreto_n_5.431__homologa_o_plano_municipal_de_contingncia.pdf)  
**Atualização:** Decreto nº 5.824/2025 homologa o PLAMCON 2025 (texto integral no site da Prefeitura; extrato no DOM).

Faixas do **Rio Itajaí do Norte**:

| Fase | Cota |
|---|---|
| Observação | 3,00 m |
| Atenção | 3,50 m |
| Emergência | 4,00 m |

Chuva no mesmo plano (referência, não pintar régua com isso):

- 50 mm/dia — observação  
- 50–100 mm — atenção  
- \> 100 mm/dia ou \> 200 mm acumulado — emergência  

Cotas aproximadas de rua no PLAMCON 2024:

- Rua Blumenau, BR-470 (Padre Anchieta), Rua Marechal Rondon — ~**4,00 m**
- Rua Dr. Getúlio Vargas, Rua 11 de Março — ~**6,00 m**

Informativos da COMPDEC em 2025 tratam 1,50 m como normalidade.

Sugestão para `estacoes.json`:

```json
{
  "id": "ibirama",
  "nome": "Ibirama",
  "rio": "Rio Hercílio / Itajaí do Norte",
  "codigo_dcsc": "DCSC-00020",
  "cotas_m": {
    "observacao": 3.0,
    "atencao": 3.5,
    "emergencia": 4.0
  },
  "fonte_cotas": "PLAMCON Ibirama 2024, Decreto 5.431/2024",
  "mapa_risco": "https://www.google.com/maps/d/viewer?mid=1AhHZ_XgW2E1Hio97Xshoy1YBsOaRllY",
  "verificado": true
}
```

Ibirama **não** está na fila do tronco do Açu: a cheia entra no Itajaí-Açu perto de Rio do Sul.

---

## API de nível

Não há API municipal no estilo Taió (`api-scr.uniparking.com.br`). O site [defesacivilibirama.com.br](https://www.defesacivilibirama.com.br/) é institucional. Nível ao vivo no monitor vem da rede estadual (Asthon / DC-SC), estação **DCSC-00020**.

Não misturar com a Barragem Norte (outra escala, painel de Rio do Sul).

---

## Como usar no monitor

1. Cadastrar `cotas_m` 3,00 / 3,50 / 4,00 na DCSC-00020.
2. Opcional: importar o KML e filtrar só os 10 polígonos hidrológicos (tabela acima) como camada “área que alaga”.
3. Não usar o mapa inteiro como mancha de cota — a maioria é encosta.
4. Se a COMPDEC publicar mancha por metro (como Ituporanga), substituir esta camada.

Contato do autor do mapa = coordenador da Defesa Civil. Dá para pedir a tabela de cotas de rua e o shapefile bruto sem passar por My Maps.

---

## 04/10/2026 — o plano identifica a estação, mas a validade terminou

Conferido no original (`data/brutos/varredura-pintar-2026-10-03/Ibirama_Decreto-5431-2024_PLAMCON.pdf`):
- **Tabela (p. 11, seção 4.2):** "NÍVEL DO RIO ITAJAÍ DO NORTE¹ 3,00m – OBSERVAÇÃO / 3,50 m - ATENÇÃO / 4,00 m -
  EMERGÊNCIA".
- **Régua (nota 1, p. 11; também p. 9):** "Dados provenientes da Estação Hidrometeorológica da Defesa Civil de
  Santa Catarina, localizada na ponte Prefeito Osvaldo Tadeu Beltramini." ✅ É a identificação física.
- **Vigência (p. 32, seção 5):** "Este plano tem validade até 07/08/2025, devendo ser reavaliado e atualizado."
  ❌ A tabela não pode ser tratada como vigente em out/2026.
- **Decreto 5.824/2025:** homologa um "PLAMCON 2025" sem anexo, e o texto do plano não foi achado.
  O boletim municipal de 11/09/2026 às 22h45 chamou 4,04 m de "atenção", contra a "emergência" a 4,00 m do
  plano de 2024.
- **Equivalência com o código:** o PLAMCON não escreve "DCSC-00020". O par boletim × DCSC-00020 de 11/09
  (4,04 × 4,04 m) e os de 14/08 e 01/09 indicam que é a mesma estação. 🟡
- **Nomes:** "Observação" fica "Observação". Não vira "atenção".
- **Enviado em 04/10/2026 o C26** (lembrete do pedido de 13/09). Ele pergunta se as faixas são lidas na
  DCSC-00020 e qual tabela vale.

---

## 04/10/2026 — decisão do Jefferson: a tabela de 2024 fica só como histórico

A tabela do PLAMCON 2024 (observação 3,00 · atenção 3,50 · emergência 4,00 m, Decreto nº 5.431/2024, p. 11) saiu
de `cotas_pendentes_de_vinculo` e foi para `cotas_historicas_plancon_2024` em `estacoes.json`, com a validade
encerrada (até 07/08/2025, p. 32). Não colore a leitura atual: a validade acabou, o PLAMCON 2025 não tem texto
público, e o boletim de 11/09/2026 chamou 4,04 m de "atenção". Ibirama continua com a leitura da DCSC-00020 e a
faixa da própria Defesa Civil de SC, quando houver. Volta a ser considerada só com a tabela vigente (C26).
