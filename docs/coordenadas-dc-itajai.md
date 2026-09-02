# Coordenadas das 11 réguas DC de Itajaí — busca no ArcGIS (02/09/2026)

Objetivo: preencher `coordenadas` das réguas DC-01..DC-11 em `data/estacoes.json` para ordenar o
Itajaí-Mirim (e os demais) **pela descida do rio em direção ao mar**, em vez de por descrição.

## Resultado: ❌ as réguas NÃO estão no ArcGIS público — estão atrás de token

Varredura completa do ArcGIS da Prefeitura (`arcgis.itajai.sc.gov.br/server/rest/services`), pelo
navegador:

- **Raiz** (200 serviços): filtrada por `estac|telemetr|pluvio|regua|sensor|pcd|monitora|alerta|defesa`
  → **zero** estação de medição. Os `Hidrografia_*` são feições (área úmida, barragem, canal, ilha,
  massa d'água, oceano), não réguas.
- **Pasta `defesacivil`**: existe, mas **"Token Required"**. É quase certo que as réguas estão aqui.
- **Pasta `Hosted`** (621 serviços): busca por `telemetr|estac|régua|fluvi|maregraf|linimetr|hidrolog|
  nivel_rio|DC-\d` → **zero**. Os `Cotas_Inundação_*` são as manchas por evento (já temos); `Cota_20`
  é curva de nível topográfica, não régua.

**Conclusão:** a camada de estações da Defesa Civil está fechada por token. A régua DC segue **sem
coordenada em fonte pública**, então a ordenação por descida do rio **não pode ser feita sem inventar**
— e o projeto não inventa coordenada.

### Caminhos para obter as coordenadas (em ordem)
1. **Ofício C2 (GEOItajaí)** — enviado 31/08; **complementar** pedindo explicitamente lat/lon das 11
   réguas DC-01..DC-11.
2. **GPS em campo** — 11 pontos em Itajaí, ~meia manhã; resolve de vez e com precisão.
3. **Reunião Univali (03/09)** — perguntar se têm as coordenadas das réguas da DC.

Enquanto não vierem, o `/rios` mostra o Mirim na ordem do cadastro (cidade→rio), e as réguas de Itajaí
saem por código (DC-03..DC-10). A ordem física real (descida ao mar) fica pendente da coordenada.

> **Nota hidrográfica** (por descrição do Plano da COMPDEC, Tabela 11 — NÃO por coordenada, a confirmar):
> em Itajaí o Mirim se divide em dois braços paralelos até o estuário. DC-10 (Limoeiro) é o ponto mais a
> montante; depois o rio se separa em **curso antigo** (DC-05 Sítio Sr. Hilário, DC-06 Clube Itamirim) e
> **canal retificado** (DC-03 Captação SEMASA, DC-04 Vitalmar Pescados, junto ao estuário). Dois canais
> paralelos: "quem vem antes de quem" só a coordenada resolve.

## 🎁 Achado colateral: 45 abrigos oficiais COM coordenada (público, sem token)

`Hosted/Abrigos_Defesa_Civil_view_completo` (FeatureServer) — público, sem token.
- 45 abrigos, **todos com lat/lon**, mais `nome_do_ab`, `endereco`, `capacida_2` (capacidade),
  `sigla_do_a` (zona de Defesa Civil, ex. Z2-2), `situacao`, `lotacao`.
- Query (usar `f=json`; `f=geojson` dá 500 neste serviço):
  `/server/rest/services/Hosted/Abrigos_Defesa_Civil_view_completo/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json`

**Por que importa:** Blumenau já mostra o abrigo mais próximo junto da cota de rua (do PDF de 2014).
Itajaí não tinha — com coordenada, dá "abrigo mais próximo de você" por distância real, não por bairro.
Encaixa no Bloco 4 da tela de Itajaí.

**Ressalva (regra do AVISO-LEGAL):** a lista traz `situacao`/`lotacao`, mas é **cadastro, não estado
atual**. NÃO exibir como "aberto agora" — quem ativa abrigo é a Defesa Civil.

### Para entrar no repo (precisa do arquivo bruto)
O JSON dos abrigos foi baixado na sessão de navegador (`itajai-abrigos-defesa-civil.json`), mas **ainda
não está no repositório**. Passos quando o arquivo estiver disponível (subir aqui ou mover na VPS):
1. `data/brutos/itajai-abrigos-defesa-civil.json` (bruto) → `data/abrigos-itajai.json` (normalizado).
2. Tela de Itajaí, seção "Meu ponto": os 3 abrigos mais próximos (distância em linha reta), com endereço
   e capacidade, e o aviso de que a ativação é decisão da Defesa Civil.
