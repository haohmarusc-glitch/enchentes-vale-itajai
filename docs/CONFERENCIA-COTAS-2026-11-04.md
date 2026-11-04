# Conferência das cotas do cadastro contra o que as Defesas Civis publicam (04/11/2026, 21h05 UTC)

Pedido do Jefferson, no PR do vínculo da DC-10 no Mirim (#568): "verifique se as réguas batem com as cotas das
Defesas Civis". Fonte lida **ao vivo**, só leitura: o portal da Defesa Civil de Itajaí
(`monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios`, JSON embutido na página, municípios 1 a 4) e, para
o Plano de Contingência v17 (22/12/2025, Tabela 11), o que o cadastro guarda via `comum.cotas_do_plano`. Nada foi
alterado no cadastro. Nenhum ofício.

## Itajaí — as onze réguas DC (portal, município 1)

| Régua | Portal (A / Al / E) | Cadastro | Plano v17 | Veredito |
|---|---|---|---|---|
| **DC-10 Limoeiro** | 8,00 / 9,00 / 10,00 | 8,00 / 9,00 / 10,00 | igual | **bate** (cotas_verificado) |
| **DC-05 Sítio Hilário** | 1,60 / 2,20 / 3,00 | igual | igual | **bate** |
| **DC-06 Itamirim** | 1,50 / 1,85 / 2,55 | igual | igual | **bate** |
| **DC-04 Vitalmar** | 1,50 / 1,85 / 2,25 | igual | igual | **bate** (travada: estuário) |
| DC-11 Santa Regina | 3,00 / 4,00 / 5,00 | igual | igual | bate (cotas_verificado) |
| DC-02 Praça | 1,60 / 2,00 / 2,50 | igual | igual | bate (travada) |
| DC-03 SEMASA | 1,48 / 1,85 / 2,50 | igual | igual | bate |
| DC-07 Portal I | 1,00 / 1,40 / 1,50 | igual (provisória) | 1,00 / 1,35 / 1,65 | cadastro = portal; Plano diverge, **já documentado** (10/10/2026) |
| DC-08 Canhanduba | 1,70 / 2,30 / 2,89 | igual (provisória) | 1,80 / 2,30 / 2,89 | cadastro = portal; Plano diverge, **já documentado** (08/10/2026) |
| DC-01 CEPSUL | 1,21 / 1,61 / 1,75 | 1,16 / 1,36 / 1,56 | igual ao cadastro | **portal ≠ Plano**, igual a 13/09/2026; travada, sem aviso |
| DC-09 Lidia Puel | 1,22 / 1,42 / 1,62 | 1,12 / 1,32 / 1,52 | igual ao cadastro | **portal ≠ Plano**, igual a 13/09/2026; travada, sem aviso |

As **quatro réguas do vínculo novo** (DC-10, DC-05, DC-06, DC-04) batem nas três fontes. As duas divergências
(DC-01 e DC-09) são as mesmas da conferência de 13/09/2026 (`cotas_conferencia_2026_09_13`): o portal mudou e o
município não publicou a troca; as duas estão travadas (estuário) e não pintam nem avisam. Decisão de 19/09/2026
mantida: o cadastro segue o Plano.

## As outras cidades que o portal de Itajaí republica (municípios 2–4)

| Cidade / régua | Portal de Itajaí (A / Al / E) | Cadastro (fonte) | Veredito |
|---|---|---|---|
| Blumenau — PADKND | 4,00 / 6,00 / 8,00 | 3,00 (monitoramento) / 4,00 / 6,00 / 8,00 (AlertaBlu, `nivel_oficial.json`) | **bate** |
| Brusque — DCSC-00019 | 3,50 / 5,00 / 6,00 | 3,00 (atenção) / 5,00 (emergência) — legenda da estação 79 do portal de Brusque, 07/09/2026 | **diverge**, a "terceira escala" já registrada em `cotas_divergencia` (19/09/2026). Portal de Brusque não responde daqui (sem conexão); conferir de novo pela VPS ou pelo navegador |
| Rio do Sul — DCSC-00013 | 5,00 / 6,00 / 7,00 | 4,50 / 5,50 / 6,50 (API Asthon, `band_thresholds` da Ponte Dom Tito Buss) | **diverge**, a "quarta escala" já anotada em `coleta_itajai_portal.py`; o portal de Itajaí republica sem coordenada |

Nas duas divergências o portal de Itajaí é um **repasse** (estação "MKS", sem coordenada), e o cadastro segue a fonte
do próprio município (Brusque) ou do operador da régua (Rio do Sul). Nada muda sem documento do operador.

## O que isso significa agora (leitura das 21h00 UTC, 18h00 de Brasília, cheia em curso)

| Régua | Nível | Pelo cadastro | Pelo portal de Itajaí |
|---|---|---|---|
| Brusque DCSC-00019 | 5,51 m (18h01) | **emergência** (≥ 5,00) | "alerta" (5,00–6,00) |
| DC-10 Limoeiro | 8,41 m (18h00), subindo | **atenção** | atenção |
| DC-05 Sítio Hilário | 2,08 m | atenção | atenção |
| DC-08 Canhanduba | 2,51 m | alerta | alerta |
| Rio do Sul DCSC-00013 | 7,70 m | **inundação** (≥ 6,50) | emergência (≥ 7,00) |
| Blumenau PADKND | 4,71 m | atenção | atenção |

Em Brusque e Rio do Sul a faixa de hoje só difere no **nome** do degrau mais alto, não no fato de o rio estar acima
dele. Com o PR #568, o Mirim abaixo do Limoeiro passa a mostrar a atenção da DC-10 (8,41 m) em vez da emergência de
Brusque — que é exatamente o caso que motivou o vínculo.

## Como refazer

```
curl -sS -A 'enchentes-vale-itajai' 'https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/rios?municipio_id=1' \
  | python3 -c "import sys,re,html,json; p=json.loads(html.unescape(re.search(r'data-page=\"([^\"]*)\"', sys.stdin.read()).group(1))); \
  [print(e['codigo'], e.get('atencao_m'), e.get('alerta_m'), e.get('emergencia_m')) for e in p['props']['estacoes'] if 'rios' in e['capacidades']]"
```
