# Camadas de fundo no mapa — especificação para implementar

Decisão tomada em 03/09/2026 depois de comparar os três fundos lado a lado
(demo: `monitor-camadas.html`, aberto localmente — ver "Como testar" no fim).

---

## Decisão
**Adicionar seletor de fundo com três opções, mantendo "Escuro" como padrão.**

| Opção | Fonte | Quando serve |
|---|---|---|
| **Escuro** (padrão) | CARTO Dark Matter | monitoramento — o rio é a única coisa brilhante na tela |
| **Satélite** | Esri World Imagery | localização: reconhecer bairro, molhes, mancha urbana |
| **Mapa** | OpenStreetMap | achar rua e ponto de referência |

O padrão continua escuro **por função, não por estética**: qualquer fundo com textura concorre
visualmente com as faixas de alerta. Numa noite de chuva, com o celular na mão, isso pesa mais que
parecer bonito. Satélite e mapa entram como escolha do usuário, não como padrão.

---

## Fontes, licença e atribuição (obrigatória)

```js
// Escuro — CARTO (gratuito para uso não comercial)
'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
// atribuição: '© CARTO · © OpenStreetMap'   maxZoom 19

// Satélite — Esri World Imagery (gratuito para uso não comercial)
'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
// atribuição: 'Imagem: Esri, Maxar, Earthstar Geographics'   maxZoom 18
// ⚠️ ordem {z}/{y}/{x} — Esri inverte y e x em relação ao padrão

// Mapa — OpenStreetMap (ODbL)
'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
// atribuição: '© colaboradores do OpenStreetMap'   maxZoom 19
```

**A atribuição é condição de licença, não cortesia.** Tem de estar visível na tela enquanto a camada
estiver ativa — trocar de camada troca a atribuição.

**NÃO usar Google Earth / Google Maps.** A licença não permite embutir capturas nem tiles em site
próprio; para web seria a Google Maps Platform, paga e com chave. Além disso, o link que o usuário
tentou é uma vista 3D com ângulo de câmera — não é imagem georreferenciada, não alinharia com os
marcadores.

---

## Implementação

### 1. Pane próprio para o fundo — o ponto que quebra se ignorado
```js
mapa.createPane('fundo');
mapa.getPane('fundo').style.zIndex = 180;   // abaixo do overlay (400)
L.tileLayer(url, { pane:'fundo', maxZoom, attribution });
```
**Por quê:** sem pane dedicado, a troca de camada precisa de `bringToBack()`, que manda a camada nova
para trás das tiles antigas que o Leaflet ainda mantém no DOM — o fundo novo carrega, fica escondido, e
a tela não muda. Foi o bug da primeira demo. Com pane fixo, trocar é só remover uma e adicionar outra.

### 2. Troca
```js
function trocar(q){
  if (q === atual) return;
  mapa.removeLayer(FUNDOS[atual]);
  FUNDOS[q].addTo(mapa);
  atual = q;
  // aria-pressed nos botões
}
```

### 3. O Monitor hoje é canvas próprio (`mapaMotor.ts`), não Leaflet
Duas saídas, em ordem de esforço:
- **(a) Só na tela de Itajaí (recomendado começar por aqui).** É onde o satélite mais rende: ver a barra,
  os molhes e a mancha urbana ajuda o morador a se localizar na foz. Se essa tela já usa Leaflet (o mapa
  de manchas usa), o seletor entra direto.
- **(b) No Monitor da bacia.** Exige desenhar tiles no canvas do `mapaMotor.ts` **ou** trocar o motor por
  Leaflet com o canvas como overlay. É trabalho real, e pela comparação o ganho é pequeno — o escuro já
  cumpre a função. Avaliar depois de (a).

### 4. Contorno escuro sob cada traço (necessário se houver satélite)
Sobre imagem de satélite, laranja e amarelo somem contra mata e telhado. Cada polilinha precisa de uma
sombra por baixo:
```js
L.polyline(pts, { color:'#040709', weight: peso+5, opacity:.5, lineCap:'round' });  // por baixo
L.polyline(pts, { color: CORdaFaixa, weight: peso, lineCap:'round' });              // por cima
```
Sem isso o satélite prejudica a leitura de risco — que é a função da tela.

### 5. Preferência do usuário
`localStorage` é opção, dentro de `try/catch`, e a tela tem de funcionar quando vier vazio (cair para
"escuro"). Não é obrigatório — o padrão escuro já é o caso comum.

---

## O que a comparação revelou (justifica as escolhas)

**O satélite atrapalha justamente o dado mais delicado.** O cinza dos trechos sem leitura quase desaparece
contra a mata — e cinza é a maior parte do mapa (102 de 141 trechos no Açu não têm régua). A informação
"não temos dado aqui" é a que o satélite mais degrada.

**O satélite ganha na foz.** Em Itajaí, reconhecer a barra e a mancha urbana ajuda de um jeito que o traço
abstrato não consegue.

**Risco de saturação:** no fundo escuro, um trecho em alerta salta muito. Se um dia metade da bacia estiver
em alerta, o mapa inteiro vira laranja e perde hierarquia. Vale monitorar — no fundo claro (OSM) esse risco
é menor.

---

## Como testar (importante)
**Tiles não carregam em preview de artifact publicado** — a política de segurança da plataforma bloqueia
imagens de outros domínios, e nenhuma das três camadas aparece. Isso não é bug do código.
Testar sempre: arquivo aberto localmente no navegador, ou no site pelo GitHub Pages (onde o OSM já carrega).

## Verificação antes de fechar
- [x] As três camadas carregam e trocam
- [x] A atribuição muda junto com a camada e fica visível
- [x] Padrão é "escuro" ao abrir
- [ ] Com satélite, o cinza de "sem leitura" continua distinguível (tracejado + contorno escuro)
- [x] Botões com `aria-pressed` e foco visível
- [x] Funciona em tela de celular (o seletor não pode cobrir o mapa)

---

## O que foi implementado (03/09/2026)

Caminho **(a)**: `web/src/componentes/MapaManchas.tsx`, a tela de Itajaí. O Monitor
(caminho **b**) segue no `<canvas>` do `mapaMotor.ts`, sem seletor — e por isso o item 4
da lista acima continua **em aberto por não se aplicar ainda**: o cinza de "sem leitura"
é dado do Monitor, e lá não há satélite para degradá-lo. Quando (b) for avaliado, o
contorno escuro sob cada polilinha (seção 4) passa a ser obrigatório antes de ligar o
satélite, não depois.

O equivalente para as manchas foi feito: `estiloDaMancha(cores, sobreSatelite)` engrossa o
contorno para 1,4 px `#04141f` e sobe o preenchimento para 0,72 de opacidade sobre imagem,
contra 0,6 px `#1f5f96` e 0,55 nos fundos lisos. Mesma ideia, mesmo motivo — o fundo pode
mudar, a leitura do risco não pode piorar.

Três decisões que o código registra e a especificação não previa:

- **A atribuição do rodapé também troca.** Havia um crédito fixo "Mapa base: © colaboradores
  do OpenStreetMap" no fim do cartão. Com o satélite ligado ele creditaria a fonte errada —
  que é exatamente o que a licença proíbe. Passou a ler `FUNDOS[fundo].atribuicao`, a mesma
  string que vai para o Leaflet.
- **Trocar de fundo não rebaixa o GeoJSON.** São até 651 kB por evento. A troca chama
  `setStyle` na camada que já está em memória.
- **`localStorage` dentro de `try/catch` nos dois sentidos** (ler e gravar): navegador com
  dados de site bloqueados tem de abrir a tela no padrão, não quebrar.

### Como isto foi conferido
Navegador headless a 320 px, contra o `vite preview`. Conferidos: URL montada por camada
(a do Esri com `{z}/{y}/{x}` invertido — validada comparando com a do CARTO no mesmo ponto:
`12/1493/2365` vira `12/2365/1493`), atribuição nos dois lugares, padrão escuro ao abrir,
preferência sobrevivendo ao recarregamento, `aria-pressed` nos três botões, foco de 2 px por
navegação de teclado real, e o seletor acima do mapa (não sobreposto), com alvo de toque de
44 px.

**As tiles em si não foram vistas.** Os domínios de mapa estão bloqueados no ambiente de
desenvolvimento — o que a seção "Como testar" já previa. O que se verificou foi a URL, não a
imagem. **Confirmar no GitHub Pages** que as três aparecem de fato.
