# Registro na mão das ruas alagadas

Decisão do Jefferson em 05/10/2026: nenhuma fonte publica, com hora e de forma legível por robô, quando
cada rua alagou (`docs/GUARDAR-CHEIAS.md`, item 2). Então quem acompanha a cheia anota. Depois, a conta
"como estavam as réguas N horas antes" usa essas horas.

O registro **não é alerta, não vai para a tela e não muda faixa nem cota**. Serve para estudar a cheia
depois.

## Durante a cheia: a planilha

Abra o modelo `docs/modelos/ruas-alagadas.csv` no Google Planilhas ou no Excel. Funciona no celular.
Uma linha para cada coisa vista:

| Coluna | O que pôr | Exemplo |
|---|---|---|
| cidade | o nome da cidade | Itajaí |
| rua | como a fonte escreve | R. José Domingos Machado |
| ponto | trecho, esquina ou número, se a fonte diz | esquina com a Rua Brusque |
| bairro | se a fonte diz | São Vicente |
| data | dia/mês/ano | 12/09/2026 |
| hora | hora de Brasília, a do relógio daqui | 14:30 ou 14h30 |
| situacao | **começou a alagar**, **alagada**, **interditada** ou **liberada** | alagada |
| quando_e | **hora do fato** ou **hora da publicação** (ver abaixo) | hora do fato |
| precisao | **exata** ou **aproximada**; em branco vale exata | aproximada |
| lamina | altura da água, como a fonte descreve | na canela; 30 cm |
| fonte_tipo | **Defesa Civil**, **Prefeitura**, **imprensa**, **foto/vídeo** ou **relato** | Defesa Civil |
| fonte | de onde veio: boletim, link, descrição | Boletim 12 da Defesa Civil de Itajaí, 14h45 |
| confianca | em branco: o script põe a do tipo de fonte | |
| nota | qualquer observação | água vinda do ribeirão |

### A coluna que mais importa: `quando_e`

- **hora do fato:** a água estava lá naquela hora. Vale para a foto ou o vídeo com hora e para o boletim
  que diz *"às 14h a rua X alagou"*.
- **hora da publicação:** só se sabe quando a notícia ou o post saiu. A água chegou **antes**. A conta
  trata essa hora como limite, não como o momento.

Na dúvida, marque **hora da publicação**. Errar para esse lado não engana a conta.

### Confiança

Em branco, o script usa a confiança do tipo de fonte. Pode baixar, mas não pode passar do teto.

| Tipo de fonte | Confiança em branco | Teto |
|---|---|---|
| Defesa Civil, Prefeitura | alta | alta |
| imprensa | media | media |
| foto/vídeo | baixa | media, se a hora e o lugar foram conferidos |
| relato | baixa | baixa |

### Dado pessoal não entra

- Nada de nome, telefone ou e-mail de morador.
- Relato entra como *"relato de morador"*. O script recusa a linha que tiver telefone ou e-mail.

## Depois: importar

```bash
python3 scripts/ruas_alagadas.py --planilha cheia.csv --seco   # confere, não grava
python3 scripts/ruas_alagadas.py --planilha cheia.csv          # grava as linhas boas
```

- Cada linha recusada sai com o número e o motivo. As boas entram assim mesmo; corrija as outras e importe
  de novo.
- Linha já importada é ignorada. A importação **só acrescenta**: nada é apagado nem reescrito. Corrigir um
  registro é editar `data/ruas-alagadas.json` à vista, no commit.
- O CSV pode ser separado por vírgula (Google Planilhas) ou por ponto e vírgula (Excel em português).
- Para registrar uma linha só, sem planilha:

  ```bash
  python3 scripts/ruas_alagadas.py --cidade Itajaí --rua "R. José Domingos Machado" --data 12/09/2026 \
      --hora 6h30 --situacao alagada --quando-e "hora do fato" --fonte-tipo "Defesa Civil" \
      --fonte "Boletim da Defesa Civil de Itajaí"
  ```

- `scripts/validar_dados.py` aplica as mesmas regras ao arquivo. A CI reprova o que escapar.

## A conta

```bash
python3 scripts/nivel_antes.py --registradas                   # todas as ruas registradas
python3 scripts/nivel_antes.py --registradas "Domingos Machado" --horas 3 6 12
python3 scripts/nivel_antes.py --relatorio docs/NIVEL-ANTES.md # o relatório ganha a seção das ruas
```

Para cada rua registrada, a conta mostra:
- **as réguas da própria cidade naquela hora.** Itajaí tem onze, cada uma no seu zero.
- **em Itajaí, a maré mais próxima,** da tábua da Marinha.
- **a cota oficial da rua, quando existe uma rua com esse nome** em `data/cotas-ruas.json`. Serve para
  conferir a cota contra o que se viu.
- **as réguas rio acima N horas antes.** Itajaí é foz dos dois rios, então entram as do Açu e as do Mirim.

Exemplo do que a conta responde: "quando a R. José Domingos Machado alagou, como estavam Brusque, Blumenau
e a maré 6 horas antes?". Brusque só entra se a série inteira da VPS for lida (`--series`).
