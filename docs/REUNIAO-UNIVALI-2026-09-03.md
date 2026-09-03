# Reunião Univali — Prof. Mauro Michelena Andrade
**Quinta, 03/09/2026, 9h30 · LOF (Laboratório de Oceanografia Física), sala 117, bloco E2**
Contato: michelena@univali.br · (47) 3341-7720

---

## 1. Objetivo do site (abrir com isto, em 1 minuto)

Um site aberto e sem fins comerciais que mostra, para o morador do Vale do Itajaí:
- o **nível do rio em cada cidade**, com a fonte e a idade de cada leitura à vista;
- **a partir de quantos metros a rua dele alaga** (6.229 cotas de rua já levantadas em 4 cidades);
- **até onde a água chegou** nas enchentes passadas (manchas de 1983 a 2015 em Itajaí);
- uma **estimativa** de quando a cheia chega na cidade seguinte.

**O que o site NÃO é, e isso está em todas as páginas:** não é sistema oficial de alerta, não emite ordem
de evacuação, não substitui a Defesa Civil. Quem avisa e manda sair de casa é a Defesa Civil (199 / 193).
O site descreve a faixa e aponta para a autoridade.

Código e dados públicos: `github.com/haohmarusc-glitch/enchentes-vale-itajai`
No ar: `haohmarusc-glitch.github.io/enchentes-vale-itajai`

**Por que isso interessa à Univali:** o projeto credita a fonte de cada dado, é aberto, e a parte mais
frágil dele hoje é justamente a que o LOF domina — a foz.

---

## 2. O que falta no site (panorama honesto, para dar contexto ao pedido)

### Já resolvido
- Tempo real de 5 fontes (Defesa Civil de Itajaí, Defesa Civil SC, AlertaBlu, Asthon, CEMADEN)
- 6.229 cotas de rua (Blumenau, Brusque, Gaspar, Rio do Sul)
- Coordenadas das 11 réguas DC de Itajaí e das estações estaduais da bacia
- Topologia verificada dos dois rios (o Açu é árvore; o Mirim se ramifica dentro de Itajaí)
- 45 abrigos de Itajaí georreferenciados
- Manchas de inundação de Itajaí, 1983–2015

### O que falta, por tipo
| Falta | Situação |
|---|---|
| **Maré medida em Itajaí** | ⬅️ **é o assunto desta reunião** |
| Relação maré × cota do rio na foz | ⬅️ **desta reunião** |
| Cota por endereço de Itajaí | pasta do ArcGIS fechada por token — ofício enviado ao GEOItajaí |
| Cotas de atenção/alerta do Mirim em Brusque | hoje só existe a de inundação (4,80 m) — sem aviso adiantado |
| Séries históricas da ANA | credenciais pedidas (e-mail 02/09) |
| Faixas de nível da EPAGRI | endpoint exige credencial — ofício enviado |
| Calibrar offset das estações estaduais | precisa de evento-âncora por estação |

### A lacuna específica de Itajaí, que é o motivo de estar aqui
Itajaí é a única cidade da bacia onde o nível **não depende só do rio**: depende do rio **e da maré**.
Hoje o site tem as 11 réguas com cotas oficiais, tem as manchas históricas, tem 5.237 pontos cotados —
mas **não tem a maré medida**, e sem ela não é possível dizer se um mesmo nível de rio vai alagar ou não.
A tela de Itajaí está especificada e parada nesse ponto.

---

## 3. O que já levantamos sobre a Univali (para não fazer o senhor repetir)

Da resposta do Prof. Mauro (30/08) e da pesquisa:

| Item | O que sabemos |
|---|---|
| **Marégrafo de Cabeçudas** | Univali (Escola do Mar) + Porto de Itajaí + Iate Clube; instalado em parceria com a Defesa Civil; **em reinstalação**. Os dados devem aparecer na página de marés da Defesa Civil de Itajaí — hoje ela mostra "nenhum dado disponível". |
| **Projeto MAPI / LibGeo** | monitora o estuário do Itajaí-Açu (descarga fluvial, nível dentro e fora do estuário); estação meteorológica no molhe sul desde nov/2018, medindo a cada 5 min. Foco em dragagem/porto. O portal bloqueia acesso automatizado. |
| **Estudo maré × cota** | só trabalhos em congresso por ora; a Univali está trabalhando para determinar formalmente. **"Já sabemos empiricamente"** — frase do próprio Prof. Mauro. |
| **Papel institucional** | Prof. Mauro é o titular da Univali no GRAC da Defesa Civil de Itajaí (Plano de Contingência, item 5.4). |

**Precedente útil:** em dez/2020 a Defesa Civil de Brusque revisou uma projeção de 6,5 m para um pico real
de 4,95 m **depois que um hidrólogo da Univali analisou a maré de sizígia**. Ou seja: a influência da maré
já mudou uma previsão oficial na prática — é exatamente o efeito que o site precisa representar.

---

## 4. As perguntas — em ordem de valor

### A. Maré (o principal)
1. O **marégrafo de Cabeçudas** vai ter acesso aberto? Página, API, arquivo periódico? Em que prazo?
2. Enquanto ele não opera, o que o senhor recomenda usar: a **tábua de maré da DHN/Marinha** (previsão) ou
   alguma série do MAPI? A tábua serve para o site marcar "maré prevista" em vez de "medida"?
3. Qual o **fuso** dos dados (UTC ou local)? *(No projeto o contrato é: carimbo sem fuso = UTC. Já tivemos
   erro de 3 h por misturar fontes.)*

### B. A relação maré × rio — o que a Univali sabe empiricamente
4. **A partir de que combinação** de cota do rio e altura de maré Itajaí começa a alagar? Existe uma regra
   prática que a Defesa Civil já usa?
5. Quanto a **preamar de sizígia** segura o escoamento? Dá para dizer em horas ou em metros de cota?
6. O efeito é diferente entre o **Açu** e o **Mirim**? (No Mirim, o canal retificado e o curso antigo
   respondem igual à maré?)
7. Há **defasagem** entre a maré na barra e o efeito nas réguas de dentro da cidade (DC-02, DC-11)?

### C. Dados do MAPI
8. As séries de **nível d'água do estuário** e da **estação do molhe sul** podem ser usadas num projeto
   comunitário aberto? Quais os critérios de uso e a forma de citar?
9. Existe alguma **PCD de maré** além do Cabeçudas no estuário?

### D. Duas perguntas técnicas que só a Univali responde
10. Os **5.237 pontos cotados altimétricos** da Prefeitura estão em que **datum** (nível do mar? IBGE?) —
    e existe o **offset** entre esse datum e o zero das réguas DC? *Sem isso não dá para dizer "faltam X
    metros para a água chegar aqui"; hoje o site só consegue mostrar as manchas históricas.*
11. A Univali tem as **coordenadas das réguas da Defesa Civil**, ou sabe se elas foram levantadas com GPS
    geodésico? *(As que temos vieram do mapa público e podem ter erro de dezenas de metros.)*

---

## 5. O que oferecer (a conversa é de mão dupla)

- **Crédito e link** para a Univali/LOF em toda tela que usar dado deles.
- O projeto é **aberto**: o código, os dados tratados e a documentação ficam públicos — inclusive as
  coordenadas e a topologia que levantamos, que podem ser úteis a eles.
- A **série de nível** que o projeto acumula (coleta a cada 10–15 min de 5 fontes) fica disponível.
- Disposição de **ajustar o uso** ao que a universidade considerar adequado, inclusive tirar do ar
  qualquer dado se pedirem.

---

## 6. Levar
- Este documento (impresso ou no celular)
- O site aberto no celular, na tela de Itajaí — mostra melhor que explicar
- Bloco para anotar: **fuso, datum, offset e a regra empírica maré×rio** são as quatro respostas que mais
  valem
- Caneta. Se ele desenhar a relação maré/rio num papel, isso vale mais que qualquer documento.

## 7. Depois da reunião
- Registrar as respostas em `docs/fontes-academicas.md` e, se vier a regra empírica, em `docs/tela-itajai.md`
- Se autorizarem o MAPI: escrever o coletor e creditar
- Se vier o offset datum↔régua: destrava o Bloco 4 da tela de Itajaí ("faltam X m para a água chegar aqui"),
  que hoje está proibido por regra justamente por falta desse número
