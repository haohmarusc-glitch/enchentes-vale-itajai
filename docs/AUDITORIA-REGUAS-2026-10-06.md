# Auditoria das réguas do Monitor (06/10/2026)

Pedido do Jefferson, com a inspeção visual das 19 cidades do seletor do Monitor no Chrome, fundo Satélite. A
inspeção achou 8 cidades em que a câmera abria sem o pino na tela: Ituporanga, Ibirama, Blumenau, Itajaí,
Timbó, Rio dos Cedros, Trombudo Central e Guabiruba. Ela também trouxe as coordenadas das fichas da Defesa
Civil de SC, calculadas pelo Plus Code de cada ficha.

## A causa

Das hipóteses da inspeção, duas se confirmaram no código. Elas são o mesmo defeito.

- **O pino era encaixado no traçado do rio da tela.** `construirCena` punha cada cidade no vértice do traçado mais
  perto da coordenada dela, e o traçado era sempre o do Açu ou do Mirim. Para as cidades do tronco, isso é
  dezenas de metros. Para as de fora, o pino ia parar em outro rio:

  | Cidade | Pino até 06/10 a quantos km da régua |
  |---|---|
  | Ituporanga | 28,0 |
  | Rio dos Cedros | 16,6 |
  | Trombudo Central | 10,5 |
  | Timbó | 8,2 |
  | Guabiruba | 4,2 |
  | Blumenau | 3,0 |
  | Ibirama | 2,6 |
  | Itajaí | 0,9 |

- **A câmera centrava na coordenada do cadastro, não no pino.** Abria no lugar certo, e o pino estava longe.
- **Timbó e Rio dos Cedros abriam no mesmo lugar** por um terceiro motivo: a câmera é presa aos limites do
  mapa, e os limites eram só os traçados. As duas ficam ao norte da borda (−26,84). As duas paravam na borda,
  na mesma longitude (−49,27).

As demais hipóteses não se confirmaram:
- a seleção atualiza ao trocar de cidade;
- o fundo é posicionado tile a tile pela mesma projeção dos pinos (`logica/tiles.ts`);
- cidade sem coordenada cai na bacia inteira, de forma explícita;
- a falta de traçado não sumia com o pino: puxava o pino para o tronco.

## O que mudou (com o rótulo `monitor-autorizado`)

- **O pino fica na coordenada da régua** (`pontoDoPino`, em `mapaMotor.ts`). O encaixe no traçado continua só
  na espinha que pinta o rio, onde ele é preciso.
- **Exceção: Blumenau.** O cadastro declara `coordenadas_sao_da_regua: false`, porque a coordenada é da
  DCSC-00026, um pluviômetro a 3 km do rio. Ali o pino fica no rio, no ponto mais perto, marcado como
  aproximado. Desenhá-lo no pluviômetro diria que a régua está no morro.
- **A câmera centra no pino como ele está desenhado**, não no cadastro.
- **No celular**, o painel da cidade cobre até 52% de baixo. A câmera põe o pino a 36% da altura, acima do painel
  (`vistaAcimaDaFolha`). Os botões de zoom mantêm o centro, então o pino continua ali.
- **Tocar de novo na cidade aberta**, no menu "Cidades", volta a enquadrá-la.
- **O enquadramento da bacia cabe a régua de todas as cidades**, e não só os traçados. Assim a câmera alcança
  Timbó e Rio dos Cedros.
- **O painel diz de onde vem o ponto:**
  - "Pino na coordenada da estação DCSC-000NN da Defesa Civil de SC (lat, lon)";
  - "Posição aproximada…" (Blumenau);
  - "Este pino marca a cidade. Cada régua aparece no seu próprio ponto" (Itajaí);
  - para cidade sem código, "a fonte do nível não confirma o ponto exato da régua".

## Conferência

- `web/src/logica/pinoNaRegua.test.ts`, com o cadastro e os traçados reais:
  - o pino de cada cidade está na coordenada da régua, ou no rio e aproximado em Blumenau;
  - na bacia inteira, todo pino cabe na tela;
  - abrindo cada uma das 19 cidades com a câmera dela, o pino fica no meio da tela, e no celular a 36% da
    altura;
  - Timbó e Rio dos Cedros abrem a mais de 5 km um do outro.
- **No navegador** (Chromium, 900×700 e 390×844), as 19 cidades abriram com o pino no meio do mapa. Isso inclui
  a troca Timbó → Rio dos Cedros pelo menu. O satélite não carrega no ambiente de teste, então a conferência
  foi sobre o traçado.
- `npm test`, build, trava do Monitor, fumaça e auditoria de regressão passaram.

## O inventário

O inventário fica em `docs/INVENTARIO-REGUAS.md`, gerado por `scripts/inventario_reguas.py` e travado por
`teste_inventario_reguas.py`. A comparação usa a coordenada da API da DCSC (`data/brutos/`), só com a ficha da
mesma estação. As coordenadas da inspeção, tiradas do Plus Code, batem com as da API.

- **As 12 cidades com código DCSC de régua batem com a ficha, a até 10 m:** Taió, Ituporanga, Rio do Sul,
  Ibirama, Ascurra, Indaial, Gaspar, Ilhota, Vidal Ramos, Botuverá, Guabiruba e Brusque. Isso confirma que o
  pino está na estação estadual. Não confirma que ela seja o mesmo equipamento da leitura municipal (Gaspar lê
  a estação municipal 21, por exemplo).
- **Blumenau:** código de pluviômetro (Meteo), já declarado no cadastro. Posição aproximada.
- **Cidades sem código, com coordenada sem fonte declarada:** Lontras, Apiúna, Timbó, Rio dos Cedros, Trombudo
  Central e Itajaí. Itajaí é referência da cidade; as 11 réguas DC têm coordenada própria, do mapa da Defesa
  Civil de Itajaí.
- **Nenhuma coordenada do cadastro mudou.** A estação estadual mais próxima de uma cidade sem código não foi
  copiada para ela.

## Decisões do Jefferson (06/10/2026, depois da auditoria)

1. **Blumenau: coordenada da régua confirmada.**
   - **Informação da Prefeitura:** as réguas ficam na escadaria logo após a Ponte Adolfo Konder, na Avenida
     Presidente Castelo Branco (Beira-Rio), e foram fornecidas pela ANA/Epagri. O sensor automático fica no
     guarda-corpo da ponte.
   - **No cadastro:**
     - `coordenadas` = −26,9186, −49,0656, a da ANA 83800002;
     - `coordenadas_sao_da_regua: true`;
     - `coordenadas_fonte`: "Prefeitura de Blumenau/Defesa Civil — Ponte Adolfo Konder, Beira-Rio";
     - o antes e o depois ficam em `coordenadas_nota`.
   - **O que muda com isso:**
     - o "aproximado" sai;
     - o painel diz a fonte;
     - o bot volta a dar a distância, agora até a régua;
     - as exceções de Blumenau no validador (`LONGE_ACEITO`, `PINO_LONGE_DA_REGUA`) saíram.
   - **A DCSC-00026** continua em `codigo_dcsc`, só para a chuva.
2. **Timbó, Rio dos Cedros, Trombudo Central e Lontras: equivalência não confirmada.**
   - **Por quê:** distância de 0,24 a 1,6 km não prova que seja a mesma régua. Zero, seção do rio e referência
     altimétrica podem diferir.
   - **No cadastro:** cada uma tem `equivalencia_estadual` com `status: "não confirmada"`.
   - **Trava:** `valida_equivalencia_estadual` reprova o código em `codigo_dcsc` enquanto não houver
     confirmação, e reprova "confirmada" sem `fonte`.
   - **Quando vincular:** só quando existir documento, código comum ou comparação de referência/zero da régua. Proximidade não basta.
3. **Itajaí: seletor de régua na própria tela do Monitor.**
   - **Opções:** "Todas as 11 réguas" (padrão), depois DC-01 a DC-11.
   - **Escolher uma régua:** o mapa centraliza nela, com ~3 km de largura, e o painel dela abre. No celular, o
     ponto fica acima do painel.
   - **"Todas":** volta ao enquadramento das onze.
   - **Toque no mapa:** tocar numa régua também muda o seletor.
   - **Código e testes:** `logica/seletorDeRegua.ts`, testado com o cadastro real.

## O que fica

- [x] **Rios ainda sem traçado:** o Benedito, o Rio dos Cedros, o Itajaí do Sul, o Trombudo e o curso de
  Guabiruba (Rio Guabiruba Norte → Rio Guabiruba) foram desenhados em 06/10/2026
  (`docs/TRACADOS-AFLUENTES-2026-10-06.md`).
