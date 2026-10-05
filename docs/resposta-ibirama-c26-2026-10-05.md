# Resposta da Defesa Civil de Ibirama — C26

Recebida em 05/10/2026 às 14:55 BRT, do endereço institucional `defesacivil@ibirama.sc.gov.br`. Ela responde à
conversa de 13/09/2026 («Régua e cotas de referência para o monitoramento de enchentes em Ibirama») e ao lembrete
C26, enviado em 04/10/2026.

Este documento resume só os dados técnicos. O e-mail traz aviso de confidencialidade, então não se reproduzem
o texto da conversa nem os contatos pessoais.

## Informações recebidas

- **Régua:** as faixas de monitoramento do Rio Itajaí do Norte são lidas na estação **DCSC-00020**, na ponte
  Osvaldo Tadeu Beltramini.
- **Cotas de rua e manchas:** Ibirama não tem mapeamento de cotas de inundação. A COMPDEC atribui isso ao baixo
  histórico de inundação no município e diz que estudos mais aprofundados continuam necessários.
- **Faixas do PLAMCON:** os limites de observação, atenção e emergência são metragens históricas e aproximadas.
  O plano de contingência de 2026 está em ajustes finais.
- **Site:** a COMPDEC tem interesse em conhecer o site e pediu o cadastro.

## Incorporação

- **Feito em 05/10/2026, no cadastro de Ibirama em `data/estacoes.json`:**
  - `regua_das_cotas` = DCSC-00020 e `regua_das_cotas_fonte` citando esta resposta;
  - `cotas_pendencia` atualizada: a régua está resolvida, a tabela não.
- **Não feito, de propósito:** a resposta não diz qual tabela vale hoje. A de 2024 (3,00 / 3,50 / 4,00 m)
  continua só como histórico, pela decisão do Jefferson de 04/10/2026. Por isso:
  - `cotas_m` continua vazio;
  - a DCSC-00020 **não** entrou em `REGUAS_COM_COTA_PROPRIA`;
  - Ibirama segue com a leitura da rede estadual, sem faixa municipal.
- **Quando o PLAMCON 2026 sair com a tabela:**
  1. gravar as faixas em `cotas_m`, com a fonte;
  2. pôr a DCSC-00020 em `REGUAS_COM_COTA_PROPRIA` (`scripts/coleta_estadual_com_cota.py`). O teste do par já
     encontra a régua e a fonte escrita no cadastro.
- **Resposta à COMPDEC:** enviada em 05/10/2026, na mesma conversa, com a aprovação do Jefferson (Gmail, id
  `1a10d96037b29127`). Ela:
  - agradece a resposta;
  - confirma que o e-mail `defesacivil@ibirama.sc.gov.br` foi cadastrado no Access e manda o link do site. Por
    decisão do Jefferson: a regra de não pôr link em e-mail vale para quem não tem cadastro;
  - avisa que o site está em construção e pode ter erros, e pede sugestões;
  - diz que o site não substitui a Defesa Civil de SC nem a de nenhuma cidade (emergência: 199);
  - oferece ajuda no que estiver ao alcance.
