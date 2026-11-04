# O que o projeto ganhou — varredura de 04/11/2026 e o que veio junto

Relatório para o Jefferson, escrito em 04/11/2026 depois do merge do PR #563. Linguagem direta; cada ganho diz o que
entrou, onde está e o que ainda depende de decisão.

## 1. Ganhos que já estão no repositório

| Ganho | O que é | Onde | Uso hoje |
|---|---|---|---|
| **Tabela do Mendeley (Senac SC), cruzada** | 102 cheias de Blumenau de 1852 a 2024, CC BY 4.0, original com sha256 conferido e transcrição reproduzível | `data/brutos/varredura-fontes-2026-11-04/`, `docs/VARREDURA-FONTES-2026-11-04-CRUZAMENTO-BLUMENAU.md`, `scripts/cruzar_mendeley_blumenau.py` | **101 das 102 datas já estavam no projeto.** A tabela não traz cheia nova; vale como **confirmação independente** do que o projeto tem e como prova de que a lista pública de Blumenau mistura três réguas (IBGE até 2001, régua antiga 2008–2011, régua de hoje desde 2013) |
| **Dois números a conferir na tabela deles, não na nossa** | 1852: 10,30 m (a fonte original diz 16,30); 2022: 9,40 × 9,41 | mesmo doc | Nada muda no projeto; serve se um dia a tabela for citada |
| **Índice de fontes atualizado** | uma linha por fonte nova, com status (funciona / descartada / pendente) | `docs/fontes-tempo-real.md`, `docs/fontes-academicas.md`, README | Quem chegar depois não refaz a busca |
| **Conferência pelo navegador** | o que este ambiente não alcança, aberto no seu Chrome | `docs/VARREDURA-FONTES-2026-11-04-NAVEGADOR.md` | Registro do que abre e do que não abre, com data |
| **Queda do portal de Itajaí registrada** | 30/10 ~07h30 → voltou até 04/11; 11 réguas sem leitura; erro no servidor deles | README | Lição: o `app.json` cai junto; não é redundância |

## 2. Fontes novas que FUNCIONAM e ainda não têm código

| Fonte | O que dá | O que seria preciso | Regra que vale |
|---|---|---|---|
| **Defesa Civil de SC — `wp-json` / `feed`** | avisos e alertas oficiais, com data e texto (5.098 posts de Alerta, 1.040 de Aviso, 802 de Monitoramento) | um coletor pequeno que filtre as categorias 6 e 7 e procure "Vale do Itajaí", "Foz do Itajaí", "Litoral Norte" no texto; mostrar no chat e na tela "Fontes" como **aviso da DCSC, por região** | o texto só diz a região, nunca o município; não vira faixa nem cor |
| **SGB — `gestaoterritorial/inundacao`** | suscetibilidade a inundação (Alta/Média/Baixa) por município: Blumenau, Brusque, Gaspar, Ilhota, Itajaí, Navegantes, Taió, Timbó, Apiúna, Benedito Novo, José Boiteux, Luiz Alves, Rodeio | consulta REST por município; camada opcional na "minha rua" | **contexto, nunca cota** nem previsão |
| **SGB — `gestaoterritorial/risco`** | setores de risco alto/muito alto, inclusive Rio do Sul (set e nov/2025), Itajaí (2012), Navegantes (2018), Brusque e Gaspar (2018–19) | idem | idem |
| **Canais oficiais da DC de Itajaí** | WhatsApp, X, Instagram | links na tela "Fontes" de Itajaí | não é dado; é onde o aviso oficial chega |

## 3. O que a varredura FECHOU (não precisa procurar de novo)

- Não existe sistema de alerta hidrológico do SGB/CPRM para a bacia do Itajaí.
- Não há portal de nível em Navegantes, Pomerode, Benedito Novo, Apiúna, Lontras ou Laurentino: essas cidades seguem só
  pela rede estadual.
- Não há marégrafo público do porto de Itajaí além do que já entra (Cabeçudas, via portal de Itajaí e UNIVALI).
- Não há dado ao vivo da Barragem Norte; o que existe é o registro de uma comporta não operacional (ALESC, 2026) e o
  contrato de recuperação.
- As manchas de inundação do SGB não cobrem a bacia; o GeoNode da FURB é do inventário florestal, sem enchente; o
  recorte CEMADEN do geoportal do SGB é de Alagoas.
- Rios On-Line da Epagri continua fechado; API do INMET continua só com acordo (C31 enviado).

## 4. O que veio junto nesta semana (fora da varredura)

- **Coletor da rede estadual mais resistente (#561, em produção desde 04/11 12h47 UTC):** se a DCSC bloquear o
  `rio_alarmes` de novo, o site diz "classificação estadual indisponível" em vez de "não publicou", e os campos que
  continuarem liberados não se perdem. A DCSC liberou o campo entre 27/10 e 31/10; a coleta de hoje confirma
  `consulta: completa`, com faixa em 20 das 26 estações.
- **ArcGIS de Itajaí (#548):** confirmado, só com leitura, que o serviço das manchas históricas declara edição pública.
  Prints prontos para WhatsApp; comunicação é decisão sua.

## 5. Pendências que dependem de você

1. **Avisos da DCSC no chat** — aprovar o coletor (seção 2) ou deixar como está.
2. **Suscetibilidade/risco do SGB na "minha rua"** — aprovar como camada de contexto ou não.
3. **CEMADEN `mapservices`/`resources`** — recusam conexão da sua rede e daqui; do Actions o `robots.txt` também não
   respondeu (a próxima rodada grava o motivo — `docs/VARREDURA-FONTES-2026-11-04.md`, seção 12); resta testar da VPS, só leitura.
4. **Copernicus GFM/EMS** — **alcançável pelo Actions** (4ª rodada, 04/11: os quatro endereços respondem 200; daqui e da sua
   rede, nenhum abre). Falta ler o conteúdo: se há ativação do EMS para o Vale e o que a API do GFM dá sem cadastro
   (`docs/VARREDURA-FONTES-2026-11-04.md`, seção 12). Serviria para a extensão observada das cheias, como contexto.
5. **Tabela do Mendeley** — se quiser, citar nas notas dos registros de Blumenau como fonte de cruzamento (confiança
   média); nada a cadastrar.
6. Continuam de antes: C32–C35 (envio), C36 (destinatário), ArcGIS de Itajaí (comunicar ou não), pergunta à DCSC sobre
   o bloqueio do `rio_alarmes`.

## 6. O que NÃO mudou

`enchentes.json`, `estacoes.json`, cotas, avisos, bot e o que o site mostra. Nenhuma escrita em serviço externo;
nenhum e-mail enviado.
