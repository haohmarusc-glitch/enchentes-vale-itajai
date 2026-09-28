# Corpo bruto do portal novo de Itajaí

Fonte: https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios

Consulta declarada no corpo: 2026-09-19T16:38:08+00:00 (13h38min08 de Brasília).

- `itajai-novo.html`: resposta original, 87.637 bytes, obtida por curl no PC, sem executar JavaScript.
- `itajai-novo.json`: atributo `data-page` do elemento `#app`, decodificado como JSON e formatado. É uma extração do HTML, não resposta de endpoint JSON independente.
- O corpo contém 11 estações em `props.estacoes`, com códigos DC01 a DC11. Esta resposta é do município 1, Itajaí. Não pressupor que também contenha Brusque, Blumenau ou Rio do Sul.

## Contrato observado

O HTML usa `div#app[data-page]`. Um parser HTML decodifica as entidades do atributo; depois basta aplicar `json.loads`.

Campos relevantes de cada estação:

- `id`, `codigo`, `nome`, `municipio_id`, `fonte`, `latitude`, `longitude`;
- `nivel_rio_m`: nível numérico em metros;
- `medido_em`: data ISO com offset explícito +00:00, em UTC;
- `qualidade.nivel_rio_m.estado` e `qualidade.nivel_rio_m.medido_em`: qualidade e horário específicos da grandeza;
- `atualizacao_esperada_segundos`;
- `atencao_m`, `alerta_m`, `emergencia_m`;
- `tendencia`, `situacao`;
- `serie_12_h`: pontos com `medido_em` e `nivel_rio_m`.

Normalizar os códigos DC01 → DC-01 somente através de associação explícita com as estações existentes. Converter a medição UTC para Brasília antes de gravar `medido_em` sem offset no contrato antigo do repositório. Não usar `props.consultadoEm` para renovar a idade da medição. Não extrair níveis com regex sobre o HTML inteiro: cada estação contém vários valores históricos.

## Cotas divergentes: pendência adicional

Comparação com os valores exibidos pelo site auditado anteriormente em 19/09. Não é comparação com uma revisão posterior às correções anunciadas pelo usuário.

| Régua | Site auditado: atenção / alerta / emergência | Portal novo: atenção / alerta / emergência |
|---|---|---|
| DC01 | 1,16 / 1,36 / 1,56 m | 1,21 / 1,61 / 1,75 m |
| DC07 | 1,00 / 1,35 / 1,65 m | 1,00 / 1,40 / 1,50 m |
| DC08 | 1,80 / 2,30 / 2,89 m | 1,70 / 2,30 / 2,89 m |
| DC09 | 1,12 / 1,32 / 1,52 m | 1,22 / 1,42 / 1,62 m |

As outras sete trincas coincidem. Preservar as duas fontes e conferir revisão, instrumento e significado antes de substituir. Esta divergência não autoriza remover as restrições de aviso das réguas de estuário.

## Barragens: encaminhamento da auditoria

Para o texto, usar por exemplo: **“Chuva equivalente ao volume de armazenamento: aproximadamente 80 mm (JICA, 2011). Não é um limiar de chuva para enchimento.”**

Fonte primária: JICA, 2011, seção 3.2.2 e tabela 3.2.4, https://openjicareport.jica.go.jp/pdf/12043659_02.pdf . A equivalência é capacidade de armazenamento dividida pela área de drenagem.

A divergência de capacidade deve ficar registrada como pendência de conciliação:

| Barragem | JICA 2011, armazenamento bruto | Asthon, campo capacidade_maxima, consulta da auditoria |
|---|---:|---:|
| Oeste | 83 hm³ | aproximadamente 99,96 |
| Sul | 93,5 hm³ | aproximadamente 104,03 |

Endpoint consultado: https://public.asthon.com.br/public/dams?city_id=4214805 . A resposta preservada está em `enchentes-auditoria-2026-09-19/evidencias/fonte-barragens.json`.

Não concluir apenas desses números que houve ampliação, nem que ambos os campos representam o mesmo volume ou referência operacional. Confirmar unidade, volume bruto/útil/de contenção, nível de referência e data de vigência com documentação do operador. Identificar as fichas atuais como referência histórica de 2011 enquanto isso. Não recalcular os percentuais publicados pela Asthon usando o volume histórico da JICA.

Esta entrega não alterou coletores, cotas ou produção.

## Conferência de 27/09/2026

Captura feita pelo GitHub Actions, porque o ambiente das sessões de código recebe 403 do proxy para o host do portal. Fluxo `.github/workflows/capturar-portal-itajai.yml`, run [36350320996](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/actions/runs/36350320996), 21h04 UTC. O corpo voltou pelo log em gzip+base64 e foi remontado com o sha256 conferido nos quatro arquivos. Manifesto: `data/brutos/itajai-portal-captura-2026-09-27.json`.

| Página | HTTP | Bytes | Estações | 19/09–21/09 |
|---|---:|---:|---:|---:|
| Itajaí (`municipio_id` 1) | 200 | 179.632 | 11 | 87.637 |
| Brusque (2) | 200 | 15.469 | 1 | 44.334 |
| Blumenau (3) | 200 | 15.463 | 1 | 37.438 |
| Rio do Sul (4) | 200 | 15.430 | 1 | 44.355 |

**O que continua igual, e é o que o projeto usa:**

- Os mesmos onze códigos, DC01 a DC11, todos a 0 m da coordenada do cadastro.
- As mesmas cotas de 19/09 nas onze. As quatro divergências com o PLANCON v17 (DC-01, DC-07, DC-08, DC-09) persistem idênticas. O cadastro segue no v17.
- Leituras com `qualidade.nivel_rio_m.estado = "atual"`, cadência declarada de 600 s, `serie_12_h` com 71 a 73 pontos.
- `coleta_itajai_portal.py` lê as onze sem nenhum ajuste.
- Brusque, Blumenau e Rio do Sul: uma estação cada, mesmo código, fonte e cotas, e ainda **sem coordenada**. Continuam fora.

**O que mudou na forma:**

- **Campo novo `historico_monitoramento`** em cada estação de Itajaí: vinte registros com `nivel_rio_m`, `variacao_nivel_m`, `tendencia_nivel`, `tendencia_chuva` e seis janelas de chuva (`chuva_10_min_mm` a `chuva_48_h_mm`), em UTC com offset. É o que dobrou o tamanho da página. O coletor não o lê, e há teste travando que a leitura continua com as mesmas cinco chaves.
- **A moldura "Situação atual em Itajaí" saiu do HTML servido.** As páginas dos outros municípios caíram para cerca de 15 KB, só o `data-page`. A armadilha do cabeçalho de outra cidade passou para o navegador; a regra de conferir `props.municipioId` continua valendo igual.

**Chuva das réguas de Itajaí: existe no portal, não foi ligada.** As onze declaram `capacidades: ["chuvas", "rios"]`, e o histórico traz as janelas de chuva. Na captura estavam todas em zero, num dia seco, então não há como distinguir sensor parado de ausência de chuva. Ligar exige uma captura com chuva real para conferir coerência entre estações, como o coletor da rede estadual já faz.

Esta conferência não alterou coletor, cotas nem cadastro. Os testes estão em `scripts/teste_coleta_itajai_portal.py`, classe `TestCapturaDe27DeSetembro`.
