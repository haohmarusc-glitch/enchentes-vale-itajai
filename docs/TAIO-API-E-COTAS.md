# Taió — APIs, nível do rio e cotas

**Site:** https://defesacivil.taio.sc.gov.br/  
**Uso:** alimentar o [monitor do Vale do Itajaí](https://haohmarusc-glitch.github.io/enchentes-vale-itajai/#/monitor)  
**Leitura conferida:** 3 de setembro de 2026, 20:41 (horário de Brasília)  
**Emergência:** 199. Este arquivo não substitui aviso oficial.

---

## O que o site mostra agora

| Campo na home | Valor às 20:41 |
|---|---|
| Nível no Centro — Rio Itajaí (do Oeste) | **5,25 m** |
| Chuva 24 h | 0,0 mm |
| Montante Barragem Oeste | vazio na home; API devolve **17,2 m** |
| Jusante Barragem Oeste | vazio |
| Cota de Alagamento / Cota de Atenção | **em branco** na home e `null` na API |
| Canal extravasor | Fechado (`–` na API) |
| Comportas Barragem Oeste | **7 de 7** abertas |

A home pinta o card do nível de **amarelo** a 5,25 m — coerente com a faixa de monitoramento do plano (> 5 m e ≤ 7 m).

---

## API principal (pronta para o coletor)

Provedor: **Uniparking / SCR** (`api-scr.uniparking.com.br`).  
Não exige autenticação. CORS aberto o bastante para o próprio site chamar no browser.

### Cards (estado atual)

```
GET https://api-scr.uniparking.com.br/v1/defesa-civil-taio/dados/cards?v=1
```

Resposta real (03/09/2026 20:41:58):

```json
{
  "dataUltimaAtualizacao": "03/09/2026 20:41:58",
  "nivelCentro": "5.25",
  "chuvas": null,
  "percentualReservatorio": "",
  "montante": "17.2",
  "jusante": "",
  "cotasAlagamento": null,
  "cotaEmergencia": null,
  "aberturaExtravasor": "–",
  "comportasAbertas": "7 de 7",
  "chuva1Hora": "0.0",
  "chuva12Horas": "0.0",
  "chuva24Horas": "0.0",
  "chuva48Horas": null,
  "chuva72Horas": null,
  "chuva96Horas": null
}
```

Campos úteis para o monitor:

| Campo | Unidade | Uso |
|---|---|---|
| `nivelCentro` | m, string | régua da cidade (Centro) |
| `dataUltimaAtualizacao` | `dd/MM/yyyy HH:mm:ss` | idade da leitura |
| `montante` | m | nível no reservatório (Barragem Oeste) — **outra régua** |
| `jusante` | m | jusante da barragem (hoje vazio) |
| `chuva1Hora` / `12Horas` / `24Horas` | mm | chuva |
| `comportasAbertas` | texto `"N de 7"` | operação da barragem |
| `aberturaExtravasor` | texto | canal extravasor |
| `cotasAlagamento` / `cotaEmergencia` | deveria ser m | **sempre null** — não usar |

### Histórico (últimas ~24 h, 1 ponto/hora)

```
GET https://api-scr.uniparking.com.br/v1/defesa-civil-taio/dados/historico?v=1
```

Lista de 24 objetos. Amostra:

```json
{
  "dataUltimaAtualizacao": "03/09/2026 20:00:34",
  "dataHora": "03/09 20:00",
  "data": "2026-09-03T20:00:34",
  "nivel": "5.17",
  "chuva": "0.0",
  "montante": "17.2",
  "jusante": "",
  "comportaAberta": "7",
  "comportaFechada": "0"
}
```

Série do dia (nível no Centro): 4,59 m (02/09 21h) → 5,17 m (03/09 20h) → 5,25 m no card.

---

## Outras fontes no mesmo site

### Estações Plugfield (chuva / clima, não régua do rio)

Widget: `https://wdg.plugfield.com.br/device/plugfield-widget-v1-sd-x.js`  
API (403 sem o referer do widget):

- `https://prod-api.plugfield.com.br/widgets/device/9596` — **Volta Grande Mirim**
- `https://prod-api.plugfield.com.br/widgets/device/9365` — **Serra Kraemer**

Console do site: `Estação Defesa Civil Taió SC (Volta Grande Mirim)` e `(Serra Kraemer)`.  
Não serve como cota de cidade. Só chuva/clima.

### WordPress

`https://defesacivil.taio.sc.gov.br/wp-json/` — CMS (páginas, formulário). Sem série hidrológica.

### Documentos oficiais no próprio domínio

- [Plano de Contingência — janeiro/2026](https://defesacivil.taio.sc.gov.br/wp-content/uploads/2026/01/PLANO-DE-CONTINGENCIA-TAIO-JAN-2026.pdf)
- [Plano de Contingência Taió — agosto/2026](https://defesacivil.taio.sc.gov.br/plano-de-contingencia-taio-agosto-2026/)
- [Manual de Operação das Barragens 2025](https://defesacivil.taio.sc.gov.br/wp-content/uploads/2026/08/2025-Manual-de-Operacao-das-Barragens-Atualizacao-2025.pdf)
- Menu **Mapa de Alagamento**: https://defesacivil.taio.sc.gov.br/ (item do topo)

---

## Cotas oficiais da régua da cidade

Fonte: Plano de Contingência jan/2026, critérios de acionamento do **Rio Itajaí do Oeste** (régua do Centro — **não** a da barragem).

| Fase | Critério |
|---|---|
| Normal (verde) | ≤ 5,00 m |
| Monitoramento (amarelo) | > 5,00 m e ≤ 7,00 m |
| Atenção (laranja) | > 7,00 m e ≤ 8,00 m |
| Alerta (vermelho) | > 8,00 m e ≤ 9,00 m |
| Emergência (roxo) | > 9,00 m |

Sugestão para `estacoes.json`:

```json
{
  "id": "taio",
  "nome": "Taió",
  "rio": "Rio Itajaí do Oeste",
  "codigo_dcsc": "DCSC-00041",
  "codigo_ana": "83050000",
  "cotas_m": {
    "normal_ate": 5.0,
    "observacao": 5.0,
    "atencao": 7.0,
    "alerta": 8.0,
    "emergencia": 9.0
  },
  "fonte_cotas": "Plano de Contingência COMPDEC Taió, jan/2026 — https://defesacivil.taio.sc.gov.br/wp-content/uploads/2026/01/PLANO-DE-CONTINGENCIA-TAIO-JAN-2026.pdf",
  "fonte_tempo_real": "https://api-scr.uniparking.com.br/v1/defesa-civil-taio/dados/cards?v=1",
  "campo_nivel": "nivelCentro",
  "verificado": true
}
```

A API **não publica** essas faixas (`cotasAlagamento` / `cotaEmergencia` vêm `null`). As faixas entram no cadastro estático, o nível entra pelo `nivelCentro`.

---

## Como ligar no coletor do monitor

1. GET em `.../dados/cards?v=1` a cada 5–10 min.
2. Parser:
   - `nivel_m = float(nivelCentro)` se string não vazia.
   - `idade` a partir de `dataUltimaAtualizacao` (`%d/%m/%Y %H:%M:%S`, fuso America/Sao_Paulo).
   - ignorar `montante` na faixa da cidade (é reservatório, hoje ~17 m — pintaria emergência falsa).
3. Pintar faixa com as cotas do plano (5 / 7 / 8 / 9).
4. Opcional: série de 24 h em `.../dados/historico?v=1` (`nivel` + `data`).
5. Barragem Oeste: card à parte (`montante`, `comportasAbertas`, `aberturaExtravasor`). Emergência de reservatório no painel de Rio do Sul é **23,30 m** — outra escala.

Robots / ética: o endpoint é o mesmo que a home consome em público, sem token. Respeitar intervalo ≥ 1 min. Identificar User-Agent do projeto.

---

## Armadilhas

- **Duas réguas.** `nivelCentro` ≈ 5 m (cidade). `montante` ≈ 17 m (barragem). Nunca misturar.
- **Jusante e cotas na API estão vazias.** Não esperar `cotasAlagamento`.
- **Plugfield 403** fora do widget. Não usar como fonte primária.
- Site estadual / Asthon de Taió publica sobretudo a **barragem**, não a régua do Centro. Esta API municipal fecha exatamente essa lacuna.
- Obra / operação de comporta muda a curva do rio a jusante (Rio do Sul). A cota de Taió é local.
