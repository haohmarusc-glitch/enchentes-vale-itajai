# O inventário da ANA cruzado com as réguas do projeto (06/09/2026)

Fonte: `Inventario31_08_2026.mdb` (157 MB), tabela `Estacao`, 1.099.296 registros, aberto com
`mdbtools`. É o **catálogo público** de estações da Agência Nacional de Águas. O arquivo foi lido
fora deste repositório; o que está aqui é o que dele se aproveitou, e o que foi **medido de volta**
contra `data/`.

---

## ⛔ Primeiro: o inventário NÃO responde a pergunta do datum

A tabela **`fichareferencianivel`** existe no arquivo, com as colunas certas (`rn`, **`cota`**,
`altitude`, `MetodoAltimetricoCodigo`) — e está **vazia**. Só o cabeçalho. As demais fichas
(`fichadescritiva`, `fichasecaomedicao`, `PerfilTransversal`, `CurvaDescarga`, `Cotas24`) também.

**Errata.** Na sessão anterior eu escrevi, no PR que trouxe os CSV do HidroWeb, que o inventário da
83800002 era *"a próxima busca de maior valor, porque traz a cota do zero da régua e responde o
datum diretamente"*. **Estava errado.** O inventário público traz só o catálogo; a cota do zero está
na área restrita ou vem pela API. A `REGRA_REFERENCIA_BLUMENAU` **continua bloqueada**, e o caminho
volta a ser a API da ANA (ofício) ou o teste dos picos instantâneos pós-1989.

Foi uma indicação minha que custou um download de 157 MB. O que ela rendeu está abaixo — mas não é
o que eu tinha prometido.

---

## ✅ A lacuna de coordenada dos três códigos está fechada

Os três campos `codigo_ana_verificacao` em `data/estacoes.json` diziam, em letras maiúsculas,
*"⚠️ Falta a COORDENADA da estação — sem ela o vínculo continua por NOME"*. Agora não falta.

| Código | Nome ANA | Lat | Lon | Alt. | Área | Escala |
|---|---|---|---|---|---|---|
| 83050000 | TAIÓ | −27,1139 | −49,9953 | 360 m | 1.570 km² | desde 1929 |
| 83300200 | RIO DO SUL - NOVO | −27,2078 | −49,6292 | 350 m | 5.160 km² | desde 1978 |
| 83800002 | BLUMENAU (PCD) | −26,9186 | −49,0656 | 12 m | 11.803 km² | 1939 → **12/2021** |

**Medido aqui**, contra o traçado em `data/rios/itajai-acu.geojson` e contra os pinos das cidades:

| Estação | ao traçado do rio | ao pino da cidade |
|---|---|---|
| 83050000 TAIÓ | 0,07 km | 0,56 km |
| 83300200 RIO DO SUL | 0,09 km | 0,43 km |
| 83800002 BLUMENAU | **0,05 km** | **6,93 km** |

As três caem em cima do rio — é o que se espera de uma régua fluviométrica, e é o que a nova trava
passa a exigir. A anomalia é a última coluna de Blumenau.

---

## ⚠️ O pino de Blumenau não é uma régua de rio

O pino de Blumenau está a **2,99 km do talvegue** (medido em 06/09/2026). Isso já era conhecido:
é a exceção `LONGE_ACEITO["blumenau"]` no validador. O que o inventário acrescenta é **por quê**.

O motivo escrito na exceção dizia *"a coordenada publicada é a da ESTAÇÃO, ~3 km do talvegue — não é
erro"*, o que dava a entender que era **a régua**. Não é: a DCSC-00026 é do tipo `Meteo`, com
`tem_nivel_do_rio: false`. **Mede chuva.** A fluviométrica da ANA em Blumenau fica a 6,93 km dali.

Terceira confirmação independente do mesmo fato — e agora nem a ANA reconhece a DCSC-00026 como a
estação de Blumenau (a mais próxima dela, a 83700002, está a 3,3 km).

**O pino NÃO foi movido.** A convenção diz que `coordenadas` é a posição da régua **cuja leitura o
site mostra**, e essa é a do AlertaBlu/Defesa Civil, cuja coordenada o projeto não tem. Trocar pela
da ANA seria trocar uma coordenada errada por uma de **outra rede** — o mesmo erro de método que o
projeto evita em toda parte. O que mudou: o motivo da exceção agora diz a verdade, e diz o que a
remove. **Decisão do Jefferson.**

---

## 🎯 A emenda à regra nº 1: coordenada **e** tipo

O cruzamento foi refeito contra **todas** as estações da ANA em Santa Catarina. Cinco caíram a menos
de 750 m de uma régua do projeto:

| Régua do projeto | ANA mais próxima | Distância | Mede |
|---|---|---|---|
| DCSC-00041 Taió | 2750017 TAIÓ | **53 m** | ⚠️ **chuva** |
| DC-01 CEPSUL (Itajaí) | 2648065 ITAJAÍ_Centro | 172 m | ⚠️ **chuva** |
| DCSC-00006 Indaial | 2649084 INDAIAL | 348 m | ⚠️ **chuva** |
| DCSC-00024 Vidal Ramos | 2749097 VIDAL RAMOS_Centro | 723 m | ⚠️ **chuva** |
| DCSC-00040 Barragem Oeste | 83030000 BARRAGEM OESTE | 30 m | ✅ nível, desde 1966 |

**Quatro dos cinco são pluviômetros.** Município certo, nome certo, coordenada certa, **grandeza
errada** — um pluviômetro e uma régua cabem no mesmo poste. A regra nº 1 do projeto (vínculo por
coordenada, não por nome) continua certa, mas é **condição necessária, não suficiente**.

A emenda virou trava: **`scripts/validar_dados.py::valida_codigo_ana`**. A tabela
`ESTACOES_ANA_CONHECIDAS` guarda tipo e coordenada de cada estação já lida no inventário, e três
coisas reprovam:

1. `codigo_ana` que a ANA cadastra como pluviométrica — inclusive **com zero à esquerda**
   (`02648008`), que é a forma em que esses códigos circulam e passa na trava de oito dígitos;
2. estação fluviométrica cuja coordenada caia a mais de 1 km do traçado do ramo da cidade;
3. (aviso) estação com a escala encerrada e sem `codigo_ana_sucessor` declarado.

Testada por sabotagem em `scripts/teste_validar_dados.py::CodigoAnaEhReguaDeRio`. **A primeira
versão não mordia**: chamava `le_json` com um `Path`, e o resto do validador chama pelo nome, então
o monkeypatch dos testes não pegava e a sabotagem lia o arquivo real. Mesma classe de erro do
`nivel_m`/`pico_m` de ontem — e de novo quem achou foi o teste, não a leitura.

---

## 🎯 Salseiro não é Vidal Ramos — o ofício C9 está respondido

O README perguntava há dias se a estação **`83892990` "Salseiro"**, que o Boletim 150/2026 da EPAGRI
publica como *"Vidal Ramos / Salseiro"*, é a nossa régua de Vidal Ramos. O bloqueio era sempre o
mesmo: **o boletim não publica coordenada**, e por isso o ofício C5/C9 à EPAGRI pedia exatamente
essa relação código ↔ coordenada.

**A ANA publica.** SALSEIRO fica a **6,8 km** da nossa régua (−27,38547 / −49,35812) e drena
**286 km²** — sub-bacia bem menor. Mesmo município, estações diferentes. **Não vincular.**

Gravado em `data/estacoes.json` como `vidal-ramos.codigo_ana_nao_e`, e travado por teste: o registro
precisa ficar **no dado**, senão o próximo boletim da EPAGRI convida ao mesmo vínculo de novo.

O ofício C5 continua valendo pelo outro lado — os **limiares por faixa** que a EPAGRI publica e que
faltam a Taió, Ituporanga e Vidal Ramos. O que saiu da lista foi a pergunta do Salseiro.

---

## ⛔ Errata do próprio levantamento: Porto Itajaí não indexa nada

A primeira rodada anunciou a **`83920000 PORTO ITAJAÍ`** (Rio Itajaí-Açu, 15.200 km², a 846 m da
DC-01) como *"a estação da foz que faltava — a que permite indexar as 357 manchas"*. **Errado.**
A escala dela vai de **setembro/1927 a novembro/1937**: dez anos, encerrada há 89. Não tem 2011,
2013, 2014 nem 2015.

**Não existe estação fluviométrica ativa da ANA em Itajaí.** O único nível na foz são as onze réguas
DC do município — e é por elas que as manchas terão de ser indexadas, se houver histórico. Isso
mantém de pé o resultado negativo do levantamento de picos de Itajaí, e a proibição que veio com
ele: **nada entra em `enchentes.json` para Itajaí.**

O erro foi ler o cadastro sem olhar o período — a mesma classe da coordenada sem tipo. **Campo
isolado não basta; é o registro inteiro que diz o que a estação é.**

---

## ⚠️ Dezembro de 2021: quatro réguas de referência morreram no mesmo mês

| Código | Estação | Escala |
|---|---|---|
| 83800002 | BLUMENAU (PCD) | 1939 → 12/2021 |
| 83690000 | INDAIAL | 1929 → 12/2021 |
| 83840000 | GASPAR (MONTANTE ETA) | 1927 → 12/2021 |
| 83440000 | IBIRAMA | 1928 → 12/2021 |

Não é coincidência: é reestruturação da rede. Séries de 80 a 90 anos terminam em 12/2021.

**Explica Gaspar.** A DCSC-00005 fica a **10 m** da 83840000 — é a mesma estação — e declara
`tem_nivel_do_rio = false`. Não é intermitência nem "só chuva": é **desativação, com data**. Terceira
explicação para o mesmo campo, e a primeira que traz um mês.

**Para Blumenau, o código ativo hoje é a `83800003`**, na mesma coordenada. O `codigo_ana` do projeto
segue `83800002` porque é dele a série histórica que usamos (1939–2021); o sucessor está declarado em
`codigo_ana_sucessor`, e o aviso do validador cobra essa declaração de quem esquecer. **Não se sabe
se os dois compartilham o mesmo zero** — o inventário não traz a cota de nenhum dos dois.

---

## ✅ Barragem Oeste: uma quarta fonte, e o Vol. II segue isolado

`83030000 BARRAGEM OESTE`, fluviométrica, escala desde **julho/1966**, telemetria desde 2002,
**área 854 km²**.

| Fonte | Área |
|---|---|
| **ANA (inventário)** | **854 km²** |
| API estadual (DC-SC) | 851 km² |
| JICA Vol. III-A, Tab. 2.1.1 | 851,2 km² |
| JICA Vol. II, Tab. 3.2.4 | 1.042 km² ← **fora da curva** |

Três fontes independentes em ~851–854. A divergência continua **registrada, não fundida** — a regra
de `hidraulica.json` não muda —, mas agora se sabe qual lado é o isolado. Gravado como
`area_drenagem_km2_ana`.

---

## Rio do Sul: quatro estações da ANA em três rios

| Código | Nome | Rio (ANA) | Área |
|---|---|---|---|
| 83094000 | RIO DO SUL | Itajaí do **Oeste** | 5.160 |
| 83300000 | RIO DO SUL | Itajaí do **Sul** | 2.030 |
| 83300002 | RIO DO SUL | Itajaí-**Açu** | 5.160 |
| 83300200 | RIO DO SUL - NOVO | Itajaí-**Açu** | 5.160 |

Espelha as três réguas físicas do município (Ponte BR 470 no Oeste, Ponte Ricardo Kanitz no Sul,
Ponte Dom Tito Buss no Açu) — a mesma multiplicidade que `docs/reguas-rio-do-sul.md` já registrava,
e a razão de o projeto se recusar a pintar uma régua com a cota de outra.

⚠️ **A área de 83094000 (Oeste) aparece como 5.160 km², igual à do Açu** — o que não faz sentido para
uma cabeceira. Provável erro de cadastro no rio ou na área. **Não usar essa área sem conferir.**

⚠️ E o nosso `codigo_ana` de Rio do Sul (83300200, Açu) **não é a estação que fica junto da nossa
régua DCSC-00013**: essa fica a 35 m da 83094000, que a ANA cadastra no **Oeste**. São grandezas de
rios diferentes. Ainda não resolvido — anotado aqui para não virar par silencioso.

---

## As estações "DCSC" na ANA: só quatro no país

`83029940 DCSC BARRAGEM OESTE TAIÓ` · `83145100 DCSC BARRAGEM SUL ITUPORANGA` ·
`83145140 DCSC BARRAGEMSUL ITUPORANGA JUSANTE` · `71620200 DCSC RIO CAVEIRAS` (fora da bacia).

A ponte entre os dois sistemas **existe, mas é mínima** — três estações na bacia, todas de barragem.
**Não serve** como mapeamento geral ANA ↔ DCSC, como a primeira rodada tinha sugerido.

---

## As que estão vivas com série longa

| Código | Estação | Rio | Área | Desde |
|---|---|---|---|---|
| 83250000 | ITUPORANGA | Itajaí do Sul | 1.650 | **1929** |
| 83300200 | RIO DO SUL - NOVO | Itajaí-Açu | 5.160 | 1978 |
| 83520000 | WARNOW (Indaial) | Itajaí-Açu | 9.790 | **1927** |
| 83800003 | BLUMENAU (PCD) | Itajaí-Açu | 11.803 | sucessora |
| 83870001 | ILHOTA-JUSANTE | Itajaí-Açu | 12.357 | sucessora |
| 83900000 | BRUSQUE (PCD) | Itajaí-Mirim | 1.240 | **1929** |
| 83892998 | BOTUVERA-MONTANTE | Itajaí-Mirim | 827 | 1985 |
| 83892990 | SALSEIRO | Itajaí-Mirim | 286 | 1987 |
| 83030000 | BARRAGEM OESTE | Itajaí do Oeste | 854 | 1966 |

Ituporanga, Warnow e Brusque têm **quase 100 anos de série** — é o material de calibração mais longo
da bacia. **Nenhum desses códigos foi gravado como `codigo_ana` de cidade nenhuma**: para isso falta
a coordenada de cada um, e a lição desta sessão é justamente que nome e município não bastam. Os
tipos estão na tabela do validador, o que já impede o vínculo errado; o vínculo certo espera a
coordenada.

---

## O que fica pendente

1. **A cota do zero da régua** — não está no inventário público. Só pela API da ANA ou pela área
   restrita. Continua sendo o que destrava a `REGRA_REFERENCIA_BLUMENAU`.
2. **Coordenadas das demais estações** (Ituporanga, Brusque, Warnow, Ilhota, Botuverá, Barragem
   Oeste) — com elas os `codigo_ana` que faltam podem ser gravados **e conferidos pela trava**.
3. **Qual coordenada o pino de Blumenau deve usar** — decisão do Jefferson.
4. **Rio do Sul: qual régua pareia com qual série da ANA** (Oeste × Sul × Açu).
5. A área de 5.160 km² da 83094000 — conferir antes de qualquer uso.
