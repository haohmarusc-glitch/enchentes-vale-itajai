# Vidal Ramos — cabeceira do Itajaí-Mirim

**Posição no monitor:** primeira cidade do ramo `itajai-mirim` (`ordem`: 1)  
**Coordenadas da régua no cadastro:** −27,38547, −49,35812  
**Consulta:** 3 de setembro de 2026  
**Emergência:** 199. Este arquivo não substitui aviso oficial.

A COMPDEC de Vidal Ramos **não publicou** tabela nomeada atenção / alerta / emergência. O que existe é comportamento observado + uso da régua por Brusque (jusante).

---

## Comportamento do rio

O município é o **berço do Itajaí-Mirim**. A régua responde **muito rápido** a volume alto na cabeceira: enxurrada ou alagamento pontual no centro e em vias como a **Avenida Jorge Lacerda**, sem o tempo de deslocamento que o tronco do Açu tem entre Taió e Blumenau.

A mesma onda desce para **Botuverá** e **Brusque**. A Defesa Civil de Brusque projeta o pico local a partir do pico de Vidal Ramos (e revisa depois que a onda passa por Botuverá). Exemplo: em 11/07/2026, com 67,1 mm/24 h em Vidal Ramos, Brusque projetou 4,70 m no Mirim.

---

## Patamares observados (não são faixa oficial)

Em cheias recentes, **cerca de 3,00 m até quase 3,80 m** na régua de Vidal Ramos já indicam **atenção ou transbordo da calha** em trechos sensíveis (centro / Av. Jorge Lacerda).

A Defesa Civil local, citada em 2015 pelo jornal *O Município*, disse que o rio transborda **“acima de 3 metros”**, sem metragem exata; o mesmo levantamento apontava ~**3,50 m**. Tempos de descida no mesmo texto: **5–6 h** até Botuverá, **~12 h** até Brusque.

| Valor | Como tratar |
|---|---|
| ~3,00 m | COMPDEC (2015): transborda “acima de 3 m” |
| ~3,50 m | levantamento 2015 (imprensa) |
| ~3,80 m | teto visto em eventos recentes |

Isso **não** está num PLANCON homologado. Obras e a intensidade da chuva mudam o impacto. Não copiar as cotas de Brusque (atenção ~4,80 / inundação 6,00; pico 2023 = 8,96 m) — zeros diferentes.

Sugestão **provisória** para `estacoes.json` (`verificado: false`):

```json
{
  "id": "vidal-ramos",
  "nome": "Vidal Ramos",
  "rio": "Rio Itajaí-Mirim",
  "ordem": 1,
  "cotas_m": {
    "atencao_observada": 3.0,
    "transbordo_observado": 3.8
  },
  "fonte_cotas": "comportamento recente da régua (imprensa local + operação de Brusque); COMPDEC sem tabela publicada",
  "verificado": false,
  "observacao": "Cabeceira: sobe rápido. Av. Jorge Lacerda e centro são os primeiros pontos. Jusante: Botuverá, depois Brusque. Confirmar com a COMPDEC antes de pintar emergência."
}
```

Pendência já anotada no repo (ofício C5 / EPAGRI-CIRAM).

---

## Tempo real

| Fonte | URL | Nota |
|---|---|---|
| EPAGRI/CIRAM — Rios on-line | https://ciram.epagri.sc.gov.br/rios-online/ | monitoramento hidrológico oficial da cabeceira |
| Mapa DC-SC | https://monitoramento.defesacivil.sc.gov.br/mapa | estação Asthon ≈ DCSC no cadastro do monitor |
| Defesa Civil de Vidal Ramos | Prefeitura / 199 | impacto local, obras, interdição |

Sem API municipal tipo Taió. O coletor atual (Asthon + DC-SC) cobre o nível; CIRAM é a checagem da cabeceira.

---

## Como usar no monitor

1. Não deixar `cotas_m` vazio se for pintar: usar 3,00 / 3,80 só como **observado**, badge “não homologado”.
2. Card da cidade: “cabeceira — sobe em minutos; olhe CIRAM + Av. Jorge Lacerda”.
3. Encadear tempo de descida Vidal Ramos → Botuverá → Brusque (é o único ramo em fila do monitor). Não misturar com o tronco do Açu.
4. Quando a COMPDEC ou o CIRAM publicar faixa oficial, substituir esta nota.

---

## O endpoint `panel` da Asthon NÃO tem a cota — medido em 04/09/2026

A hipótese em aberto era que `public.asthon.com.br/public/panel?city_id=4214805`
trouxesse `band_thresholds` por régua e fechasse esta pendência com o dado na
fonte. **Foi capturado na VPS e não tem.** Para a régua de Vidal Ramos,
`station_id` `bd65df3e-a5e3-4760-a879-56df0fb90787`, às 11:35 (−03):

| campo | valor |
|---|---|
| `level_m` | 2,50 m |
| `level_sensor` | `1` (é régua de rio) |
| `band_thresholds` | **`null`** |
| `attention_level` | **`null`** |
| `overflow_cota_m` | **`null`** |
| `river_name` | **`null`** |

Não é captura incompleta — é ausência do campo na fonte. **Não repetir a
consulta.** Restam a EPAGRI (ofício C5; o "Rios On-Line" classifica cada estação
em faixas) e a COMPDEC de Vidal Ramos.

### Por que os 3,50 m continuam fora do `estacoes.json`

O número existe e é público: 3,50 m de transbordo (O Município, 2015), com a
Defesa Civil local citada na mesma matéria dizendo "acima de 3 m", sem faixa.
Tentador, porque Vidal Ramos comanda **84,2 km cinza** — 45% do Mirim.

O que impede não é purismo. É que **gravar uma cota não acende só o amarelo:
acende o verde por baixo dela.** Hoje, sem cota, a cabeceira e o trecho a jusante
saem CINZA, e cinza no mapa diz "não sei" — que é a verdade. Com 3,50 m gravado,
a leitura de 2,50 m de hoje pintaria 84 km de rio de VERDE, ou seja, o mapa
afirmaria segurança com base num número de imprensa sobre *comportamento
observado*, não numa faixa de acionamento. E "transbordo" é justamente o ponto em
que a água **já saiu** — como os 6,00 m de Indaial e a cota de Brusque —, então
o amarelo chegaria tarde e o verde chegaria cedo, os dois erros na direção que
mata.

Indaial tem o número gravado e Vidal Ramos não pela diferença que importa: os
6,00 m saem da **página da própria COMPDEC**, e os 3,50 m saem de uma matéria de
jornal de dez anos atrás. A escala de confiança do projeto separa as duas
(`alta` = oficial, `media` = imprensa), e limiar que dispara aviso é o último
lugar onde `media` serve.

Se a decisão mudar, ela é do Jefferson — e o caminho honesto seria gravar como
`inundacao` (a faixa que diz "a água já está fora"), nunca como `atencao`.
