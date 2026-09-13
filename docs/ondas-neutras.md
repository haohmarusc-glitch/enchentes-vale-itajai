# Regra única para ondas — 12/09/2026

O motor tinha duas regras incompatíveis: a correnteza tracejada ignorava o
cinza, mas a crista continuava pulsando nele. Agora ambos os efeitos consultam
`podeAnimarTrecho`, que exige autorização `direcional` explícita na cena.
Ausência dessa autorização significa parado, mesmo em trecho colorido.

Cor e movimento são independentes:

- A cor continua sendo calculada pela leitura, idade e cotas da régua vinculada.
- Um trecho cinza autorizado mostra ondas discretas na mesma cor cinza. Não
  afirma nível atual, normalidade, segurança, velocidade ou chegada da cheia.
- A velocidade visual é constante e baseada no tempo; não depende de chuva,
  cota, maré ou frequência de quadros.
- Os dois efeitos respeitam a autorização. A crista não pulsa em afluentes sem
  direção definida nem nos trechos excluídos do monitor municipal.
- Pausa, movimento reduzido e aba oculta conservam o controle do loop existente.

## Como o trecho recebe autorização

Nesta versão, somente os traçados existentes do Açu e Mirim podem receber
autorização. A linha precisa ter pelo menos duas âncoras no eixo, avanço positivo
entre suas extremidades e progresso não decrescente ao longo dos pontos,
usando a orientação montante–jusante já empregada pelo motor.

Adotamos limites **conservadores de apresentação**, não limites oficiais do
estuário: Ilhota no Açu e Brusque no Mirim. Linhas que ultrapassam essas âncoras
ficam inteiramente paradas. Não inferimos o sentido da corrente real pela maré.
Se uma linha cruza o limite ou tem orientação ambígua na projeção, ela para;
isso pode deixar lacunas na animação mesmo onde há calha desenhada.

Esta verificação geométrica não é um modelo hidráulico. Sua finalidade é
evitar mostrar movimento direcional onde o desenho não sustenta a orientação.
Refinar a orientação em meandros e subdividir linhas junto aos limites são
melhorias futuras que exigem testes geográficos próprios.

## Limites que permanecem

Não foram adicionados traçados nem cotas nesta alteração. Hercílio, Benedito,
Rio dos Cedros e a cobertura até Ituporanga continuam como trabalho geográfico
separado. Não se desenha uma ligação inventada para preencher essas lacunas.
Réguas sem vínculo confirmado continuam sem classificação, mesmo quando uma
linha próxima tenha animação neutra. Nenhuma medição foi alterada.

Na conferência com os traçados locais, houve trechos neutros autorizados em
Lontras, Indaial, Gaspar, Botuverá e Vidal Ramos, entre outros. Essa constatação
é por trecho, não significa que toda a extensão territorial de cada cidade
tenha cobertura ou animação.

## Validação

- Testes chamam ambos os renderizadores com cinza, normal, alerta e várias
  réguas, autorizados, parados e sem autorização.
- Cena sintética testa trecho cinza orientado a montante, bloqueio a jusante
  e afluente sem âncoras.
- A fase visual permanece igual no mesmo instante, independentemente da faixa
  ou de chamadas anteriores.
- Auditoria de navegador confirma que pausar interrompe os desenhos no canvas
  e retomar os reativa; inclui as regressões de dados e camadas existentes.
- Build TypeScript/Vite e suíte de testes do site.

Não houve medição de FPS; não se promete 60 FPS em todos os aparelhos.
