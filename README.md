# Enchentes do Vale do Itajaí

Site com dados históricos de enchentes nos rios **Itajaí-Açu** e **Itajaí-Mirim** (SC): nível do rio em cada cidade, previsão empírica para a cidade a jusante e tempo estimado de chegada da cheia. Itajaí, na foz, recebe os dois rios e a influência da maré.

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
python3 coleta_mares.py --verificar # mostra a tábua lida do site, sem gravar
python3 coleta_mares.py             # grava data/mare-itajai.json
python3 coleta_niveis.py            # coleta e acumula a série dos níveis
python3 extrair_picos.py            # propõe registros de pico a partir da série
python3 calibrar_transito.py        # relata o que dá para calibrar
```

### Registrar uma cheia nova

O que falta em quase todo registro de `enchentes.json` é o **horário do pico** — e é
ele que troca o hidrograma de projeto da JICA por medição de cheia real. O caminho:

1. `coleta_niveis.py` no cron (`*/15 * * * *`) acumula uma linha por medição em
   `data/tempo-real/AAAA-MM.ndjson`. Deduplica pelo carimbo da fonte, então rodar
   com mais frequência não infla o arquivo: a página atualiza a cada 15–30 min.
   São ~110 bytes por leitura, algo como 40 MB por ano; `--compactar` reduz os meses
   fechados a cerca de um décimo. Esses arquivos ficam **fora do git**.
2. Passada a cheia, `extrair_picos.py` lê a série, separa os episódios acima da cota
   de atenção de cada cidade e imprime os registros propostos, com data e hora.
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

O site é estático e usa `HashRouter`, então funciona em GitHub Pages ou Vercel sem reescrita de rotas no servidor.

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

## Pendências

Em ordem de impacto.

- [ ] **Rodar `coleta_mares.py` contra o site no ar e conferir a leitura.** O analisador foi escrito sem acesso ao domínio (bloqueado no ambiente de desenvolvimento) e cobre três formatos plausíveis de página, testados com fixtures. Rode `--verificar` uma vez e ajuste se preciso.
- [ ] **Levantar picos de Itajaí (foz).** Nenhum registro até agora — a tela da foz não estima altura nenhuma sem eles.
- [ ] **Registrar o horário do pico** (campo `hora`, `HH:MM`) nos eventos. Só 2 dos 116 têm. É o que troca o hidrograma de projeto da JICA por medição de cheia real, em `calibrar_transito.py`.
- [ ] Conferir o mês do pico de 1911 em Rio do Sul: a série local indica maio, mas o grande pico de Blumenau foi em 02/10. Se forem o mesmo evento, vira mais um par.
- [ ] Levantar picos de Gaspar, Ilhota, Indaial, Apiúna e Ibirama — hoje sem nenhum registro.
- [ ] Confirmar a posição de Guabiruba no eixo do Itajaí-Mirim (entrou pelo relatório-fonte, ainda sem carta oficial).
- [ ] Solicitar acesso à API da ANA (hidro@ana.gov.br) e conferir as rotas em `ana_hidroweb.py`, que ainda não foram validadas contra a API real.
- [ ] Verificar os códigos ANA já cadastrados (`verificado: false` em Taió, Rio do Sul e Blumenau).
- [ ] Localizar estações do Itajaí-Mirim e das cidades do Açu ainda sem `codigo_ana`.
- [ ] Levantar cotas de atenção/alerta/inundação das demais cidades; hoje só Rio do Sul, Blumenau e Brusque têm.
- [ ] Colocar `coleta_niveis.py` e `coleta_mares.py` no cron de uma máquina e mostrar o nível em tempo real na tela, com aviso de leitura velha.

## Concluído

- [x] Scaffold do site (React + Vite + TypeScript strict) com as quatro telas e leitura direta dos JSONs de `data/`.
- [x] Diagrama linear do rio com cotas, fontes de tempo real e tempo de trânsito entre cidades.
- [x] Gráfico de picos históricos por cidade, com cor por confiança e tabela de fontes.
- [x] Lógica de previsão empírica com as travas de segurança descritas acima, coberta por 22 testes.
- [x] `scripts/validar_dados.py` e CI rodando validação, testes e build a cada push.
- [x] Série histórica do relatório documental incorporada: 116 registros (97 de Blumenau desde 1852, 9 de Rio do Sul, 8 de Brusque, Taió e Timbó), cada um com fonte, confiança e divergências.
- [x] Eixo do Itajaí-Açu completo em `transito.json` a partir do estudo JICA, incluindo Ituporanga, Apiúna e os trechos entre Blumenau e a foz.
- [x] Painel de maré na tela da foz, com coletor da tábua oficial e cálculo de sizígia.
- [x] Caminho completo para registrar cheias novas: coleta acumulada em formato enxuto, extração de picos com data e hora, e calibração dos tempos de descida a partir deles.
