# Cheia de 11–12/09/2026 — a maior que este projeto já observou

Congelado em 13/09/2026 22:00Z (19:00 BRT) a partir do que a nossa própria coleta publicou:
`data/brutos/evento-2026-09-11-12-serie-recente-2200Z.json` (janela de 48 h) e
`data/brutos/evento-2026-09-11-12-ultimo-2200Z.json`.

**Por que congelar agora:** a série publicada é uma JANELA MÓVEL DE 48 H. Quando este arquivo foi
escrito ela já começava em **11/09 19:05**, com Blumenau em 6,75 m — ou seja, **a subida já tinha
saído**. Em poucas horas as próprias cristas sairiam também. O registro completo (a subida inclusive)
só existe em `data/tempo-real/2026-09.ndjson`, na VPS, que não é publicado — ver "O que falta" no fim.

## As cristas, e o que cada uma significa na régua da própria cidade

| cidade · régua | crista | quando | faixa que alcançou | agora (13/09 ~19:00) |
|---|---|---|---|---|
| **Blumenau** (DC Itajaí) | **7,87 m** | 12/09 02:15 | **ALERTA** (6,00); parou **13 cm** abaixo da emergência (8,00) | 4,34 m, ainda em atenção |
| Blumenau (AlertaBlu, horária) | 7,86 m | 12/09 05:00 | idem — as duas fontes concordam | 4,34 m |
| **Rio do Sul** (Ponte Dom Tito Buss) | **5,89 m** | 11/09 23:12 | **ALERTA** (5,50); 61 cm abaixo da inundação (6,50) | 5,31 m, **ainda em atenção** |
| **Taió** (Centro) | **6,95 m** | 12/09 03:43 | monitoramento (5,00); parou **5 cm** abaixo da atenção (7,00) | 4,46 m |
| **Brusque** (Ponte Estaiada – DCSC) | **4,62 m** | 12/09 01:35 | **atenção** (3,00); 38 cm abaixo da emergência (5,00) | 1,77 m |
| Itajaí · DC-10 Mirim, Limoeiro | 8,08 m | 12/09 03:30 | sem cotas cadastradas | 4,01 m |
| Itajaí · DC-11 Açu, Santa Regina | 4,37 m | 12/09 04:00 | sem cotas cadastradas | 3,14 m |
| Indaial (régua municipal) | 4,10 m | 12/09 22:00 | acima do **alerta** municipal (4,00) | **uma leitura só, e já com mais de 24 h** |
| Gaspar (estação 21) | 2,98 m | 13/09 08:11 | abaixo da atenção (5,00) | 2,72 m — a coleta só voltou depois do pico |

Nas 48 h da janela, **Rio do Sul não desceu da atenção em nenhuma leitura** (197 de 197 acima de
4,50) e Blumenau passou 138 leituras acima de 4,00.

## O que este evento prova, e o que não prova

**Prova que o par régua ↔ cota funciona sob carga.** Blumenau chegou a alerta com as duas fontes
independentes (Defesa Civil de Itajaí e AlertaBlu) concordando em 1 cm na crista — 7,87 contra 7,86 —,
o que é a melhor confirmação possível de que as duas leem a mesma régua.

**Não prova tempo de trânsito.** A crista de Rio do Sul (11/09 23:12) vem ANTES da de Taió
(12/09 03:43), que fica a montante. Não é a onda de Taió descendo: é chuva na bacia inteira, cada
cidade cheia pela sua própria sub-bacia. O mesmo padrão do evento de 10/09. Calcular trânsito com
estes horários daria um número invertido.

**Não fecha a magnitude.** A crista de Rio do Sul está a 18 leituras do início da janela; a subida
inteira, e qualquer pico anterior a 11/09 19:00, ficaram fora deste congelamento.

## ⚠️ ACHADO NA SÉRIE COMPLETA (13/09/2026): as duas fontes de Blumenau estão 3 h fora de fase

A régua de Blumenau (ANA 83800002) chega ao projeto por dois caminhos, e o projeto inteiro os trata
como UMA régua pelo campo `resgate_de`: a **Defesa Civil de Itajaí**, que a repassa a cada ~10 min, e o
**AlertaBlu**, de hora em hora, como resgate. Comparando as duas na série completa da cheia, ponto a
ponto, elas **não descrevem o mesmo rio no mesmo instante** — mas descrevem, com precisão quase
perfeita, se uma for deslocada 3 horas:

| deslocamento aplicado | pares | diferença média | desvio | maior diferença |
|---|---:|---:|---:|---:|
| nenhum | 56 | −0,135 m | 0,522 m | **1,80 m** |
| −1 h | 56 | −0,087 m | 0,347 m | 1,25 m |
| −2 h | 56 | −0,054 m | 0,188 m | 0,66 m |
| **−3 h** | 54 | **−0,004 m** | **0,015 m** | **0,05 m** |
| −4 h | 53 | +0,044 m | 0,153 m | 0,55 m |

Um desvio de 1,5 cm entre 54 pares, nos três dias (10, 11 e 12/09, medido em cada um separadamente),
não é coincidência: é a mesma régua, com os relógios separados por exatamente 3 horas.

**Qual dos dois está certo.** O do AlertaBlu está ancorado três vezes: (1) o `horaLeitura` do bruto é
UTC de verdade — na coleta das 23:45Z de 10/09 o ponto mais novo era 23:00Z, 45 min antes; se o "Z"
fosse rótulo falso sobre hora local, o ponto mais novo estaria 3 h no futuro, o que é impossível;
(2) o `coleta_alertablu.py` converte, e esse ponto (23:00Z = 4,23 m) está na nossa série como
**20:00 = 4,23 m**, como manda o contrato do projeto; (3) a página oficial da Defesa Civil de Blumenau
marcava 4,23 m caindo por volta das 20:40 daquele dia.

**Logo é o repasse da Defesa Civil de Itajaí que carrega `medido_em` ~3 h ATRÁS do instante real:** o
valor que ele rotula 17:05 aconteceu por volta das 20:05.

**E é específico de Blumenau, não do coletor.** Brusque vem da MESMA página, pelo MESMO coletor, e o
relógio dela bate no minuto: a tela aberta às 19:35 de 10/09 mostrava 2,19 m, e a nossa série tem
2,19 m às 19:35. Só a linha de Blumenau está fora de fase.

### O que isso corrige neste documento

**A crista de Blumenau provavelmente foi por volta das 05:15 de 12/09, não às 02:15.** O valor não
muda (7,87 m); o horário, sim. O próprio AlertaBlu põe a crista dele às **05:00** com 7,86 m — que é
exatamente 02:00 + 3 h. A tabela lá em cima traz o horário como veio do repasse; o horário real está
3 h à frente até isto ser resolvido.

### O que isso quebra fora daqui

- **Idade da leitura.** O site decide pintar ou não pela idade do `medido_em`. Com 3 h de atraso no
  rótulo, a leitura primária de Blumenau nasce "velha" e a cidade passa a depender do resgate horário
  do AlertaBlu — que é o que se via em 10/09, quando a primária aparecia parada às 16:35 e o número
  que pintava a tela vinha do AlertaBlu.
- **Qualquer tempo de trânsito que use Blumenau** sai 3 h errado, e Blumenau é o meio do Açu.
- **Cristas já registradas** com o relógio do repasse (esta e a de 10/09) carregam o mesmo desvio.

### O teste que fecha isso em dois minutos

Ler as duas fontes no MESMO minuto e comparar valor e carimbo:

```
cd /opt/enchentes-vale-itajai
date '+%Y-%m-%d %H:%M %Z'
python3 -c "import json,requests;d=requests.get('https://defesacivil.blumenau.sc.gov.br/static/data/nivel_oficial.json',headers={'User-Agent':'enchentes-vale-itajai'},verify='scripts/certs/blumenau.pem',timeout=30).json();print('AlertaBlu bruto:', d['niveis'][-1])"
python3 scripts/coleta_itajai.py | grep -i blumenau
```

Se o AlertaBlu trouxer, por exemplo, `23:00Z = X` e o repasse disser `X` com carimbo de 20:00, a
conclusão acima está confirmada e o conserto é no `coleta_itajai.py` (ou no pedido à Defesa Civil de
Itajaí, se o carimbo vier errado da própria página).

## O que falta

1. **Extrair o evento completo do ndjson da VPS**, antes que alguém limpe a pasta:
   ```
   cd /opt/enchentes-vale-itajai
   grep -h '"2026-09-1[012]' data/tempo-real/2026-09.ndjson > /tmp/cheia-2026-09-11-12.ndjson
   wc -l /tmp/cheia-2026-09-11-12.ndjson
   ```
   e trazer o arquivo para `data/brutos/`. Com ele sai a subida, a taxa de variação em cm/h e o
   horário real de cada crista.
2. **Decidir se as cristas entram em `enchentes.json`.** São picos de 2026 medidos pela nossa coleta,
   com régua nomeada nos dois lados — o material mais limpo que o projeto tem. Decisão do Jefferson.
3. **Conferir se o aviso saiu.** Blumenau em alerta é exatamente o caso que o bot existe para cobrir;
   `data/tempo-real/estado_alertas.json` na VPS diz o que ele fez.
4. **Resolver o desvio de 3 h de Blumenau** (seção acima) antes de usar qualquer horário de crista dela.
5. **Indaial**: a leitura municipal de 12/09 22:00 (4,10 m, acima do alerta municipal) é a única que
   chegou. Conferir se a coleta parou ou se a fonte publica esparso.
