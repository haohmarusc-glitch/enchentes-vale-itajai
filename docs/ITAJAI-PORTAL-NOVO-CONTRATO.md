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
