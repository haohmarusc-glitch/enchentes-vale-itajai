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

`data/cotas-ruas.json` — 57 registros de Blumenau, Gaspar e Brusque, cada um com
fonte, data e confiança. Regras que o validador e os testes travam:

- **O registro é por PONTO, não por rua.** A Rua São Rafael, em Blumenau, alaga
  a 7,40 m no final e a 7,75 m perto do nº 169. Deduplicar por nome perderia a
  cota mais baixa, que é a que importa.
- **`cota_m` nulo é resposta legítima** — a fonte cita a rua e não publica o
  número — mas exige uma nota dizendo isso. Sem a nota vira buraco silencioso,
  e alguém depois preenche com um chute.
- **O aviso não pode chegar depois da água.** Se a cota mais baixa cadastrada
  para a cidade for maior que a da primeira rua, o validador dá ERRO. Foi assim
  que descobrimos que o aviso de Brusque disparava 1,20 m tarde demais.

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

- [ ] **Rodar `scripts/medir_mare.py` depois de algumas semanas de série** e decidir, por medição, quais das nove réguas de estuário de Itajaí podem disparar aviso. Hoje a trava está posta por julgamento sobre três leituras.
- [ ] **Pedir à prefeitura de Itajaí as cotas por endereço.** O REST do ArcGIS foi sondado (`scripts/sonda_cotas_ruas.py` e `2`): a raiz abre sem token, com 108 serviços, mas a pasta `defesacivil` responde `499 Token Required` — é lá que o app "Cotas de Inundação" busca. O que é público em `historico_inundacoes` são as dez camadas de mancha, com 48/58/55/155 feições nas de 2013 a 2015: exatamente os arquivos do GeoItajaí que já estão no repositório. Ou seja, a cota por endereço de Itajaí **não é fonte aberta** — vira ofício, não código.
- [ ] **Cotas de rua de Itajaí.** As cotas por RÉGUA chegaram (Plano de Contingência); faltam as por rua, e a sondagem acima mostrou que elas não estão em fonte aberta. Itajaí segue sendo a cidade com manchas de inundação no repositório e nenhuma cota de rua. **Não usar `Relevo_Ponto_Cotado_Altimetrico` para preencher isso:** o campo `cota` dele é altura do terreno acima do nível do mar, não nível de régua. Mesmo nome, grandeza oposta.
- [ ] **Mapa base do OpenStreetMap durante uma cheia.** O mapa das manchas usa os servidores públicos de tiles do OSM, cuja política desencoraja uso pesado. Numa noite de enchente o acesso ao site multiplica; vale medir e, se preciso, passar para um provedor de tiles ou servir os próprios.
- [ ] **Resolver a referência altimétrica de Blumenau** — teste no HidroWeb (estação 83800002, cotas de 09/07/1983 e 07/08/1984) ou resposta da FURB. Enquanto não sair, a regra bloqueante do `CLAUDE.md` vale: o site rotula cada ponto e recusa parear referências diferentes, ao custo de a previsão Rio do Sul → Blumenau ficar em "dados insuficientes".
- [ ] _(opcional)_ Seletor régua/IBGE nos gráficos de Blumenau, aplicando ±0,20 m só para visualizar. Só vale a pena se a verificação acima demorar — o gráfico já mostra a referência de cada ponto e avisa quando mistura.
- [ ] **Levantar os picos de Itajaí de 1983, 1984, 2001, 2008, 2011, jul e set/2013, jun/2014 e out/2015.** As manchas de inundação desses nove eventos já estão no repositório, mas nenhuma tem o nível do rio correspondente — a legenda do mapa fica sem dizer "isto foi com o rio em X m", que é o que tornaria a mancha comparável com o nível de hoje.
- [ ] **Conseguir as tabelas de cota de rua que faltam.** Rio do Sul saiu (554 logradouros oficiais, ver Concluído). Restam: Blumenau (AlertaBlu, `robots.txt` proíbe raspagem — pedir à Defesa Civil; a FURB está refazendo ~20 mil edificações), Brusque (planilha não pública — ofício), Gaspar (mapa "Pesquise sua cota"; o host deu timeout de conexão nas duas sondagens de 31/08/2026, vale repetir) e Itajaí (acima). Hoje são **611 pontos**: 554 de Rio do Sul, 27 de Brusque, 23 de Gaspar e 7 de Blumenau.
- [ ] **Resolver a discordância entre as fontes de tempo de descida.** Somados por caminhos diferentes, os trechos de `transito.json` produzem janelas fora da ordem do rio: no eixo do Açu, Blumenau aparece podendo receber a água antes de Apiúna, que fica acima. O site e o bot **dizem** isso quando acontece, em vez de esconder — mas a correção de verdade é conciliar o hidrograma de projeto da JICA com os modelos acadêmicos, trecho a trecho.
- [ ] **Ampliar a cobertura de chuva.** A fonte de Itajaí só publica pluviômetro em Itajaí, Brusque, Ilhota e Rio do Sul. Vidal Ramos, Botuverá, Guabiruba, Taió, Ituporanga, Ibirama, Apiúna, Indaial, Blumenau e Gaspar ficam sem chuva na tela. Candidatas: CEMADEN (nacional, tem pluviômetro na maioria dos municípios de risco de SC), AlertaBlu (Blumenau) e a Defesa Civil de SC.
- [ ] **Acumular a série de chuva**, como já se faz com o nível. Com nível de montante explicando pouco o de jusante (r² = 0,21), a chuva é a candidata mais forte a preditor de verdade — mas só depois de meses de série pareada com os picos.
- [ ] **Aguardar a Defesa Civil publicar a maré.** O endpoint `ajax/mares.php` respondia `{"tides":[],"astronimical_tides":[]}` em 30/08/2026 — o gráfico do próprio site fica em branco nesse estado. O coletor já está escrito para o formato certo e passa a encher sozinho quando a fonte voltar. Enquanto isso, a tela da foz aceita a tábua digitada.
- [ ] **Levantar picos de Itajaí (foz).** Nenhum registro até agora — a tela da foz não estima altura nenhuma sem eles.
- [ ] **Mostrar nível ao vivo nas cidades com mais de uma régua.** Itajaí tem onze réguas com zeros diferentes, e o site se recusa a eleger uma como "o nível de Itajaí" — o que é o certo, mas deixa a foz sem número na tela. As **cotas** dessas réguas já aparecem (tela de rio e tela da foz, com a marca de estuário); falta a leitura de cada uma, lado a lado, sem somar nem escolher. O mesmo vale para `extrair_picos.py`, que continua se recusando a analisar essas estações.
- [ ] **Registrar o horário do pico** (campo `hora`, `HH:MM`) nos eventos. Só 2 dos 116 têm. É o que troca o hidrograma de projeto da JICA por medição de cheia real, em `calibrar_transito.py`.
- [ ] Conferir o mês do pico de 1911 em Rio do Sul: a série local indica maio, mas o grande pico de Blumenau foi em 02/10. Se forem o mesmo evento, vira mais um par.
- [ ] Levantar picos de Gaspar, Ilhota, Indaial, Apiúna e Ibirama — hoje sem nenhum registro.
- [ ] Confirmar a posição de Guabiruba no eixo do Itajaí-Mirim (entrou pelo relatório-fonte, ainda sem carta oficial).
- [ ] Solicitar acesso à API da ANA (hidro@ana.gov.br) e conferir as rotas em `ana_hidroweb.py`, que ainda não foram validadas contra a API real.
- [ ] Verificar os códigos ANA já cadastrados (`verificado: false` em Taió, Rio do Sul e Blumenau).
- [ ] Localizar estações do Itajaí-Mirim e das cidades do Açu ainda sem `codigo_ana`.
- [ ] **Levantar cota de atenção e de alerta de Brusque.** Hoje só a de inundação (6,00 m) está cadastrada, e o aviso por Telegram pula direto de "abaixo das cotas" para "inundação": não existe aviso adiantado nenhum no Itajaí-Mirim. O `--seco` marca a estação com ⚠ por causa disso.
- [ ] Levantar cotas de atenção/alerta/inundação das demais cidades; hoje só Rio do Sul, Blumenau e Brusque têm — e Brusque só a de inundação.
- [ ] Descobrir por que **Blumenau não aparece na coleta**. A cidade tem as três cotas cadastradas, mas a estação não vem no `ultimo.json` (o analisador já prevê o caso: "Blumenau às vezes vem vazio"). Enquanto não vier, a cidade com a série histórica mais longa do projeto fica sem aviso e sem nível ao vivo.

## Concluído

- [x] Scaffold do site (React + Vite + TypeScript strict) com as quatro telas e leitura direta dos JSONs de `data/`.
- [x] Diagrama linear do rio com cotas, fontes de tempo real e tempo de trânsito entre cidades.
- [x] Gráfico de picos históricos por cidade, com cor por confiança e tabela de fontes.
- [x] Lógica de previsão empírica com as travas de segurança descritas acima, coberta por 22 testes.
- [x] `scripts/validar_dados.py` e CI rodando validação, testes e build a cada push.
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
