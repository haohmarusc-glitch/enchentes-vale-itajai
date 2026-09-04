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
