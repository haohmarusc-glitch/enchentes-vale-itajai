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
