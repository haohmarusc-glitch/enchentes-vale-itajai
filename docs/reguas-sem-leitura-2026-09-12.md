# Réguas sem leitura — 12/09/2026

A captura do monitor mostrava ausência simultânea de dados estaduais. O acesso
direto a `raw.githubusercontent.com` devolveu HTTP 503 `Backend.max_conn reached`,
enquanto a API de conteúdo do mesmo repositório devolveu o arquivo publicado.
É falha de entrega ao navegador, não ausência dessas estações.

Na publicação estadual de 18h46 (Brasília), havia Indaial 6,73 m, Ilhota 11,05 m,
Ibirama 3,01 m, Botuverá 3,56 m e Vidal Ramos 2,62 m. São valores daquele instante,
não números fixos no site. Ascurra também tinha leitura. Os dados continuam com
estação e horário próprios; níveis estaduais não recebem cotas de outra régua.

## Correção

- Se o CDN falhar, ler o mesmo arquivo do branch `tempo-real` pela API pública
  de conteúdo do GitHub, sem token. Tentativas limitadas a três segundos cada.
- Só URLs padrão deste projeto recebem essa alternativa. URLs configuradas
  pelo operador não são substituídas silenciosamente por outra fonte.
- Falha temporária mantém a leitura anterior e seu horário original. Sua idade
  continua crescendo e as regras de expiração continuam valendo. JSON estadual
  válido com lista vazia limpa o mapa de níveis estaduais.
- Cidade com código DCSC não é descrita como “sem régua”.
- Pino com várias réguas indica “várias réguas · toque para ver”, sem eleger
  um nível único para Itajaí. A publicação municipal consultada tinha 11 réguas
  de Itajaí com leituras de 18h40–18h50.

A alternativa também pode falhar ou atingir o limite público da API. Não
garante disponibilidade permanente nem corrige um coletor parado na VPS.

## Gaspar e limitações

Gaspar não estava em `ultimo.json`. O coletor atual, executado no PC sem gravar,
conseguiu 4,09 m às 18h31 da fonte municipal. A correção da estação 21 já está
no main (PR #306). É necessário conferir a versão e o acesso da VPS ao portal;
esta verificação local não prova que o servidor consegue alcançá-lo. Não usar
o pluviômetro estadual de Gaspar como nível, nem o nível de Blumenau no lugar.

Guabiruba continua sem nível utilizável no monitor: a coleta separa a leitura
altimétrica entre as suspeitas. Trombudo Central 2 continua sem vínculo à régua
da cidade no cadastro. Estes casos exigem confirmar a referência, não converter
ou atribuir números pelo nome.

Após atualizar o main na VPS, executar a coleta e examinar seus avisos antes
de publicar: `python3 scripts/coleta_niveis.py`,
`python3 scripts/coleta_nivel_sc.py`, `bash scripts/publicar_tempo_real.sh`.

## Validação

Testes cobrem 503, JSON inválido, falha dos dois caminhos, cancelamento, fonte
configurada e conservação do horário. A auditoria de navegador força 503 no
CDN e verifica os níveis pela alternativa. Chrome no PC confirmou Indaial
6,72 m com quatro minutos de idade, sem aplicar as cotas da régua da Celesc.
