# Brusque volta a ter nível com cor: a régua é a DCSC-00019 (03/10/2026)

Pedido do Jefferson: *"faça os 3 itens das cidades"*. O primeiro era religar a régua de Brusque.

## O que tinha acontecido

- **Até 19/09/2026:** o site lia Brusque pela página antiga da Defesa Civil de Itajaí, estação "Brusque".
- **A troca:** em 19/09 a página mudou de endereço e de formato, e a leitura "Brusque" saiu do ar.
  - O portal novo publica Brusque (município 2), mas **sem coordenada**.
  - Por isso `coleta_itajai_portal.py` não a liga (`docs/ITAJAI-PORTAL-NOVO-CONTRATO.md`).
- **Desde então:** Brusque aparecia só com o número bruto da rede estadual (DCSC-00019), sem cor.

## Por que a DCSC-00019 pode pintar com as cotas de Brusque

1. **As cotas são da legenda desta estação.**
   - As cotas são atenção 3,00 m e emergência 5,00 m.
   - A Defesa Civil de Brusque as publica na legenda da estação "Ponte Estaiada – DCSC" do portal dela
     (`defesacivil.brusque.sc.gov.br/estacao/ver/79`).
   - Essa estação é repasse da DCSC-00019. Brusque não opera régua de rio própria.
2. **Par provado em 07/09/2026** por três leituras do mesmo minuto: 1,27 · 1,27 · 1,28 m.
3. **Reconfirmado em 03/10/2026** com a série guardada no servidor.
   - Para cada leitura "Brusque", foi tomada a leitura da DCSC-00019 a até 5 min dela.
   - Período: de 02/09 (início da série estadual) a 19/09 (fim da municipal).

| dias | pares | diferença "Brusque" − DCSC-00019 |
|---|---:|---|
| 02/09 a 19/09/2026, com as cheias de 10–12/09 | **1.287** | mediana **0,00 m** · 90% entre −0,01 e +0,01 m · máximo **0,03 m** |

Nenhum dia teve mediana fora de ±0,01 m. É a mesma régua, com a mesma escala.

**A ressalva antiga** ("Brusque, 01/09: offset ~0 às 17 h virou 1,9 m às 23 h") é de antes de a série estadual
ser guardada. Ela não se repetiu em 17 dias de pares, cheias incluídas. O mais provável é horário de publicação
diferente numa subida rápida, como aconteceu com a publicação de Blumenau na mesma página.

## O que mudou

- **Coletor:** `scripts/coleta_estadual_com_cota.py` ganhou a DCSC-00019 em `REGUAS_COM_COTA_PROPRIA`.
  - A leitura vai para `leituras` como "Brusque — Ponte Estaiada (DCSC-00019)", no Mirim, com `codigo` e
    `usar_para_cota: true`. É o mesmo caminho de Ascurra.
- **Testes:** `teste_coleta_estadual_com_cota.py` trava o par com o cadastro (`codigo_dcsc`, cota de atenção e
  `regua_das_cotas_fonte`) e o fuso.
- **Cadastro (`data/estacoes.json`, Brusque):** `regua_das_cotas_fonte` registra a reconfirmação, e
  `fontes_tempo_real` diz de onde vem a leitura agora.

## O que NÃO mudou

- **As cotas:** continuam 3,00/5,00. A divergência entre as três escalas publicadas para a DCSC-00019 segue
  aberta (`cotas_divergencia` no cadastro).
- **O site:** já lia a leitura com cota por cidade e não precisou de mudança. Quando a leitura chega, o número
  bruto deixa de aparecer.
- **O efeito só aparece depois do deploy:** o coletor da VPS precisa ser atualizado para começar a mandar a
  leitura (`scripts/deploy.sh`).
