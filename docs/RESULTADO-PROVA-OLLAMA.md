# Resultado da prova do chat com IA local (Ollama)

Medido em 05/10/2026, no PC do Jefferson: i3-10100F, 16 GB de memória, GTX 1650 com 4 GB.
Como rodar a prova: `docs/PROVA-CHAT-IA.md`, seção "Rodar com o Ollama".

## Números

| Modelo | Acerto (±95%) | Fato certo | Regras | Tempo médio | Custo |
|---|---|---|---|---|---|
| **Chat sem IA** (a régua) | **91%** (31/34) | — | — | instantâneo | zero |
| `qwen2.5:3b` no Ollama (GTX 1650) | **41% ± 17** (14/34) | 41% | 97% | 10,7 s | zero |

**Configuração da rodada:**
- Prova inteira: 34 perguntas, 1 repetição, 6 minutos.
- Pela velocidade, a janela foi de 8 mil tokens (`OLLAMA_CONTEXTO=8192`), com o modelo inteiro na placa. Com 16 mil,
  21% do modelo transbordava para o processador e cada pergunta levava ~1,5 min.

## Onde o modelo de 3B errou

- os 4 recordes;
- as 3 contagens;
- as 2 comparações entre cidades;
- as 2 ruas;
- os 3 casos do Atlas;
- a média.

Acertou bem só as cheias de um ano e a chuva.

## O que as conversas mostram (`.claude/hillclimb/chat-ia/v3/traces/`)

- **Escolhe a ferramenta errada.** Pede a lista inteira de picos em vez do motor.
- **Mistura fatos com tom de certeza.** Recebe o dado certo e monta a resposta com pedaços de cheias diferentes.
  - Pergunta: maior cheia de Blumenau.
  - Ele respondeu: "13 m em 8/9/2011, às 2h, baixou para 8,92 m às 14h", juntando 2011, 2013 e 2015.
  - O certo é 17,3 m em 1880.
- **A nota de "Regras" (97%) é generosa.** O corretor pega o fato errado, mas uma mistura de fatos verdadeiros não
  casa com nenhum padrão proibido.

## Conclusão

- Um modelo de 3B local fica **muito abaixo do chat sem IA** e erra inventando com certeza. **Não usar no site.**
- O de 7B (`v4`) seria mais lento na placa de 4 GB (~1,5–3 min por pergunta) e dificilmente chegaria aos 91%.
  Não vale a rodada.
- O chat sem IA continua sendo a melhor opção grátis.
- Se um dia houver IA no site, o candidato é o Claude Sonnet pela API, depois de passar pela mesma prova (piloto de
  ~US$ 1).
