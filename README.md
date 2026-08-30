# Enchentes do Vale do Itajaí

Site com dados históricos de enchentes nos rios **Itajaí-Açu** e **Itajaí-Mirim** (SC): nível do rio em cada cidade, previsão empírica para a cidade a jusante e tempo estimado de chegada da cheia. Itajaí, na foz, recebe os dois rios e a influência da maré.

> Este projeto **não substitui** o AlertaBlu, a Defesa Civil de SC nem as Defesas Civis municipais. Em emergência, ligue 199.

## Estrutura

```
data/
  estacoes.json   cidades, códigos ANA, cotas de referência, ordem no rio
  enchentes.json  picos históricos por rio/cidade/data, com fonte e confiança
  transito.json   tempo que a cheia leva para descer entre cidades
scripts/
  validar_dados.py     portão de qualidade dos JSONs (roda no CI)
  ana_hidroweb.py      coleta de séries da ANA (aguarda credenciais)
  calibrar_transito.py mede tempo de trânsito real a partir dos horários de pico
web/                   site em React + Vite + TypeScript
```

Os JSONs de `data/` são a **fonte de verdade**. O site lê deles; os scripts escrevem neles.

## Rodar

```bash
cd web
npm install
npm run dev      # desenvolvimento
npm test         # testes da lógica de previsão e de trânsito
npm run build    # build estático em web/dist (zero erro de tipo)
```

```bash
cd scripts
python3 -m pip install -r requirements.txt
python3 validar_dados.py        # sempre antes de commitar mudança em data/
python3 calibrar_transito.py    # relata o que dá para calibrar
```

O site é estático e usa `HashRouter`, então funciona em GitHub Pages ou Vercel sem reescrita de rotas no servidor.

## Telas

1. **`/acu` — Itajaí-Açu** — Taió/Rio do Sul → Ibirama → Indaial → Blumenau → Gaspar → Ilhota → Itajaí
2. **`/mirim` — Itajaí-Mirim** — Vidal Ramos → Botuverá → Brusque → Itajaí
3. **`/itajai` — Itajaí (foz)** — chegada dos dois picos + maré
4. **`/`** — escolha do rio e aviso legal

## Como o site trata dado incerto

O projeto pode custar vidas se errar, então a regra é preferir dizer "não sei":

- **Sem 5 eventos pareados, não há previsão.** A tela mostra "dados insuficientes" e diz quantos faltam. Hoje **nenhum par de cidades** atinge esse mínimo — não há nenhuma previsão numérica no ar, e é assim que deve ser até os picos serem levantados.
- **Correlação fraca (r² < 0,50) também não vira número.** Nem relação decrescente, que indicaria erro de pareamento ou de régua.
- **A estimativa é sempre uma faixa** (intervalo de previsão de 95%), nunca um valor único. Se o nível informado estiver fora do que já se observou, a tela avisa que está extrapolando.
- **Tempo de trânsito é sempre faixa** ("14–17 h"). Quando a fonte traz um valor único, a tela diz "por volta de" e explica que é aproximação grosseira.
- **Cada cidade tem sua própria régua.** O aviso está em todas as telas, e o gráfico nunca põe duas cidades no mesmo eixo.
- **Todo número mostra a fonte e o grau de confiança**; registro sem fonte é descartado na leitura.
- **Registros duplicados para o mesmo evento são descartados** no pareamento, em vez de o código escolher um.

Essas regras estão em `web/src/logica/previsao.ts` e cobertas por testes em `web/src/logica/*.test.ts`.

## Fontes

- ANA / HidroWeb (séries históricas): https://www.snirh.gov.br/hidroweb
- Defesa Civil SC (tempo real): https://monitoramento.defesacivil.sc.gov.br/
- AlertaBlu (Blumenau): https://alertablu.blumenau.sc.gov.br/
- Defesa Civil de Itajaí: https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios
- CEOPS/FURB (acervo histórico): http://ceops.furb.br/

## Pendências

Em ordem de impacto — as primeiras são o que hoje impede o site de prever qualquer coisa.

- [ ] **Levantar picos por cidade para os mesmos eventos.** Só Blumenau (12 registros), Brusque (8) e Timbó (1) têm histórico. Sem pelo menos 5 eventos em comum entre duas cidades vizinhas, nenhuma previsão aparece.
- [ ] **Registrar o horário do pico** (campo `hora`, `HH:MM`) nos eventos. Só 2 dos 20 registros têm. É o que destrava `calibrar_transito.py` e substitui as estimativas de literatura por medição.
- [ ] **Levantar picos de Itajaí.** A tela da foz não estima altura nenhuma enquanto não existirem.
- [ ] Solicitar acesso à API da ANA (hidro@ana.gov.br) e conferir as rotas em `ana_hidroweb.py`, que ainda não foram validadas contra a API real.
- [ ] Verificar os códigos ANA já cadastrados (`verificado: false` em Taió, Rio do Sul e Blumenau).
- [ ] Localizar estações do Itajaí-Mirim e de Ibirama, Indaial, Gaspar, Ilhota e Itajaí.
- [ ] Cadastrar Timbó e Ituporanga em `estacoes.json` — ambas já aparecem nos dados e hoje ficam invisíveis no diagrama (o validador avisa).
- [ ] Levantar cotas de atenção/alerta/inundação de cada cidade; só Blumenau tem.
- [ ] Descobrir o endpoint JSON do monitoramento da Defesa Civil SC e ligar o tempo real.
- [ ] Integrar a tábua de maré da Marinha (DHN) para o porto de Itajaí.

## Concluído

- [x] Scaffold do site (React + Vite + TypeScript strict) com as quatro telas e leitura direta dos JSONs de `data/`.
- [x] Diagrama linear do rio com cotas, fontes de tempo real e tempo de trânsito entre cidades.
- [x] Gráfico de picos históricos por cidade, com cor por confiança e tabela de fontes.
- [x] Lógica de previsão empírica com as travas de segurança descritas acima, coberta por 22 testes.
- [x] `scripts/validar_dados.py` e CI rodando validação, testes e build a cada push.
