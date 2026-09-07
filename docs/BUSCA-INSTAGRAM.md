# Busca no Instagram — roteiro de campo

Data: 07/09/2026. Para uso no celular, fora deste repositório.

## Antes de tudo: a regra

**Rede social é fonte de evento, não fonte de número.**

Nenhum post do Instagram entra em `enchentes.json`, `cotas-ruas.json` ou
`estacoes.json`. Post não tem endereço estável, não declara datum e não se cita
numa nota de fonte. O que ele faz é dizer *"existe um pico às 14h do dia
20/11/2023 em Ibirama"* — e aí vamos atrás do boletim, do ofício ou do HidroWeb
que sustente aquilo. O post é a **pista**; a fonte oficial é a **prova**.

**Descartar sempre:** nível sem régua identificada. "O rio está em 8 m" sem
dizer *qual* medidor não serve. As réguas não conversam entre si — em Indaial há
três identidades de régua não vinculadas, em Itajaí há onze. Um número sem régua
vira erro de 20 cm ou de 2 m, dependendo do dia.

## O que está faltando na base (medido em 07/09/2026)

- `data/enchentes.json`: **149 eventos, nenhum com hora.** Todo campo `data` é só
  o dia. Sem hora de pico, `transito.json` continua sendo faixa de tabela, não
  medida.
- **13 das 19 cidades não têm pico nenhum** (Itajaí conta nos dois rios).
- A base inteira se apoia em seis cidades: Blumenau 113, Indaial 16, Rio do Sul
  9, Brusque 9, Taió 1, Timbó 1.

| Cidade | Rio | Picos na base |
|---|---|---|
| Ituporanga | Açu | 0 |
| Ibirama | Açu | 0 |
| Lontras | Açu | 0 |
| Ascurra | Açu | 0 |
| Gaspar | Açu | 0 |
| Ilhota | Açu | 0 |
| Itajaí | Açu e Mirim | 0 |
| Rio dos Cedros | Açu | 0 |
| Trombudo Central | Açu | 0 |
| Vidal Ramos | Mirim | 0 |
| Botuverá | Mirim | 0 |
| Guabiruba | Mirim | 0 |
| Taió | Açu | 1 |
| Timbó | Açu | 1 |

## Contas confirmadas

| Perfil | Cidade | Observação |
|---|---|---|
| `@defesacivilbrusque` | Brusque | ~22 mil seguidores |
| `@defesacivil_itajai` | Itajaí | ~26 mil |
| `@defesacivilbnu` | Blumenau | ~32 mil |
| `@defesacivilriodosul` | Rio do Sul | ~22 mil |
| `@defesacivilsc` | Estado | cita municípios sem perfil próprio — o mais útil para as cidades zeradas |

Não foram encontradas contas oficiais de Gaspar, Ituporanga nem Ibirama.

## Prioridade 1 — o link da bio de Brusque

- [ ] Abrir `@defesacivilbrusque` → tocar no link da bio → chegar em
      `defesacivil.brusque.sc.gov.br` → procurar o **estudo de cotas atualizado**.

É o item de maior valor da lista inteira, e não é um post: é o PDF. As 377 cotas
de rua de Brusque que o site mostra hoje são todas de 2023, e o município as
revisou depois — ver `docs/BRUSQUE-COTAS-DESATUALIZADAS.md`. A revisão **baixou**
cotas a montante e a jusante, que é a direção perigosa: rua marcada como mais
segura do que é.

## Prioridade 2 — horário de pico

O horário só existe no tempo real, e o tempo real de ontem só sobreviveu em
post. É o que destrava a calibração de `transito.json`.

Procurar frase com hora explícita: *"o rio atingiu 9,20 m às 14h"*, *"nível às
06h: 7,84 m"*, *"pico registrado às 03h40"*.

Ir ao feed **por data**, nas janelas abaixo. Marcar o que achar.

| Janela | Perfis a varrer | Achou hora? |
|---|---|---|
| 11/2008 | bnu, riodosul, sc (retrospectivas) | [ ] |
| 09/2011 | bnu, riodosul, brusque, sc | [ ] |
| 10/2011 | bnu, sc | [ ] |
| 09/2013 | bnu, sc | [ ] |
| 06/2014 | bnu, riodosul, sc | [ ] |
| 10/2015 | bnu, riodosul, sc | [ ] |
| 06/2017 | bnu, riodosul, sc | [ ] |
| 12/2020 | brusque, sc | [ ] |
| 05/2022 | bnu, sc | [ ] |
| 06/2022 | brusque, sc | [ ] |
| 10/2023 | bnu, riodosul, brusque, itajai, sc | [ ] |
| 11/2023 | bnu, riodosul, brusque, itajai, sc | [ ] |
| 05/2024 | bnu, itajai, sc | [ ] |
| 10/2024 | brusque, itajai, sc | [ ] |

Contas de Defesa Civil postam pouco antes de ~2015; de 2015 em diante o feed
fica denso. As janelas de 2008 e 2011 valem pelas publicações de aniversário
("há 15 anos"), que às vezes reproduzem o boletim da época com hora.

## Prioridade 3 — as cidades zeradas

Nas mesmas janelas, qualquer post que dê nível de uma destas cidades vale mais
que o centésimo décimo quarto registro de Blumenau. `@defesacivilsc` é o caminho
principal, porque nomeia municípios que não têm perfil.

- [ ] Gaspar
- [ ] Ilhota
- [ ] Ascurra
- [ ] Ituporanga
- [ ] Ibirama
- [ ] Lontras
- [ ] Rio dos Cedros
- [ ] Trombudo Central
- [ ] Itajaí (Açu e Mirim)
- [ ] Vidal Ramos
- [ ] Botuverá
- [ ] Guabiruba
- [ ] Taió (só 1 registro)
- [ ] Timbó (só 1 registro)

## Prioridade 4 — cotas de rua novas

Só se sobrar tempo. Post de Brusque ou de Itajaí anunciando revisão de cotas,
com link para o documento.

- [ ] Brusque — revisão de cotas
- [ ] Itajaí — revisão de cotas

## O que anotar em cada achado

Copiar os quatro campos, sem resumir:

1. **Permalink** do post (`instagram.com/p/…`).
2. **Data do post.**
3. **Frase exata, entre aspas** — não parafrasear. A diferença entre "atingiu" e
   "está em" muda se aquilo é pico ou leitura pontual.
4. **Qual régua ou estação é citada nominalmente.** Se nenhuma for citada,
   registrar "régua não identificada" — e o dado fica só como pista de que
   existe um boletim para procurar.

## Depois

Nada disso vira linha em JSON direto. O caminho é: pista no Instagram →
localizar o boletim/ofício/HidroWeb correspondente → aí sim registro com `fonte`
e `confianca`. Enquanto a prova não aparecer, o achado fica neste documento.
