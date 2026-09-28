# Captura das fontes de tempo real das cidades — 28/09/2026

O ambiente das sessões de código recebe 403 do proxy para todas as fontes municipais. A captura roda no GitHub Actions (`.github/workflows/capturar-portal-itajai.yml`), com a lógica em `scripts/capturar_fontes.py`: robots.txt antes de cada host, User-Agent do projeto, TLS sempre verificado, um pedido por alvo sem insistir. Os corpos voltam pelo log em gzip+base64 e são remontados com `capturar_fontes.py --remontar`, que só grava o que bate com o sha256 do runner.

Run [36374094642](https://github.com/haohmarusc-glitch/enchentes-vale-itajai/actions/runs/36374094642), 03h32 UTC de 28/09 (00h32 em Brasília). Corpos e manifesto em `data/brutos/captura-fontes-2026-09-28/`. Doze de treze alvos responderam 200, e os doze conferem.

## O que cada fonte entregou, lido pelo coletor dela

Horários em Brasília, como o repositório grava.

| Cidade | Fonte | Leitura | Medido em |
|---|---|---|---|
| Itajaí | Portal da DC, onze réguas DC | onze leituras, como em 27/09 | 28/09 00h30 |
| Taió | API Uniparking, régua do Centro | 5,24 m | 28/09 00h31 |
| Taió | Barragem Oeste | montante 13,20 m, 7 de 7 comportas abertas, vertendo | 28/09 00h31 |
| Rio do Sul | Asthon, Ponte Dom Tito Buss | 5,19 m | 28/09 00h31 |
| Blumenau | AlertaBlu | 3,20 m | 28/09 00h00 |
| Gaspar | DC de Gaspar, estação 21 | 1,84 m | **27/09 19h28** |
| Ituporanga | Página da prefeitura, "Centro" | 2,05 m, rotulado "Alerta" pela página | **25/09 07h00** |
| Indaial | Documento da Defesa Civil | não pedido: o robots.txt do host recusou | — |

Todos os coletores leram o formato de hoje sem ajuste. Os testes estão em `scripts/teste_capturar_fontes.py`, classe `TestCapturaDe28DeSetembro`.

## Achados

**Gaspar responde fora da VPS.** O host dá timeout na VPS desde 31/08, e por isso Gaspar está sem nível ao vivo no site. Do runner do GitHub, a tabela e a estação 21 responderam 200, com o robots.txt permitindo. O coletor leu 1,84 m. A leitura, porém, tinha cinco horas na hora da captura, enquanto o ribeirão Belchior, na mesma tabela, tinha sete minutos. A estação 21 publica com atraso por conta própria, o que confirma a pendência de cadência já aberta. Coletar Gaspar a partir do GitHub Actions resolveria o acesso, mas é decisão de infraestrutura, não desta captura.

**Ituporanga parou em 25/09.** A página da prefeitura publica duas leituras por dia, às 7h e às 17h, e a última é de três dias antes da captura. O rótulo "Alerta" em 2,05 m é da própria página e da régua do Centro, que não tem nome nem vínculo provado com a estação da ANA. Nada disso entra no cadastro; a cidade segue sem cota, pelo motivo já registrado em `estacoes.json`.

**Indaial: a captura respeitou o robots.txt, o coletor não o consulta.** O robots.txt de `docs.google.com` recusou o caminho de exportação, e a captura não fez o pedido. O coletor de produção `coleta_indaial.py` pede a mesma URL sem consultar robots.txt. Fica como pendência de decisão, sem mudança no coletor.

**Taió: a Barragem Oeste estava vertendo.** Montante em 13,20 m, as sete comportas abertas. O Centro estava em 5,24 m, acima dos 5,00 m de monitoramento do cadastro, cujas cotas ainda estão marcadas como não verificadas.

Esta captura não alterou coletor, cotas nem cadastro.
