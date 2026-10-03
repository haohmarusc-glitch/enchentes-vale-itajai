# As cidades que não apareciam como o cartão de Blumenau (03/10/2026)

Pergunta do Jefferson: *"as outras cidades são como a imagem?"* — a imagem era o cartão "Agora" de Blumenau,
com faixa, número e régua colorida. Com as leituras reais das 16h de 03/10, só quatro das dezoito cidades
apareciam assim: Taió, Rio do Sul, Ascurra e Blumenau. Pedido seguinte: *"faça os 3 itens das cidades"*.

## 1. Brusque: religada à DCSC-00019

- **Causa:** a régua municipal saiu do ar com o portal novo de Itajaí em 19/09.
- **Correção:** a DCSC-00019 é a mesma régua, provado em 1.287 pares com no máximo 3 cm de diferença. Ela entra
  como leitura com cota pelo `coleta_estadual_com_cota.py`.
- **Detalhes:** `docs/BRUSQUE-DCSC-00019.md`.
- **Efeito:** depois do deploy na VPS, Brusque volta a ter faixa, número e régua desenhada.

## 2. Indaial, Vidal Ramos e Gaspar: por que a coleta parou

Captura feita pelo GitHub Actions em 03/10 às 19h13 UTC, run
[37147113197](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/actions/runs/37147113197). Doze de
treze fontes responderam 200. Os corpos lidos foram remontados com o sha256 conferido.

| cidade | o que parou | onde está o problema |
|---|---|---|
| **Gaspar** | A estação 21 da Defesa Civil de Gaspar publica o Açu pela última vez em **02/10 às 06h04**. A tabela do município não traz mais a linha do Açu, só o Ribeirão Belchior e pluviômetros. | **Na fonte.** O coletor lê a página certa; ela é que não atualiza. Lembrete: a VPS não alcança o site de Gaspar desde 31/08, e a leitura chega pela ponte do PC (`enviar_gaspar_pc.py`), que recusa leitura com mais de 3 h. |
| **Vidal Ramos** | A estação `bd65df3e…` **não está mais** no painel da Asthon (`panel?city_id=4214805`), que lista 25 estações. A última leitura é de 11/09 às 15h37. | **Na fonte.** A Asthon tirou a estação do painel. O coletor não tem o que ler. |
| **Indaial** | O documento da Defesa Civil de Indaial tem como última medição **12/09 às 22h** (o coletor da VPS ainda o lê). | **Na fonte**, que só é atualizada à mão durante as cheias. A captura não baixou o documento: o robots.txt do Google recusa o caminho (pendência antiga: o coletor de produção não consulta o robots.txt). A estação estadual DCSC-00006 está sem leitura agora. |

Nenhum dos três tem conserto no nosso código. O que mudou para quem olha a tela está no item 3:
- Vidal Ramos passa a mostrar a faixa estadual da DCSC-00024.
- Indaial mostra a estadual quando a DCSC-00006 voltar a medir.

## 3. A faixa da Defesa Civil de SC nas cidades sem régua municipal

**O dado já existia.** Desde 14/09, o `coleta_nivel_sc.py` guarda, por estação, a faixa que a própria Defesa
Civil de SC publica (`rio_alarmes`, validada no coletor). O Monitor já pintava o pino com ela, com traço
tracejado. As telas da versão 2 não mostravam.

**Agora** o cartão "Agora", a lista do rio e as linhas de cidade mostram essa faixa nas cidades sem leitura
municipal de agora:
- o chip diz **"Atenção · Defesa Civil SC"** (ou Normal, Alerta, Emergência), com borda tracejada;
- o número é o da rede estadual;
- o texto diz que a régua tem zero próprio e não se compara com as cotas da cidade.

**Regras, travadas em `web/src/dados/usarAoVivo.test.ts`:**
- A municipal manda: com leitura municipal de agora, a faixa estadual não aparece.
- A faixa da cidade (`faixa`) continua `sem-dado`. A estadual fica num campo separado (`faixaEstadual`), que
  frase, WhatsApp e aviso não leem.
- Estadual velha, sem carimbo ou sem faixa publicada: sem cor.
- Com a leitura municipal velha (Indaial), o cartão diz também o nível estadual de agora, quando houver.

**Com os dados das 16h de 03/10, a Defesa Civil de SC classificava:**
- Ituporanga: Emergência (4,29 m);
- Ibirama: Atenção (2,26 m);
- Botuverá: Atenção (3,37 m);
- Timbó, Rio dos Cedros e Vidal Ramos: Normal;
- Ilhota: sem faixa configurada.

A tela mostra essas classificações como sendo da Defesa Civil de SC, não do projeto.
