# Blumenau — tronco do Itajaí-Açu (Ponte Adolfo Konder)

**Portal / app:** [AlertaBlu](https://alertablu.blumenau.sc.gov.br/) (bloqueia robô; app Android/iOS)  
**SEDECI:** secretaria.defesacivil@blumenau.sc.gov.br · 199  
**Régua:** a fonte não a nomeia — o `nivel_oficial.json` publica UMA escala e UMA série, sem
identificar o ponto. Ver `regua_nota` de Blumenau em `data/estacoes.json`.  

> ⚠️ **CORRIGIDO em 18/09/2026.** Esta linha dizia "Ponte Adolfo Konder · ANA 83800002 ·
> DCSC-00026", empilhando três identificadores como se fossem a mesma coisa. Dois problemas.
> **A DCSC-00026 não mede nível de rio**: é do tipo `Meteo`, com `tem_nivel_do_rio: false`
> (inventário da ANA, lido em 06/09/2026) — é a estação de CHUVA cuja coordenada o cadastro usa
> como pino da cidade. E **"Ponte Adolfo Konder" não tem fonte**: entrou no primeiro commit do
> projeto, e no repositório o nome aparece ligado à série do CEOPS/FURB, que está na referência
> IBGE — o outro lado da REGRA BLOQUEANTE. O que ESTÁ provado, por medição e não por nome, é que
> a cota e a leitura são da mesma régua: as duas publicações de Blumenau divergem em mediana
> +0,065 m (`conferir_par_regua.py`). O título deste arquivo guarda o nome antigo de propósito,
> para o caminho continuar achável; ele não é declaração de fonte.
**Já no monitor (desde 09/09/2026):** Observação 3 · Atenção 4 · Alerta 6 · Alerta Máximo 8

---

## Faixas da régua do Centro

Fonte: `static/data/nivel_oficial.json`, campo `condicoes` (fonte "AlertaBLU"), lido na VPS
em 09/09/2026 — bruto `data/brutos/blumenau-alertablu-nivel-oficial-sem-serie-2026-09-09.json`.

| Condição na fonte | A partir de | Chave no cadastro |
|---|---|---|
| Normalidade | 0 m | — |
| Observação | **3,00 m** | `monitoramento` |
| Atenção | **4,00 m** | `atencao` |
| Alerta | **6,00 m** | `alerta` |
| Alerta Máximo | **8,00 m** | `emergencia` (a tela escreve "Alerta Máximo", via `cotas_nomes_na_fonte`) |
| ~~Inundação histórica (cadastro)~~ | ~~8,50 m~~ | **retirada em 17/09/2026 — ver abaixo** |

Até 09/09/2026 o cadastro trazia **6,00 / 6,50 / 7,40**, rotulados "AlertaBlu" sem bruto —
origem desconhecida (7,40 coincide com a menor cota de rua, Rua São Rafael). A tela pintava
atenção **dois metros tarde**. Ficaram em `cotas_divergencias`.

Cores do AlertaBlu (rio, chuva e encosta **separados**, por região): verde normal · amarelo observação · laranja atenção · vermelho alerta · roxo alerta máximo.

Previsão hidrológica própria da SEDECI (assumiu o CEOPS em 2024): até **6 h** de antecedência. Dados a cada **5 min** (antes 15 min).

Revisão de cotas de rua contratada com a FURB (R$ 580 mil, dez/2024, 8 meses). Última revisão 2011–2012. Mapearam ruas até lâmina de **16 m**.

```json
"cotas_m": {
  "monitoramento": 3.0,
  "atencao": 4.0,
  "alerta": 6.0,
  "emergencia": 8.0
}
```

### 17/09/2026 — a "inundação histórica" de 8,50 m saiu do cadastro

A tela e o bot escreviam **"Inundação histórica: 8,50 m"** para o morador de Blumenau.
Medido contra o `enchentes.json` deste repositório: dos **117 registros** de Blumenau com pico,
**101 (86%) ficam acima de 8,50 m**, e o maior é **17,10 m** (1880). 1983 deu 15,34 m; 2011,
12,80 m; 2023, 9,14 m.

O número não é o pico histórico — é a **cota de inundação urbana** da régua da Ponte Adolfo
Konder, que `docs/cotas-de-ruas.md` registra como **faixa de 8,00 a 8,50 m**. Grandeza diferente,
e faixa, não ponto.

O sentido do erro é o que pesa: dizer que o pior já visto fica logo acima da emergência de
8,00 m **tranquiliza** quem lê. Quem viu 2011 sabe que é falso e deixa de acreditar na tela;
quem não viu, acredita.

Foi retirada de `cotas_m` e guardada em `cotas_divergencias`, com a medição, para não voltar por
memória. **Não** virou `inundacao` (a faixa que pinta), porque a Defesa Civil de Blumenau publica
cinco estágios e nenhum deles é este — cor que a fonte não declarou é o erro que este projeto
não comete.

Trava: `valida_marca_historica`, em `scripts/validar_dados.py`, avisa sempre que uma
`inundacao_historica` ficar abaixo de algum pico já registrado para a mesma cidade.

---

## Rede e coletor

- 17 pluviômetros + 1 meteo + 1 hidro (Ramiro, integrada à DC-SC).  
- Barragens Taió / Ituporanga / José Boiteux no app.  
- Rotas de fuga no AlertaBlu.  
- Site antigo: `alertablu.cob.sc.gov.br`.  
- Sem API pública estável (WAF). Usar DC-SC / página de Itajaí “Blumenau” como fallback.

Não misturar com Timbó (Benedito) nem com DC-10 de Itajaí.

---

## ✅ 09/09/2026 — conferido: a escala de cinco estágios é a oficial (histórico da decisão)

Levantamento externo (não conferido daqui; host bloqueado) relata, da página
oficial `defesacivil.blumenau.sc.gov.br/d/nivel-do-rio`, uma escala de **cinco
estágios**: Normalidade 0–3 m · Observação 3–4 · Atenção 4–6 · Alerta 6–8 ·
Alerta Máximo acima de 8 m. Os nomes batem com as cinco cores listadas acima; os
números não batem com os três que este arquivo cadastra desde 30/08 (commit
`9ae8f87`, "AlertaBlu", sem bruto). Se a escala de cinco for a vigente, a tela
pinta atenção **2 m tarde**.

Decidir: `python3 scripts/conferir_faixas_blumenau.py` na VPS imprime as faixas
que `static/data/nivel_oficial.json` publica. Enquanto isso a tela avisa em
texto (`cotas_aviso_publico`). Registro em `cotas_divergencias` de Blumenau.
