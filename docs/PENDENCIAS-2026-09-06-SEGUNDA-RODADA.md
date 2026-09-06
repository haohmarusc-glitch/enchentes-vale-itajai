# Segunda rodada de investigação — o que confere, o que não

Recebido em 06/09/2026, sobre as três pendências abertas. **Nada importado.**
Duas das três recomendações não devem ser seguidas como estão, e o motivo de
cada uma está abaixo.

---

## 1. Gaspar — a suspeita CONFERE, e a correção proposta troca uma coisa por outra

**O que confere, e é importante:** a URL usada na extração
(`/mapas/cotas-de-enchente`) não é a do site atual (`/mapas/cotas-de-enchente-0`),
e a página atual é um **contêiner de iframe para um Google My Maps**. Se a
extração leu o HTML dessa página como se ele contivesse as cotas, os ~70
candidatos podem ter vindo de elementos que não são registro de cota.

**Isso é o segundo sinal independente do mesmo problema.** O primeiro veio do
teste 19 no navegador do Jefferson: `defesacivil.gaspar.sc.gov.br/enchentes`
devolveu conteúdo idêntico ao `/monitoramento/tabela`.

Dois sinais independentes apontando que a extração de Gaspar leu a página
errada. **A decisão de não importar os 70 estava certa** — e agora por um
segundo motivo, mais grave que o primeiro (a data ser de início de evento).

### Mas `/cotas/afetadas` NÃO substitui os 70

A recomendação é reconstruir o conjunto de Gaspar a partir da página de ruas
afetadas (`Rua | Bairro | Cota`). **São dois tipos de dado diferentes**, e
trocar um pelo outro colocaria dado de rua dentro do arquivo de picos:

| | os 70 candidatos | `/cotas/afetadas` |
|---|---|---|
| tem data? | **sim** — 54 anos distintos, de 1855 a 2023 | **não** |
| faixa dos valores | **6,19 a 12,56 m** | ~6,20 a 6,72 m |
| o que é | pico do rio num evento | altura em que a água chega na rua |
| arquivo do projeto | `enchentes.json` | `cotas-ruas.json` |

Dos 70, apenas **2** caem na faixa 6,20–6,80 m onde vivem as cotas de rua
citadas. Os outros 68 são de outra natureza — 12,56 m não é a altura de uma
rua, é um pico de cheia.

O projeto já tem guarda contra essa confusão (`valida_cota_de_rua_nao_e_lamina`),
e ela existe porque a confusão já aconteceu antes.

**O que fazer com cada um:**

- **`/cotas/afetadas` é um achado bom, e vai para `cotas-ruas.json`.** Gaspar
  hoje tem cotas de rua no projeto; uma fonte estruturada oficial com
  Rua/Bairro/Cota é exatamente o que falta em várias cidades. Entra com fonte
  e com a referência da régua a que essas cotas se referem — que **ainda
  precisa ser dita pela fonte**, porque cota de rua sem saber de qual régua é
  não serve para comparar com leitura ao vivo.
- **Os 70 continuam fora.** Reextrair da fonte certa (a tabela com datas, onde
  quer que ela esteja hoje) é outro trabalho, e continua valendo a ressalva
  original: a data publicada é de **início do evento**, não do pico, e o
  trânsito é medido de pico a pico.

---

## 2. Maré — seis horários de fonte secundária NÃO resolvem a lacuna

Foram encontrados 6 eventos de maré para **01/10/2026**. A própria investigação
classifica: *"fonte secundária / dado provisório"*, a confirmar contra a
DHN/Marinha.

**Não devem entrar.** Três razões, em ordem de peso:

1. **Resolvem um dia de um buraco que não tem fim à vista.** A tábua acaba em
   30/09/2026; importar 01/10 deixa 02/10 em diante igualmente vazio. A tábua
   anual do CHM — que o Jefferson já localizou, e que cobre **até 31/12/2026** —
   resolve 92 dias de uma vez.
2. **Misturam proveniência dentro da mesma série.** Todas as linhas de
   `mare-itajai.json` hoje vêm da previsão harmônica do Laboratório de
   Oceanografia Física da UNIVALI. Uma linha de origem diferente, com nível de
   redução não confirmado, no meio das outras, é o que o próprio arquivo manda
   evitar — e a tela cruza esses horários com a janela de chegada do pico.
3. **O uso é alerta de cheia.** "Provisório" é aceitável num gráfico; não é
   aceitável no número que diz se a maré vai travar a saída da água quando o
   pico chegar.

**O caminho é a tábua do CHM**, com `nivel_medio: 0.6` e Carta 1841 na
proveniência, importada de uma vez. O validador continua avisando enquanto isso
não acontecer, que é o comportamento certo.

---

## 3. Indaial — o avanço é real, mas são TRÊS réguas, não duas

A investigação identificou a estação **83690000** (Rio Itajaí-Açu, EPAGRI-SC /
ANA) e montou a conversão régua → altimetria a partir do RN 1402-X (61,49 m).
Ela mesma diz para **não aplicar** o deslocamento automaticamente. Certo.

**Duas coisas a acrescentar, e a segunda muda a pergunta.**

### O cadastro já sabia: a escala da 83690000 acabou em 12/2021

Está em `estacoes.json._meta.notas.quebra_de_12_2021`:

> QUATRO estações de referência da ANA encerraram a escala convencional no MESMO
> mês, 12/2021: 83800002 BLUMENAU, **83690000 INDAIAL**, 83840000 GASPAR e
> 83440000 IBIRAMA.

Ou seja, a 83690000 **não é a régua atual de Indaial** — é uma série histórica
que parou há quase cinco anos. Reconciliar o datum dela resolve o **histórico**,
não o aviso de hoje.

### São três identidades de régua, sem deslocamento provado entre nenhum par

| # | Régua | O que se sabe | O que falta |
|---|---|---|---|
| 1 | A da **COMPDEC** | escala 3 / 4 / 5,5 m; zero no RN 1402-X (61,49 m) — provado hoje pelo próprio PDF (5,5 m ≈ cota 67 m; 67 − 5,5 = 61,5) | qual ponto físico é |
| 2 | **DCSC-00006** (rede estadual) | é a leitura AO VIVO que a tela mostra (6,06 m em 06/09) | `datum: bruto_estadual`, `offset_datum: null` — deslocamento desconhecido |
| 3 | **ANA 83690000** | série histórica; escala convencional encerrada em 12/2021 | datum, e se é a mesma régua da COMPDEC |

A investigação assume que 1 e 3 são a mesma régua. **Nada estabelece isso.** E
mesmo que fossem, sobraria o par que importa para o alerta: **1 ↔ 2**, porque é
a 2 que publica número hoje.

### A pergunta, dita com precisão

Para o **aviso de hoje** funcionar em Indaial, falta uma coisa só: **o
deslocamento entre a régua da COMPDEC (zero no RN 1402-X) e a estação
DCSC-00006.** Nem a 83690000 nem a conversão para altimetria respondem isso.

Para o **histórico** (os 16 picos, e o pareamento montante↔jusante), aí sim vale
reconciliar a 83690000 — e a nota da quebra de 12/2021 já diz que essa
reconciliação atinge Blumenau, Gaspar e Ibirama junto, não só Indaial.

---

## Resumo

| Pendência | Situação real | Próximo passo |
|---|---|---|
| **Gaspar** | suspeita **confirmada** por dois sinais independentes; os 70 seguem fora | `/cotas/afetadas` → `cotas-ruas.json` (com a régua de referência dita pela fonte); reextrair os picos de onde a tabela com datas estiver |
| **Maré** | **não resolvida** — um dia de fonte secundária não fecha o buraco | importar a tábua anual do CHM (até 31/12/2026) |
| **Indaial** | avanço real no histórico; o **aviso de hoje continua parado** | deslocamento COMPDEC ↔ DCSC-00006 |
