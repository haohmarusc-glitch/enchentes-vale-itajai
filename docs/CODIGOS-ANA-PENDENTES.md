# Os códigos ANA que faltam — o que fechou aqui e o que só fecha de fora

Data: 07/09/2026. Continua `docs/INVENTARIO-ANA.md`.

## ⛔ O ambiente de desenvolvimento não alcança a ANA

Medido em 07/09/2026: **todo `*.ana.gov.br` responde 403 no CONNECT do proxy**, e o
mesmo vale para `snirh.gov.br` e `dadosabertos.ana.gov.br`. Testados e bloqueados:

```
dadosabertos.ana.gov.br   www.snirh.gov.br   metadados.snirh.gov.br
www.ana.gov.br            arcgis.ana.gov.br  telemetriaws1.ana.gov.br
```

Isso não é intermitência nem falta de credencial: o inventário público
(`telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroInventario`) **não exige
autenticação** e mesmo assim não passa. **Nenhuma coordenada da ANA pode ser lida
daqui.** O que dava para fechar sem a ANA está abaixo; o resto virou script para
rodar de fora.

---

## ✅ Brusque fechou — e o que faltava não era da ANA

`codigo_ana` de Brusque agora é **83900000 BRUSQUE (PCD)**, fluviométrica no
Itajaí-Mirim, 1.240 km², escala desde 1929 e sem fim declarado.

O `falta` registrado no candidato dizia: *"o nosso `codigo_dcsc` de Brusque é NULL —
os 51 m são até a DCSC-00019, que este repositório nunca afirmou ser este pino"*.
Estava certo, e a resposta estava dentro de casa, em dois lugares:

1. **A coordenada.** O pino de Brusque em `estacoes.json` fica a **3,5 m** da
   DCSC-00019 em `data/brutos/dcsc-estacoes-coordenadas-bacia-itajai.json` —
   medido aqui, mesma ordem de grandeza das nove ligações do Açu (0,9 a 5,9 m).
2. **O coletor.** `scripts/coleta_nivel_sc.py` **já lia** `DCSC-00019` como
   `brusque` para publicar a leitura ao vivo que o site mostra. A ligação existia
   em CÓDIGO e não estava no DADO.

Com o elo escrito, a cadeia fecha por desigualdade triangular: a 83900000 está a
51 m da DCSC-00019, que está a 3,5 m do nosso pino — logo **≤ ~55 m do pino**. É um
**limite, não um ponto**: a coordenada da 83900000 continua não transcrita, então a
trava de distância ao traçado não roda sobre ela. Está dito assim no
`codigo_ana_verificacao`, para ninguém ler o limite como medição.

### Três cidades ganharam `codigo_dcsc` no caminho

Vidal Ramos (DCSC-00024, 1,1 m), Botuverá (DCSC-00018, 1,5 m) e Guabiruba
(DCSC-00029, 2,0 m) estavam na mesma situação: pino em cima da estação, coletor já
usando o código, campo `null`. **O Mirim inteiro estava de fora do
`CODIGO_DCSC_ESPERADO`** do validador — a trava que existe justamente para o código
não sumir ou trocar em silêncio valia só para o Açu. Agora vale para as treze.

Novo teste: o pino de **toda** cidade com `codigo_dcsc` tem de cair a menos de 50 m
da estação. Passa nas treze.

---

## ⏳ As sete que faltam, e o que cada uma espera

`scripts/ana_inventario.py` busca exatamente isto. Rodar **de fora deste ambiente**:

```
python3 scripts/ana_inventario.py --json data/brutos/ana-inventario-2026-09-07.json
```

Ele imprime, para cada estação, o tipo, a coordenada, a distância até o pino da
cidade e a linha pronta para colar em `ESTACOES_ANA_CONHECIDAS`. **Não grava em
`estacoes.json`** — a decisão continua humana, como em `ana_hidroweb.py`.

| Estação | Destrava | O que falta |
|---|---|---|
| 83250000 ITUPORANGA | Ituporanga | a **coordenada** (tipo já se sabe: fluviométrica, 1.650 km², desde 1929) |
| 83145140 DCSC BARRAGEMSUL JUSANTE | Ituporanga | o **tipo** (coordenada já se sabe: 45 m da DCSC-00039) |
| 83520000 WARNOW | Indaial | a **coordenada** — é a sucessora da 83690000, morta em 12/2021 |
| 83870001 ILHOTA-JUSANTE | Ilhota | a **coordenada** — sucessora; a antecessora ficava a 1,2 km da DCSC-00030 |
| 83440000 IBIRAMA | Ibirama | a **coordenada**, e a escala encerrou em 12/2021 → precisa declarar sucessora |
| 83892998 BOTUVERA-MONTANTE | Botuverá | a **coordenada** — a 3,5 km da DCSC-00018, provável OUTRA estação |
| 83094000 RIO DO SUL (Oeste) | Rio do Sul | a **coordenada** — conflita com a 83300200 que já usamos; ver `codigo_ana_ressalva` |

**Ituporanga é a de melhor desfecho possível:** os dois candidatos são
complementares, cada um com a metade que falta ao outro. Uma execução resolve os
dois — e diz se são a mesma estação com dois cadastros ou duas de verdade.

**Botuverá provavelmente vai fechar como NÃO.** 3,5 km é a mesma ordem do Salseiro
(6,8 km), que já foi recusado para Vidal Ramos. Um "não" gravado vale tanto quanto
um "sim": impede que o próximo levantamento proponha o mesmo vínculo.

---

## ⚠️ O que este script NÃO resolve

- **A cota do zero da régua.** Não está no inventário público (a tabela
  `fichareferencianivel` do `.mdb` vem vazia). A `REGRA_REFERENCIA_BLUMENAU`
  continua bloqueada, e o caminho é a API autenticada ou a área restrita.
- **Os nomes dos campos do XML não foram conferidos** contra o serviço real,
  porque daqui não dá. O parser procura cada informação por uma lista de grafias
  possíveis e, quando não acha, **imprime os nomes que o XML trouxe** — o conserto
  vira uma linha em vez de uma caçada. Mesma disciplina de `ana_hidroweb.py`: não
  chutar nome de campo e fingir que deu certo.

## Por que isso vale a corrida

Cada estação fluviométrica confirmada traz **série de cota com hora**. Hoje a base
tem 149 picos e **nenhum com hora**, o que mantém `transito.json` como tabela de
projeto e deixa `scripts/calibrar_transito.py` sem o que calibrar. As sete acima
cobrem seis cidades, e duas delas — Ituporanga (1929) e Warnow (1927) — têm quase
cem anos de série. É o material de calibração mais longo da bacia.
