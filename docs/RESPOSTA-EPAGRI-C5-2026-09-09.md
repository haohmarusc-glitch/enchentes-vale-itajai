# Resposta da EPAGRI/CIRAM ao ofício C5 — a rede telemétrica do litoral está sendo desmontada

Data: 09/09/2026. Remetente: Equipe de Hidrologia da EPAGRI/CIRAM (sshidrosc@epagri.sc.gov.br),
em resposta ao C5 de `docs/oficios-prontos.md`. Tabela anexa transcrita em
`data/brutos/epagri-ciram-resposta-c5-2026-09-09-estacoes.tsv` (de captura de tela: códigos e
nomes confiáveis; coordenadas e datas podem ter erro de leitura).

## O que a carta diz, na ordem em que pesa

1. **Sem acesso ao Rios On-line, porque ele vai deixar de existir.** A rede de estações
   fluviométricas telemétricas da Vertente Atlântica de SC pertence à ANA e era operada pela
   EPAGRI/CIRAM. A pedido da própria ANA, a manutenção parou em **junho de 2025**; desde meados de
   2026 a rede está sendo **desmobilizada**, com equipamentos removidos ainda em **setembro de 2026**;
   até o fim de 2026 a operação encerra por completo. O site Rios On-line e os boletins diários
   continuam **só até as estações serem removidas**; depois, o site sai do ar.
2. **Os dados atuais podem não estar corretos.** A EPAGRI não garante que sejam fidedignos para
   divulgação por terceiros nem para decisão em situação de risco.
3. **Os limiares de criticidade não serão divulgados**: não são revisados desde **2023**.
4. **Quem assume a divulgação é a SDC** (Secretaria de Proteção e Defesa Civil), no site de
   monitoramento estadual que o projeto já lê. Desde 2024 a Sala de Situação é da **Semae** com a SDC.
5. **O que a ANA ainda recebe está no Hidrotelemetria**, acessível pela API por código de estação —
   e a carta lista as estações da bacia que passaram pelo Rios On-line. **Só quatro seguem ativas:**
   Barragem Taió Montante (83029900), Saltinho (83050000), Ituporanga (83250000) e Salseiro
   (83892990). As demais foram desativadas por falta de manutenção ou qualidade de dado.
6. **Salseiro fica em Vidal Ramos**, com coordenada (−27,3228 / −49,3512).
7. O SGB/CPRM publica limiares das estações da **Vertente do Interior** em
   sgb.gov.br/sace — não é a nossa bacia.

## O que ela explica de graça

| Mistério no repo | Explicação |
|---|---|
| A telemetria da ANA devolvia vazio para 83900000 (Brusque) e 83800002 (Blumenau), com o inventário dizendo "telemétrica, operando" | **As duas estão desativadas**: Brusque em 27/03/2025, Blumenau em 04/04/2026. As cinco estações que `sonda_ana_api.py` testou eram todas desativadas; "vazio" era a resposta certa. O e-mail à ANA sobre isso deixa de ser necessário |
| "Salseiro é de Vidal Ramos?" | Sim. Coordenada da EPAGRI a ~7,0 km da nossa régua (−27,38547 / −49,35812): confirma o `codigo_ana_nao_e` — mesmo município, outra régua |
| A 83050000 de Taió | A EPAGRI a chama de **Saltinho** (ativa, desde 1997); a **83050001 "Taió"** é outra, desativada em 20/12/2024, a ~100 m. O HidroWeb chama a 83050000 de "TAIÓ" |
| Rio do Sul | A EPAGRI lista **83270000 "Rio do Sul – Novo"**, em manutenção; o cadastro usa **83300200** com o mesmo nome. Dois códigos, um nome: conferir no inventário qual é qual |

## O que muda para o projeto

- **Ituporanga:** a 83250000, que a SPDC/SC designa como estação oficial da cidade (escala
  1,40 / 1,90 / 2,60), é operada pela EPAGRI e **será desmontada até o fim de 2026**. A escala
  estadual ficará sem estação. Mais um motivo para a régua municipal (Ponte Vitório Sens) e para
  a pergunta ao Elias Sieves.
- **Vidal Ramos:** o caminho "EPAGRI/Rios On-line" para a cota (citado em
  `docs/API-ASTHON-COMPLETA.md` e `cotas-municipais/vidal-ramos.md`) **fechou**. Resta a COMPDEC.
- **Rede estadual (SDC):** vira a fonte oficial de telemetria por decisão do estado, não só por
  conveniência nossa. O que já está no cadastro sobre datum bruto (`usar_para_cota: false`)
  continua valendo.
- **Boletins da EPAGRI** (`data/brutos/epagri-ciram-boletim-*.pdf`): fonte com prazo; a partir
  de outubro podem parar.
- **Marégrafos da EPAGRI** (`coleta_mare_ciram.py`, seção 3b de `docs/fontes-tempo-real.md`): a
  carta fala da rede **fluviométrica** da ANA; não diz nada dos marégrafos. Perguntar antes de
  supor que continuam.

## O que testar (VPS, com a credencial da ANA)

A sonda testou só estações desativadas. Testar as quatro ativas, e num evento passado:

```
python3 scripts/sonda_ana_api.py --estacoes 83029900,83050000,83250000,83892990 --data 2023-11-17 --intervalo DIAS_7
```

Se a série telemétrica vier, são níveis **horários** de Taió, Ituporanga e Salseiro na cheia de
novembro de 2023 — hora de pico nas cabeceiras, que é o que o gabarito de trânsito não tem.
