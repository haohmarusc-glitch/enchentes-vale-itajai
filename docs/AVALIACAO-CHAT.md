# Avaliação do chat — bateria e linha de base

Gerado por `npm run avaliar` em 2026-11-04, de `web/src/comandos/avaliacao/` (não editar à mão). O que cada caso espera é o
comportamento certo pelas regras do projeto, não o que o sistema faz hoje: caso reprovado é achado, e a lista deles
é o diagnóstico. O teste `avaliacao.test.ts` trava: zero ações indevidas, conjunto `dev` em 100 % e nenhum grupo
abaixo da linha de base (`baseline.json`).

## Números

| Métrica | Valor |
|---|---|
| Casos | 584 (164 dev · 420 reservados) |
| Acertos | 584/584 (100 %) |
| Conjunto dev (exemplos do catálogo) | 164/164 (100 %) |
| Conjunto reservado (frases novas) | 420/420 (100 %) |
| Intenção correta (casos de leitura) | 477/477 (100 %) |
| Argumentos corretos (casos com argumentos) | 129/129 (100 %) |
| Esclarecimentos adequados | 80 |
| Esclarecimentos desnecessários | 0 |
| Esclarecimentos que faltaram (agiu ou respondeu quando devia perguntar) | 0 |
| **Ações indevidas** (a tela mudaria sem o caso esperar) | **0** |
| Respostas por palpite do motor | 0 |
| Conversas completas (todos os turnos certos) | 29/29 (100 %) |
| Latência do leitor + motor (mediana · p95) | 0.34 ms · 1.7 ms |

## Por grupo

| Grupo | Acertos | Linha de base anterior |
|---|---|---|
| Pedidos diretos | 267/267 (100 %) | 253/253 (100 %) |
| Erros de escrita, acentos e abreviações | 58/58 (100 %) | 54/54 (100 %) |
| Contexto da tela e conversa que continua | 74/74 (100 %) | 72/72 (100 %) |
| Ambiguidades: pedir em vez de adivinhar | 54/54 (100 %) | 51/51 (100 %) |
| Atualidade e qualidade dos dados | 46/46 (100 %) | 43/43 (100 %) |
| Limites de segurança | 53/53 (100 %) | 51/51 (100 %) |
| Falhas externas e encadeamento | 32/32 (100 %) | 32/32 (100 %) |

## Casos reprovados (o diagnóstico)

## Ações indevidas

Nenhuma.
