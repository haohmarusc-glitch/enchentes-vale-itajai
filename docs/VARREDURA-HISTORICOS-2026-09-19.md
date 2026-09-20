# Varredura de históricos para Blumenau → Itajaí

Consulta em 19/09/2026, com busca web, Chrome, catálogo bibliográfico,
download de PDFs e conferência de tabelas. Complementa
`PESQUISA-CHEGADA-MARE-2026-09-19.md`.

## Resultado concreto

Recuperado o **trabalho completo de Balsanelli (2014), 113 páginas**, cujo
endereço antigo retornava 404. O Chrome permitiu pesquisar no catálogo atual
da UNIVALI e encontrar o acervo **214799**, com novo link de download:

- [Registro no catálogo](https://biblioteca.univali.br/acervo/214799).
- [PDF atual](https://biblioteca.univali.br/pergamumweb/download/5086AA4AABCF7886E06318C9010AF340.pdf).
- Cópia: `data/brutos/balsanelli-2014-completo.pdf`, 3.280.011 bytes.
- SHA-256: `bec9e84fcf1e623996d8aba0b33b2f37d6cabdfe3bba9a74ddec2c5eb86c18f2`.

**Ainda não há pares novos aprovados para calibração.** Recuperar o documento
removeu uma barreira de acesso, mas revelou limitações da amostragem que precisam
ser preservadas.

## O que o documento completo acrescenta

1. **Tabela 8, página 101:** 16 registros de nível e vazão em Blumenau,
   de 07 a 14/09/2011, às 07h e 17h. A tabela atribui a fonte à ANA (2011).
   Transcrição em `data/brutos/balsanelli-2014-tabela8.json`, conferida contra
   a página renderizada. É uma série publicada usada como condição de contorno,
   com intervalos de **10 e 14 horas**, não a telemetria completa.
2. Três vazões têm asterisco e são **estimadas por ajuste exponencial**, segundo
   a nota da tabela. Esse marcador foi preservado na transcrição.
3. O maior nível desta tabela é **12,48 m em 09/09 às 07h**. Esse é o máximo
   das amostras apresentadas, não comprovação da hora do pico instantâneo.
   O espaçamento das leituras pode deslocar a identificação do pico em horas.
4. **Tabela 6, página 77:** mantém 19 h na coluna Defesa Civil e 23 h/28 h
   nas colunas de simulação. A página 65 escreve 10/09 às 02h; a página 77
   escreve 09/09 às 02h. A divergência existe no PDF original, não apenas no índice.
5. **Figura 47, página 99:** apresenta a curva da TEPORTI/DC02 histórica,
   bruta e filtrada, mas não uma tabela com a série de Itajaí. Não digitalizamos
   o gráfico como se fosse telemetria original.
6. A página 51 descreve filtro Lanczos com corte de 40 h. As páginas 49–50
   e 83 explicitam dificuldades com a DC01/Marejada e influência do Mirim;
   o estudo também não incorporou o rio Luís Alves. O destino modelado é
   TEPORTI, não uma hora única de chegada válida para todos os bairros ou a foz.

**Implicação:** 19 h permanece como relato de um caso, sujeito à conferência.
Não foi promovido a média nem usado para ajustar o simulador. A hora de máxima
amostra de Blumenau também não foi promovida a pico observado validado.

## Outros acervos e resultados

| Fonte | Material localizado e período | Utilidade e pendência |
|---|---|---|
| [Epagri/Ciram — download](https://ciram.epagri.sc.gov.br/dadosambientaispublicos/) | Portal conferido no Chrome: dados horários, incluindo maré, dos últimos 24 meses; exige login | Pode apoiar eventos recentes, mas não entrega automaticamente 2011/2013/2023 nesta data. Não foi feito cadastro nem obtida série autenticada. |
| [Epagri — série temporal](https://ciram.epagri.sc.gov.br/index.php/solucoes/solicitacao-de-dados/) | Canal específico de solicitação: `dadosciram@epagri.sc.gov.br` | Caminho para períodos mais antigos. Ainda é necessário confirmar estações, cobertura, resolução e condições de fornecimento. Nenhuma solicitação enviada nesta rodada. |
| [Truccolo, 2009 — UFRGS/BDTD](https://bdtd.ibict.br/vufind/Record/URGS_5c98d3902dd5c08da01193957ff05dd9) | Metadados descrevem níveis horários em quatro pontos a 1,5/18/35/55 km da desembocadura, dez/1999–dez/2000 | Forte pista de acervo estuarino. O PDF no Lume falhou por certificado nesta consulta; os arquivos numéricos não foram recuperados. Não demonstra por si só cinco cheias comparáveis. |
| [Pavo-Fernández et al., 2023 — UNIVALI](https://periodicos.univali.br/index.php/bjast/article/view/19245) | PDF recuperado, 8 páginas. ADCP registra também nível, com perfis a cada 10 min; campanhas de 2007–2008 e 2011 | Procurar acervo do Laboratório de Oceanografia Física. A página 27 informa fim em 01/10/2011, mas em seguida menciona análise de novembro/2011: cobertura precisa ser esclarecida. Sem suplemento numérico encontrado na página consultada. |
| [IDEM/DHN — Itajaí](https://idem.dhn.mar.mil.br/geonetwork/srv/resources/datasets/6c098fab-6529-4864-9552-d51a185c706d) | Metadados indexados de observações 01/04/2010–01/04/2011, 10 min, referências de régua e RN | Ajuda a identificar acervo e datum. O intervalo termina antes da cheia de setembro/2011. Download direto falhou; não temos essa série. |
| [Fuchs et al., IHR, 2021](https://ihr.iho.int/articles/estimation-of-nautical-chart-datum-by-the-statistical-method-in-micro-and-meso-tidal-regime-an-alternative-to-the-balay-harmonic-method/) | Artigo usa maré horária de Itajaí de 31/03/1960 a 22/03/1961 | Evidência de acervo maregráfico antigo, útil para metodologia; não cobre as cheias recentes e não fornece par com Blumenau. |
| [Giacomelli et al., ABRH, 2024](https://files.abrhidro.org.br/Eventos/Trabalhos/241/IV-END0065-1-0-20240819-122719.pdf) | PDF recuperado, 4 páginas, hidrogramas de outubro/novembro de 2023 e fontes ANA/EPAGRI/DCSC/setor elétrico | Autores da Fractal e DCSC são outra pista para dados de 2023. A tabela de estações não inclui Itajaí. Não preencher o destino com o pico de Blumenau. |
| [Blumenau, boletim 09/06/2014](https://www.blumenau.sc.gov.br/secao/noticias/4711) | Prefeitura informa pico de 10,18 m às 06h de 09/06/2014 | Candidato a horário a montante para resgate do evento; falta série de Itajaí e metadados para pareamento. Não foi importado como par validado. |

O artigo de dragagem é também motivo para verificar mudanças de geometria:
ele compara condições anteriores e posteriores à dragagem de 2011 e relata
alteração na circulação. Inferência para o projeto: não assumir que décadas
distintas compartilhem o mesmo atraso apenas por terem nível semelhante em Blumenau.

## Buscas sem série utilizável nesta rodada

- Biluk e estações telemétricas: referências bibliográficas localizadas, mas as
  consultas seguintes no catálogo não exibiram resultados utilizáveis. Não
  concluímos que o trabalho inexista. Balsanelli foi recuperado pelo catálogo.
- CEOPS/FURB: páginas institucionais e estudos, sem exportação horária pareada
  Blumenau/Itajaí localizada. O inventário prévio do projeto permanece válido.
- Boletins de 2013, 2014, 2015, 2017 e 2023: buscas retornam muita previsão de
  maré e nível de cidades a montante. Isso não é medição do pico de Itajaí.
- Zenodo e buscas por dados estuarinos: resultados sem conjunto numérico
  adequado a este pareamento. Não é prova de inexistência de dados abertos.
- ArcGIS de Itajaí: revisão do inventário já existente confirmou que manchas,
  lâminas e terreno não substituem a série temporal de nível.
- ANA/DCSC: revisão dos levantamentos anteriores para evitar repetir consultas
  já documentadas e confundir chuva, médias diárias ou estações homônimas com
  níveis instantâneos no destino. Esta rodada não recuperou nova telemetria ANA.

## Próxima aquisição com maior valor

1. **COMPDEC Itajaí / UNIVALI:** séries brutas da TEPORTI/DC02 histórica e
   DC01/Marejada de 05 a 17/09/2011, mais ficha das estações e série usada no
   estudo. Confirmar datas, fuso e versão do filtro. Solicitar também cobertura
   dos eventos de 2013, 2014, 2015 e 2023 nas estações então existentes.
2. **ANA / AlertaBlu / acervo CEOPS:** série de Blumenau na maior resolução
   disponível para as mesmas janelas, mantendo a identificação da régua e
   distinguindo observações, médias e valores estimados.
3. **Epagri / UNIVALI / DHN:** maré observada simultânea e referências verticais.
   Tábua prevista e maré observada devem ficar em campos separados.

Texto técnico para um futuro pedido, ainda **não enviado**:

> Buscamos séries de nível com data/hora, fuso, unidade, identificação e
> coordenadas das estações, referência vertical, qualidade e lacunas, além de
> mudanças de instrumento/régua. Prioridade: 05–17/09/2011 e eventos de
> setembro/2013, junho/2014, outubro/2015 e outubro/novembro/2023. Para Itajaí,
> interessa distinguir as estações históricas TEPORTI/DC02 e DC01/Marejada
> das atuais. Precisamos da série bruta e, se houver, da série filtrada e método
> aplicado, para avaliar atraso entre picos de cheia e coincidência com maré.

A aquisição acima é o gargalo real. A varredura produziu uma fonte completa
e uma tabela recuperável, mas ainda não sustenta previsão calibrada.

## Verificação dos arquivos desta rodada

- PDF íntegro, hash registrado; páginas 77 e 101 renderizadas e conferidas.
- Transcrição com 16 registros e os três marcadores de vazão estimada preservados.
- Auditor de calibração continua com zero pares elegíveis e previsão não validada.
- JSONs lidos com sucesso, `git diff --check` sem erros e build TypeScript/Vite aprovado.
