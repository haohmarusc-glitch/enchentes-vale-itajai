# Resolução do reteste de 19/09/2026

O monitor de Brusque usava a classificação publicada pela rede estadual como alternativa à ausência de faixa municipal (`mapaMotor.ts`, `origemFaixa: estadual`). O painel ignorava essa origem ao escrever a faixa e a ação: daí “Rio abaixo da cota de atenção”, mesmo sem leitura municipal compatível. A correção preserva a camada estadual e identifica sua origem; não compara o nível estadual com cotas locais.

O resumo da série agora informa até quando houve medição e avisa quando ela está parada. O limite de frescor é o mesmo usado pelas demais telas, inclusive a exceção de Blumenau.

O início do gráfico de Blumenau já distinguia fontes de uma mesma régua. Seu rodapé não aplicava a mesma condição. A correção usa `mesmaRegua` nos dois lugares, preservando as séries separadas e a referência histórica IBGE.

A observação pública de Brusque ainda afirmava que 4,80 m estava cadastrada como atenção, embora o próprio cadastro já mantivesse 3,00/5,00 m. A observação foi atualizada; os limiares e o histórico de alterações foram preservados. Não se inferiu a identidade de réguas nem se autorizou cálculo com a leitura estadual.

Os links ativos de níveis de Itajaí apontam para o novo portal. Referências históricas da MKS e evidências brutas permanecem preservadas.

## Pendências que exigem evidência

- Comprovar a régua e referência das cotas de rua de Brusque. Há anotações conflitantes no cadastro; não se deve resolver esse conflito por coincidência de nome ou valor.
- O arquivo contém 377 registros de Brusque: 350 da camada municipal de cotas de 2023 e 27 da lista histórica reproduzida pela imprensa. São 372 registros numéricos no total. Os 350 exibidos correspondem à camada de 2023; continua pendente identificar de onde veio o total de 338 mencionado no encaminhamento. Não excluir registros para forçar igualdade de contagens.
- Manter no Plano v17 as quatro cotas divergentes de Itajaí até confirmação municipal.
- A divergência de capacidade das barragens continua exigindo conciliação de época e definição; não foi alterada aqui.

Estas são correções de apresentação, sem mudança de leitura, cotas, alertas ou regras de coleta.

## Validação

594 testes web passaram; TypeScript sem erros; build Vite concluído. O validador de dados terminou com zero erros e 14 avisos. A instalação local do componente nativo de Windows atualizou dependências apenas em node_modules, sem alteração de package.json ou lockfile; o build também deve ser confirmado pela CI com o lockfile do projeto. O site público ainda precisa receber e ter verificada esta correção após revisão.
