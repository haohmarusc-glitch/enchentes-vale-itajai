# Indaial — cotas de enchente

**Página oficial:** [Cotas de enchente — Defesa Civil Indaial](https://indaial.atende.net/subportal/defesa-civil-indaial/pagina/cotas-de-enchente)  
**Portal:** https://indaial.atende.net/subportal/defesa-civil-indaial  
**Estação no monitor:** DCSC-00006 · tronco do Itajaí-Açu (`ordem_no_ramo`: 3)  
**Consulta:** 3 de setembro de 2026  
**Emergência:** 199. Este arquivo não substitui aviso oficial.

---

## O que a COMPDEC publica

Não há tabela nomeada “atenção / alerta / emergência” como em Taió ou Ibirama. Há um **limiar operacional de rua**:

> Com **6 m** do nível do Rio Itajaí-Açu já se tem registro de alagamentos nas ruas:

| Via | Observação |
|---|---|
| Rua Sete de Setembro | Centro / baixa |
| Avenida Carlos Schroeder | sede da Defesa Civil fica no 815, Nações |
| Rua Melvin Jones | |
| Rua Bagé | |
| Beco 2 de Julho | |
| Beco Itapuã | |
| Rua Presidente Nereu | |
| Rua Mariana | |
| Rua 3 Corações | |
| Rua ID 24 | |
| Rua 24 de Outubro | |
| Rua Brusque | |

Aviso no rodapé da página: **“Moradores devem ficar atentos!!”**

Na mesma tela, aba **Arquivos**:

- PDF **“Indaial - cotas de enchente”** — a própria página manda olhar ali os **picos máximos das cheias** (série histórica, não a faixa de acionamento). O arquivo é servido pelo Atende.Net (SPA); o link direto muda com sessão.

Não há mancha por cota (não é o formato My Maps de Ituporanga). Não há API municipal de nível.

---

## Picos históricos (contexto, não faixa)

Documentados no [Portal de Indaial — enchentes 1983/1984](https://www.indaial.com.br/enchentes):

| Evento | Pico na régua de Indaial |
|---|---|
| Julho de 1983 | **7,78 m** acima do nível normal |
| 1984 | **8,04 m** acima do nível normal |

Conferir no PDF da aba Arquivos se a COMPDEC atualizou a série (2011, 2022, 2023 etc.).

---

## Sugestão para `estacoes.json`

A página **não** chama 6,00 m de “atenção” nem de “emergência”. Chama de **primeiro registro de alagamento**. Usar esse nome, para não inventar faixa.

```json
{
  "id": "indaial",
  "nome": "Indaial",
  "rio": "Rio Itajaí-Açu",
  "ramo": "tronco_acu",
  "codigo_dcsc": "DCSC-00006",
  "cotas_m": {
    "primeira_inundacao": 6.0
  },
  "fonte_cotas": "https://indaial.atende.net/subportal/defesa-civil-indaial/pagina/cotas-de-enchente",
  "verificado": true,
  "observacao": "A COMPDEC lista 12 vias com alagamento já registrado a 6,00 m na régua do Itajaí-Açu. Não publica atenção/alerta/emergência. Picos clássicos: 7,78 m (1983) e 8,04 m (1984). Estação alimenta a curva-chave do CEOPS/FURB para vazão em Blumenau — outra escala, outro uso."
}
```

Leitura alternativa, se o monitor exigir três chaves (marcar `verificado: false` nas duas inferidas):

```json
"cotas_m": {
  "atencao": 6.0,
  "alerta": 7.0,
  "emergencia": 7.78
}
```

`7,00` e `7,78` **não** estão na página de cotas. Só o `6,00`.

---

## API / tempo real

- Nível ao vivo: rede estadual, estação **DCSC-00006** — [mapa DC-SC](https://monitoramento.defesacivil.sc.gov.br/mapa).
- Sem endpoint municipal tipo Taió (`api-scr.uniparking.com.br`).
- Facebook da COMPDEC ([Defesa Civil Indaial](https://www.facebook.com/indaialdefesacivil/)) republica boletim estadual; moradores pedem medição local no mural.
- Zoneamento / lote: [IndaGeo](https://indaial.atende.net/) no Portal do Cidadão — não é mancha de enchente.
- Declaração de área sujeita a alagamento: serviço no AprovaDigital (`indaial.prefeituras.net`), não mapa.

---

## Como usar no monitor

1. Preencher `cotas_m.primeira_inundacao = 6.0` (ou `atencao = 6.0` se a UI só pinta três cores).
2. Pintar amarelo/laranja a partir de 6,00 m — é quando a própria Prefeitura diz que já alaga rua.
3. Não copiar as faixas de Blumenau (6,00 / 6,50 / 7,40) nem as de Gaspar. Zeros diferentes.
4. Lista das 12 vias pode ir num popup da cidade (“ruas que já alagam a 6 m”).
5. Se alguém baixar o PDF da aba Arquivos, acrescentar aqui a tabela de picos.

Contato COMPDEC: defesacivil@indaial.sc.gov.br · Av. Carlos Schroeder, 815 — Nações.
