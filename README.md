# Enchentes do Vale do Itajaí

Site com dados históricos de enchentes nos rios **Itajaí-Açu** e **Itajaí-Mirim** (SC): nível do rio em cada cidade, previsão empírica para a cidade a jusante e tempo estimado de chegada da onda de cheia. Itajaí, na foz, recebe os dois rios e a influência da maré.

> Este projeto **não substitui** o AlertaBlu, a Defesa Civil de SC nem as Defesas Civis municipais. Em emergência, ligue 199.

## Estrutura

```
data/
  estacoes.json   cidades, códigos ANA, cotas de referência, ordem no rio
  enchentes.json  picos históricos por rio/cidade/data, com fonte e confiança
  transito.json   tempos de trânsito da onda de cheia entre cidades
scripts/          coleta (ANA, Defesa Civil) e cálculo de correlações (Python)
web/              site (React)
```

## Telas previstas

1. **Itajaí-Açu** — Taió/Rio do Sul → Ibirama → Indaial → Blumenau → Gaspar → Ilhota → Itajaí
2. **Itajaí-Mirim** — Vidal Ramos → Botuverá → Brusque → Itajaí
3. **Itajaí (foz)** — chegada dos dois picos + maré

## Fontes

- ANA / HidroWeb (séries históricas): https://www.snirh.gov.br/hidroweb
- Defesa Civil SC (tempo real): https://monitoramento.defesacivil.sc.gov.br/
- AlertaBlu (Blumenau): https://alertablu.blumenau.sc.gov.br/
- Defesa Civil de Itajaí: https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios
- CEOPS/FURB (acervo histórico): http://ceops.furb.br/

## Pendências

- [ ] Solicitar acesso à API da ANA (hidro@ana.gov.br)
- [ ] Verificar códigos ANA das estações (`verificado: false` em `estacoes.json`)
- [ ] Localizar estações do Itajaí-Mirim e de Gaspar/Ilhota/Itajaí
- [ ] Levantar picos por cidade para os mesmos eventos (calibrar tempos de trânsito)
- [ ] Descobrir o endpoint JSON do monitoramento da Defesa Civil SC
