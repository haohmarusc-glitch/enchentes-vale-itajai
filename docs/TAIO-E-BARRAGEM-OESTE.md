# Taió e a Barragem Oeste — achados de 03/09/2026

## 1. Taió TEM portal de Defesa Civil
`https://defesacivil.taio.sc.gov.br/` — descrição própria: *"Monitoramento em tempo real e informações
sobre nível de barragem e rio em Taió-SC"*.
**Ainda não explorado** (a extensão do navegador teve a permissão negada para o domínio).
É a 5ª cidade da bacia com portal próprio — ver `docs/PORTAIS-POR-CIDADE.md`.

Contatos citados na imprensa: Coordenador de Proteção e Defesa Civil **Márcio Farias**; chefe da Defesa
Civil **Jonata Retke**; Coordenadora Regional da Defesa Civil Estadual **Cleunice Forster**.

## 2. Pico histórico de Taió: 12,11 m em 09/10/2023
Superou a cheia de 2011, que era a maior recente. A água atingiu o **segundo piso** dos imóveis; bairro
mais atingido: **Victor Konder**. Cinco abrigos, 200 pessoas.
Em 03/11/2023 houve nova cheia com previsão de 10 m e **seis abrigos abertos, 182 pessoas** — algumas
famílias ainda no abrigo desde a cheia do mês anterior.
O projeto tem `data/tempo-real/leitura-manual-2026-08-31.json` com Taió a 5,40 m — para dimensionar:
o pico de 2023 foi **mais que o dobro** disso.

## 3. ⚠️ A BARRAGEM OESTE MUDA DE REGIME — e isso quebra qualquer previsão
Dois trechos de imprensa, ambos da Defesa Civil, descrevem o mecanismo:

> *"No momento, seis comportas da barragem estão fechadas e às 19h a sétima e última comporta será
> fechada."* — a barragem tem **7 comportas**, operadas uma a uma.

> *"Pelo fato de a barragem Oeste estar cheia e vertendo em mais de 1 metro há quase um dia, **a chuva que
> cai sobre as localidades acima de Taió não é mais retida pela estrutura**."*

**Isto é a informação mais importante deste achado.** A Barragem Oeste tem dois regimes:
- **Retendo:** a chuva a montante fica na barragem; Taió e Rio do Sul recebem menos.
- **Vertendo (cheia):** a barragem deixa de amortecer; a chuva de cima passa direto.

**Consequência para o site:** qualquer correlação chuva→nível ou montante→jusante no Itajaí do Oeste
**muda completamente** quando a barragem passa a verter. Um modelo calibrado no regime "retendo"
subestima drasticamente o regime "vertendo". É provavelmente parte da explicação para correlações fracas
no Alto Vale.

**O que o site precisa fazer:** exibir o **estado da barragem** (retendo × vertendo, e quantas comportas)
junto com o nível de Taió e Rio do Sul. Sem isso, o número do rio não diz o que vai acontecer.
O projeto já coleta o nível das barragens Oeste e Sul (Asthon, `dams`), mas **não o estado das comportas**.
⬅️ **Nova lacuna identificada.**

Também citado: *"Tem muita água do município de **Rio do Campo**"* — Rio do Campo está acima de Taió no
Itajaí do Oeste. Existe estação DCSC-00125 "Rio do Campo (H)", mas é de altitude (576 m), não régua.

## 4. ⭐ Rio do Sul tem páginas que o projeto não usou
O menu do portal (visto em resultado de busca) tem:
- **`index.php?r=soscota-rua/tabela`** — "Cota de Cheias por Rua", **555 itens, com botão "Exportar Dados"**
  e escolha de formato. **É a fonte exata dos nossos 555 registros** — e permite exportar em vez de raspar.
- **"Planilha Histórica Rio"** — série histórica do rio. O projeto não tem histórico de Rio do Sul.
- "Metragem Itajaí-Açu (Sensores)" · "Atestado Enchente" · "Mapa Inund. e Abrigos" · "Mapa Áreas de Risco" ·
  "Nova Transenchente" · "Cadastro Voluntários" · "Painel Alternativo"
- **Um link direto para "Taió"** — sugere integração entre as duas Defesas Civis.

## Ações
1. **Abrir `defesacivil.taio.sc.gov.br`** (aprovar a permissão no Chrome): buscar cotas de referência,
   histórico, abrigos e o estado das comportas da Barragem Oeste.
2. **Exportar as cotas de rua de Rio do Sul** pelo próprio botão do site (`soscota-rua/tabela`) — mais
   confiável que a transcrição via imprensa que temos hoje.
3. **Buscar a "Planilha Histórica Rio"** — fecharia o histórico de Rio do Sul, que hoje é lacuna.
4. **Coletar o estado das comportas** da Barragem Oeste (e Sul). Verificar se o endpoint `dams` da Asthon
   traz comportas ou só nível.
5. Registrar o pico de 2023 (12,11 m) no histórico de Taió quando houver a série.
