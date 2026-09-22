# Chat local do histórico (sem IA, sem API) — especificação para implementação

Repositório: `haohmarusc-glitch/enchentes-vale-itajai`
Criado em: 22/09/2026
Estado: **motor pronto e testado (13 testes passando com os dados reais; tipos do componente conferidos com React 18)**. Falta encaixar no site.

Este documento é para ser entregue **inteiro** ao Claude Code. Leia tudo antes de mexer em qualquer arquivo.

---

## 0. O que é, e por que sem API

Uma caixa de perguntas nas páginas dos rios que responde **só com os JSONs de `data/`**. Roda inteira no navegador.

- **Sem backend e sem chave:** funciona no GitHub Pages como o resto do site.
- **Custo zero:** não há limite de uso para controlar.
- **Não inventa por construção:** o motor não gera texto livre. Ele escolhe uma intenção, busca o registro e preenche um modelo de frase. Todo número mostrado é um campo de um registro.
- **Contrapartida:** entende menos formas de perguntar que uma IA. Quando não entende, diz isso e mostra exemplos clicáveis. Nunca chuta.

O chat com IA (`CHAT-HISTORICO.md`, pacote `chat-historico-inicio.zip`) fica guardado como fase 2. Se um dia for publicado, este chat local continua sendo a opção sem backend.

---

## 1. Regras do produto (valem acima de qualquer outra instrução)

1. **Não é alerta.** Pergunta sobre agora, hoje, amanhã, previsão, "está subindo" ou "devo sair de casa" recebe o texto fixo `TEXTO_ALERTA`, que manda para o 199 / 193 e para as réguas ao vivo do site. Isso é checado antes de qualquer outra coisa.
2. **Todo número sai de um registro** e vem com a fonte. Quando existirem, vêm também a confiança, a nota, as divergências, a referência da régua e a cobertura da chuva.
3. **Ausência não é zero.** Estação sem dado aparece como "sem dado válido", nunca como 0 mm. Cidade sem registro recebe "o site não tem", e nunca um número de outra cidade.
4. **Não compara réguas diferentes em metros** e **não soma trechos de trânsito.** Se o trecho pedido não existe, o chat diz que não tem.
5. O chat só **lê** `data/`.

---

## 2. Arquivos (pacote `chat-local.zip`)

```
web/src/chat-local/
  motor.ts            funções puras: norm, extrair, responder (roteador) + 1 função por intenção
  carregar.ts         import dinâmico dos JSONs (cotas da ANA em segundo plano)
  ChatLocal.tsx       componente React: <ChatLocal rio="itajai-acu" | "itajai-mirim" />
  testes/
    carregar.ts       lê os JSONs do disco (Node) para os testes
    motor.test.ts     13 testes em node:test, com os dados reais
data/                 (arquivos NOVOS — os mesmos do pacote do chat com IA)
  atlas/eventos_itajai_acu.json, atlas/eventos_itajai_mirim.json
  chuva/chuva_eventos_atlas.json
  ana/cotas_itajai_mirim_diaria.json, ana/picos_itajai_mirim_1997_2021.json
docs/CHAT-LOCAL.md    este arquivo
```

Usa também, do repo: `data/enchentes.json`, `data/transito.json` e `data/estacoes.json`.

---

## 3. Como o motor entende a pergunta

1. **Normaliza** o texto: sem acento, minúsculo, sem pontuação.
2. **Barreira de "agora"** (expressões regulares). Se casar, devolve `TEXTO_ALERTA` e para.
3. **Extrai entidades:**
   - **Rio:** "itajaí-mirim", "mirim", "itajaí-açu" ou "açu". O nome do rio é retirado do texto antes de procurar cidade, para "Itajaí" do nome do rio não virar a cidade.
   - **Cidades:** de `estacoes.json` e dos municípios do Atlas, com o nome mais longo primeiro ("rio do sul" antes de "sul"). A primeira e a segunda que aparecerem ficam guardadas.
   - **Números:** ano (1800–2099; dois anos formam intervalo), mês por extenso, nível em metros ("10 m") e "N maiores".
4. **Escolhe a intenção** pela ordem abaixo. A primeira que casar vence.

| Ordem | Intenção | Gatilho | Lê | Exemplo |
|---|---|---|---|---|
| 1 | `transito` | "quanto tempo / demora / leva / chega" + 2 cidades | `transito.json` | Quanto tempo a cheia leva de Rio do Sul até Blumenau? |
| 2 | `chuva` | "chov" / "chuva" + ano | `atlas/*` + `chuva_eventos_atlas.json` | Quanto choveu antes da enchente de novembro de 2008? |
| 3 | `antecedencia_mirim` | "antecedência", ou Botuverá + Brusque + "pico" | `picos_itajai_mirim…` | Qual a antecedência do pico em Botuverá antes de Brusque? |
| 4 | `cota_ana` | "ana / cota / cm" + Salseiro / Botuverá / Brusque | `cotas_itajai_mirim_diaria.json` | Cota da ANA em Brusque em novembro de 2008 |
| 5 | `atlas` | desabrigados, desalojados, mortos, atingidos, desastre, cidades, municípios | `atlas/*` | Quais cidades tiveram desastre em setembro de 2011? |
| 6 | `contar_acima` | "quantas" + nível em m | `enchentes.json` | Quantas cheias passaram de 10 m em Rio do Sul? |
| 7 | `maiores_cheias` | maior, maiores, recorde, pior, máxima (sem ano) | `enchentes.json` | As 5 maiores cheias de Blumenau |
| 8 | `cheias_periodo` | cidade + ano | `enchentes.json` | Cheias de Gaspar em 2011 |
| 9 | `maiores_cheias` (5) | só a cidade | `enchentes.json` | brusque |
| 10 | `atlas` | só o ano | `atlas/*` | 2008 |
| — | `ajuda` / `nao_entendi` | "oi", "ajuda", ou nada casou | — | devolve 8 exemplos clicáveis |

Comportamentos que foram checados com os dados reais em 22/09/2026:

- **Chuva sem mês:** o motor usa o mês do ano com mais municípios no Atlas e lista os outros meses daquele ano.
- **Chuva em cidade sem estação do INMET** (ex.: Brusque): avisa que as estações servem só como referência regional.
- **Chuva antes de 2006:** diz que o site não tem dado de chuva.
- **Cota da ANA antes do fim do carregamento:** as cotas (~1,2 MB) chegam por último. Se a pergunta vier antes, a resposta é "carregando, tente em instantes".

---

## 4. Tarefas, em ordem

### L1 — Trazer o pacote e rodar os testes
- Descompactar na raiz do repo. Se os arquivos de `data/atlas`, `data/chuva` e `data/ana` já tiverem vindo do pacote do chat com IA, são os mesmos; manter um só.
- Os testes estão em `node:test`. Descobrir qual executor o `web/` usa (`npm test`; provavelmente Vitest) e **portar** `testes/motor.test.ts` para ele: trocar `node:test`/`assert` por `describe`/`it`/`expect`, mantendo as mesmas 13 verificações.
- **Pronto quando:** `cd web && npm test` roda os 13 testes novos, todos passam, e os testes que já existiam continuam passando.

### L2 — Carregar os dados do jeito que o site já carrega
- `carregar.ts` usa `import("../../../data/…json")`. Antes de manter isso, ver como o site hoje lê `enchentes.json` e `transito.json` (import direto, `fetch` de `public/`, módulo compartilhado) e **usar o mesmo mecanismo**, para não baixar o mesmo JSON duas vezes nem criar um segundo caminho de dados.
- Se o dev server do Vite reclamar de importar fora de `web/`, ajustar `server.fs.allow`, ou seguir o mecanismo que o site já usa.
- Manter as cotas da ANA carregando depois, em segundo plano.
- **Pronto quando:** `npm run build` não dá erro de tipo e, no build, os JSONs do chat só são baixados quando o componente aparece na tela (conferir na aba Rede do navegador).

### L3 — Pôr o chat nas páginas dos rios
- `<ChatLocal rio="itajai-acu" />` e `<ChatLocal rio="itajai-mirim" />`, abaixo da tabela de cheias.
- Estilo: as classes começam com `chat-` (`chat-historico`, `chat-aviso`, `chat-mensagens`, `chat-msg`, `chat-usuario`, `chat-assistente`, `chat-sugestoes`, `chat-entrada`, `chat-erro`). Usar as variáveis de cor e fonte do site. O texto usa `white-space: pre-line`, porque as respostas têm quebras de linha.
- Conferir no celular: as mensagens rolam dentro da caixa, a página não rola junto e os botões de sugestão quebram linha.
- **Pronto quando:** as duas páginas mostram o chat e as 3 sugestões iniciais respondem.

### L4 — Testes de navegador
Acrescentar ao `docs/testes-navegador.md`, com critério de passa/falha:
1. "Qual foi a maior cheia de Rio do Sul?" → mostra 13,58 m, julho de 1983 e a fonte.
2. "vai encher hoje?" → mostra o texto com 199 e nenhum número de nível.
3. "me conta uma piada" → "Não entendi" e os exemplos clicáveis; clicar num exemplo responde.
4. "Cota da ANA em Brusque em novembro de 2008", perguntada logo ao abrir a página → responde 507 cm, ou "carregando" e depois 507 cm ao perguntar de novo.
5. Com a rede do navegador bloqueando os JSONs → aparece "Não foi possível carregar os dados do chat" e a página continua funcionando.
- **Pronto quando:** os 5 passam no desktop e no celular.

### L5 — Aplicar a decisão de Rio do Sul, mai/2018
Decisão do Jefferson em 22/09/2026 (opção a): manter maio e baixar a confiança.
- Em `data/enchentes.json`, no registro `cidade: rio-do-sul`, `data: 2018-05`, trocar **só** `confianca` para `"baixa"` e **acrescentar** ao fim da `nota` (mantendo o texto atual):
  > MÊS DUVIDOSO (decisão do Jefferson em 22/09/2026: mantém maio, confiança baixa): em maio de 2018 as 4 estações automáticas do INMET (A817, A861, A863, A868) estavam completas e marcaram 29–69 mm no mês, nenhum dia acima de 28 mm — não sustentam os 114,6 mm em 4 dias desta linha. Candidato forte: set/2018 (31/08–03/09: 133 mm em Ituporanga, 81 mm em Indaial; Atlas registra inundação em Rio do Sul em 04/09/2018; a tabela municipal não tem linha de set/2018). Confirmar com a série da ANA em Rio do Sul ou com a Defesa Civil municipal.
- Não mexer em `data`, `pico_m`, `chuva_mm`, `dias_de_chuva` nem `fonte`. Não usar `divergencias`, que é para outro **valor** do mesmo pico.
- Acrescentar um teste: "cheias de Rio do Sul em 2018" → contém "7,55 m", "confiança BAIXA" e "MÊS DUVIDOSO". O motor já mostra a nota de todo registro com confiança baixa.
- **Pronto quando:** `python3 scripts/validar_dados.py` passa e o teste novo passa.

### L6 — Aprender com as perguntas reais (depois, só com aprovação do Jefferson)
- Hoje o chat não registra nada, porque não há backend. Se o Jefferson quiser saber o que as pessoas perguntam e o chat não entende, a opção mínima é contar só as intenções `nao_entendi` com um contador anônimo, **sem guardar o texto da pergunta**.
- Não implementar sem pedir: envolve decidir onde gravar e o que dizer na página sobre privacidade.

---

## 5. Como acrescentar uma pergunta nova

1. Escrever a função da intenção em `motor.ts`. Ela recebe `(e: Extraido, d: Dados)` e devolve `{ intencao, texto, sugestoes? }`.
2. O texto é montado **só** com campos do registro, e sempre termina com `Fonte: …`. Se o registro tiver confiança baixa, divergência ou cobertura menor que 1, a ressalva entra no texto.
3. Caso sem dado: dizer "o site não tem …". Nunca devolver 0 ou um valor vizinho.
4. Colocar o gatilho no roteador (`responder`) **na posição certa da ordem**. Gatilho amplo demais "rouba" pergunta de outra intenção; conferir que os 13 testes continuam passando.
5. Um teste com os dados reais para o caso com dado e outro para o caso sem dado.
6. Se a pergunta pedir um dado que não está em `data/`, a tarefa é **primeiro** trazer o dado para `data/`, com fonte e validação, e só depois ensinar o chat.

---

## 6. Limites conhecidos (não são defeito)

- **Frases de "agora" não previstas** passam pela barreira. Mesmo assim, o chat não tem nenhuma intenção que fale do presente: o pior caso é responder com histórico ou dizer "não entendi".
- **"Hoje" em pergunta histórica** ("o que aconteceu hoje há 10 anos?") é barrado. É de propósito: preferimos errar para o lado seguro.
- **Nome de cidade com erro de digitação** ("blumenal") não é reconhecido.
- **Perguntas compostas** ("maior cheia de Blumenau e de Gaspar") respondem só a primeira cidade.
- **Mês por número** ("11/2008") não é reconhecido; só o mês por extenso.
- **Período do Atlas:** 1991–2025.
- **Período das estações do INMET:** Indaial desde 2006, Ituporanga e Rio do Campo desde 2008, Itajaí desde 2010.
- **Cotas da ANA:** só nas estações do Itajaí-Mirim que vieram no pacote.

---

## 7. O que NÃO fazer

- Não trocar o motor por geração de texto livre, nem "completar" resposta com dado que não está em `data/`.
- Não mostrar 0 mm quando a estação não tem dado.
- Não comparar cotas de cidades ou réguas diferentes em metros.
- Não encadear trechos de trânsito.
- Não remover a barreira de "agora".
- Não mudar o mês do registro de Rio do Sul 2018 (ver L5).

---

## Implementação (22/09/2026) — o que foi feito, e onde saiu da especificação

Executado na mesma sessão em que o pacote chegou. Estado: **L1 a L5 feitos; L6 não** (exige
aprovação, ver abaixo). `cd web && npm test` roda **622** testes (607 + 15 do chat), `npm run build`
sem erro de tipo, `python3 scripts/validar_dados.py` 0 erros.

### L1 — pacote e testes
- Os testes do pacote já eram `node:test`, e o site **também** roda `node:test` (via `tsx`), não
  Vitest. Nada foi portado: `web/src/chat-local/motor.test.ts` (13 do pacote + 1 do "carregando"
  + 1 do L5) entrou no glob do `npm test`, que passou a incluir `src/chat-local/*.test.ts`.
- Os 13 casos e os números que eles afirmam (13,58 m em julho de 1983; 14 picos ≥ 10 m em Rio do
  Sul; 141,2 mm; 507 cm; 7 a 10 h) foram conferidos com os dados **atuais** do repositório, que
  ganharam cinco cheias de Brusque no mesmo dia (PR #406) — não mudou nenhum.
- `motor.ts` foi reescrito para o TypeScript **estrito** do site (`noUncheckedIndexedAccess`,
  `noUnusedLocals`): tipos explícitos em vez de `any`, guardas nos índices. Comportamento igual.

### L2 — dados, um arquivo só
- **Nenhum arquivo novo em `data/atlas`, `data/chuva` ou `data/ana`.** Três dos cinco JSONs do
  pacote já estavam em `data/brutos/`, **byte a byte** (sha256 conferido): os dois recortes do
  Atlas (`atlas-desastres-recorte-itajai-{acu,mirim}-2026-09-21.json`), a chuva por evento
  (`inmet-chuva-eventos-atlas-2026-09-22.json`) e os picos do Mirim
  (`hidroweb-mirim-2026-09-22/picos_itajai_mirim_1997_2021.json`). O chat lê **esses**.
- O quarto, `cotas_itajai_mirim_diaria.json` (1,2 MB), entrou em
  `data/brutos/hidroweb-mirim-2026-09-22/` ao lado dos zips de que deriva. Antes de aceitar,
  `scripts/hidroweb_csv.py` o reproduziu do bruto: **65 399 médias diárias iguais, 0 diferentes**
  (regra: nível 2 quando o dia tem consistido, senão nível 1); o único dia com média no bruto e
  ausente no arquivo é 25/03/2024, o erro de digitação de 167 165 cm — bem tirado.
- `enchentes.json`, `transito.json` e `estacoes.json` **não são baixados de novo**: o chat
  reaproveita `eventos`, `trechos` e `estacoes` de `web/src/dados/carregar.ts`, já validados e
  já no pacote principal. Só os quatro JSONs próprios vêm por `import()` dinâmico, pelo alias
  `@dados` que o site já usa; o Vite os separa em chunks próprios (66 KB, 19 KB, 141 KB, 7,5 KB e
  1,2 MB para as cotas, que chegam por último).
- **Só baixa quando aparece:** o componente é `lazy()` na `TelaRio`, e dentro dele um
  `IntersectionObserver` (margem de 600 px) dispara a carga quando a caixa se aproxima da tela.
  Quem abre `/acu` para ver o nível e não rola até o fim não baixa nada do chat.

### L3 — nas páginas dos rios
- `<ChatLocal rio=… />` no fim da coluna de dados de `/acu` e `/mirim`, depois do painel do
  cenário anterior (não há "tabela de cheias" na tela; o equivalente é o gráfico de picos e o
  cenário). Não entra em `/itajai` nem nas páginas de cidade.
- Estilo em **CSS Modules**, que é a convenção do site (CLAUDE.md), com os nomes da especificação
  (`chat-aviso`, `chat-mensagens`, `chat-msg`, `chat-usuario`, `chat-assistente`,
  `chat-sugestoes`, `chat-entrada`, `chat-erro`) e a classe `cartao` do site na seção. Mensagens
  rolam dentro da caixa (`max-height: 55vh`, `overscroll-behavior: contain`), botões de
  sugestão quebram linha, entrada com 16 px para o iOS não dar zoom.

### Desvio de texto, de propósito
- A resposta de `cota_ana` do pacote dizia "em Brusque, o zero dessa régua mudou ao longo das
  décadas". Isso **não foi provado**: `docs/HIDROWEB-MIRIM-2026-09-22.md` mostra a 83900000
  coincidindo com a régua municipal ao centímetro em 2019–2021 e **não se sabe desde quando**;
  as diferenças de 1984 e 2008 são leituras de 07h/17h que perderam a crista, não prova de
  zero diferente. O texto passou a dizer exatamente isso. O `_meta.aviso` do JSON de cotas, que
  traz a frase original, ficou como veio (é derivado do Jefferson, não é lido pelo chat).

### L4 — testes de navegador
Cinco testes novos em `docs/testes-navegador.md` (20 a 24), com critério de passa/falha.

### L5 — Rio do Sul, mai/2018
Aplicado como escrito: só `confianca` → `baixa` e a nota acrescida; `data`, `pico_m`,
`chuva_mm`, `dias_de_chuva` e `fonte` intactos. O teste de `teste_bot.py` que exigia
`confianca: media` nos 65 registros da tabela municipal passou a admitir **esta** exceção, com
a decisão citada. Teste do chat: "cheias de Rio do Sul em 2018" → 7,55 m, confiança BAIXA,
MÊS DUVIDOSO.

### L6 — não feito
Contar `nao_entendi` exige decidir onde gravar e o que dizer sobre privacidade. Fica como
pendência no README, para aprovação do Jefferson.
