# Propostas da auditoria de 03/10/2026 — itens 2, 3 e 4

Os itens 2, 3 e 4 da auditoria tocam dado ou topologia. Aqui ficam a investigação e a proposta de cada um.

> **Decisões do Jefferson de 04/10/2026, aplicadas:**
> - **Item 2 — sim:** Guabiruba virou afluente lateral do Mirim (`_topologia` no Mirim, tronco Vidal Ramos →
>   Botuverá → Brusque → Itajaí). O Monitor passa a mostrar o Mirim em Tronco e Afluentes; nenhum arquivo
>   protegido foi editado.
> - **Item 3 — sim, zero local:** a DCSC-00029 abaixo de 10 m vale como régua do ribeirão (zero próprio);
>   ≥ 10 m continua suspeita (`SUSPEITA_SO_ACIMA_DE_M`). O histórico continua cortado em 01/04/2026 até a
>   data da volta ser conferida no servidor (comandos abaixo): juntar o "antes" e o "depois" afirmaria
>   que o zero é o mesmo, e isso não foi conferido.
> - **Item 4 — opção B:** rótulo que declara a referência, sem mexer em `referencia` dos registros.

## Item 2 — Guabiruba como afluente lateral do Mirim

### O que está errado hoje
- O Mirim é uma fila: Vidal Ramos → Botuverá → **Guabiruba** → Brusque → Itajaí (`ordem` 1 a 5).
- A estação de Guabiruba fica no **ribeirão Guabiruba**, afluente. O pino está a 4,24 km do Mirim
  (`cotas_ressalva` de Guabiruba). O próprio cadastro de Brusque lista `"afluentes": ["rio Guabiruba"]`.
- Efeito na tela: Brusque diz "A água vem de Guabiruba" e "Rio acima: Guabiruba". Guabiruba diz
  "A água vem de Botuverá" e "desce para Brusque". A água de Botuverá não passa por Guabiruba.

### Não há caminho leve
- O validador distingue árvore de fila só pela presença de `_topologia`. Uma fila não admite cidade fora
  dela, e uma cidade com `ordem: null` numa fila quebra o `sorted()` do validador.
- Mudar Guabiruba para `afluentes_monitorados` não serve. A trava do `codigo_dcsc` exige que ela continue
  em `rios['itajai-mirim'].cidades`, e essa lista não aparece em tela nenhuma.

### Mudança proposta

**`data/estacoes.json`**
- Mirim ganha `_topologia` com `tipo: "arvore"` e `tronco_sequencia: [vidal-ramos, botuvera, brusque, itajai]`.
- `cabeceiras_paralelas: []` precisa existir: a tela inicial espalha a lista sem `?? []`.
- `afluentes_laterais: [{ id: "guabiruba", entra_perto_de: "brusque", rio: "Ribeirão Guabiruba" }]`.
  O ponto exato da confluência não tem fonte. Fica "perto de Brusque", como o Açu faz com Ibirama e Timbó.
- Todas as cidades do Mirim passam a `ordem: null`. As quatro do tronco ganham `ramo: "mirim_tronco"`
  (já existe em `RAMOS_VALIDOS`) e `ordem_no_ramo` de 1 a 4. Guabiruba ganha `ramo: "ribeirao_guabiruba"`
  e `ordem_no_ramo: 1`.
- A `observacao` de Guabiruba ("posição na sequência ainda não conferida") é reescrita.

**Validador e scripts**
- `validar_dados.py`:
  - a conferência do tronco e as posições do trânsito usam `"tronco_acu"` fixo; passam a usar o ramo do
    tronco de cada rio;
  - entra `ribeirao_guabiruba` em `RAMOS_VALIDOS`;
  - entra `"mirim_tronco": "itajai-mirim"` em `TRACADO_DO_RAMO`; sem isso, os pinos do Mirim deixam de ser
    conferidos no traçado e a exceção de 5 km de Guabiruba nunca é usada.
- `bot.py`:
  - a previsão a jusante só acha posição no `tronco_acu` e precisa ser generalizada;
  - `/rios` passa a imprimir o Mirim em blocos.
- `calibrar_transito.py` pareia vizinhos por `ordem` e geraria botuvera→guabiruba→brusque; tem de ler a
  topologia. `auditar_lacunas.py` também.
- O gabarito do trânsito é regenerado com `npm run gabarito` e o diff é conferido. Guabiruba não está em
  nenhum trecho de `transito.json`.

**Telas:** nenhum código novo. Tudo já lê a topologia quando ela existe:
- cartão de descida;
- "Rio acima", que vira Botuverá para Brusque;
- lista do rio com tronco e afluentes;
- menu das cidades;
- descrição do rio;
- mapa do rio, onde Guabiruba deixa de pintar o Mirim e continua como pino.

**Testes que mudam de propósito**
- `web/src/dados/topologia.test.ts` exige que o Mirim seja fila.
- `menuDasCidades.test.ts`, `descricaoDoRio.test.ts` e `arvoreDaBacia.test.ts` fixam a fila do Mirim.
- `scripts/teste_validar_dados.py` exige "o Mirim é fila".
- `teste_auditar_lacunas.py` espera o elo guabiruba→brusque como "roteamento".
- Conferir também `canalDoTronco.test.ts`, `rotulosDaBacia.test.ts` e `teste_bot.py` (`/rios`).

**Documentos:**
- `TOPOLOGIA-CANONICA.md`: diz que o Mirim é fila e lista os ramos;
- `CLAUDE.md`: linha do `/mirim`;
- `_meta`, `convencoes` e os comentários de `tipos.ts` e `carregar.ts` ("hoje só o Açu").

### Decisão necessária: o Monitor muda de comportamento
Nenhum arquivo protegido do Monitor precisa ser editado. Mesmo assim o Monitor muda, pelo dado e por
arquivos não protegidos:
- o menu do Mirim vira Tronco e Afluentes;
- Guabiruba deixa de pintar o Mirim no mapa;
- o painel lateral marca Guabiruba como fora do eixo.

A CI não acusa isso, porque nenhum arquivo protegido muda. A regra "o Monitor não muda" pede a sua
decisão: aplicar com o rótulo `monitor-autorizado`, ou não aplicar.

Também ficou desatualizado no `TOPOLOGIA-CANONICA.md`: ele diz que Apiúna saiu do eixo, mas o
`estacoes.json` ainda a tem em `tronco_sequencia`.

## Item 3 — A regra de suspeita de Guabiruba

### O que existe hoje
- `SUSPEITAS` marca a DCSC-00029 pelo valor de "~24,8 m".
- `QUEBRAS_DE_SERIE` corta a série em 01/04/2026 17:40 e mantém só o "antes".
- O coletor manda Guabiruba para `suspeitas`. O site e o bot não a mostram.

### Evidência
| Quando | O que mostra | Fonte |
|---|---|---|
| 01/04/2026 17:30 → 17:50 | 0,51 → 16,21 → 24,68 m, num passo | série DCSC, `cadastro_dcsc.py` |
| 01/04 a 09/09/2026 23:10 | 22.054 leituras, **nenhuma** abaixo de 10 m | `data/brutos/dcsc-historico-resumo-2026-09-15.json` |
| 03/10/2026 23:01 | **0,63 m**, em `suspeitas` | `ultimo_nivel_sc.json` do branch `tempo-real` |
| 03/10/2026 23:50 UTC | 0,63 m | evidência entregue com a auditoria |

### Conclusão
- A estação voltou a publicar um valor de régua local em algum momento **entre 09/09/2026 23:10 e
  03/10/2026 23:01**. A data exata não pôde ser conferida daqui: a API da DCSC é bloqueada neste ambiente.
  A série inteira (`data/series/dcsc/`) fica fora do git.
- A tabela de 26/09 no `CLAUDE.md` dá 2,14 m em 11/07 e 2,04 m em 31/08. Isso **contradiz** o download
  de 15/09, que não tinha nada abaixo de 10 m depois de 01/04. Há duas explicações possíveis, e a série
  baixada de novo decide entre elas:
  - a DCSC reprocessou o histórico para o zero local depois de 15/09;
  - os números de 26/09 passaram por alguma conta.

### Como conferir no servidor
Os comandos só leem: baixam para uma pasta nova e não mexem em cadastro.

```
cd /opt/enchentes-vale-itajai/scripts
python3 baixar_historico_dcsc.py DCSC-00029 --dias 88 --destino /tmp/guabiruba-2026-10-04
python3 - /tmp/guabiruba-2026-10-04 <<'EOF'
import glob, json, sys, collections
pts = {}
for f in glob.glob(sys.argv[1] + "/DCSC-00029/*.json"):
    for it in json.load(open(f))["resposta"]["data"]["historic"]["items"] or []:
        v = it.get("rio_nivel")
        if it.get("ts") and isinstance(v, (int, float)):
            pts[it["ts"][:16]] = v
s = sorted(pts.items())
print("leituras:", len(s), "de", s[0][0] if s else "-", "a", s[-1][0] if s else "-")
dia = collections.defaultdict(list)
for t, v in s:
    dia[t[:10]].append(v)
for d, vs in sorted(dia.items()):
    print(d, "min %.2f max %.2f n=%d" % (min(vs), max(vs), len(vs)))
for (t0, v0), (t1, v1) in zip(s, s[1:]):
    if (v0 >= 10) != (v1 >= 10):
        print("TROCA:", t0, v0, "->", t1, v1)
EOF
```

- Se as linhas "TROCA" mostrarem um passo de ~24 m para ~0,5 m, essa é a data da volta.
- Se julho e agosto já vierem perto de 2 m, a DCSC reprocessou o histórico.

### Proposta, depois da data conferida
- `QUEBRAS_DE_SERIE["DCSC-00029"]` vira uma lista de quebras. Entra a segunda, com a data da volta,
  `grandeza_depois: "régua do ribeirão (zero local)"` e a evidência.
  - O consolidador e o coletor passam a manter os trechos de régua local e cortar o trecho em altitude.
  - Há teste para os dois cortes.
- `SUSPEITAS`: o motivo passa a valer só para leituras no trecho em altitude. Também entra uma trava por
  valor (acima de 10 m continua suspeita), para o caso de a estação trocar de novo.
- Antes de juntar o "antes" e o "depois", conferir que o zero é o mesmo: 0,51 m em 01/04 antes do passo,
  0,63 m hoje. Se a DCSC não disser, o "depois" fica como série própria.
- O que **não** muda: Guabiruba continua sem cota, no ribeirão, com `usar_para_cota: false`. Os picos de
  2026 continuam fora de `enchentes.json` até a sua decisão.

## Item 4 — Rótulo do histórico de Brusque

### O que a tela afirma
- "Alturas na régua de Brusque (Ponte Estaiada – DCSC). Não compare com outra cidade." vale para os 28
  picos, desde 1961.
- O texto sai de `legendaDaEscala` (`web/src/logica/referencias.ts`). Ela afirma a régua sempre que a
  série não mistura referências. Nenhum dos 28 registros tem o campo `referencia`, e campo ausente é
  tratado como "régua".

### De onde vêm os 28 picos
| Período | Fonte | Registros |
|---|---|---|
| 1961, 1978, 1983, 2001, 2015 | ANA 83900000 (leitura das 07h/17h ou média) | 5 |
| 1984, 2008, 2011, 2013 | imprensa, UNIVALI, Revista Portuária | 4 |
| 2019–2024 | boletins e lista da Defesa Civil de Brusque, Prefeitura | 19 |

A nota dos registros da ANA diz que a 83900000 coincide com a régua municipal ao centímetro em
2019–2021 (590 × 5,90; 568 × 5,68), "e não se sabe desde quando".

### O mecanismo de `referencia` serve, sem código novo
O filtro de `cenarioAnterior.ts`, usado no "Quanto falta", e o pareamento de `previsao.ts` valem para
qualquer cidade:
- `referencia: null` sai da conta, e a tela diz quantos ficaram de fora;
- a legenda do gráfico vira o aviso de mistura.

### Proposta A — dado (recomendada)
- Os 19 registros de 2019–2024 da Defesa Civil de Brusque recebem `referencia: "régua"`.
  - A nota cita a coincidência de 2019–2021 e o par provado em 2026 (1.287 pares).
  - 2022–2024 é a mesma fonte, sem cruzamento direto. Se preferir, esses ficam `null` até conferir.
- Os 9 anteriores a 2019 recebem `referencia: null` e
  `referencia_hipotese: "zero da ANA 83900000; coincide com a régua de hoje em 2019–2021, antes não conferido"`.
  Nenhum deslocamento é inventado.
- Efeito:
  - o gráfico avisa que mistura referências;
  - o "Quanto falta" usa só os 19 e diz que 9 ficaram de fora;
  - a previsão a jusante pareia igual com igual.

### Proposta B — só texto, sem mexer em dado
`legendaDaEscala` ganha uma nota por cidade. Para Brusque:

> Alturas de Brusque como foram publicadas: de 2019 a 2024, boletins da Defesa Civil de Brusque; antes,
> a ANA (estação 83900000) e outras fontes. A ANA coincide com a régua de hoje (Ponte Estaiada – DCSC)
> ao centímetro em 2019–2021; antes disso a referência não foi conferida. Não compare com outra cidade.

A proposta B corrige o cabeçalho, mas o "Quanto falta" continua comparando a leitura de hoje com 1961.
Por isso a recomendação é a A. O texto da B pode entrar junto, como explicação.

## O que foi só relatado
- **Monitor, item 1:** no motor do mapa, uma leitura municipal velha também bloqueia a faixa e o número da
  rede estadual naquele pino. No mapa do rio isso deixou de acontecer, porque a leitura velha sai antes do
  motor. No Monitor, corrigir exige editar `mapaMotor.ts` (arquivo protegido). O Monitor mostra a idade
  junto do número, então o "número seco" não acontece lá.
- **Monitor, menores:** o rótulo do pino de Itajaí fica atrás do chip da maré, e há rolagem horizontal em
  1463 px. Não foi mexido.
- **Rio do Sul:** "Alerta" com 5,77 m (cota 5,50). Há quatro escalas divergentes, nenhuma confirmada com
  a COMPDEC. Fica como pendência de ofício.
