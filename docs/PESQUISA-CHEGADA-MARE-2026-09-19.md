# Pesquisa de chegada da cheia e simulação de maré

Consulta: 19/09/2026. Base do trabalho: `cdd4035` do repositório.

## Resultado

Encontrada uma evidência histórica nova para o projeto: **19 horas no evento de
2011**, relatadas no resumo de Balsanelli (UNIVALI, 2014). Não foi obtida uma
série de cheias pareadas que permita calcular uma média histórica confiável.
A calibração permanece pendente. Nenhuma faixa de `transito.json` nem nenhum
pico de `enchentes.json` foi alterado.

O cenário experimental de `/itajai` cruza um horário informado e uma faixa de
trânsito com a tábua astronômica. Não utiliza o caso de 2011 como ajuste, não
estima nível de inundação, não detecta picos em tempo real e não presume que
uma cheia da mesma altura repetirá o comportamento de outro ano.

## Fontes e evidências recuperadas

### 1. Balsanelli (2014), UNIVALI

[Resumo original](https://www.univali.br/Lists/TrabalhosGraduacao/Attachments/3791/Resumo%20TICT%20Roberto%20Balsanelli.pdf),
uma página. HTTP 200; PDF baixado, texto extraído e página renderizada e
conferida. Cópia em `data/brutos/balsanelli-2014-resumo.pdf`.

SHA-256: `6fa91a0856cba401300adda12a12a7116cf61d10d4388841d8877559479e27f1`.

O trabalho modela um trecho de 63 km e compara cenários com e sem maré. O resumo
distingue explicitamente 19 h nos dados reais de tempos produzidos pelo modelo.
É uma referência observacional publicada sobre **um evento**, não uma nova
extração da telemetria. Não fornece a série numérica nem todos os metadados
necessários à reprodução.

[Trabalho completo, endereço indexado](https://biblioteca.univali.br/pergamumweb/vinculos/pdf/Roberto%20Balsanelli.pdf):
texto recuperado pelo índice de busca, mas download direto e nova abertura
retornaram HTTP 404. A Figura 15 identifica TEPORTI/DC02 histórica; a Tabela 6
separa 19 h (Defesa Civil) de 23 h e 28 h (modelagem). Existe divergência de
data: o parágrafo da comparação menciona 09/09 às 02h, enquanto a discussão
anterior menciona 10/09 às 02h. Não corrigimos isso por inferência, não
reconstruímos timestamps e não importamos um pico a partir dessa ambiguidade.
Também não equiparamos o código histórico à estação atual por semelhança do nome.

### 2. Portal atual de Itajaí

[Rios](https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios):
HTTP 200, resposta com `props.estacoes` no atributo público `data-page`.
As 11 estações DC expõem `serie_12_h`; DC01 e DC02 continham 70 pontos cada
na consulta. O JavaScript público usa esse campo para os gráficos. Não foi
localizada consulta histórica por intervalo nessa tela/código. Isso não
prova que a Defesa Civil não tenha um acervo interno ou outro serviço.

Essa janela recente não serve para calibrar as grandes cheias. O relatório
não trata flutuações de maré ou água baixa como tempo de propagação de cheia.

### 3. Lemfers e Pacheco Tena, Itajaí-Mirim

[Artigo da ABRH](https://files.abrhidro.org.br/Eventos/Trabalhos/60/PAP022601.pdf),
PDF recuperado com HTTP 200. Descreve séries de 2011 obtidas da Defesa Civil
e ANA e filtragem do efeito da maré. Indica onde procurar a série original,
mas não entrega um segundo evento independente para Blumenau → Itajaí.

### 4. Acervo já existente e pesquisa complementar

O `enchentes.json` desta revisão tem 117 registros de Blumenau, quatro com
data completa e hora, e nenhum de Itajaí. Foram lidos os levantamentos locais
da ANA, DCSC e auditorias de Itajaí. A consulta histórica da ANA anteriormente
documentada não resolveu picos instantâneos de eventos antigos. A estação
estadual de chuva de Blumenau não deve ser promovida a régua de rio.

Buscas adicionais nos portais municipais por picos de 2011, 2013 e 2023,
TEPORTI e telemetria não produziram nesta rodada séries horárias pareadas.
O [boletim municipal de 06/06/2017](https://itajai.sc.gov.br/noticias/17590/alagamentos-atingem-45-ruas-na-cidade-de-itajai-145-residencias-permanecem-em-alerta)
traz leituras e referências de Blumenau/Brusque e tendência em Itajaí,
mas não um par de picos identificados no município de Itajaí.

### 5. Referência para cenário, sem calibração

[JICA 2011, seção 3.5.4](https://openjicareport.jica.go.jp/pdf/12043659_02.pdf)
resume hidrogramas de projeto em 14–17 h de diferença entre Blumenau e Itajaí.
Essa é a faixa explicitamente identificada como estudo na interface. Não é
média de observações, intervalo probabilístico nem limite universal; o próprio
caso de 2011 localizado não cabe nela. Não ampliar a faixa para 14–19 h juntando
uma simulação e uma observação isolada.

## O que permite concluir a calibração

Solicitar/obter séries de Blumenau e das estações do Açu em Itajaí,
preferencialmente nos eventos de setembro/2011, setembro/2013, junho/2014,
outubro/2015 e outubro/novembro/2023, com janela anterior e posterior a cada
cheia. Não presumir que toda estação já existia nesses anos.

Campos necessários: código e coordenadas da estação, data/hora com fuso,
nível, unidade e referência, frequência de amostragem, qualidade, falhas,
mudanças de régua e histórico do instrumento. Para Itajaí, obter maré observada
e registrar o método de separação entre oscilação marítima e onda fluvial.
TEPORTI, CEPSUL e Santa Regina devem ser analisadas separadamente.

Parear a mesma cheia, verificar lacunas e picos largos/múltiplos, calcular o
atraso entre picos compatíveis e preservar incerteza de amostragem. Exigir pelo
menos cinco eventos independentes por par de estações como portão mínimo do
projeto, não como garantia estatística. Comparar média, mediana e amplitude;
testar o desempenho em eventos não usados no ajuste antes de chamar de previsão.

`scripts/calibrar_chegada_itajai.py` é somente leitura: recusa relatos,
timestamps sem fuso, metadados ausentes, duplicatas e séries/maré não conferidas.
Agrupa por par de estações; só calcula estatísticas descritivas com pelo menos
cinco eventos conferidos. Não grava `transito.json` nem autoriza previsão.

## Comportamento da simulação

- Entrada de data/hora explícita em Brasília; nenhuma leitura atual é promovida a pico.
- Faixa JICA identificada como estudo ou intervalo hipotético informado pelo usuário.
- Datas impossíveis, faixa invertida, zero, ponto único e valores não finitos são recusados.
- Coincidência significa preamar **dentro** da janela, incluindo seus limites.
  Não utiliza a margem de ±2 h do módulo antigo como se fosse evidência física.
- Exige extremos alternados que cerquem toda a janela e não tenham lacunas >12 h.
  Sem cobertura, informa tábua insuficiente; nunca conclui ausência de coincidência.
- Alturas são dos extremos astronômicos publicados sobre o NR. Não interpola uma
  altura exata de chegada, não soma réguas e não prevê contribuição meteorológica.
- Ausência de pico de maré na janela não é sinal de segurança.
- Alterar qualquer entrada apaga o resultado anterior até nova simulação.

O caso de 2011 permanece visível como evidência pendente em
`data/historico-chegada-itajai.json`, separado da faixa de estudo.

## Verificação da implementação

- 603 testes TypeScript aprovados; build TypeScript/Vite aprovado.
- Sete testes Python do auditor de calibração aprovados; ruff aprovado.
- Validador do acervo: zero erros, 13 avisos preexistentes.
- Teste de navegador do novo painel: 390 px em Asia/Tokyo e 1280 px em
  America/Sao_Paulo. Conferidos mudança de dia, tábua insuficiente, faixa
  invertida, troca de hipótese e descarte de resultado antigo. Sem overflow
  horizontal nem erro de página. Capturas desktop/celular inspecionadas.
- Teste de fumaça aprovado, inclusive sem acesso às fontes externas.

Reproduzir após o build, a partir de `web/`:
`node testes-navegador/simulacao-chegada.mjs`. A CI executa esse
teste explicitamente, além dos testes de lógica e Python.

No Windows deste ambiente o Node do sistema é antigo; os testes/build foram
executados com Node 24.19.0 e as versões fixadas no lockfile. Nenhuma dependência
ou lockfile foi alterado.
