# CEMADEN e INMET — investigação e estado dos coletores (02/09/2026)

Investigação feita pelo navegador (Chrome, Mapa Interativo do CEMADEN e API do
INMET). Resumo do que ficou pronto, do que espera credencial e do que depende do
usuário.

## CEMADEN — ✅ coletor pronto e ligado ao tempo real

**Endpoint:** o Mapa Interativo carrega JSONP estático de
`https://resources.cemaden.gov.br/dados/{311_24|327mi_24|332_24|333_24}.json?callback=estacoes`.
Sem auth. `fetch` do navegador bate em CORS; de script é um GET simples.

**Campos do registro bruto:** `estacao_cod` (ex. 420290901A), `estacao_id`,
`estacao_nome`, `estacao_munic` ("BRUSQUE-SC" — com o `-UF`), `estacao_uf`,
`estacao_latlon` ("[lat][lon]"), `icon` (flag_verde=ativo, flag_cinza=sem dado),
`lbl` (chuva acumulada em mm). **Não há carimbo por estação** — o arquivo `_24` é
o retrato do acumulado de 24 h vigente; por isso o coletor carimba a leitura com
a hora da coleta.

**Bacia do Itajaí:** 228 pluviômetros, 137 ativos. Por cidade (ativos):
Blumenau 14, Itajaí 10, Gaspar 5, Brusque 5, Ilhota 4, Pomerode 4, Ituporanga 3,
Ibirama 3, Guabiruba 3, Indaial 2, Botuverá 1, Taió 1, Vidal Ramos 1,
Rio do Sul 0. Catálogo com as 228 + coordenadas em
`data/cemaden-estacoes-bacia.json` — **é a "relação com coordenadas" que o pedido
LAI C7 pediu; já temos.**

**Não serve para nível:** as hidrológicas do CEMADEN na área são ~9, quase todas
inativas ou fora do Açu/Mirim; Acqua na bacia = 0. Só chuva. E chuva é
**contexto — nunca cota, nunca aviso sozinha.**

**Fuso:** UTC (declarado pelo CEMADEN). Casa com o contrato do projeto.

**No repositório:**
- `scripts/coleta_chuva_cemaden.py` — baixa as quatro regiões, desembrulha o
  JSONP, mapeia por município (sem o `-UF`) contra as cidades do projeto, ignora
  inativas (flag_cinza) e valores fora de faixa. Vínculo por município; Timbó de
  fora (afluente sem tela), como no `coleta_chuva_sc.py`.
- `scripts/teste_coleta_chuva_cemaden.py` — 22 testes das funções puras.
- `coleta_niveis.baixar_chuva_cemaden()` junta a chuva do CEMADEN à das outras
  fontes na mesma lista (o site já mostra o maior de vários por cidade). Falha
  isolada: uma coleta do CEMADEN fora do ar não derruba o nível.

## INMET — ⚠️ catálogo aberto, DADOS fechados (esperar a LAI C8)

- **Catálogo público, sem token:** `https://apitempo.inmet.gov.br/estacoes/T` →
  674 estações automáticas (código, nome, UF, lat/lon, altitude, início,
  situação). Testado: 200.
- **Na bacia (bbox): 6 estações** — 4 operantes: A868 ITAJAÍ (-26.951, -48.762),
  A863 ITUPORANGA (-27.418, -49.647), A870 RANCHO QUEIMADO, A861 RIO DO CAMPO;
  2 em pane: A817 INDAIAL, A806 FLORIANÓPOLIS.
- **Dados horários fechados:** a rota `/estacao/{ini}/{fim}/{codigo}` existe (não
  dá 404), mas devolve **204 vazio para qualquer período** (2024–2026, estações
  operantes), sem `WWW-Authenticate`. O INMET abriu o catálogo e passou a exigir
  credencial para os dados — o contrário do que as docs de 2022 diziam.
- Portanto o pedido **LAI C8** (protocolo 21210.009435/2026-61) é o caminho: o
  item 2 pergunta cadastro/token e procedimento para uso não comercial. Prazo
  22/09. Até lá, **INMET não entra no tempo real** — o coletor é trivial quando o
  token vier (a rota já está mapeada). Ressalva a exibir: "dados brutos, sem
  validação" (declarado pelo INMET).

## Maré da EPAGRI — depende do usuário

Pede cadastro pessoal no portal `dadosambientaispublicos` (o assistente não faz
login por outrem — ver `docs/fontes-tempo-real.md`, seção EPAGRI). Fica para o
usuário: abrir o portal logado, ver se há PCD de maré no estuário de Itajaí,
baixar 1 mês → aí o coletor é escrito e a maré medida entra na tela do Itajaí.

## Placar do que rende agora

1. **CEMADEN** → ligado ao cron. Chuva por bairro em 137 pontos. Pronto.
2. **INMET** → esperar a LAI C8. Nada a codar até o token.
3. **Maré EPAGRI** → depende do usuário abrir o portal logado.
