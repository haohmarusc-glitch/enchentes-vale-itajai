# AIBH do Rio Itajaí-Açu — o que aproveitar (e o que não)

Fonte: **Avaliação Integrada da Bacia Hidrográfica do Rio Itajaí-Açu**, Volume 3 (Diretrizes,
Recomendações e Conclusões), março/2021. Consultoria CEDRO + ENGERA, para o IMA (Termo de Referência
via Ofício DIRA/GELOP nº 3225/2019). Audiência pública em Indaial, 14/06/2023.
PDF: `apiuna.sc.gov.br/uploads/sites/390/2023/03/3_AIBH_Diretrizes-Recomendacoes-e-Conclusoes.pdf`

---

## ⚠️ CREDIBILIDADE — ler antes de usar qualquer número daqui

**Formalmente sólido:** exigência legal do IMA, equipe com registro em CREA/CRBio, modelagem hidráulica
em HEC-RAS 1D num trecho de 85,5 km (Lontras → Blumenau), audiência pública realizada.

**MAS o estudo foi pago pelos empreendedores das 12 usinas.** O próprio documento diz: os empreendedores
se dispuseram a fazê-lo *"valendo-se exclusivamente de recursos próprios"*. O objetivo é licenciar PCHs.
E a conclusão sobre cheias é exatamente a que interessa a eles:
> "os estudos de modelagem hidrológica e hidráulica demonstraram que **não são ampliados os impactos das
> cheias** na bacia em decorrência dos aproveitamentos hidrelétricos"

Pode ser verdade — mas **não é fonte neutra sobre risco de enchente**. Regra para o projeto: usar daqui
apenas dados **descritivos e verificáveis** (vazões, geografia, existência de obras). NÃO usar as
conclusões sobre impacto de cheia como se fossem avaliação independente de risco.

---

## ✅ O QUE APROVEITAR

### 1. Confirmação independente da topologia (o mais valioso)
O AIBH confirma, por fonte oficial e independente, a árvore que levantamos no mapa:
- **"PCH Foz do Hercílio, localizada após a confluência dos rios Hercílio e Itajaí-Açu"**
  → confirma que o **Hercílio é afluente** e onde ele entra. Bate com nosso achado de que Ibirama está
  no Hercílio, não no tronco.
- **"trecho localizado entre os municípios de Ascurra e Indaial, a montante da confluência com o Rio
  Benedito, com aproximadamente 14 km"**
  → **RESOLVE a pendência do Benedito**: ele entra **depois de Ascurra e antes de Indaial**, e o trecho
  livre entre a confluência e Ascurra tem ~14 km. Era a dúvida que o `achar_confluencias.py` iria medir.
- CGHs Tafona, J. Grabowski e Gunther Faller descritas como **"a montante da confluência do rio Itajaí-Açu
  com o rio Hercílio"** → reforça a mesma estrutura.

### 2. Vazões de referência do trecho Lontras–Blumenau
| Condição | Vazão |
|---|---|
| Estiagem | 7 a 20 m³/s |
| Média | 100 a 230 m³/s |
| **Cheia QTR2** (2 anos) | **800 a 4.000 m³/s** |
| **Cheia QTR1000** | **1.500 a 8.500 m³/s** |
Uso: contexto e sanidade. Não é cota — é vazão, e o site trabalha com nível de régua. Serve para dizer
a ordem de grandeza de uma cheia e para futuros trabalhos com curva-chave.

### 3. ⚠️ ALERTA OPERACIONAL: obra que pode MUDAR as cotas de Rio do Sul
O documento descreve o **"Projeto de Melhorias Fluviais no Rio Itajaí, trecho Rio do Sul até Lontras"**,
da Secretaria de Defesa Civil de SC, derivado do *Plano Integrado de Prevenção e Mitigação de Riscos de
Desastres Naturais na Bacia do Rio Itajaí* (SANTA CATARINA, 2009). O projeto prevê:
- **rebaixamento do leito** do Itajaí-Açu no trecho Rio do Sul–Lontras;
- **estrutura de controle de nível com comporta segmento**;
- tempo de retorno de projeto: **50 anos**.

**STATUS (informado pelo usuário, 02/09/2026): a obra NÃO foi executada e está EM LICITAÇÃO pelo governo
estadual neste ano.** Ou seja: não é hipótese remota — é obra que vai acontecer.

**Por que isso importa ao site, e muito:**
1. **As cotas de Rio do Sul vão mudar.** Rebaixar o leito altera a relação nível↔vazão (a curva-chave):
   a mesma vazão passará a dar um nível MENOR na régua. As cotas atuais (atenção 4,50 / alerta 5,50 /
   emergência 6,50 / abrigos 7,00 m) valem para o rio de hoje.
2. **A comporta passa a controlar o nível em cheia.** Deixa de ser um rio livre naquele trecho — o nível
   passa a depender também de decisão operacional, como já acontece com as barragens Oeste e Sul.
3. **O histórico de picos de Rio do Sul vira série quebrada.** Níveis medidos antes e depois da obra não
   são diretamente comparáveis — é o mesmo tipo de problema da referência IBGE×régua em Blumenau, mas
   causado por mudança física do rio, não por datum.
4. **Afeta a previsão a jusante.** Rio do Sul é o ponto onde nasce o Açu e a primeira referência do tronco;
   qualquer correlação Rio do Sul → Indaial/Blumenau calibrada com dados de hoje precisará ser refeita.

**AÇÃO:**
- Acompanhar a licitação e o cronograma de execução (Defesa Civil de SC / SDC).
- Ao concluir a obra: revalidar as cotas com a Defesa Civil de Rio do Sul e **marcar a data no histórico
  como quebra de série** — `data/enchentes.json` precisa de um campo indicando "antes/depois das melhorias
  fluviais" para os picos de Rio do Sul.
- Perguntar à SDC se haverá **nova curva-chave** para a estação após a obra.

### 4. Cotas absolutas citadas (referência altimétrica, não régua)
No eixo da PCH Rio do Sul (Lontras): **nível normal 327,10 m**, soleira da comporta basculante **324,10 m**.
São cotas em **datum altimétrico absoluto**, NÃO na régua de Rio do Sul. Não misturar — é o mesmo tipo de
erro de referência já registrado no projeto (regra: elevação absoluta ≠ nível de régua).

### 5. Infraestrutura que condiciona a bacia
"Ao longo do rio desenvolve-se a BR-470, que interliga os maiores núcleos urbanos situados ao longo da
calha fluvial." Explica por que as cidades da cadeia estão todas à beira do rio — contexto útil para a
tela, não dado.

---

## ❌ O QUE NÃO USAR
- **As figuras "Alterações de níveis d'água"** (Fig. 3-1 a 3-4, 3-10 a 3-13): são **diferenças entre
  cenários** com e sem usina, não perfis absolutos de cheia. Não servem para cota nem para previsão.
- **A conclusão de que as PCHs não agravam cheias**: pode ser verdade, mas vem de estudo pago pelos
  empreendedores. Não citar como avaliação independente.
- Modelagem HEC-RAS **1D**: o próprio documento reconhece a limitação — *"o modelo HEC-RAS 1D não foi
  desenvolvido com o objetivo de avaliar impactos localizados"* e recomenda modelagem 2D para áreas
  urbanas. Não usar para inferir alagamento de bairro.

---

## Pergunta para a reunião da Univali (03/09)
O Prof. Mauro pode dizer se a modelagem HEC-RAS 1D desse trecho tem valor fora do contexto de
licenciamento — e se a Univali participou ou revisou o AIBH.

## Fonte relacionada, achada na mesma busca (a investigar)
**"Aplicação de redes neurais artificiais para previsão de enchentes no rio Itajaí-Açu em Blumenau, SC"**
— usa dados de chuva e nível das estações telemétricas do SNIRH/ANA a **15 min**, com 7 eventos de alerta
registrados na estação limnimétrica de Blumenau. É diretamente relevante ao problema de previsão do site,
e usa as MESMAS fontes que já coletamos. Vale ler antes de investir em modelo próprio.

## Fonte de baixo valor (avaliada e descartada)
**"Caracterização morfométrica da Bacia Hidrográfica do Rio Itajaí"** (ResearchGate) — geomorfologia
descritiva: densidade de drenagem, ordenamento de Strahler. Confirma o vocabulário formal da rede
hierárquica (o que chamamos de "árvore"), mas não fornece nível, cota nem tempo de trânsito. Sem uso
prático para o site.
