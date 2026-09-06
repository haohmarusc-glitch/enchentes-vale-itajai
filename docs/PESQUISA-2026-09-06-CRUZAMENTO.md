# Cruzamento da pesquisa de 06/09/2026 com o repositório

Documentos recebidos: `RESULTADOS.md` e `historicos-candidatos.json` (96 registros
candidatos, nenhum importado). Este arquivo registra **o que o cruzamento com o
repositório revelou** — não é importação nem certificação.

> **RESOLVIDO EM 07/09/2026.** O Jefferson abriu o PDF no navegador dele e a
> pesquisa estava certa: o repositório é que estava errado, para o lado
> perigoso. As cotas foram corrigidas para 3 / 4 / 5,5 e os 16 picos entraram.
> O registro do problema fica abaixo, porque como o erro entrou importa tanto
> quanto o número certo. Ver `docs/INDAIAL-RESOLVIDO.md`.

## ⚠️ ~~URGENTE~~ RESOLVIDO — Indaial: as cotas do site estavam 3 m acima da fonte

O repositório tem, para Indaial:

```
cotas_m:      { "atencao": 6.0 }
fonte_cotas:  Página "Cotas de enchente" da Defesa Civil de Indaial
              https://indaial.atende.net/subportal/defesa-civil-indaial/pagina/cotas-de-enchente
```

A pesquisa leu o **PDF oficial vinculado a essa MESMA página** e relata:

> normalidade até 3 m, atenção de 3 a 4 m, alerta de 4 a 5,5 m e emergência
> acima de 5,5 m

**As duas leituras não podem estar certas ao mesmo tempo.** Se o PDF estiver
correto, o site mostra "abaixo da atenção" num nível (5,6 m, por exemplo) que o
município já trata como **emergência**. É a direção perigosa: alguém se sentindo
mais seguro do que está.

Não foi corrigido em nenhuma direção, porque a fonte não é alcançável do
ambiente onde este cruzamento foi feito (o proxy recusa
`indaial.atende.net`). **Resolver isto vem antes de qualquer importação de
histórico.**

O que decide: abrir a página, baixar o PDF de cotas e ver (a) qual escala ele
publica e (b) se ela é da mesma régua a que o app se refere. A pesquisa também
registra que o documento identifica o **RN 1402-X do IBGE, perto da rua
Tiradentes, cota 61,49 m** — o que sugere que a escala do PDF pode estar
amarrada a outra referência que não a régua operacional.

Enquanto não se resolver, o `atencao: 6.0` fica como está: trocá-lo por 3,0 sem
conferir a régua criaria alarme onde não há, e trocar por nada apagaria a única
cota que Indaial tem.

## ✅ Confirmações independentes (nada a mudar)

| Cidade | Repositório | PLANCON citado pela pesquisa | Resultado |
|---|---|---|---|
| **Taió** | monitoramento 5,0 · atenção 7,0 · alerta 8,0 · emergência 9,0 | jan/2026: normal ≤5 · monitoramento >5–7 · atenção >7–8 · alerta >8–9 · emergência >9 | **bate exatamente** |
| **Ilhota** | atenção 9,2 · alerta 10,0 · emergência 10,5 | 2025–2028 p.16: normal ≤9,20 · atenção 9,20–10 · prontidão 10–10,50 · emergência >10,50 | **bate**; o repo mapeia "prontidão" → `alerta` |

São corroborações por leitura independente da mesma fonte — não dado novo, mas
elevam a confiança nas duas únicas cidades do tronco com cotas completas.

## Barragem Oeste: mais uma divergência de capacidade, a registrar sem escolher

- Repositório (`data/hidraulica.json`): `armazenamento_Mm3: 83` (JICA).
- PLANCON de Taió, jan/2026: **~100,6 hm³**.

O repositório já tem a regra para isso, no próprio arquivo
(`_areas_divergentes`): *"Registrar as duas, nunca fundir nem escolher em
silêncio."* A pesquisa chega à mesma conclusão: *"não devem ser escolhidos
apenas por parecerem mais recentes"*. Falta identificar, para cada número, se é
volume **útil, total ou de espera**, a cota associada e a vigência.

## Histórico: 86 registros para duas cidades que hoje têm ZERO

| Cidade | No `enchentes.json` hoje | Candidatos |
|---|---:|---:|
| Gaspar | **0** | 70 |
| Indaial | **0** | 16 |
| Blumenau | 113 | 10 |

Gaspar e Indaial estão entre as "10 de 14 cidades ainda sem pico histórico
levantado" que a tela declara. Preencher as duas destravaria o pareamento
montante↔jusante no tronco (hoje "dados insuficientes" por < 5 eventos).

**O que impede a importação direta, por cidade:**

- **Gaspar (70):** a fonte publica a **data de INÍCIO do evento, não a do pico**
  (a própria pesquisa marca isso nos 70 registros), e **não explicita a
  referência vertical**. Importar data de início como data de pico corromperia
  justamente o cálculo de tempo de trânsito, que é medido de pico a pico. Um
  registro traz término em **24/11/9855**, erro evidente da fonte, preservado
  sem correção inferida — correto, e sinal de que a tabela tem sujeira.
- **Indaial (16):** bloqueado pelo item urgente acima. Não faz sentido importar
  picos de 1852–2022 antes de saber a que régua a escala se refere. A linha de
  2014 é literalmente **08/09/2014, 6,38 m**, e a própria pesquisa pede
  corroboração dessa data.
- **Blumenau (10):** risco de **duplicação**, não de falta. A pesquisa avisa:
  *"ausência por data exata não prova evento novo"*, e o repo tem registros com
  data incompleta que podem ser os mesmos eventos. Some-se a
  `REGRA_REFERENCIA_BLUMENAU`: todo registro precisa de `referencia` do conjunto
  fechado, e conflito de valor no mesmo (cidade, evento) usa `divergencias`,
  nunca dois registros.

**Caminho sugerido, na ordem:** (1) resolver Indaial; (2) importar Gaspar com
`data` marcada como início-do-evento e `referencia: null`, sem usá-la para
calibrar trânsito; (3) Blumenau por último, um a um, contra os 113 existentes.

## Maré: a lacuna de outubro tem fonte

A tábua anual do **CHM/Marinha** para o Porto de Itajaí cobre janeiro a
dezembro, **inclusive outubro**, que falta na base. Cabeçalho: UTC−03,
26°54,3′ S, 48°39,2′ W, nível médio 0,6 m, carta 1841.

Duas ressalvas que a própria pesquisa faz, e que valem: é **previsão
astronômica**, não medição nem maré meteorológica; e o "nível médio 0,6 m" do
cabeçalho **não é conversão para a régua fluvial**. Importar exige parser
próprio e proveniência por evento, sem misturar em silêncio com a série UNIVALI
que a tela já usa.

## O que a pesquisa NÃO resolveu

Continuam abertos, e são os mesmos de antes: horários de pico e identificação de
estação/zero por registro histórico (sem isso não há calibração de trânsito);
cotas de rua conflitantes; versão vigente do PLAMCON de Ibirama; e a ressalva de
que cotas de Ascurra em boletins podem se referir ao **Ribeirão São Paulo**, não
ao Itajaí-Açu — associar automaticamente seria erro.
