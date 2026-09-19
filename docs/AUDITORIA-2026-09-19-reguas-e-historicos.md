# Auditoria das réguas e dos históricos de enchentes

**Data da consulta:** 19/09/2026  
**Escopo:** auditoria pelo Chrome, com consulta aos portais oficiais, Instagram e dados do repositório. Nenhum dado ou configuração do sistema foi alterado. Este documento registra os resultados da consulta; as leituras dos portais podem mudar.

O diagnóstico é que existem problemas diferentes: identificação da régua, leituras antigas, cotas conflitantes e históricos sem referência comprovada.

## 1. Brusque: existe medição, mas a régua consultada é da DCSC

Foi aberta e capturada a estação selecionada **Ponte Estaiada – DCSC** no portal municipal. Ela mostrava **1,90 m em 19/09 às 19h**. O monitor de Itajaí identifica a estação de Brusque como **MKS DCSC-00019**. Portanto, estar no site municipal não comprova uma régua municipal independente.

Fonte: [Estação oficial DCSC](https://defesacivil.brusque.sc.gov.br/estacao/ver/79).

Há também a **Ponte Estaiada – ANA**, com **1,10 m e atualização em 08/09**. São fontes distintas, com limites diferentes:

| Fonte | Atenção | Emergência |
|---|---:|---:|
| DCSC | 3 m | 5 m |
| ANA | 4 m | 7 m |

O cabeçalho do portal ainda apresentava outra leitura ANA, de **04/09**. Essa mistura de fontes e datas ajuda a explicar a confusão. **Não se deve aplicar os limites da ANA à leitura DCSC.**

Fonte: [Estação ANA](https://defesacivil.brusque.sc.gov.br/estacao/ver/4).

A captura da estação está conferida; a existência de uma régua municipal independente continua **não comprovada**. A captura foi apresentada na conversa e não está incorporada neste arquivo.

## 2. Itajaí: as quatro divergências continuam no portal atual

Foram comparados os valores registrados na auditoria do Plano v17 com as legendas do monitor atual. Valores em metros, na ordem **atenção / alerta / emergência**:

| Estação | Plano v17 | Portal atual |
|---|---|---|
| DC01 — CEPSUL | 1,16 / 1,36 / 1,56 | **1,21 / 1,61 / 1,75** |
| DC07 — Murta Portal | 1,00 / 1,35 / 1,65 | **1,00 / 1,40 / 1,50** |
| DC08 — Canhanduba | 1,80 / 2,30 / 2,89 | **1,70 / 2,30 / 2,89** |
| DC09 — Murta Lídia Puel | 1,12 / 1,32 / 1,52 | **1,22 / 1,42 / 1,62** |

O site ainda apresenta o plano atualizado em **22/12/2025** como vigente. Não foi encontrada, nas fontes consultadas, uma explicação formal que concilie essas diferenças. **A divergência está confirmada; qual documento substitui o outro permanece sem comprovação.**

Fontes: [Monitor atual](https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios) · [Plano de contingência](https://defesacivil.itajai.sc.gov.br/plano-de-contingencia).

Outro achado importante: **o endereço antigo `/monitoramento/nivel-rios` retorna 404**. Isso exige verificar o endereço usado pelo coletor, mas não basta para afirmar que o coletor do site está quebrado.

## 3. Itajaí sem histórico: eventos encontrados, mas sem picos suficientes para preencher o arquivo

O `enchentes.json` consultado tem **zero registros de Itajaí**. A Defesa Civil disponibiliza histórico e mapas de inundação, mas isso não fornece automaticamente um pico com **data, estação e referência de medição**.

Fonte: [Histórico oficial](https://defesacivil.itajai.sc.gov.br/historico-de-inundacoes).

Um boletim municipal cita **12,60 m em 2011**, mas identifica esse valor como **Blumenau**, não Itajaí. Importá-lo como pico de Itajaí seria incorreto.

Fonte: [Boletim oficial](https://itajai.sc.gov.br/noticias/17590/alagamentos-atingem-45-ruas-na-cidade-de-itajai-145-residencias-permanecem-em-alerta).

## 4. Os 147 bloqueados não dependem todos da mesma solução

Contagem conferida no arquivo atual do repositório:

| Referência cadastrada | Registros |
|---|---:|
| Régua | 68 |
| IBGE | 72 |
| Sem referência | 75 |
| **Total** | **215** |

Os **147 = 72 + 75**. Os 75 sem referência estão distribuídos entre Blumenau, Brusque, Rio do Sul, Taió e Timbó.

Fonte: [Arquivo `enchentes.json`](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/blob/main/data/enchentes.json).

A verificação do HidroWeb **já foi tentada em 08/09**, conforme a documentação. Retornou médias diárias para os eventos históricos consultados; elas não validam picos instantâneos nem comprovam a conversão fixa de 20 cm. Portanto, **os 72 não são considerados destravados**. Essa conclusão se baseia na tentativa documentada, e não em uma nova execução da consulta histórica nesta auditoria.

Fonte: [Auditoria da ANA](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/blob/main/docs/ANA-API-2026-09-08.md).

Há ainda uma inconsistência adicional: a tabela oficial atual de Blumenau informa **12,60 m para 2011**, enquanto o histórico adotado no projeto usa 12,80 m. Isso precisa ser conciliado antes da liberação.

Fonte: [Tabela oficial de Blumenau](https://defesacivil.blumenau.sc.gov.br/p/enchentes).

## 5. Consulta ao Instagram

Foram consultados os perfis oficiais das duas cidades. O boletim de Brusque de 01/09 divulga uma **projeção de 5,50 m**, sem identificar suficientemente a referência para resolver essa pendência. As publicações consultadas de Itajaí também não esclarecem as quatro cotas.

Fontes: [Publicação de Brusque](https://www.instagram.com/defesacivilbrusque/p/DcvZWNoxu1x/) · [Defesa Civil de Itajaí](https://www.instagram.com/defesacivil_itajai/).

## Recomendações da auditoria

- Priorizar a conferência do **endereço do coletor de Itajaí**.
- Manter as fontes de Brusque separadas.
- Preservar os bloqueios históricos até comprovar estação e referência.

A pesquisa avançou nas evidências, mas não justifica preencher medições ou liberar os 147 registros automaticamente. As recomendações não foram implementadas.
