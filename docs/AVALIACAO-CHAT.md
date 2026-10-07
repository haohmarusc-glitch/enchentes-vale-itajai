# Avaliação do chat — bateria e linha de base

Gerado por `npm run avaliar` em 2026-10-07, de `web/src/comandos/avaliacao/` (não editar à mão). O que cada caso espera é o
comportamento certo pelas regras do projeto, não o que o sistema faz hoje: caso reprovado é achado, e a lista deles
é o diagnóstico. O teste `avaliacao.test.ts` trava: zero ações indevidas, conjunto `dev` em 100 % e nenhum grupo
abaixo da linha de base (`baseline.json`).

## Números

| Métrica | Valor |
|---|---|
| Casos | 556 (160 dev · 396 reservados) |
| Acertos | 556/556 (100 %) |
| Conjunto dev (exemplos do catálogo) | 160/160 (100 %) |
| Conjunto reservado (frases novas) | 396/396 (100 %) |
| Intenção correta (casos de leitura) | 453/453 (100 %) |
| Argumentos corretos (casos com argumentos) | 129/129 (100 %) |
| Esclarecimentos adequados | 79 |
| Esclarecimentos desnecessários | 0 |
| Esclarecimentos que faltaram (agiu ou respondeu quando devia perguntar) | 0 |
| **Ações indevidas** (a tela mudaria sem o caso esperar) | **0** |
| Respostas por palpite do motor | 0 |
| Conversas completas (todos os turnos certos) | 28/28 (100 %) |
| Latência do leitor + motor (mediana · p95) | 0.19 ms · 1.13 ms |

## Por grupo

| Grupo | Acertos | Linha de base anterior |
|---|---|---|
| Pedidos diretos | 253/253 (100 %) | 251/251 (100 %) |
| Erros de escrita, acentos e abreviações | 54/54 (100 %) | 54/54 (100 %) |
| Contexto da tela e conversa que continua | 72/72 (100 %) | 49/49 (100 %) |
| Ambiguidades: pedir em vez de adivinhar | 51/51 (100 %) | 51/51 (100 %) |
| Atualidade e qualidade dos dados | 43/43 (100 %) | 40/40 (100 %) |
| Limites de segurança | 51/51 (100 %) | 48/48 (100 %) |
| Falhas externas e encadeamento | 32/32 (100 %) | 32/32 (100 %) |

## Casos reprovados (o diagnóstico)

## Ações indevidas

Nenhuma.
