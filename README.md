# Enchentes do Vale do Itajaí

Site com dados históricos de enchentes nos rios **Itajaí-Açu** e **Itajaí-Mirim** (SC): nível do rio em cada cidade, previsão empírica para a cidade a jusante e tempo estimado de chegada da cheia. Itajaí, na foz, recebe os dois rios e a influência da maré.

**No ar:** https://haohmarusc-glitch.github.io/enchentes-vale-itajai

> Este projeto **não substitui** o AlertaBlu, a Defesa Civil de SC nem as Defesas Civis municipais. Em emergência, ligue 199.

## Estrutura

```
data/
  estacoes.json   cidades, códigos ANA, cotas de referência, ordem no rio
  enchentes.json  picos históricos por rio/cidade/data, com fonte e confiança
  transito.json   tempo que a cheia leva para descer entre cidades
  mare-itajai.json tábua de maré do porto de Itajaí (preamares e baixa-mares)
  tempo-real/      série coletada dos níveis (fora do git; só ultimo.json entra)
scripts/
  validar_dados.py     portão de qualidade dos JSONs (roda no CI)
  publicar_tempo_real.sh publica a última leitura no branch `tempo-real`
  auditar.py           audita a coleta e compara a defasagem observada com a publicada
  coleta_mares.py      baixa a tábua de maré da Defesa Civil de Itajaí
  coleta_niveis.py     coleta contínua dos níveis, acumulando a série de uma cheia
  coleta_itajai.py     leitura avulsa dos níveis (mostra e sai)
  extrair_picos.py     acha os picos na série e PROPÕE registros para enchentes.json
  ana_hidroweb.py      coleta de séries da ANA (aguarda credenciais)
  calibrar_transito.py mede o tempo real de descida a partir dos horários de pico
web/                   site em React + Vite + TypeScript
```

Os JSONs de `data/` são a **fonte de verdade**. O site lê deles; os scripts escrevem neles.

## Rodar

```bash
cd web
npm install
npm run dev      # desenvolvimento
npm test         # testes da lógica de previsão e de trânsito
npm run build    # build estático em web/dist (zero erro de tipo)
```

```bash
cd scripts
python3 -m pip install -r requirements.txt
python3 validar_dados.py            # sempre antes de commitar mudança em data/
python3 teste_coleta_mares.py       # testes do analisador da tábua de maré
python3 coleta_mares.py --verificar # mostra a tábua lida do endpoint, sem gravar
python3 coleta_mares.py             # grava data/mare-itajai.json
python3 coleta_niveis.py            # coleta e acumula a série dos níveis
python3 extrair_picos.py            # propõe registros de pico a partir da série
python3 calibrar_transito.py        # relata o que dá para calibrar
python3 auditar.py                  # audita os últimos 15 dias de coleta
```

### Auditar

`auditar.py` responde três perguntas sobre a série já coletada:

1. **A coleta está viva?** Estação que parou de publicar, buraco na série, sensor travado
   repetindo o mesmo valor. Descobrir na cheia que uma régua está muda há três dias é tarde.
2. **As leituras são plausíveis?** Valor fora de faixa, salto impossível.
3. **A defasagem observada bate com a publicada?** Por correlação cruzada entre as duas pontas
   de cada trecho de `transito.json`.

Sobre a terceira, o limite que não dá para contornar: **onda de cheia viaja mais rápido que
água baixa**. Uma defasagem medida em período seco não confirma nem refuta a faixa da JICA,
que vale para cheia — serve para pegar erro grosseiro (trecho invertido, cidade trocada, faixa
fora de ordem de grandeza). O relatório repete isso, para ninguém ler o resultado como
validação do que não foi validado.

Ele sai com código 1 quando há problema de **coleta**, que é operacional e precisa acordar
alguém. Defasagem fora da faixa em água baixa é observação, não erro, e não derruba o código
de saída. No cron, uma vez por dia já basta.

### Registrar uma cheia nova

O que falta em quase todo registro de `enchentes.json` é o **horário do pico** — e é
ele que troca o hidrograma de projeto da JICA por medição de cheia real. O caminho:

1. `coleta_niveis.py` no cron (`*/15 * * * *`) acumula uma linha por medição em
   `data/tempo-real/AAAA-MM.ndjson`. Deduplica pelo carimbo da fonte, então rodar
   com mais frequência não infla o arquivo: a página atualiza a cada 15–30 min.
   São ~110 bytes por leitura, algo como 40 MB por ano; `--compactar` reduz os meses
   fechados a cerca de um décimo. Esses arquivos ficam **fora do git**.
2. Passada a cheia, `extrair_picos.py` lê a série **régua por régua** — nunca juntando
   estações da mesma cidade, que têm zeros diferentes — separa os episódios acima da cota
   de atenção e imprime os registros propostos, com data e hora.
   Ele **não grava**: confira cada pico contra o boletim da Defesa Civil antes.
3. Conferido, `extrair_picos.py --escrever` inclui os registros, e
   `calibrar_transito.py` passa a ter material para medir os tempos de descida.

Isso só rende a partir da **próxima** cheia: a página publica o nível de agora, não
o histórico. Para as antigas, o caminho continua sendo os boletins da Defesa Civil e
o acervo do CEOPS.

Para manter a maré em dia, `coleta_mares.py` deve rodar de tempos em tempos (cron numa
máquina qualquer) e o `data/mare-itajai.json` resultante ser commitado. Enquanto o arquivo
estiver vazio, a tela da foz pede a tábua a quem estiver usando — ela não estima horário
de preamar.

O site é estático e usa `HashRouter`, então funciona em GitHub Pages ou Vercel sem reescrita de
rotas no servidor. `.github/workflows/pages.yml` publica a cada push no `main` — e **valida os
JSONs antes de construir**: se os dados não passarem, nada vai ao ar e o site no ar continua o de
antes. As publicações de tempo real vão para o branch `tempo-real` e não disparam build; a página
busca aquele branch em tempo de execução.

## Telas

1. **`/acu` — Itajaí-Açu** — Taió/Rio do Sul → Ibirama → Indaial → Blumenau → Gaspar → Ilhota → Itajaí
2. **`/mirim` — Itajaí-Mirim** — Vidal Ramos → Botuverá → Brusque → Itajaí
3. **`/itajai` — Itajaí (foz)** — chegada dos dois picos + maré
4. **`/`** — escolha do rio e aviso legal

## O que os dados sustentam — e o que não sustentam

**Tempo de chegada: sim.** O estudo JICA (Preparatory Survey, 2011) dá o eixo do Itajaí-Açu
inteiro: Rio do Sul → Blumenau em 7 a 10 h, Blumenau → Itajaí em 14 a 17 h, e a tabela do
hidrograma de projeto fecha os trechos intermediários (Blumenau → Gaspar 2 h, Gaspar →
Ilhota 5 h, Ilhota → Itajaí 10 h). O pico na foz cai no dia seguinte ao pico em Rio do Sul.

**Altura a jusante: não.** Com 5 eventos pareados entre Rio do Sul e Blumenau, a correlação
dá r² = 0,21 — e o site se recusa a exibir número. Não é falta de dado, é a bacia: em agosto
de 1984, 12,80 m em Rio do Sul viraram 15,46 m em Blumenau; em novembro de 2023, 13,04 m
viraram 9,14 m. O que decide o nível lá embaixo é onde a chuva caiu, não o nível lá em cima.
A tela mostra a nuvem de pontos para que isso fique visível, em vez de pedir fé no r².

**Fontes de tempo real: pelo endpoint, não pelo HTML.** A tábua de maré vem de
`ajax/mares.php`, o mesmo JSON que o gráfico do site consome — `tidelevel` em centímetros
na série observada, `level` em metros na astronômica (a chave `astronimical_tides` tem o
erro de digitação na própria API). Os níveis dos rios vêm do HTML da página de níveis, cuja
estrutura está documentada em `coleta_itajai.py` e coberta por testes com o markup real.

**Nível ao vivo: com a idade sempre à vista.** O site busca a última leitura em tempo de
execução (não no build, que teria a idade do último deploy). A idade aparece junto do número;
passando de 3 h a tela diz, em letras, que aquilo não serve como nível atual. O cálculo de
chegada a jusante só roda com leitura de até 45 minutos — com dado velho os horários sairiam
já vencidos, com cara de previsão. E é sempre condicional: **se** o pico for agora, porque o
tempo de descida é medido de pico a pico e o rio pode subir por mais horas.

Cidade com mais de uma régua não mostra nível ao vivo. Itajaí tem cinco só no Mirim, com
zeros diferentes — escolher uma e chamar de "o nível de Itajaí" seria comparar réguas.

**Maré em Itajaí: qualitativa, nunca em metros.** A preamar não soma centímetros — ela trava
o escoamento. O site cruza a janela de chegada com as preamares da tábua oficial e diz se a
cheia chega na maré alta, e se é período de sizígia (calculado da fase da lua, que é exata).
Não converte isso em altura: não há nada nos dados do projeto que calibre esse número.

## Como o site trata dado incerto

O projeto pode custar vidas se errar, então a regra é preferir dizer "não sei":

- **Sem 5 eventos pareados, não há previsão.** A tela mostra "dados insuficientes" e diz quantos faltam.
- **Leituras da mesma cidade a até 7 dias uma da outra são a mesma cheia**, e o pico do evento é a maior delas. Sem isso, 8 e 9 de setembro de 2011 em Blumenau contariam como dois eventos. Quando um registro de mês inteiro casa com duas cheias distintas, o par é descartado em vez de o código escolher uma.
- **Valores divergentes ficam guardados, não apagados.** Setembro de 2011 em Blumenau tem três leituras publicadas — 12,60 m (imprensa), 12,80 m (série municipal) e 13,00 m (CEOPS, Ponte Adolfo Konder). O arquivo adota uma e mostra as outras em `divergencias`, com a fonte de cada uma.
- **Previsão não vira histórico.** A cota de 9,10 m divulgada para Brusque em 17/11/2023 era previsão de pico; o registro guarda a medição (8,96 m) e a previsão como divergência.
- **Correlação fraca (r² < 0,50) também não vira número.** Nem relação decrescente, que indicaria erro de pareamento ou de régua.
- **A estimativa é sempre uma faixa** (intervalo de previsão de 95%), nunca um valor único. Se o nível informado estiver fora do que já se observou, a tela avisa que está extrapolando.
- **Tempo de trânsito é sempre faixa** ("14–17 h"). Quando a fonte traz um valor único, a tela diz "por volta de" e explica que é aproximação grosseira.
- **Cada cidade tem sua própria régua.** O aviso está em todas as telas, e o gráfico nunca põe duas cidades no mesmo eixo.
- **Todo número mostra a fonte e o grau de confiança**; registro sem fonte é descartado na leitura.
- **Registros duplicados para o mesmo evento são descartados** no pareamento, em vez de o código escolher um.

Essas regras estão em `web/src/logica/previsao.ts` e cobertas por testes em `web/src/logica/*.test.ts`.

## Fontes

- ANA / HidroWeb (séries históricas): https://www.snirh.gov.br/hidroweb
- Defesa Civil SC (tempo real): https://monitoramento.defesacivil.sc.gov.br/
- AlertaBlu (Blumenau): https://alertablu.blumenau.sc.gov.br/
- Defesa Civil de Itajaí: https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios
- CEOPS/FURB (acervo histórico): http://ceops.furb.br/

## Avisos (Telegram)

O site é *pull*: só serve para quem o abre. Ninguém abre uma página às três da
manhã, que é quando várias das cheias do Vale atingiram o pico. Estes dois
scripts vão atrás da pessoa.

```bash
cp .env.example .env          # preencher TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID
python3 scripts/notificador.py --teste
python3 scripts/alerta_cotas.py --seco    # mostra o que enviaria, sem enviar
python3 scripts/saude_coleta.py           # sai 0 se a coleta está viva, 1 se não
```

No cron, logo depois da coleta:

```cron
*/15 * * * * cd /root/enchentes-vale-itajai && python3 scripts/coleta_niveis.py && python3 scripts/alerta_cotas.py
17 * * * *   cd /root/enchentes-vale-itajai && python3 scripts/saude_coleta.py --avisar
```

### As regras de aviso, e por que não são as de um bot comum

**Não há horário de silêncio.** Um bot de notificação normal cala de madrugada.
Aqui isso mataria gente: 2008 e 2011 subiram de noite, e o aviso da madrugada é
o único que dá tempo de sair de casa. Quem quiser silêncio configura no próprio
Telegram — não no código de todo mundo.

**O intervalo entre avisos não é cronômetro.** Repetir "está em alerta" a cada
45 min vira ruído, e ruído faz a pessoa desligar o bot justamente antes da noite
em que ele importaria. Então: mudança de faixa avisa sempre; a mesma faixa só
repete depois de 3 h **e** se o rio tiver subido 30 cm desde o último aviso; a
descida e a volta ao normal avisam uma vez.

**Cada régua tem sua cota.** O limiar vem da própria estação. A cota da cidade
só vale onde a cidade tem uma régua só — em Itajaí são onze, com zeros
diferentes. Sem cota por régua, o script **não avisa** aquela estação e diz por
quê. Alarme com cota errada é pior que alarme nenhum: ensina a ignorar o
próximo.

**O aviso não calcula chegada a jusante.** O encadeamento de tempo de descida
vive em TypeScript (`web/src/logica/transito.ts`), e reescrevê-lo em Python
criaria duas contas de vida diferentes que podem divergir em silêncio. A
mensagem manda o link do site, onde a conta é uma só.

### O vigia da coleta

A coleta também se confere sozinha: se uma estação veio na rodada anterior e não
veio agora, `coleta_niveis.py` nomeia as que sumiram no `stderr` e grava a lista
em `estacoes_ausentes` no `ultimo.json`. O aviso **não** muda o código de saída,
de propósito — o cron encadeia `coleta_niveis.py && publicar_tempo_real.sh`, e
sair com erro faria o site congelar no dado anterior em vez de receber as
leituras que chegaram. Isso importa porque o vigia roda de hora em hora enquanto
a coleta roda a cada quinze minutos: sem esta conferência, três de cada quatro
coletas nunca seriam olhadas.

`saude_coleta.py` responde a duas perguntas, e a segunda é a traiçoeira:

1. **a coleta rodou?** (`coletado_em`) — cron morto, disco cheio, pacote quebrado;
2. **a fonte publicou?** (`medido_em` mais recente) — o cron correndo
   perfeitamente a cada 15 min sobre uma página que parou de atualizar há seis
   horas. O arquivo fica novo; o dado, velho.

Falha avisa na hora e não repete antes de 6 h. A recuperação avisa sem esperar.

## Chuva acumulada

Ao lado do nível, cada cidade mostra quanto choveu, do pluviômetro da própria
cidade. Coletado por `scripts/coleta_chuva.py` da segunda página da mesma
fonte (`/monitoramento/chuvas`) e publicado junto do nível em `ultimo.json`.

**As janelas são as da fonte: 10 min, 1 h, 12 h, 24 h e 48 h.** Ela não publica
6 h, e aqui não se estima — numa cheia a chuva não cai constante, e dividir o
acumulado de 12 h suporia justamente o contrário. A metade final de um período
de 12 h pode conter toda a chuva.

**É pluviômetro, não radar.** Radar mede refletividade e estima intensidade
sobre uma área; não vira milímetro acumulado confiável num ponto. Um número de
radar ao lado do nome da cidade teria cara de medição sem ser uma.

**Milímetro se compara entre cidades; metro de régua não.** Por isso a chuva de
uma cidade com vários pluviômetros é agregada e o nível não: cinco aparelhos em
Itajaí medem a mesma grandeza. Mostra-se o **maior**, não a média — o que enche
o rio é a chuva onde ela caiu, e a média entre um ponto encharcado e um seco
inventa um meio-termo que não aconteceu em lugar nenhum. Quando os pontos
discordam, a faixa inteira aparece: em 30/08/2026, Itajaí marcava
`14,0–39,6 mm em 24 h` entre seis pluviômetros.

**Trava de coerência.** As janelas são encaixadas, então o acumulado tem de ser
não-decrescente. A fonte publica série que viola isso: a estação Guarani, em
Brusque, registrava 0,20 mm nos últimos 10 minutos e 0,00 mm em 1 h, 12 h, 24 h
e 48 h no mesmo instante. Zero ali quase certamente é "sem dado", e mostrá-lo ao
lado de uma vizinha com 39 mm mandaria a pessoa para o lado errado. A leitura vai
marcada e a tela diz **"dado inconsistente na fonte"** em vez de um número.

### A coleta insiste quando vale a pena

Toda coleta passa por `comum.baixar()`. Antes cada script fazia `requests.get`
seco: um soluço de rede num servidor municipal — que é o que estas fontes são —
derrubava a coleta inteira e, no cron encadeado com `&&`, derrubava junto a
publicação. Quinze minutos sem número novo no site por causa de um TCP reset.

A ideia veio do Fila-Disney, e o motivo dele vale ainda mais aqui: *um ciclo
perdido é histórico perdido para sempre*. Numa cheia o ciclo perdido pode ser
justamente o do pico — o dado que depois faltaria para calibrar o tempo de
descida da próxima.

Insiste em 5xx e timeout, com espera crescente. **Não** insiste em 4xx que não
seja 429 (página que mudou de endereço não volta na segunda tentativa) nem em
rede fora (DNS quebrado não melhora esperando). Em 429 respeita o `Retry-After`
que o servidor mandou — ignorar isso é o caminho para levar bloqueio de uma
fonte pública que usamos de graça.

## Bot de consulta no Telegram

O `alerta_cotas.py` fala sozinho quando um rio cruza cota. O `bot.py` é o
contrário: responde quando a pessoa pergunta — de madrugada, sem abrir o site,
com internet ruim. Uma mensagem de texto passa onde uma página não passa.

| Comando | O que devolve |
|---|---|
| `/rua <cidade> <rua>` | a partir de quantos metros aquela rua alaga, e quanto falta o rio subir |
| `/nivel <cidade>` | nível agora, estação e idade da leitura |
| `/chuva <cidade>` | acumulado de 1 h, 12 h, 24 h e 48 h |
| `/previsao <cidade>` | se o pico fosse agora, quando chega em cada cidade a jusante |
| `/cotas <cidade>` | cotas de referência daquela régua |
| `/rios` | panorama de tudo que está sendo medido |
| `/emergencia` | telefones e fontes oficiais |
| `/ajuda` | a lista |

```bash
sudo cp deploy/enchentes-bot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now enchentes-bot
journalctl -u enchentes-bot -f
```

**Três regras em toda resposta:** nunca inventa número (sem dado, diz que não
tem); toda leitura sai com a idade; toda resposta lembra que isto não é alerta
oficial e que emergência é 199.

**Qualquer pessoa pode perguntar.** Diferente do bot do Fila-Disney, que
restringe comandos a um chat, aqui o público é a razão de existir — e tudo que
os comandos devolvem já é público. O que continua restrito é o *aviso
automático* de cota, que vai só para o `TELEGRAM_CHAT_ID`.

### O gabarito de trânsito

`/previsao` precisa do mesmo encadeamento de tempos de descida que o site faz —
e o site é TypeScript, o bot é Python. Duas implementações de uma conta de vida
podem divergir em silêncio: o site dizendo uma coisa, o bot outra, sem ninguém
perceber até a noite errada.

O que impede isso é `data/transito-esperado.json`: o resultado de **todo par de
cidades**, gerado a partir do `transito.ts` do próprio site. Os dois lados têm
teste que o reproduz, e a CI roda os dois.

```bash
cd web && npm run gabarito     # depois de mexer em transito.json ou transito.ts
git diff data/transito-esperado.json   # e CONFERIR: o gabarito só vale se alguém olhou
```

Se um dos testes ficar vermelho, não ajuste o gabarito para calar o teste: ou
uma implementação divergiu da outra, ou alguém mudou a lógica sem regerar. Nos
dois casos a pergunta é qual das duas está certa.

## Cotas de rua e manchas de inundação

O dado mais direto do projeto: **a partir de que nível do rio cada rua começa a
alagar**. Não passa por modelo nenhum — é leitura de tabela. E responde a
pergunta que a pessoa realmente faz, que nunca foi "quantos metros" e sim
"a minha rua".

`data/cotas-ruas.json` — 4.592 registros de Blumenau, Gaspar, Rio do Sul e Brusque,
cada um com fonte, data e confiança — e, em Blumenau, com o **abrigo** daquele
ponto. Regras que o validador e os testes travam:

- **O registro é por PONTO, não por rua.** A Rua São Rafael, em Blumenau, alaga
  a 7,40 m no final e a 7,75 m perto do nº 169. Deduplicar por nome perderia a
  cota mais baixa, que é a que importa.
- **`cota_m` nulo é resposta legítima** — a fonte cita a rua e não publica o
  número — mas exige uma nota dizendo isso. Sem a nota vira buraco silencioso,
  e alguém depois preenche com um chute.
- **O aviso não pode chegar depois da água.** Se a cota mais baixa cadastrada
  para a cidade for maior que a da primeira rua, o validador dá ERRO. Foi assim
  que descobrimos que o aviso de Brusque disparava 1,20 m tarde demais — e, na
  importação de 31/08/2026, que há um ponto da Av. Beira Rio (Limoeiro) alagando
  a **3,76 m**, 1,04 m antes da cota de atenção da cidade.
- **Número verdadeiro entra; o que ele move é outra conversa.** Esse ponto de
  3,76 m aparece na tela e no bot com a ressalva, mas leva `usar_para_aviso:
  false`: baixar o limiar da cidade inteira por causa de um ponto faria o aviso
  tocar em dia de sol, e aviso que toca à toa é desligado antes da noite em que
  importaria. Quem fecha essa lacuna é a Defesa Civil, pelo ofício C1.

`data/manchas/` — as áreas atingidas em nove eventos entre 1983 e 2015, em
GeoJSON, publicadas pela **própria prefeitura de Itajaí** na organização
GeoItajaí do GitHub, sob licença MIT. Dado oficial e aberto, o oposto do resto
que este projeto raspa de HTML. Os arquivos `inundaMÊSAAAA` trazem a
profundidade da lâmina d'água por trecho.

```bash
python3 scripts/baixar_manchas_itajai.py
```

**A mancha não promete nível de rio.** Os polígonos não trazem cota; a ligação
com o pico é feita pela data, cruzando com `enchentes.json`, e só aparece
quando aquele pico está registrado. Inventar essa ligação faria alguém olhar o
mapa de 2011 e concluir que a sua rua alaga a tal metro.

## Mapa das manchas de inundação

Na tela de Itajaí, um mapa Leaflet com as áreas atingidas em nove enchentes
entre 1983 e 2015 — dado da **própria prefeitura**, na organização GeoItajaí do
GitHub, licença MIT. Os arquivos `inundaMÊSAAAA` trazem a profundidade da
lâmina d'água por trecho, e a cor vai do azul claro ao escuro conforme a água
fica mais funda.

Três coisas que o mapa diz, e uma que ele se recusa a dizer:

- **Não é previsão.** É onde a água chegou naquele evento, na cidade que
  existia naquele ano — aterro, drenagem e construção mudaram o terreno.
- **Não estar na mancha não quer dizer que não alaga**: o levantamento cobre o
  que foi mapeado.
- Quando a fonte publica **faixas de profundidade que se sobrepõem** (out/2015
  tem "0,41 a 0,60" e "0,51 a 1"), a tela diz isso em vez de corrigir por conta.
- **Não diz com quantos metros de rio aquilo aconteceu.** Os polígonos não
  trazem cota, e o pico de Itajaí dessas datas ainda não está levantado. Sem
  isso o mapa não se compara com o nível de hoje — e essa é hoje a pendência
  mais valiosa do projeto.

O Leaflet carrega à parte, como o gráfico de picos: ele pesa mais que todo o
resto do site somado, e o mapa existe só nesta tela. Quem abre o site no celular
durante a chuva para ver o nível do rio não paga por ele.

## Cotas de Itajaí e a maré

As onze estações de Itajaí ganharam **cota oficial** de atenção, alerta e
emergência — Tabela 11 do Plano de Contingência da COMPDEC, versão 17 de
22/12/2025. A palavra "emergência" é da fonte e ficou como está: lá é a terceira
subfase, não sinônimo de inundação.

Cada uma tem seu próprio zero. A **DC-10**, no Limoeiro, usa régua de 8 a 10 m e
não se compara com as demais.

### Por que nove delas não disparam aviso sozinhas

Itajaí fica na foz. Nas réguas do estuário o nível sobe e desce com a maré duas
vezes por dia, e essa oscilação é **maior que a distância até a cota**. Medido
nos nossos próprios dados: em 30/08/2026 a **DC-01 marcou 1,24 m às 17:21** —
acima da sua cota de atenção, 1,16 m — e **0,70 m três horas depois**, sem
enchente nenhuma.

A subfase do Plano de Contingência é um estado que a Defesa Civil **declara**
olhando maré, chuva e montante juntos. Automatizar a travessia de uma régua só
reproduz o número sem o julgamento — e um aviso que toca com a maré ensina a
pessoa a ignorar o que tocar na noite da cheia.

Então: **a cota aparece na tela** para as onze, e o **aviso automático** vale
para as duas que não são de estuário (DC-10 e DC-11), mais Rio do Sul e Brusque.
As nove ficam marcadas com `alerta_automatico: false` e o motivo escrito.

```bash
python3 scripts/medir_mare.py     # troca esse julgamento por medição
```

O script lê a série já coletada e, por estação, calcula a amplitude diária, a
folga até a cota e quantas vezes o nível cruzou a cota em quantos dias. Quando a
amplitude é maior que a folga, a régua cruza sozinha. Ele **sugere** e mostra o
número ao lado; mudar quem dispara aviso continua sendo decisão de quem mantém
o projeto.

## Pendências

Em ordem de impacto.

- [ ] **EPAGRI/CIRAM: a fonte que pode fechar os `codigo_ana` que faltam.** O Boletim n° 150/2026 da Equipe de Hidrologia (em `data/brutos/`) publica **código ANA** por estação — é a primeira fonte do projeto que faz isso, e é o código que destrava a série histórica no HidroWeb, que é o que falta para Vidal Ramos, Taió e Ituporanga terem cota. Traz três estações da bacia que não temos: `83105000` Alfredo Wagner/Saltinho, `83892990` Vidal Ramos/Salseiro e `83029900` Taió/Barragem Taió Montante. **Nada foi atribuído:** a nossa régua de Vidal Ramos chama-se "Vidal Ramos" (Asthon, `owner_id: DCSC`, `-27.38547, -49.35812`) e a da EPAGRI chama-se "Salseiro", sem coordenada publicada — mesmo município não é mesma estação, e o teste que resolveria não fecha porque as leituras estão a 6 h uma da outra, com o rio subindo. Destrava pelo **"Rios On-Line"** da EPAGRI — mapeado pelo navegador em 01/09. O `robots.txt` libera, e a fonte é a mais promissora que o projeto achou para as cabeceiras: publica código ANA e **classifica cada estação em faixas** (os limiares que faltam a Taió, Ituporanga e Vidal Ramos existem do lado da EPAGRI). Mas o endpoint das estações (`POST .../estacoesMapa`, bacia do Açú = código 8) exige um header `Authorization` injetado em runtime — não o cookie. Dá para achá-lo lendo o bundle na VPS, mas é frágil: endpoint interno muda no próximo build. **O caminho principal virou o ofício C5** à EPAGRI (`sshidrosc@epagri.sc.gov.br`, rascunho pronto em `docs/pendencias-navegador-e-oficios.md`), pedindo o acesso documentado e a relação código ANA ↔ coordenada — que resolve o Salseiro e, se vierem os limiares, dá cota às três cidades. Detalhe técnico em `docs/fontes-tempo-real.md` (seção EPAGRI). **Três armadilhas registradas em `docs/fontes-tempo-real.md`:** os níveis estão em **centímetros** (254 = 2,54 m); o boletim é foto das 06:00 e diz "15 de 15 em normalidade" num dia em que às 23:35 Rio do Sul estava acima da cota de inundação — nunca pode aparecer como estado atual; e não traz cota de referência, então não dispara aviso.
- [x] **DC-11 é de Itajaí, não de Ilhota — resolvido pelo Plano de Contingência.** A estação `Rio Itajaí-Açu – Santa Regina (Volta de Cima)` estava cadastrada como `ilhota`, e a leitura dela disparava "Ilhota chegou à cota" no bot (aconteceu na cheia de 31/08, 3,38 m contra 3,00 m). A Tabela 11 do Plano da COMPDEC Itajaí (p. 23) a lista como estação **de Itajaí**, e a p. 12 põe Santa Regina e Volta de Cima na **ZONA 1 da Defesa Civil de Itajaí** — localidades do município, no extremo a montante, junto à divisa. Corrigido: DC-11 passa a `itajai` (é a única das onze réguas de Itajaí que fica acima da maré, por isso dispara aviso). **Consequência:** Ilhota fica sem nível ao vivo — como Gaspar antes do Plano —, porque nunca teve régua própria; a DC-11 na divisa é de Itajaí, com zero próprio. O aviso que saía com o nome de Ilhota estava errado e agora sai como Itajaí (Santa Regina). Testes no site e no `gaspar_estadual.py` travam a atribuição.
- [ ] **Rodar `scripts/medir_mare.py` depois de algumas semanas de série** e decidir, por medição, quais das nove réguas de estuário de Itajaí podem disparar aviso. Hoje a trava está posta por julgamento sobre três leituras.
- [ ] **Pedir à prefeitura de Itajaí as cotas por endereço.** O REST do ArcGIS foi sondado (`scripts/sonda_cotas_ruas.py` e `2`): a raiz abre sem token, com 108 serviços, mas a pasta `defesacivil` responde `499 Token Required` — é lá que o app "Cotas de Inundação" busca. O que é público em `historico_inundacoes` são as dez camadas de mancha, com 48/58/55/155 feições nas de 2013 a 2015: exatamente os arquivos do GeoItajaí que já estão no repositório. Ou seja, a cota por endereço de Itajaí **não é fonte aberta** — vira ofício, não código.
- [ ] **Perguntar à Prefeitura o que é a camada `Hidrografia_Terreno_Sujeito_Inundacao`.** Os 110 polígonos chegaram e somam **38,7 hectares**, com o menor tendo 4 m² — contra 7.086 ha da mancha de 1983. Não é "a área inundável de Itajaí", seja lá o que for. Fica fora da tela até haver dicionário de dados; virou o item 3 do ofício C2. Detalhe em `docs/tela-itajai.md` e `scripts/analisar_itajai_arcgis.py`.
- [ ] **"Meu ponto" na tela de Itajaí — bloqueado por referência, não por trabalho.** A especificação da tela pede comparar a elevação do terreno com o nível do rio para dizer "faltam Z m para a água chegar aqui". **Essa subtração não pode ser feita:** a elevação é altura acima do nível do mar (0,15 a 370 m) e o nível das estações DC é leitura na régua de cada uma, com zero próprio e não publicado. O resultado teria duas casas decimais e nenhum significado — e pareceria medido. Destrava com a cota por endereço do ArcGIS (ofício C2) ou com o zero de cada régua DC em relação ao mar. Detalhe em `docs/tela-itajai.md`.
- [ ] **Conferir se a estação DC-11 (Santa Regina, 3,00/4,00/5,00) existe no Plano de Contingência.** Uma especificação recebida a cita entre as estações de Itajaí; nosso cadastro tem DC-01 a DC-10 mais a DC-00. Se existir, é dado que falta — mas entra pela leitura do Plano, não pela transcrição da especificação.
- [ ] **Vidal Ramos: já tem nível ao vivo, falta a cota.** A régua da API Asthon **está na tela** desde 01/09 (`scripts/coleta_asthon.py`, ver Concluído): nível ao vivo com a idade à vista, faixa cinza. O que resta é a **cota de referência** (atenção/alerta) da régua — sem ela o número aparece e não dispara nada. Taió e Ituporanga, ao contrário, **não** têm régua de cidade na Asthon: têm as barragens Oeste e Sul, nível de reservatório na escala do próprio barramento, que nunca pintam faixa de cidade. Ver `scripts/analisar_asthon.py`.
- [ ] **Cotas de rua de Itajaí.** As cotas por RÉGUA chegaram (Plano de Contingência); faltam as por rua, e a sondagem acima mostrou que elas não estão em fonte aberta. Itajaí segue sendo a cidade com manchas de inundação no repositório e nenhuma cota de rua. **Não usar `Relevo_Ponto_Cotado_Altimetrico` para preencher isso:** o campo `cota` dele é altura do terreno acima do nível do mar, não nível de régua. Mesmo nome, grandeza oposta.
- [x] **Mapa base do OpenStreetMap: carga sob pedido.** O chunk já era `lazy`, mas o componente era renderizado na primeira pintura — então **todo** visitante de `/itajai` baixava o Leaflet e puxava tiles, quisesse o mapa ou não. Medido: **161 kB de JS + 17 kB de CSS** (≈54 kB comprimidos), mais o GeoJSON do evento (até 175 kB no de 1984), mais os tiles. Agora o mapa entra por um botão. Isso custava duas vezes no mesmo momento: atrasava o número que a pessoa veio buscar, no celular e na rede pior, e multiplicava o tráfego nos tiles públicos numa noite de enchente — exatamente quando o site não pode cair. **Ainda em aberto:** medir o tráfego real depois de uma cheia e, se preciso, passar a um provedor de tiles ou servir os próprios; e reduzir o refetch ao trocar de evento, que hoje refaz `fitBounds` e busca outro conjunto.
- [ ] **Resolver a referência altimétrica de Blumenau** — teste no HidroWeb (estação 83800002, cotas de 09/07/1983 e 07/08/1984) ou resposta da FURB. Enquanto não sair, a regra bloqueante do `CLAUDE.md` vale: o site rotula cada ponto e recusa parear referências diferentes, ao custo de a previsão Rio do Sul → Blumenau ficar em "dados insuficientes".
- [ ] _(opcional)_ Seletor régua/IBGE nos gráficos de Blumenau, aplicando ±0,20 m só para visualizar. Só vale a pena se a verificação acima demorar — o gráfico já mostra a referência de cada ponto e avisa quando mistura.
- [ ] **Levantar os picos de Itajaí de 1983, 1984, 2001, 2008, 2011, jul e set/2013, jun/2014 e out/2015.** As manchas de inundação desses nove eventos já estão no repositório, mas nenhuma tem o nível do rio correspondente — a legenda do mapa fica sem dizer "isto foi com o rio em X m", que é o que tornaria a mancha comparável com o nível de hoje.
- [ ] **Conseguir as tabelas de cota de rua que faltam.** Rio do Sul e Blumenau saíram (ver Concluído). Brusque e Gaspar saíram também, pelos KML das respectivas Defesas Civis (ver Concluído). Resta **Itajaí** (ArcGIS fechado por token — ofício à prefeitura), que segue sendo a única cidade com manchas de inundação no repositório e nenhuma cota de rua. Hoje são **4.593 pontos**: 2.042 de Blumenau, 1.619 de Gaspar, 555 de Rio do Sul e 377 de Brusque.
- [x] **Coletar a API pública Asthon de Rio do Sul — feito para Vidal Ramos.** `public.asthon.com.br`, `city_id 4214805`. Das 29 estações do Alto Vale, `analisar_asthon.py` já dizia que **só Vidal Ramos** serve como régua de cidade; as demais são barragem (reservatório), altitude ou a cota da Ponte Dom Tito Buss (4,50/5,50/6,50) copiada para outra régua. `scripts/coleta_asthon.py` coleta Vidal Ramos por lista fechada de `station_id`, converte o carimbo de UTC para Brasília e é fiado no `coleta_niveis.py` (ver Concluído). Taió e Ituporanga **não** saem por aqui (só barragem) — seguem pela pendência do HidroWeb/ofício. As barragens ficam anotadas como sinal antecipado de cheia (subiram +12 m em 48 h em 01/09), nunca como nível de cidade.
- [ ] **Conferir as cotas de Blumenau contra o PDF oficial de 2014** (Farol Blumenau, bloqueia robôs — pelo navegador). As 1.938 estão como `confianca: media`; onde os dois baterem, ganham respaldo oficial, e onde divergirem vale o mecanismo de `divergencias`. O definitivo é a FURB, com entrega prevista para **novembro de 2026**.
- [ ] **Cota de referência de Vidal Ramos, Taió e Ituporanga.** Há nível para as três — Vidal Ramos pela API Asthon e as três pelo painel da Defesa Civil de SC (leitura manual de 31/08 em `data/brutos/`, conferida: Vidal Ramos bate entre as duas redes). O que falta é a **cota** de cada régua: sem ela o número aparece na tela e não dispara nada. Em Taió e Ituporanga há o agravante de a Asthon publicar só as barragens, em escala de reservatório.
- [ ] **AlertaBlu: destravar com dois comandos, não com argumento.** O coletor que chegou pronto continua fora, e agora há um argumento a favor dele — buscaria só assets (`/static/data/*.json`) e a página pública `/p/enchentes`, não as páginas do painel que o `robots.txt` restringe. O argumento é bom e **não é verificação**; quem o trouxe também marca a checagem como pendente. São **dois** bloqueios: o `robots.txt` nunca foi lido, e o servidor manda **cadeia de certificado incompleta** (`unable to get local issuer certificate`) — o segundo impede o primeiro. Os comandos estão em `docs/fontes-tempo-real.md`. **Nunca desligar a verificação de TLS**: abriria a coleta para qualquer um no caminho injetar nível de rio.
- [ ] **Trazer `blumenau-enchentes-registradas-alertablu.json` para o repositório — a análise já está pronta esperando.** É a tabela oficial de 102 enchentes de Blumenau (1852–2024), da página `/p/enchentes`. `scripts/conferir_blumenau_alertablu.py` roda no instante em que o arquivo aparecer e devolve um dos quatro vereditos: o AlertaBlu está em IBGE, está na régua, **muda com a época** (e aí não se converte nada), ou há uma terceira referência. Ele compara os pares rotulados IBGE com os sem rótulo em vez de tirar uma mediana só — é aí que o caso difícil se esconde, e é o que os indícios apontam: 1880, jul/1983 e ago/1984 batem ao centavo com o rótulo, e set/2011 fica 0,40 m fora.
- [x] **Cotas de régua de Gaspar — resolvidas pelo Plano de Contingência.** A cidade tinha 1.618 cotas de rua e nenhuma cota de régua; nada disparava aviso lá. O fluxograma do item 4.2.3 do Plano (p. 25) publica as quatro faixas: **0 a 5 m NORMALIDADE, 5 a 6 m ATENÇÃO/ALERTA, 6 a 7 m ALERTA/ALARME e ACIMA DE 7 m RESPOSTA**. Entraram como `atencao` 5,00 / `alerta` 6,00 / `emergencia` 7,00 — `emergencia` e não `inundacao` porque 7,00 m é a fase de resposta do Plano, e a primeira rua alaga 80 cm antes, a 6,20 m. **A margem é real:** a atenção fica 1,20 m abaixo da primeira rua, o oposto de Brusque. **Duas armadilhas no caminho:** o fluxograma é uma imagem que escreve "7 a 8 metros", e o PDF pinta por cima uma caixa opaca com "Acima de 7 metros" — vale o que o documento mostra, a faixa não tem teto; e o Plano **não nomeia o zero da régua**, então o que sustenta tratá-la como a mesma das cotas de rua é a coerência entre três publicações da mesma Defesa Civil, conferida por `scripts/conferir_gaspar_plano.py`: 24 das 26 vias do quadro do Plano batem ao centavo com o cadastro do KML, e a leitura de 31/08 (3,85 m) cai na normalidade do mesmo fluxograma. **O que sobrou é outra coisa:** ver o item da leitura de Gaspar, abaixo.
- [ ] **Nível de Gaspar: há cota, falta leitura — e a rede estadual ainda não serve.** Com as faixas cadastradas, o aviso automático passa a funcionar no instante em que houver um número. A tentativa óbvia é ler Gaspar pela rede estadual (`DCSC-00005`), contornando o host do município. **Três medições dizem que ainda não dá:** (a) no snapshot de 01/09/2026 03:09Z a estação **não devolveu nível** — trouxe chuva (77,2 mm/24h) e mais nada; (b) a rede não está num zero só — Ilhota vem **10,67 m** onde a nossa régua marca **3,34 m**, 7,33 m de diferença, e no dia anterior foram 7,09 m, enquanto Brusque bate (4,48 × 4,42); (c) as faixas de Gaspar são 5/6/7 m, e um deslocamento desse tamanho **cobre a escala inteira** — mostraria RESPOSTA com o rio no leito, ou normalidade com a água na rua. O que destrava é um **par medido**: nível estadual e leitura da tabela do município no mesmo instante. `scripts/gaspar_estadual.py` existe para juntá-lo e se recusa a propor o número para aviso enquanto `DESLOCAMENTO_CONHECIDO_M` for `None` — e também recusa par com mais de 30 min entre as duas leituras, porque numa cheia o rio sobe nesse tempo e a diferença sairia parte régua, parte subida. **Rodado na VPS em 01/09: a estação respondeu com carimbo fresco e sem valor de nível três vezes seguidas** (03:09, 03:24 e 03:33 UTC). Ela publica chuva, não régua — o mesmo que já valia para Blumenau (`DCSC-00026`, `rio_nivel: null`), a outra cidade da bacia com sistema municipal próprio. O caminho estadual está, na prática, fechado, e o que resta é o **ofício C4 à Defesa Civil de Gaspar**, com rascunho pronto e endereço confirmado (`defesacivil@gaspar.sc.gov.br`, do cabeçalho do Plano) em `docs/pendencias-navegador-e-oficios.md`. Detalhe em `docs/fontes-tempo-real.md`.
- [ ] **Conferir "Rua Lino" × "Rua Lírio" com a Defesa Civil de Gaspar.** Nosso cadastro tem "Rua Lino" a 6,57 m, vinda do estudo do CEOPS pela imprensa; o KML oficial tem "Rua Lírio" com mínima de exatamente 6,57 m e nenhuma "Rua Lino". Provavelmente é a mesma rua com erro de transcrição, mas "provavelmente" não apaga registro — os dois ficam até alguém confirmar.
- [ ] **Pedir a planilha da Defesa Civil de Brusque — a 2ª etapa do levantamento.** O KML original chegou e a camada de 2023 foi importada (ver Concluído), mas ela cobre só os pontos atingidos até 8,96 m; a 2ª etapa, dos pontos não atingidos em 2023, continua sem fonte pública. A camada **"Cotas de Cheia 2011"** do mesmo arquivo segue **recusada**, agora com uma evidência a mais: cruzando as duas camadas por vizinho mais próximo, os oito pares a menos de 30 m diferem em +2,04 m na mediana, até +5,36 m — não é a mesma grandeza. Detalhe em `docs/cotas-de-ruas.md`.
- [ ] **Resolver a discordância entre as fontes de tempo de descida.** Somados por caminhos diferentes, os trechos de `transito.json` produzem janelas fora da ordem do rio: no eixo do Açu, Blumenau aparece podendo receber a água antes de Apiúna, que fica acima. O site e o bot **dizem** isso quando acontece, em vez de esconder — mas a correção de verdade é conciliar o hidrograma de projeto da JICA com os modelos acadêmicos, trecho a trecho.
- [ ] **Responder às perguntas em paralelo — adiado de propósito (31/08/2026).** O `rodada()` responde em sequência, um POST bloqueante por vez, então a vazão é `1 ÷ latência do POST`: a 150 ms dá **~400 respostas por minuto**. O custo de CPU é irrelevante (1 ms em média; 9 ms no pior caso, `/rua`, que varre as 2.543 cotas), e o `getUpdates` traz 100 por chamada, o que não aperta. O total diário sairia em centenas de milhares — número que engana, porque ninguém pergunta do rio distribuído ao longo do dia: **todo mundo pergunta na mesma hora**. O que decide é o pico, e 400/min atende ~4.000 perguntas numa janela de 10 minutos de enchente. Acima disso forma fila; nada se perde, mas a pessoa espera. Como o teto do próprio Telegram é ~30 mensagens/s para chats diferentes, o envio em paralelo multiplicaria isso por 3 ou 4 sem esbarrar em limite externo. **Fica para quando o uso real justificar** — hoje não há medição de demanda que sustente a mudança.
- [ ] **Aviso automático para mais de um destino.** Hoje o aviso de cota vai para um único `TELEGRAM_CHAT_ID` do `.env`: o bot responde a quem pergunta, mas só alerta **uma** pessoa ou grupo. Um morador de Gaspar que nunca abriu o bot não recebe nada às três da manhã. Virar lista de inscritos traz consequências que o `bot.py` já registra: limite de envio do Telegram, gente recebendo aviso de cidade onde não mora, e responsabilidade sobre quem **não** recebeu.
- [x] **Chuva de mais onze cidades, da Defesa Civil de SC.** `coleta_chuva_sc.py` traz `chuva.acumulado` das estações da bacia — Blumenau, Ibirama, Apiúna, Botuverá, Guabiruba, Vidal Ramos, Taió, Ituporanga, Gaspar, Indaial e Ilhota. O `robots.txt` de lá libera tudo (`Disallow:` vazio). **Só chuva:** a mesma resposta traz `rio_nivel`, e ele não serve — Ilhota vinha 10,34 m enquanto a nossa régua marcava 3,25 m, as estações `(H)` trazem valores na casa das centenas, e não vem cota por estação, então nada disso poderia virar aviso. Milímetro, ao contrário de metro de régua, é a mesma grandeza em qualquer lugar.
- [ ] **Blumenau publica de três em três horas, e isso não é problema nosso.** Em 31/08/2026 a estação vinha com carimbo de ~3 h enquanto as outras treze da página de Itajaí estavam entre 18 e 29 min. A suspeita era de atraso de repasse. **Conferido no AlertaBlu, a fonte primária: ele mostra o MESMO valor com a MESMA idade** — 5,11 m há 3 h. A cadência é da estação, não do caminho; a nossa coleta está fiel. Consequências: (a) não há fonte pública mais fresca de Blumenau, e a tela mostrando "há 3 h" está certa; (b) coletar direto do AlertaBlu **não** melhora o frescor — continua valendo por ser fonte primária e ter série horária histórica, mas deixou de ser urgente; (c) o valor não é ignorável nem substituível, só velho, e a idade ao lado é a informação honesta. O que ainda vale fazer é marcar na tela quando a leitura é velha **e** a série está subindo: "5,11 m há 3 h" com o rio subindo é diferente de com o rio parado, e hoje a tela mostra os dois igual.
- [ ] **Nível das cidades que faltam.** A Defesa Civil de SC não resolve: sem cota por estação, nenhuma leitura vira aviso, e o "nível" que ela publica não é a mesma grandeza entre estações. Blumenau, em particular, vem com `rio_nivel: null` de lá — depende do AlertaBlu, hoje barrado por cadeia de certificado incompleta no servidor deles. Detalhe em `docs/fontes-tempo-real.md`.
- [x] **Série de chuva acumulada**, como já se fazia com o nível. Ela vivia só no `ultimo.json`, sobrescrito a cada rodada: quinze minutos depois o dado tinha sumido — e isso com os 29 pluviômetros de agora, não os 15 de antes. Vai para `data/tempo-real/chuva-AAAA-MM.ndjson`, separado do nível porque são grandezas com campos diferentes, e guarda as janelas e a marca de coerência: leitura incoerente entra **marcada**, não descartada, senão vira "não choveu" para quem ler a série meses depois. Falta ainda o que a torna útil: **parear a série com os picos**, que só dá depois de meses de coleta.
- [ ] **Aguardar a Defesa Civil publicar a maré.** O endpoint `ajax/mares.php` respondia `{"tides":[],"astronimical_tides":[]}` em 30/08/2026 — o gráfico do próprio site fica em branco nesse estado. O coletor já está escrito para o formato certo e passa a encher sozinho quando a fonte voltar. Enquanto isso, a tela da foz aceita a tábua digitada.
- [ ] **Levantar picos de Itajaí (foz).** Nenhum registro até agora — a tela da foz não estima altura nenhuma sem eles.
- [x] **Nível ao vivo nas cidades com mais de uma régua.** Itajaí tem onze réguas com zeros diferentes, e o site se recusava a eleger uma como "o nível de Itajaí" — o que é certo, esse número não existe —, mas o efeito era a **cidade da foz aparecer sem número nenhum** enquanto o dado estava ali. Agora saem todas, lado a lado, cada uma com o nome e com a cota **dela**. O aviso de que não se comparam vem antes dos números, não em rodapé. O pareamento é pelo **título exato** que a fonte publica, nunca por prefixo de código: conferido contra o arquivo publicado, 14 de 14 casam. Isso importa porque a DC-10, no Limoeiro, usa 8/9/10 m enquanto as do estuário usam 1,0 a 3,0 m — o mesmo 6,75 m é "abaixo de tudo" numa e alarme em outra. A previsão a jusante e a busca "minha rua" continuam desistindo com várias réguas, que é a REGRA BLOQUEANTE item 4. O `extrair_picos.py` **já estava resolvido** e eu afirmei o contrário sem conferir: ele tenta primeiro a cota da PRÓPRIA estação, e as dez réguas de rio de Itajaí têm a sua desde o Plano de Contingência — todas são analisadas. A única recusa é a DC-00, pluviômetro puro sem régua, e recusar ali é o certo.
- [ ] **Registrar o horário do pico** (campo `hora`, `HH:MM`) nos eventos. Só 2 dos 116 têm. É o que troca o hidrograma de projeto da JICA por medição de cheia real, em `calibrar_transito.py`.
- [ ] Conferir o mês do pico de 1911 em Rio do Sul: a série local indica maio, mas o grande pico de Blumenau foi em 02/10. Se forem o mesmo evento, vira mais um par.
- [ ] Levantar picos de Gaspar, Ilhota, Indaial, Apiúna e Ibirama — hoje sem nenhum registro.
- [ ] Confirmar a posição de Guabiruba no eixo do Itajaí-Mirim (entrou pelo relatório-fonte, ainda sem carta oficial).
- [ ] Solicitar acesso à API da ANA (hidro@ana.gov.br) e conferir as rotas em `ana_hidroweb.py`, que ainda não foram validadas contra a API real.
- [ ] Verificar os códigos ANA já cadastrados (`verificado: false` em Taió, Rio do Sul e Blumenau).
- [ ] Localizar estações do Itajaí-Mirim e das cidades do Açu ainda sem `codigo_ana`.
- [ ] **Levantar cota de atenção e de alerta de Brusque — a maior lacuna do Itajaí-Mirim.** A cota de 4,80 m cadastrada como atenção é o nível em que a **Av. Beira-Rio, marginal ao rio, já começa a alagar**: a própria fonte a chama de "cota de inundação da via". Ela está como atenção porque é o primeiro sinal e porque a alternativa era avisar só a 6,00 m, depois de a água estar na rua. Mas **não existe faixa de aviso antes do primeiro alagamento**: em Brusque o aviso começa quando a água já está numa via, e num rio de resposta rápida como o Mirim é onde mais falta margem. Outros pontos alagam entre 5,46 m e 5,80 m, sem cota exata publicada — e a importação de 31/08/2026 achou pior: um ponto da **Av. Beira Rio esquina com Maria Scarpa Formonti, no Limoeiro, alaga a 3,76 m**, com 5,20 m de lâmina em 2023. São **1,04 m abaixo** da cota de atenção da cidade, ou seja, naquele ponto a água chega mais de um metro antes de o aviso tocar. O ofício C1 em `docs/pendencias-navegador-e-oficios.md` pede exatamente isso. Enquanto não vier, o site **e agora o bot** dizem o que 4,80 m significa, em vez de mostrar só o número.
- [ ] Levantar cotas de atenção/alerta/inundação das demais cidades; hoje só Rio do Sul, Blumenau e Brusque têm — e Brusque só a de inundação.
- [ ] Descobrir por que **Blumenau não aparece na coleta**. A cidade tem as três cotas cadastradas, mas a estação não vem no `ultimo.json` (o analisador já prevê o caso: "Blumenau às vezes vem vazio"). Enquanto não vier, a cidade com a série histórica mais longa do projeto fica sem aviso e sem nível ao vivo.

## Concluído

### Sessão de 01/09/2026 (durante uma cheia real na bacia)

- [x] **Tela do rio no estilo Kikikuru (JMA) — os quatro itens do brief, ver `docs/kikikuru.md`.** O rio deixou de ser pontos soltos e virou linha colorida por trecho, no diagrama linear e num **mapa geográfico** novo (Leaflet + traçado do OpenStreetMap em `data/rios/*.geojson`, ODbL): cada trecho ganha a cor da faixa da cidade **a montante**, encaixando as cidades no traçado por uma espinha montante→jusante. A **cor é ação, não enfeite**: cada faixa traz a frase que remete à Defesa Civil. Entraram também a **linha do tempo de 24 h** por cidade (`LinhaDoTempo`, gráfico da régua com as cotas como faixas, lê `serie-recente.json`) e a **reprodução da onda descendo** (`AnimacaoOnda`: um play que, a cada instante, pinta cada cidade pela faixa **dela** naquele momento — reprodução do que foi MEDIDO, nunca previsão; cinza onde não há leitura fresca). O **zoom troca a informação** (nomes das cidades só de perto; tocar numa cidade abre as cotas de rua e o abrigo dela), e no **desktop** o mapa fica numa coluna fixa à esquerda com os dados rolando à direita — no celular segue coluna única, o mapa sob o botão. A projeção de chegada a jusante já existia (`PainelSePicoAgora`) e foi apontada, não duplicada.
- [x] **Blumenau parou de sumir atrás de "várias réguas" — bug visto NA cheia.** A leitura primária (página de Itajaí, que veio velha) e o resgate do AlertaBlu (fresco) são a **MESMA régua** (ANA 83800002, mesmo zero); o site as tratava como duas, avisava que "não se comparam" e **escondia que Blumenau estava em inundação**. `leituraDaCidade` passou a agrupar por régua (`resgate_de ?? estacao`, o mesmo critério do vigia): primária + resgate colam numa régua só e vale a mais fresca. Só devolve "sem nível único" quando há réguas **distintas de verdade** (Itajaí, onze zeros diferentes). Quatro testes travam os dois lados.
- [x] **`data/faixas.json`: fonte única dos textos das faixas — e o site deixou de recomendar ação.** Os textos de faixa saíram do código para um JSON que o site lê (não podem mais divergir do canon). E aplicou-se o rigor da regra de responsabilidade: o site **descreve** a faixa e **remete** ("Siga a Defesa Civil", "ligue 199"), nunca recomenda ação. Caíram "Prepare o que levar", "procure lugar seguro" e "Fique atento e confira a cota da sua rua". Varredura de toda a interface: nenhuma outra recomendação sobrou (o que parecia — "Procure a sua rua" é rótulo de busca; "não espere… para sair de área de risco" é disclaimer — remete ao uso da tela ou à autoridade).
- [x] **Série das últimas 48 h publicada (`serie-recente.json`).** O navegador só tinha o `ultimo.json` (um instante); a série acumulada em ndjson é matéria-prima gitignorada, só na VPS. Agora `coleta_niveis.py` recorta as últimas horas de **nível** por rio e cidade e `publicar_tempo_real.sh` leva o arquivo junto do `ultimo.json` no branch `tempo-real`. É a base do slider e da animação. Só nível (chuva é outra grandeza); `medido_em` em hora de Brasília, sem fuso.
- [x] **Vidal Ramos com nível ao vivo (Asthon) — 11ª cidade coberta.** A cidade era uma das dez sem nível. `scripts/coleta_asthon.py` pega Vidal Ramos por **lista fechada de `station_id`** (barragem, altitude e cota copiada de Rio do Sul ficam de fora, como `analisar_asthon.py` já dizia), converte o `last_reading_at` de **UTC → Brasília sem fuso** na entrada, e é fiado em `coleta_niveis.py` no molde do resgate do Blumenau (falha nunca derruba a coleta). Confirmado ponta a ponta na VPS. **Sem cota de referência ainda**, então mostra o nível com a idade à vista e a faixa fica **cinza** — mostra, nunca dispara.
- [x] **Classificação da estação estadual de Gaspar (`DCSC-00005`) precisada.** A metadados do GraphQL estadual **declara** sensor de rio (`rio_nivel.value=true`), então não é pluviômetro puro; mas o **valor** de nível veio nulo em 3/3 observações — na prática publica só chuva. Os docs deixaram de dizer só "publica chuva, não régua" (que negava o sensor) e passaram a dizer as duas metades; a estação **não** entra em `estacoes.json`, porque registrar uma régua que nunca devolveu número seria cobertura aparente.

- [x] Scaffold do site (React + Vite + TypeScript strict) com as quatro telas e leitura direta dos JSONs de `data/`.
- [x] Diagrama linear do rio com cotas, fontes de tempo real e tempo de trânsito entre cidades.
- [x] Gráfico de picos históricos por cidade, com cor por confiança e tabela de fontes.
- [x] Lógica de previsão empírica com as travas de segurança descritas acima, coberta por 22 testes.
- [x] `scripts/validar_dados.py` e CI rodando validação, testes e build a cada push.
- [x] **Token do Telegram não vaza mais para o log.** Eram três caminhos, todos reproduzidos antes do conserto: o `erro na rodada` do laço principal, o aviso de falha ao registrar o menu, e — o pior — `--uma-vez`, que deixava o traceback do Python subir com a URL inteira. O token viaja no caminho da URL (`/bot<token>/getUpdates`), então qualquer erro de rede o carrega. Agora tudo passa por `notificador.sem_segredo()`, que apaga o token configurado **e** o que estiver entre `/bot` e a próxima barra — o que protege também log antigo, de antes de uma troca de token. 19 testes novos, incluindo uma guarda que lê o fonte e cobra a limpeza em todo `print` e `return` que leve um erro para fora.
- [x] **As três camadas do ArcGIS de Itajaí baixadas e analisadas.** `scripts/baixar_itajai_arcgis.py` trouxe do serviço público da Prefeitura, sem navegador, as 10 camadas de inundação, os 5.237 pontos cotados e os 110 polígonos de terreno. As contagens bateram com o previsto até nos detalhes. A análise devolveu **dois "não" e um "sim"**: não trocar as nossas manchas pelas do ArcGIS (mesma geometria, atributo derivado a mais, e perderíamos a licença MIT declarada); não mostrar o terreno sujeito a inundação (38,7 ha contra 7.086 ha da mancha de 1983 — 183 vezes menos que o nome promete); e sim à área atingida por evento, que três camadas publicam e confere com a geometria: 1983 = 7.086 ha, 1984 = 7.015 ha, 2001 = 3.425 ha.
- [x] **Tocar num ponto do mapa de Itajaí diz em quais enchentes ele ficou dentro da área atingida.** É a metade do "meu ponto" que não depende de referência altimétrica nenhuma — um fato sobre polígonos que já estavam no repositório, verdadeiro ou falso, não estimado. A outra metade (responder em metros) continua bloqueada, e o porquê está em `docs/tela-itajai.md`. "Nenhuma mancha" não vira "não alaga": a resposta negativa sai com a ressalva de que o levantamento cobre o que foi mapeado. Dez testes na lógica pura, incluindo o buraco de polígono e o vértice na altura exata do ponto.
- [x] **As cotas de Blumenau conferidas contra o PDF oficial — e o abrigo de cada rua.** Os 1.938 pontos de Blumenau tinham entrado por imprensa, em `confianca: media`. O PDF da Secretaria Municipal de Defesa Civil (111 páginas, 2.034 registros) chegou, e o cruzamento pelo mesmo ponto de cada rua deu **1.891 de 1.891 batendo ao centavo, zero divergências, deslocamento mediano 0,00 m**. As conferidas subiram para `alta`; **nenhum número mudou** — a operação confirma, não corrige. O PDF ainda traz o que a imprensa não trazia: **o abrigo de cada rua**, com código, que chegou a 2.018 dos 2.042 registros e agora sai no site e no bot logo abaixo da cota. A cota diz que é hora de sair; o abrigo diz para onde. Mais 104 pontos que só o PDF tem entraram. Blumenau: 1.938 → 2.042.
- [x] **Cotas de rua de Gaspar: 23 → 1.618, com `confianca: alta`.** O KML da Defesa Civil de Gaspar chegou com a mesma armadilha do de Brusque — uma conversão pronta que já gravava tudo como `referencia: "régua"`, sem evidência nenhuma. `scripts/analisar_kml_gaspar.py` testou a afirmação com o mesmo instrumento que recusou a camada de 2011 de Brusque, e desta vez ela passou por dois caminhos independentes: as **4 ruas em comum com o nosso cadastro batem todas ao centavo, e sempre no menor valor da rua** (em Brusque eram 4 de 13, com nove divergindo até 2,3 m), e as **duas listas que o estudo do CEOPS publicou saem na ordem certa e separadas** (medianas 6,63 m e 7,07 m, P por acaso = 0,0014), sem que nada no arquivo diga a que grupo cada rua pertence. O importador refaz a análise antes de gravar e recusa se o veredito mudar. Dezoito registros sem número foram substituídos pelas cotas oficiais; os cinco com número ficaram, porque são eles a prova de escala. Na época Gaspar seguia **sem cota em `estacoes.json`**, e os números respondiam "a partir de quanto minha rua alaga" sem disparar aviso; as faixas da régua chegaram depois, pelo Plano de Contingência (ver o item das cotas de régua de Gaspar, em Pendências).
- [x] **Cotas de rua de Brusque: 27 → 377, com `confianca: alta`.** O KML original do My Maps chegou e resolveu o que a conversão anterior tinha perdido: cada marcador da camada de 2023 traz o **nome** (a cota da régua) e a **lâmina d'água** medida em 17/11/2023, e os dois somam **8,96 m** — o pico daquele dia — em **338 dos 344 pontos** que publicam lâmina, ao centímetro. Não é inferência sobre a fonte, é aritmética contra um pico conhecido, e `scripts/importar_cotas_brusque.py` a refaz a cada execução e **recusa a importação inteira** se ela deixar de fechar. Seis pontos ficaram de fora por a própria conta não fechar — quando os dois números da fonte discordam não dá para saber qual está errado. A camada de 2011 segue recusada, e `scripts/teste_analisar_kml_brusque.py` foi **apertado**, não afrouxado. Achado junto: um ponto da Av. Beira Rio alaga a 3,76 m, 1,04 m antes da cota de atenção da cidade.
- [x] **Lista de Rio do Sul completa e conferida contra segunda fonte.** Duas leituras independentes da tabela oficial — a nossa, do portal (554 ruas, `alta`), e a transcrição da NSC Total (545 ruas, `media`) — batem em **538 de 538 ruas em comum, ao centavo, com zero divergências**. A conferência achou a rua que faltava: **Visconde de Cairu, 19,01 m**, que não é grafia de nenhuma outra. Rio do Sul fecha em **555**, que é o total que o portal declara. Refazível com `scripts/conferir_rio_do_sul_nsc.py` (16 testes).
- [x] Série histórica do relatório documental incorporada: 116 registros (97 de Blumenau desde 1852, 9 de Rio do Sul, 8 de Brusque, Taió e Timbó), cada um com fonte, confiança e divergências.
- [x] Eixo do Itajaí-Açu completo em `transito.json` a partir do estudo JICA, incluindo Ituporanga, Apiúna e os trechos entre Blumenau e a foz.
- [x] Painel de maré na tela da foz, com coletor da tábua oficial e cálculo de sizígia.
- [x] Nível ao vivo no site, com selo de idade e recusa de calcular chegada a partir de leitura velha.
- [x] Site publicado no GitHub Pages, com os dados validados antes de cada publicação.
- [x] **554 cotas por rua de Rio do Sul**, da tabela oficial da Defesa Civil — dez vezes tudo que havia. A tabela viaja dentro do pacote da aplicação do portal; o importador (`scripts/importar_cotas_rio_do_sul.py`) confere o `robots.txt` antes, mescla sem tocar em outra cidade e é idempotente. Duas cotas que a fonte publica abaixo do nível normal do rio entraram com `usar_para_aviso: false` — aparecem na busca com a ressalva e não movem alarme, pelo mesmo motivo das réguas de estuário de Itajaí. A tabela saiu do pacote inicial do site: com dez vezes mais dado, ele ficou menor (310 → 285 kB).
- [x] Cotas oficiais das onze réguas de Itajaí e da de Ilhota (Plano de Contingência da COMPDEC, v17), com as nove de estuário travadas contra aviso automático — e **visíveis na tela e no bot**: antes o site dizia "cotas de referência não levantadas" e o `/cotas` dizia "ainda não foram levantadas" para duas cidades cujas cotas estão publicadas. Os ribeirões da Murta e da Canhanduba, que não estão em nenhum eixo, aparecem na tela da foz.
- [x] Registro das 14 estações de tempo real com o título exato da fonte, pronto para receber a cota de cada régua.
- [x] Bot de consulta no Telegram (`/nivel`, `/chuva`, `/previsao`, `/cotas`, `/rios`), com o encadeamento de trânsito amarrado ao do site por um gabarito compartilhado.
- [x] Chuva acumulada por cidade (1 h / 12 h / 24 h / 48 h), agregando os pluviômetros e recusando leitura que não fecha.
- [x] Aviso por Telegram quando um rio cruza cota, e vigia que percebe a coleta morrendo — ver **Avisos** abaixo.
- [x] Caminho completo para registrar cheias novas: coleta acumulada em formato enxuto, extração de picos com data e hora, e calibração dos tempos de descida a partir deles.
