# Auditoria — Relatório JICA 2011 (Itajaí) e notas da sessão 03/09/2026

Fonte primária conferida:
- Volume II, Main Report Part I: `https://openjicareport.jica.go.jp/pdf/12043659_02.pdf`
- Volume III-A, Supporting Report (Hydrology): `https://openjicareport.jica.go.jp/pdf/12043584_01.pdf`
- Equivalentes em português (ex.: `12043691_01.pdf`, `12043618_01.pdf`, `12043600_02.pdf`)
- Anexo B (capacidades / barragens): `12043584_02.pdf`
- Sumário executivo: `12043568.pdf`

Documentos internos auditados: `JICA-2011-VERIFICADO.md` e o resumo da sessão 03/09/2026.

Critério: citação literal vs. resumo vs. inferência de produto. Onde este arquivo e o PDF divergirem, o PDF manda.

---

## Veredicto

O núcleo do texto do Volume II, seção 3.5.4, está certo. A conclusão operacional da sessão — *“o relatório só dá três números; o Indaial +10 foi fabricado; não existe Tabela 7.5.1”* — não está.

A Tabela 7.5.1 existe no Volume III-A. O “Indaial +10” é uma célula dela. Os três números do Volume II são o **resumo** dessa tabela, não o inventário inteiro do relatório.

---

## 1. Erro central: a Tabela 7.5.1 existe — e o “Indaial +10” sai dela

### O que o Volume II realmente diz

Seção 3.5.4, p. 3-31, citação literal:

> *“The difference in flood peak times between Rio do Sul and Blumenau cities is around 7 to 10 hours, and around 14 to 17 hours between Blumenau and Itajaí cities. The flood propagation time from Rio do Sul to Itajai cities is around one day.”*

Isso é um resumo. A tabela que o resume **não está nesse volume**.

### Onde a tabela está

Volume III-A (Hydrology), p. A-80:

**Tabela 7.5.1 — *Largest Discharge Peak Time from each City, by Return Period***

É um hidrograma de **projeto** (HEC-HMS), calendário sintético 06–08/08, não uma série observada.

Cidades na tabela: Ituporanga, Taió, Rio do Sul, Apiúna, Ibirama, Indaial, Timbó, Blumenau, Gaspar, Ilhota, Itajaí, Brusque.

Âncora de Rio do Sul: **06/08 22:00** em todas as colunas extraídas.

| Cidade   | 5 anos        | 10 anos       | 25 anos       | 50 anos       |
|----------|---------------|---------------|---------------|---------------|
| Indaial  | +10 h (08:00) | +9 h          | +8 h          | +8 h          |
| Blumenau | +10 h (08:00) | +9 h          | +7 h          | +7 h          |
| Gaspar   | +12 h         | +11 h         | +9 h          | +8 h          |
| Ilhota   | +17 h         | +15 h         | +14 h         | +12 h         |
| Itajaí   | **+27 h**     | **+24 h**     | +21 h         | +19 h         |

### Três consequências

1. **“Não existe Tabela 7.5.1 neste volume”** é verdadeiro *só* para o Vol. II. No relatório JICA a tabela existe, tem esse nome, e cobre o tronco e as cabeceiras.
2. **“Indaial +10 foi fabricado”** é falso se a origem for a 7.5.1. No cenário de 5 anos, Indaial e Blumenau **picam no mesmo horário** (+10 h). A linha não foi copiada do teto da faixa de Blumenau: é uma célula da tabela.
3. A “contradição” `Rio do Sul → Indaial = 10 h` vs `Blumenau = 7 h` **não existe dentro de um mesmo cenário**. 7 h (Blumenau) é coluna de 25–50 anos; 10 h (Indaial) é coluna de 5 anos. Misturar colunas fabrica o paradoxo. No mesmo hidrograma, Indaial e Blumenau são quase simultâneos (diferença 0–1 h).

O texto 7–10 h / 14–17 h / ~1 dia é a leitura das colunas **5–25 anos** da própria tabela. No caso de 50 anos, Blumenau→Itajaí cai para **12 h** (fora da faixa escrita) e Rio do Sul→Itajaí para **19 h**. A âncora “~24 h” é o caso de 10 anos, não uma observação de campo.

### Correção de regra

Não apagar tempos que não sejam um dos três do texto. Usar a 7.5.1 como hidrograma canônico *de projeto*, **uma coluna por vez**, e tratar 7–10 / 14–17 / ~24 h como o resumo que o Vol. II faz dessa tabela. Não empilhar limite inferior de um trecho com célula de outro período de retorno.

Ponto de método mais grave que o “foi fabricado”: esses horários **não são tempos de trânsito observados**. São picos de um hidrograma de projeto com chuva de projeto e comportas modeladas (no Vol. II: *“releasing gates … assumed to be fully opened”*). Evento real muda com:

- onde choveu;
- se a Oeste/Sul estão retendo ou vertendo;
- a magnitude — a própria tabela já mostra celeridade maior na cheia maior.

Ponderar só por declividade, sem Q e sem operação de barragem, continua incompleto.

---

## 2. O que está sólido (conferido na fonte)

### Topologia (seção 3.1)

Oeste e Sul encontram-se em Rio do Sul e *ali começa o Açu*; Norte em Ibirama; Benedito em Indaial; Luiz Alves em Ilhota; Mirim em Itajaí. Fecha com o AIBH.

### Declividade (Tabela 3.6.2)

Os cinco números do Açu batem:

| Trecho | i |
|---|---|
| Itajaí → montante de Blumenau | 1/20.000 |
| Blumenau → montante de Indaial | 1/400 |
| Indaial → confluência do Norte | 1/1.500 |
| Confluência do Norte → jusante de Lontras | **1/85** |
| Lontras → Rio do Sul | 1/3.000 |

A leitura física está correta: o trecho rápido está no meio, o quase plano está no fim.

O Executivo e o Vol. III-A repetem que o leito em Blumenau está **abaixo do nível médio do mar**.

Larguras no Vol. III-A: 200–300 m no baixo vale; **150–200 m perto de Blumenau**; **100–150 m em Rio do Sul**. “150 m em Blumenau e 200 m em Gaspar” e o rótulo “slight bottlenecks” são um pouco mais precisos do que o parágrafo localizado no PDF — tratar 150–200 / 100–150 como o dado da fonte.

### Capacidade de vazão (Tabelas 3.6.3 / 3.6.4 e figura do Anexo B)

A hierarquia está certa no essencial:

- Rio do Sul ~1.220 m³/s (~5 anos) e Itajaí 2.000–3.000 (~5 anos) — pontos frágeis do tronco;
- Indaial 5.700 (>50 anos) — o mais folgado;
- Mirim após a reunião em Itajaí ~300 m³/s.

Há variação interna no próprio JICA para Gaspar (figura de perfil ~4.000–6.000; outra figura 5.100–6.000) e Blumenau 4.200–6.000. Não misturar esses intervalos como se fossem um único levantamento.

### Mirim 2/3 – 1/3

Citação encontrada: razão assumida pela capacidade estimada de cada braço, com a ressalva oficial de que o atalho *pode ter aumentado* a vazão a jusante em Itajaí. Isso é dado de topologia, não medição de evento.

### Barragens

Confirmação cruzada no Anexo B:

- Oeste: **7 condutos** Ø 1.500 mm;
- Sul: **5**;
- Norte: 2 com comporta + 5 sem.

Capacidade de descarga em NHWL ~163 / 194 / 258 m³/s.

A “chuva equivalente” é definida no próprio anexo como *storage / área de drenagem*:

- 83 Mm³ / 1.042 km² ≈ 80 mm (Oeste);
- 93,5 / 1.273 ≈ 73 mm (Sul);
- 357 / 2.318 ≈ 154 mm (Norte).

A frase de que Oeste e Sul enchem fácil, e que a Oeste verteu em 2001 e 2010, está no Vol. II.

As áreas (1.042 / 1.273 no JICA vs 851 / 1.164 na API estadual) são delimitações diferentes; registrar as duas, sem fundir.

O JICA ainda traz regra operacional da Oeste que interessa ao “retendo × vertendo”: em Taió, primeira comporta em 7,10 m e as sete fechadas em 7,50 m; em Rio do Sul, início de fechamento em 6,50 m (junto com a Sul).

### Curva-chave de 2008

Os três pontos existem, mas a fonte imediata no JICA é o relatório *Desastre de 2008 no vale do Itajaí*, não um levantamento próprio de seção:

- Blumenau 11,5 m → 4.200 m³/s
- Timbó 8,0 m → 710 m³/s
- Indaial 6,0 m → 3.100 m³/s

São pontos de um evento, não a curva inteira. Úteis; insuficientes para converter nível em vazão fora da vizinhança desses H.

### DEINFRA / previsão de Rio do Sul (seção 4.2.2)

A passagem é quase palavra por palavra a citada na sessão: a DEINFRA *não registrou nem informou* as vazões de saída das barragens Oeste e Sul; por isso a previsão municipal “não é apropriada para uso prático”.

O CEOPS, em 2011, previa **só Blumenau**, com 3 de 14 estações, sem dados do CIRAM.

Isso justifica ofício. O que o documento *não* autoriza é tratar 2011 como estado atual — 15 anos depois a telemetria estadual existe; o que falta verificar é se a **vazão de saída por comporta** (não só o nível do reservatório) passou a ser publicada.

### 1983 / 1984 / 2008

15,34 m e 15,46 m em Blumenau e retornos ~76 / ~66 anos aparecem no Vol. II.

2008 como chuva média de bacia “pequena” e chuva localizada em Blumenau é o diagnóstico do próprio estudo (média de 4 dias na bacia ~121–144 mm vs 575–576 mm em 4 dias em Blumenau).

O “8.400 anos” para 4 dias em Blumenau **não apareceu** nas páginas conferidas; o número que o Vol. III cita para 1 dia em Blumenau é **270 anos**. Não gravar 8.400 sem a tabela/fórmula.

---

## 3. Onde a inferência passa do que a fonte sustenta

1. **“Remover qualquer tempo que não seja um dos três.”** Demais. Os três são o resumo; a 7.5.1 é o dado. Apiúna, Gaspar, Ilhota e as cabeceiras *estão* no hidrograma de projeto.
2. **Ponderar a janela só por declividade.** Direção certa (a 3.6.2 mata interpolação por km), mas a 7.5.1 já mostra que o tempo *encurta* com a cheia. Celeridade ∝ f(Q, seção, operação). Declividade sem Q subestima a variação entre 5 e 50 anos.
3. **“7 comportas = 7 condutos”** bate. Não implica que o site da Asthon exponha estado de cada comporta — isso continua lacuna.
4. **Capacidades como “dado que faltava por completo”.** O dado é de 2011, seção de 2011, sem atualização de assoreamento/obras posteriores. Usar como ordem de grandeza e período de retorno *na geometria de então*.
5. **Gaspar pós-1986 (nota de sessão, não o JICA).** Santos & Pinheiro (*Rev. Bras. Geomorfologia*, 2002) confirmam a retificação/alargamento de 1986 na *divisa* Blumenau/Gaspar. O efeito medido por eles é o **oposto** da explicação que a sessão deu para a queda dos picos em Gaspar: a montante da obra os máximos *caem*; a **jusante** (Gaspar) os máximos *sobem*. Se a série de Gaspar realmente despenca depois de 1986, a causa não é “canal mais largo marca menos altura” nesse ponto — ou a régua mudou de zero/local, ou entram barragens/amostragem. Não comparar pré e pós-1986; também não atribuir a queda à obra de 1986 sem resolver esse sinal.

---

## 4. O que fazer no `JICA-2011-VERIFICADO.md`

- Trocar “não existe Tabela 7.5.1” por: **não está no Vol. II; está no Vol. III-A, A-80; o texto 3.5.4 a resume**.
- Trocar “Indaial +10 foi fabricado” por: **é a célula de 5 anos da 7.5.1; no mesmo cenário Blumenau também é +10 h**.
- Âncora de Itajaí: **+27 / +24 / +21 / +19 h** conforme 5 / 10 / 25 / 50 anos; “~1 dia” = coluna de 10 anos.
- Deixar explícito: hidrograma de **projeto**, comportas abertas no cálculo de vazão provável, não trânsito de evento real.
- Manter declividade, capacidades, Mirim 2/3–1/3, chuva equivalente, 7 condutos, DEINFRA 2011, leito abaixo do mar — esses aguentam a fonte.
- Separar o que é citação do que é regra de produto (ofício DEINFRA, UI “retendo × vertendo”, ponderação da janela).

A leitura do Vol. II foi boa. O que quebrou a coerência foi tratar o resumo de uma página como o inventário inteiro do relatório, e tratar um hidrograma de projeto como se fosse a ausência de números para as cidades do meio.

---

## 5. Referências rápidas dos PDFs

| Peça | URL |
|---|---|
| Vol. II Main Report Part I | https://openjicareport.jica.go.jp/pdf/12043659_02.pdf |
| Vol. III-A Hydrology | https://openjicareport.jica.go.jp/pdf/12043584_01.pdf |
| Anexo B Flood Mitigation | https://openjicareport.jica.go.jp/pdf/12043584_02.pdf |
| Executive Summary | https://openjicareport.jica.go.jp/pdf/12043568.pdf |
| Santos & Pinheiro 2002 | https://doi.org/10.20502/rbg.v3i1.10 |
