# Brusque: as cotas de rua do site são de 2023, e o município as revisou em 2024

Levantado em 06/09/2026, a partir de uma busca por "Defesa Civil de Brusque no
Instagram". **Nada foi alterado nos dados.** O que segue é o que está no
repositório, o que fontes secundárias relatam, e a pergunta que decide.

---

## O que está no repositório, medido

| | |
|---|---|
| cotas de rua de Brusque | **377** |
| data da fonte | **2023-10 (27) e 2023-11 (350)** — todas de 2023 |
| fontes | mapa "Cotas Enchente de Brusque" da Defesa Civil (Google My Maps), camada **"Cotas de cheia 2023"**; e lista oficial de out/2023 reproduzida por O Município em 17/11/2023 |
| aparecem para o morador? | **sim** — na busca "minha rua" (`CotasDeRua`, tela da cidade) e desenhadas no mapa do Monitor |

O próprio `cotas-ruas.json._meta` já avisava:

> "Cotas são aproximadas e envelhecem: obra de drenagem, aterro e enchente nova
> mudam os valores. **Brusque revisou as suas depois de novembro de 2023**"

O aviso estava lá. O que faltava era saber **o que** a revisão mudou.

---

## O que as fontes secundárias relatam

Notícias de julho/2024 (O Município, Portal da Cidade, Araguaia FM e outros)
dizem que a Defesa Civil de Brusque, com a Secretaria de Obras:

- concluiu a **primeira etapa** da atualização das cotas, com **357 pontos**
  levantados, cobrindo até **8,96 m**;
- publicou o estudo **no site da Defesa Civil** (`defesacivil.brusque.sc.gov.br`);
- previu a **segunda etapa para janeiro de 2025**, com os pontos não atingidos
  pela cheia de 17/11/2023.

E o motivo: os **canais extravasores da avenida Beira Rio** mudaram como o rio
alaga a cidade.

### O ponto que muda a prioridade

O relato é de que a alteração **não foi uniforme**:

> nos bairros a montante e a jusante da região central houve **DIMINUIÇÃO** das
> cotas; na região **central**, **aumento** significativo.

**Cota que diminui é a direção perigosa.** Se a cota de uma rua caiu, aquela rua
alaga com o rio **mais baixo** do que os nossos números de 2023 dizem — e a
tela informaria que ainda dá tempo quando já não dá.

Onde a cota subiu (centro), o erro é para o lado seguro: avisa antes.

---

## O que NÃO está estabelecido

Isto veio de **resumos de busca de notícias**, não da fonte. Deste ambiente o
proxy bloqueia `defesacivil.brusque.sc.gov.br`, os portais de notícia,
`files.abrhidro.org.br` e o `instagram.com`. **Nenhum número foi conferido na
origem**, e por isso nenhuma cota foi tocada.

Não se sabe, e é o que decide:

1. **Quais ruas diminuíram, e quanto.** Sem isso não dá para saber se alguma das
   377 do site está avisando tarde.
2. **Se as 377 de 2023 e as 357 de 2024 são o mesmo levantamento revisto** ou
   conjuntos diferentes (os números não batem).
3. **Se a segunda etapa (jan/2025) saiu**, e se há uma terceira depois de
   cheias posteriores — a própria Defesa Civil diz que "cada evento é único" e
   que as cotas precisam ser atualizadas após cada ocorrência significativa.
4. **A referência vertical** do levantamento novo, e se é a mesma régua da ponte
   estaiada Irineu Bornhausen que as leituras ao vivo usam.

---

## O que fazer

**Abrir `defesacivil.brusque.sc.gov.br` e baixar o estudo atualizado.** É um
endereço oficial e o próprio município diz que o publicou ali. Isso responde as
quatro perguntas de uma vez.

Há também um trabalho acadêmico — *"Cotas-Enchente do Município de Brusque/SC"*,
publicado pela ABRHidro (`files.abrhidro.org.br/Eventos/Trabalhos/4/PAP020944.pdf`,
também no ResearchGate) — que provavelmente traz a régua de referência e o
datum, que é o que falta para casar cota de rua com leitura ao vivo.

**Isto substitui o ofício à COMPDEC de Brusque** que estava na fila: o que o
ofício ia pedir — a lista oficial com o ponto de cada cota — aparentemente já
está publicado.

## Sobre o Instagram

A conta existe e é oficial: **@defesacivilbrusque**, ~22 mil seguidores. Não é
fonte para cota — é canal de aviso durante a cheia. Para o projeto ela serve
como **fonte de evento** (quando a Defesa Civil declara atenção/alerta), não
como fonte de número. Rede social não entra em `cotas-ruas.json` nem em
`enchentes.json`: não tem endereço estável, não tem datum e não se cita.
