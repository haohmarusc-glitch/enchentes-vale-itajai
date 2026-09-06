# Plano: manchas ligadas ao nível, e a tela por cidade — 05/09/2026

Responde ao pedido: *"tela de monitor só para cidade com ricos dados; no monitor principal a pessoa
clica na parte do rio e escolhe a cidade; as manchas aparecem quando os rios encherem; começar por
Itajaí; as outras cidades podem vir sem o dispositivo de manchas."*

**É possível seguir assim — e mais da metade já está pronta.** O que muda no plano é a ORDEM, porque a
parte das manchas tem um bloqueio que não é de código.

---

## O que já existe (medido, não suposto)

| Peça do pedido | Estado |
|---|---|
| Tela por cidade | ✅ **já feita** — `TelaCidade`, com nível ao vivo, cotas, mapa do rio, barragens, picos |
| Clicar e abrir a cidade | ✅ **já existe** — tocar no pino abre o painel com "Abrir {cidade} →" |
| Manchas de Itajaí | ✅ **10 eventos, 1983–2015** (`data/manchas/itajai/`), escolhidos por evento em `/itajai` |
| Clicar no **trecho do rio** (não no pino) | ❌ falta — hoje só o pino seleciona |
| Mancha que acende **com o nível** | ⛔ **bloqueada por dado** — ver abaixo |

## ⛔ O bloqueio, com número

As dez manchas de Itajaí têm **`pico_registrado: null`**. A causa está no cadastro de picos:

| Cidade | Registros em `enchentes.json` |
|---|---|
| Blumenau | 113 |
| Rio do Sul | 9 |
| Brusque | 9 |
| Taió · Timbó | 1 · 1 |
| **Itajaí** | **0** |

Sem o pico do evento não existe número para comparar com o nível de hoje. Dizer *"o rio está em 3,20 m,
então a área alagada é esta"* seria **inventar a correspondência** — e o erro cairia para o lado de fazer
alguém se sentir seguro fora da mancha. Não se faz.

**A segunda trava, que sobrevive à primeira:** Itajaí tem **onze réguas com zeros diferentes**. Um pico
medido na régua A não se compara com a leitura da régua B. Então não basta "o pico de 2011": é preciso
**o pico de 2011 naquela régua**.

## O que foi feito agora

`web/src/logica/manchasPorNivel.ts` — o mecanismo, **pronto e escuro**:

- separa as manchas em *"o rio já passou disto"* e *"ainda não"*, pelo nível de agora;
- **recusa** comparar pico e leitura de réguas diferentes, e recusa pico sem régua declarada;
- **recusa** tratar "sem leitura" como "abaixo de tudo";
- as frases falam no **passado**: *"Em 2011 o rio marcou 3,05 m nesta régua e a água cobriu esta área"* —
  nunca *"vai cobrir"*.

Oito testes, três sabotagens (régua não conferida, leitura ausente virando zero, frase no futuro), cada
uma reprova. **Um dos testes trava o próprio bloqueio**: ele afirma que hoje nenhuma mancha de Itajaí tem
pico. No dia em que os picos entrarem, esse teste cai — e cair é a notícia boa.

## A ordem daqui

1. ~~Levantar os picos de Itajaí~~ ⛔ **BUSCA FEITA EM 06/09/2026, RESULTADO NEGATIVO.** Tudo que
   circula com metro nas datas das dez manchas é **régua de Blumenau** — 15,34 (1983), 15,46 (1984),
   11,02 (2001), 11,52 (2008), 10,18 (2014), 10,03 (2015). A "Itajaipedia" copia a série de Blumenau; a
   estação ANA de Itajaí (**02648008**) é **pluviométrica**; e **não há código fluviométrico da barra**
   no cadastro. O JICA lista Itajaí em 1983 com 40 mil atingidos e **a célula de nível vazia**.
   **Isto não é "ainda não procuramos": é que o número pode não existir publicado.** Quem o tem, se
   alguém tem, é a **Defesa Civil de Itajaí**, que opera as onze réguas e publicou as manchas — é
   pergunta de **ofício**, não de busca. Ver `docs/ADENDO-2026-09-05-NOITE.md`.
   **A busca virou trava:** `valida_pico_copiado_de_outra_cidade` recusa um pico de Itajaí igual ao de
   outra cidade no mesmo evento, porque os números errados estão a um copiar-e-colar de distância.
2. **Acender o mecanismo** e mostrar a mancha do evento mais alto já alcançado, no mapa de Itajaí. Nesse
   ponto o pedido está cumprido para Itajaí, sem nenhuma linha de previsão.
3. **Clicar no trecho do rio** seleciona a cidade daquele trecho, no Monitor. Independente das manchas,
   vale para a bacia inteira, e é pequeno.
4. **Outras cidades, sem manchas** — como você propôs, e o inventário já diz quais dão:
   **Gaspar** está destravada (1.613 cotas de rua georreferenciadas e o par cota↔leitura provado) e
   **Brusque** está bloqueada (a régua da leitura ao vivo não é a das cotas). Ver
   `docs/VIABILIDADE-TELA-POR-CIDADE.md`.
5. **Manchas de outras cidades** só quando houver polígono publicado. Hoje **só Itajaí** tem.

## O que este plano não vai fazer

- **Interpolar entre eventos.** Duas manchas não fazem uma terceira: a cidade de 1983 não é a de 2015.
- **Preencher o vazio entre as ruas.** A ausência de cor diz corretamente "não sabemos".
- **Usar mancha como previsão.** Mancha é registro do que já aconteceu, na cidade que existia no ano.

---

## Onde os mapas das cidades pararam — 06/09/2026

### ✅ O enquadramento passou a caber as réguas da cidade

Medido contra o cadastro: as **onze réguas de Itajaí** se espalham por **20,8 x 17,6 km**, e a
**DC-10 (Bairro Limoeiro) fica a 24,2 km do pino**. O enquadramento por cidade era uma janela fixa de
24 km centrada no pino — ou seja, **abrir `/monitor/itajai` escondia uma das onze réguas da própria
cidade**, e nada na tela dizia que faltava uma. Quem mora no Limoeiro abria "Itajaí" e não achava o
número que existe.

`vistaQueCabeAsReguas` enquadra a caixa que contém o pino **e as réguas**, com 20% de folga, levando
em conta a **proporção da tela** (numa tela deitada, 16:9, a dispersão norte-sul some primeiro).
`KM_NA_TELA = 24` continua valendo — virou **piso**, não teto, pelo motivo original: caber os vizinhos
de montante e jusante. Para toda cidade que não seja Itajaí nada muda, porque só Itajaí publica a
coordenada das réguas.

Seis testes, com o cadastro real. Duas sabotagens: ignorar as réguas e ignorar a proporção da tela —
as duas reprovam.

### ✅ Blumenau parou de receber "aproxime o mapa" para não achar nada

O painel dizia a **toda** cidade sem ponto: *"Aproxime o mapa para ver as cotas de rua."* Blumenau tem
o **maior levantamento do projeto — 2.042 ruas — e nenhuma com coordenada**; Rio do Sul tem 555 na
mesma situação. A pessoa aproximava, não achava nada, e podia concluir que a rua dela não foi
levantada. **Foi** — está na tela da cidade, buscável por nome.

Agora essas duas cidades recebem a frase que diz o que é: *"tem N ruas levantadas, mas a fonte publica
rua e bairro sem a coordenada de cada ponto."* A decisão vive em `logica/cotasNoMapa.ts`
(`avisoDeRuas`), não no `.tsx`, e os dois números têm trava dos dois lados —
`valida_ruas_sem_coordenada` no Python e um teste no site — porque número copiado à mão envelhece
calado.

### ⛔ O que falta, e o que o desbloqueia

| Cidade | Cotas | Coordenada | Mapa da cidade |
|---|---|---|---|
| **Gaspar** | 1.619 | 1.613 | ✅ pontos **com estado** (par cota↔leitura provado) |
| **Brusque** | 377 | 348 | ✅ pontos **sem estado** (a régua da leitura não é a das cotas) |
| **Blumenau** | 2.023 | **0** | ❌ só por nome, na tela da cidade |
| **Rio do Sul** | 555 | **0** | ❌ idem |
| **Itajaí** | 0 | — | manchas por evento; nenhum pico para acendê-las |

**Gaspar e Brusque vieram georreferenciadas da fonte** (KML da Defesa Civil). Blumenau e Rio do Sul
vieram de tabela — rua, bairro e cota. Pôr essas duas no mapa exige **geocodificar**, e é aí que mora
o próximo perigo: uma cota é de um PONTO da rua ("final da rua", "esquina com X"), e uma rua de 2 km
tem cotas diferentes nas duas pontas. Colocar o ponto no meio da rua acerta o nome e erra o lugar —
e num mapa de enchente errar o lugar é dizer a alguém que a casa dele alaga num nível que não é o
dela.

Então **não é "rodar um geocodificador"**: é decidir o que se desenha quando só se sabe a rua, e não
o ponto. Enquanto isso não for resolvido, a lista por nome na tela da cidade é a forma honesta —
e é a que está no ar.

⚠️ Além disso, `overpass-api.de` e `nominatim.openstreetmap.org` estão **bloqueados pela política de
rede deste ambiente** (403 no CONNECT, conferido em 06/09/2026). Qualquer busca de traçado de rua sai
da VPS, como já saiu a do Itajaí do Sul.
