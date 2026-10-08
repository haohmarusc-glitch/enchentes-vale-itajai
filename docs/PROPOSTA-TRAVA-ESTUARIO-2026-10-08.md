# As nove réguas travadas de Itajaí: o que 36 dias de série dizem — proposta

**Situação:** proposta para decisão do Jefferson. **Nada foi aplicado.** As nove continuam com
`alerta_automatico: false`, sem aviso e sem cor no Monitor. A proposta da DC-11 está em
`docs/PROPOSTA-DC11-AVISOS-2026-10-08.md`.

Pendência do README: "A trava de maré é larga demais em pelo menos duas réguas" (04/09/2026), medida então com 3 dias
da série publicada. Esta medição usa 36 dias (30/08 a 05/10, `arquivo-series`), régua a régua pelo campo `estacao`,
e os mesmos métodos da DC-11:
- a maré é o resíduo da média de 25 h contra a tábua da Marinha;
- a simulação de mensagens é a de `scripts/simular_avisos_mare.py`.

## Resumo

| régua | sente a maré? | passou da atenção em 36 dias | quando passou | série | proposta |
|---|---|---|---|---|---|
| **DC-01** ICMBio/CEPSUL (foz) | **sim** (0,93; fator 0,90) | 120 vezes, 88 com a base abaixo | todo dia de sizígia | viva | **manter travada** |
| **DC-04** Vitalmar (Mirim) | **sim** (0,95; 0,81) | 47 vezes, 38 com a base abaixo | idem | viva | **manter travada** |
| **DC-09** Murta, Ponte R. Lidia Puel Peixer | **sim** (0,90; 0,66) | 48 vezes, 36 com a base abaixo | idem | viva | **manter travada** |
| **DC-02** Praça Celso Pereira | não (0,24; 0,07) | 9 vezes | cheias de 01/09, 12/09 e 22/09 | **parada**: 18 dos 35 dias com menos de 3 cm de variação; 1,53 m por 48 h com chuva | **manter travada**; série suspeita |
| **DC-03** SEMASA (Mirim retificado) | **sim** (0,91; 0,79) | 7 vezes | **só nas cheias** (01/09, 12/09, 22/09) | viva | **candidata a destravar** |
| **DC-06** Itamirim (Mirim antigo) | **sim** (0,95; 0,77) | **nenhuma** (máx 1,48 contra 1,50) | — | viva | **candidata a destravar** |
| **DC-05** Mirim antigo, propriedade privada | não (0,13; 0,03) | 4 episódios | **só em cheia ou chuva** (31/08–02/09, 10/09, 11–12/09, 21–23/09) | viva | **candidata a destravar** |
| **DC-07** Murta, Portal | não (0,01) | 3 episódios | **só em cheia ou chuva** (31/08, 10/09, 21–22/09) | viva; parada em dias secos | **candidata**, depois de escolher a cota |
| **DC-08** Canhanduba | não (0,00) | 5 episódios | **só em cheia ou chuva** (31/08, 10/09, 11–12/09, 19–20/09, 21–22/09) | viva; parada em dias secos | **candidata**, depois de escolher a cota |

**O que muda em relação a 04/09 e 05/09:**
- **A trava das quatro de maré forte está certa.** DC-01, DC-04 e DC-09 passam da cota com a maré, não com a
  cheia. Pela regra de hoje, mandariam 453, 124 e 216 mensagens em 36 dias. Mesmo com histerese, seriam 212, 77
  e 125.
- **O motivo da trava de DC-05 e DC-08 não se sustenta.** O cadastro diz que, em 05/09, elas ficaram 46,8 h e
  25,5 h acima da cota "sem cheia". Na série, esses trechos são **31/08 10h → 02/09 08h30** (DC-05, 46,5 h) e
  **31/08 10h30 → 01/09 11h40** (DC-08, 25,2 h): a cheia de 01/09. Em 36 dias, as duas só passaram da atenção
  em dia de cheia ou de chuva.
- **DC-07 e DC-08 não estão travadas como a DC-02.** Ficam paradas em dia seco, como ribeirão em vazão de base,
  mas reagiram à chuva de 06–07/10: a DC-07 foi de 0,17 a 0,87 m, e a DC-08 de 1,03 a 2,28 m. **Hoje a DC-08
  (2,28 m) e a DC-05 (1,71 m) estão acima da própria cota de atenção, travadas: sem aviso e sem cor.** É a
  direção perigosa que o item de 04/09 apontava, e que a regra "ribeirão urbano sobe rápido" justifica.
- **DC-03 e DC-06 sentem a maré, mas a maré sozinha não as leva à cota.** O nível de base fica 0,98 m (DC-03)
  e 0,87 m (DC-06) abaixo da atenção. A DC-03 só passou da cota nas três cheias. A DC-06 não passou nenhuma vez.

## Números por régua (36 dias)

| régua | cotas (at/al/em) | corr. maré (atraso) | fator | base mediana | folga | máx | passagens (base abaixo) | msgs hoje | msgs com histerese 0,30 m | dias parados |
|---|---|---|---|---|---|---|---|---|---|---|
| DC-01 | 1,16 / 1,36 / 1,56 | 0,93 (0 h) | 0,90 | 1,03 | 0,13 | 2,00 | 120 (88) | 453 | 212 | 0/35 |
| DC-02 | 1,60 / 2,00 / 2,50 | 0,24 (3 h) | 0,07 | 1,00 | 0,60 | 1,90 | 9 (7) | 18 | 7 | **18/35** |
| DC-03 | 1,48 / 1,85 / 2,50 | 0,91 (0 h) | 0,79 | 0,50 | 0,98 | 1,97 | 7 (4) | 20 | 12 | 0/35 |
| DC-04 | 1,50 / 1,85 / 2,25 | 0,95 (0 h) | 0,81 | 1,12 | 0,38 | 2,18 | 47 (38) | 124 | 77 | 0/35 |
| DC-05 | 1,60 / 2,20 / 3,00 | 0,13 (3 h) | 0,03 | 1,26 | 0,34 | 2,60 | 4 (2) | 16 | 14 | 2/35 |
| DC-06 | 1,50 / 1,85 / 2,55 | 0,95 (1 h) | 0,77 | 0,63 | 0,87 | 1,48 | 0 | 0 | 0 | 0/35 |
| DC-07 | 1,00 / 1,35 / 1,65 | 0,01 | 0,00 | 0,33 | 0,67 | 1,47 | 4 (4) | 10 | 8 | 15/35 |
| DC-08 | 1,80 / 2,30 / 2,89 | 0,00 | 0,00 | 1,05 | 0,75 | 2,80 | 5 (3) | 23 | 23 | 7/35 |
| DC-09 | 1,12 / 1,32 / 1,52 | 0,90 (1 h) | 0,66 | 0,95 | 0,17 | 1,93 | 48 (36) | 216 | 125 | 0/35 |
| *DC-10* (dispara) | 8,00 / 9,00 / 10,00 | 0,00 | 0,00 | 3,93 | 4,07 | 8,33 | 2 (1) | 4 | 4 | 0/35 |
| *DC-11* (dispara) | 3,00 / 4,00 / 5,00 | 0,91 (1 h) | 0,70 | 2,66 | 0,34 | 4,37 | 48 (41) | 112 | 52 | 0/35 |

Notas:
- **Folga:** cota de atenção menos a mediana do nível de base da janela.
- **Passagens com a base abaixo:** a régua cruzou a cota com a média de 25 h abaixo dela.
- **Dias parados:** dias com ≥ 48 leituras e menos de 3 cm entre o máximo e o mínimo.
- "Base abaixo" não é sinônimo de "falso alarme" nas réguas sem maré: num ribeirão, a chuva sobe e desce o nível
  em menos de 25 h, e a média atrasa.

## As cotas que ainda pesam

| régua | cota no cadastro (PLANCON v17) | cota no portal (13/09/2026) | efeito |
|---|---|---|---|
| DC-07 | 1,00 / 1,35 / 1,65 | 1,00 / 1,40 / 1,50 | a atenção é igual; muda o alerta e a emergência |
| DC-08 | 1,80 / 2,30 / 2,89 | 1,70 / 2,30 / 2,89 | muda a atenção (10 cm) |
| DC-05 | 1,60 / 2,20 / 3,00 | sem divergência registrada | — |
| DC-03, DC-06 | sem divergência com o portal (13/09) | — | — |

O cadastro usa o PLANCON v17. Destravar DC-07 e DC-08 com essas cotas é uma decisão: o portal é mais recente, mas
não publica a data nem o motivo da mudança (`cotas_conferencia_2026_09_13`).

## Proposta (para decisão; nada aplicado)

1. **Manter travadas DC-01, DC-04 e DC-09** e trocar o `motivo_sem_alerta` comum pelo número medido: correlação,
   fator e passagens com a base abaixo da cota.
2. **Manter travada a DC-02** e trocar o motivo para "série parada". Registrar a suspeita de sensor travado ou de
   régua isolada do rio (`docs/PROPOSTA-DC11-AVISOS-2026-10-08.md`, seção 5).
3. **Destravar, com a histerese de 0,30 m da proposta da DC-11:**
   - DC-03 e DC-06, que sentem a maré mas não chegam à cota com ela;
   - DC-05, cuja trava se apoiava numa leitura errada da cheia de 01/09.

   Juntas, mandariam 26 mensagens em 36 dias, todas nas cheias.
4. **DC-07 e DC-08: destravar depois de escolher a cota** (PLANCON v17 ou portal). Com as cotas de hoje e a
   histerese, mandariam 8 e 23 mensagens em 36 dias, todas em dia de chuva ou de cheia. A DC-08 está acima da
   atenção agora.
5. **O mapa:** destravar faz a régua ganhar cor no Monitor (`reguasNoMapa.ts`). Nos ribeirões (Murta, Canhanduba),
   o teste `web/src/logica/afluenteNaoCorre.test.ts` falha de propósito para obrigar a decidir junto se o curso
   **corre** (correnteza = faixa). É mais uma decisão, não um detalhe de implementação.
6. **O que precisa mudar no código, se aprovado:**
   - o `alerta_automatico` e o `motivo_sem_alerta` de cada régua, em `estacoes.json`;
   - a histerese em `alerta_cotas.decidir`;
   - os testes que contam "nove de estuário": `teste_bot.py`, `rotulosDasReguas.test.ts`,
     `teste_conferir_mapa_e_alarme.py` e `reguasAgora.test.ts`.

   Nenhuma cota muda.

## Como refazer

```bash
git show origin/arquivo-series:tempo-real/2026-09.ndjson > /tmp/serie/2026-09.ndjson   # e os outros meses
for c in DC-01 DC-02 DC-03 DC-04 DC-05 DC-06 DC-07 DC-08 DC-09; do
  python3 scripts/simular_avisos_mare.py --serie /tmp/serie --codigo $c
done
```

A tabela de maré por régua repete o método da Tabela 1 de `docs/ANALISE-CHEGADA-ITAJAI-2026.md`, com 36 dias.
