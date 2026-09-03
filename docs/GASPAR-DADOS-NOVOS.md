> ## ⚠️ CONFERIDO NA FONTE PRIMÁRIA — NÃO APLICAR A SEÇÃO 1 COMO CORREÇÃO
> **04/09/2026.** A seção 1 abaixo diz que "o projeto registrava 5/6/7 — errado" e propõe
> atenção 6,00 / emergência 7,00, sem faixa de alerta. **Isso foi conferido e recusado.**
>
> O `data/brutos/gaspar-plano-de-contingencia.pdf` — o Plano de Contingência da própria
> Defesa Civil de Gaspar, item 4.2.3, p. 25 — define **quatro** faixas:
> `0–5,00 normalidade · 5,00–6,00 atenção/alerta · 6,00–7,00 alerta/alarme · >7,00 resposta`.
> É exatamente o 5/6/7 que o projeto já tinha, e `scripts/conferir_gaspar_plano.py` refaz a
> conferência (as 26 vias do quadro do item 4.2.2 batem ao centavo, com duas diferenças de 2 cm).
> `scripts/teste_conferir_gaspar_plano.py` **trava** `{atencao: 5.0, alerta: 6.0, emergencia: 7.0}`.
>
> A legenda de `/estacao/ver/21` não contradiz o Plano: é a **vista operacional simplificada**,
> em três estados, do mesmo documento em quatro faixas. Duas apresentações, não duas verdades.
>
> **Por que isto importa e não é preciosismo:** aplicar a seção 1 moveria a atenção de 5,00 m
> para 6,00 m — o site passaria a avisar **um metro mais tarde**. Num sistema de aviso de cheia
> esse é o lado que machuca. A primeira rua de Gaspar alaga a 6,20 m; com atenção em 5,00 m
> sobra 1,20 m de margem, e há teste travando essa margem.
>
> **O que da seção 1 É aproveitável:** o **gatilho composto** (atenção dispara por nível **ou**
> chuva > 6 mm) é informação nova e só ACRESCENTA gatilho — nunca remove. Está registrado como
> pendência no README. O recorte de Blumenau deste site (6,00 / 8,00) segue como referência
> cruzada, não substitui o do AlertaBlu, que é a régua da própria cidade.
>
> As seções 2 a 4 (69 enchentes, abrigos com cota, contexto operacional) **não** foram
> contestadas — o que falta nelas é o arquivo: `gaspar-historico-enchentes.json` e
> `gaspar-abrigos.json` não vieram nos envios, então nada disso pôde ser importado.

# Gaspar — o que o site da Defesa Civil entregou (03/09/2026)

O site `defesacivil.gaspar.sc.gov.br` é o mais completo da bacia depois de Itajaí. Rotas úteis:
`/enchentes` · `/abrigos` · `/cotas` · `/barragens` · `/monitoramento` · `/estacao/ver/21` ·
`/mapas/-carta-enchente-municipio-de-gaspar` · `/mapas/cotas-de-enchente-0` ·
`/mapas/mapa-de-localizacao-dos-abrigos` · `/mapas/rota-de-fuga-para-os-abrigos` ·
`/mapas/mapeamento-de-areas-de-risco` · `/plano-de-contingencia` · `/alertas-regiao`

---

## 1. ✅ COTAS OFICIAIS — corrigem o dado do projeto
Fonte: `/estacao/ver/21` (estação Rio Itajaí Açu Gaspar), legenda oficial:
- **NORMALIDADE:** nível < 6,00 m
- **ATENÇÃO:** nível > 6,00 m **OU chuva atual > 6,00 mm**
- **EMERGÊNCIA:** nível > 7,00 m

**O projeto registrava "5/6/7" — errado.** Gaspar tem só DUAS cotas (6,00 e 7,00) e TRÊS estados;
**não existe faixa de "alerta" intermediária**.

**E a atenção é gatilho COMPOSTO:** dispara por nível OU por chuva. Gaspar pode estar em atenção com o rio
baixo, se estiver chovendo forte. Nenhuma outra cidade da bacia tem isso — a UI precisa suportar.

O mesmo site monitora Blumenau (`/estacao/ver/3`) com legenda simplificada: normalidade < 6,00 ·
atenção > 6,00 ou chuva > 30,00 mm · emergência > 8,00. **Diferente do que usamos para Blumenau**
(6,00 / 6,50 / 7,40 do AlertaBlu). Duas instituições, dois recortes — usar o do AlertaBlu para Blumenau
(é a régua da própria cidade) e este só como referência cruzada.

## 2. ⭐ HISTÓRICO DE ENCHENTES DE GASPAR — 69 eventos, 1852–2023
`/enchentes` traz a tabela completa. **O projeto não tinha NENHUM evento de Gaspar.**
Baixado: `gaspar-historico-enchentes.json`.

Maiores picos: **1880 = 12,56 m** · 1911 = 12,42 · 1852 = 12,00 · **1983 = 11,50** · **1984 = 11,40** ·
1891 = 10,25 · 1992 = 9,92 · 1868 = 9,90 · **2008 = 9,80** · 1980 = 9,70 · **2011 = 9,42**.

**A quebra de 1986 fica visível nos dados:** 55 eventos antes, 14 depois.
- Antes de 1986: picos de 9 a 12,5 m eram comuns (1880, 1911, 1852, 1983, 1984, 1891, 1980, 1975, 1973…)
- Depois de 1986: o maior é **2008 = 9,80 m**; os demais ficam entre 6,19 e 9,42 m
Isso é **consistente com a retificação e alargamento do canal na divisa Blumenau/Gaspar em 1986** (Santos
& Pinheiro, 2002): canal mais largo escoa o mesmo volume com menos altura. **Não é que as cheias
diminuíram — é que a régua passou a marcar menos para a mesma água.**
⚠️ Consequência direta: **nunca comparar pico pré-1986 com pós-1986 em Gaspar.** Marcar o divisor.

## 3. ⭐ ABRIGOS COM COTA — o dado que nenhuma outra cidade tem
`/abrigos` → 28 abrigos, **1.110 famílias** de capacidade. Baixado: `gaspar-abrigos.json`.
Campos: nome, responsável, **capacidade (em FAMÍLIAS)**, **cota do abrigo (m)**, endereço, situação.

**`cota_abrigo_m` é o nível do rio a partir do qual o abrigo é atingido.** 14 dos 28 têm o valor
preenchido: 6, 9, 10, 11, 12, 14 e 15 m. Os outros marcam 0,00 (não informado).

**Por que isto é único:** permite dizer *"com o rio em X metros, estes abrigos seguem acima da água"* —
Itajaí (45 abrigos) e Rio do Sul (23) não têm esse campo. É a informação que transforma uma lista de
endereços em algo utilizável durante a cheia.

⚠️ **Unidades incompatíveis entre cidades:** Gaspar conta **famílias**, Itajaí conta **vagas**, Rio do Sul
conta **pessoas**. NUNCA somar. E `capacidade` de Gaspar em famílias × ~3,5 pessoas não é conversão
oficial — não fazer.

**Regra de abertura, do próprio site:** *"os abrigos serão abertos conforme a análise do tamanho do evento
que recair sobre o município, sendo aberto primeiramente o abrigo de referência da cidade, atualmente a
Arena Multi-uso"*. Ou seja, **a abertura é decisão da Defesa Civil, evento a evento**. Todos estavam
FECHADO na coleta. O site pode mostrar a lista com a cota e a situação informada, **nunca** dizer ao
morador para ir a um abrigo.

## 4. Contexto operacional (dos boletins)
- As cotas de enchente de Gaspar foram desenvolvidas pelo **Prof. Ademar Cordeiro (FURB)**, que também faz
  os prognósticos citados nos boletins ("pode chegar a 7,4 m às 2h") — 4 a 8 h de antecedência.
- **Gaspar tem ribeirões que REPRESAM água.** A Defesa Civil orienta quem tem cota entre 6 e 7 m a
  *esperar* antes de mover móveis, por causa da água que desce do Alto Vale somada à chuva local. Efeito
  de remanso: o nível sobe por bloqueio de saída dos ribeirões, não só pela onda do rio principal.
  **A janela de chegada não captura isso.**
- A **Carta Enchente** é elaborada pelo **CEOPS** e publicada diariamente (ex.: nº 243/2026, 31/08 às 05:00,
  meteorologista Fernando). É documento diário — vale investigar se tem formato estável para coleta.

## Pendências neste site (não abertas ainda)
- `/cotas` — "Pesquise sua cota" por endereço. Se consumir um endpoint, é a busca de rua de Gaspar.
- `/barragens` — situação das barragens.
- `/mapas/-carta-enchente-municipio-de-gaspar` — a carta enchente em mapa.
- `/mapas/rota-de-fuga-para-os-abrigos` — rotas de fuga (nenhuma outra cidade tem).
- `/plano-de-contingencia` — pode ter as cotas por bairro e o gatilho de acionamento.
