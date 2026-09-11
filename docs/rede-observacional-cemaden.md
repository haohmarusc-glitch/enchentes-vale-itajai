# Cadastro observacional Cemaden de Santa Catarina

Importado de `Rede_Observacional_Santa_Catarina___SC.xlsx`, aba `Rede Cemaden SC`,
fornecido pelo responsável pelo projeto. O JSON guarda o SHA-256 do arquivo e a
linha original de cada registro. Não há data de referência do status na planilha;
a data de modificação do arquivo não comprova a data de atualização das estações.

Procedência conferida no Gmail em 11/09/2026: o aviso do Informa.BR recebido em
10/09/2026 às 14:34 BRT, protocolo 01217.006547/2026-93, contém anexo com esse
mesmo nome (39.647 bytes). O cadastro já estava importado; esta conferência não
altera os status nem acrescenta medições.

São 415 códigos únicos: 397 pluviométricas (245 operacionais e 152 inativas) e
18 hidrológicas (6 operacionais e 12 inativas), conforme o cadastro.
As 13 linhas vazias finais não são estações. O recorte é SC inteira, não a bacia.

## Integração

`data/cemaden-rede-observacional-sc.json` complementa o catálogo anterior do
Mapa Interativo. O coletor de chuva vincula por código e município, adicionando
`cadastro_observacional` às leituras: coordenadas, status cadastral, linha e fonte.
Uma leitura recebida de estação cadastrada como inativa expõe `divergencia_status`.
O feed continua decidindo a disponibilidade; o status estático não bloqueia uma
estação reativada nem transforma uma estação sem leitura em chuva zero.

Sem cadastro disponível ou sem correspondência, a coleta anterior é preservada.
Registros hidrológicos não são aceitos como chuva. A planilha não fornece medidas,
nomes de bairros, rios, cotas de acionamento, datum, horários ou endpoints.
Nenhum nível, previsão, alerta ou novo marcador no mapa é criado por esta importação.

## Pontos para investigação

- Gaspar: 7 de 9 pluviômetros operacionais no cadastro.
- Ilhota: 4 de 7 pluviômetros operacionais no cadastro.
- Pomerode: hidrológica `421320321H`, operacional, lat -26.7259, lon -49.172.
  Confirmar curso d'água, variável, acesso às leituras e zero antes de integrar nível.
- Brusque: hidrológica `420290901H` inativa no cadastro. Esse código não identifica
  a estação DCSC-00019; não transferir status entre redes.

Esses números não substituem as contagens do retrato do Mapa Interativo de 02/09.
O catálogo antigo e seu campo `ativa` permanecem com a origem original.

## Reimportação

```sh
python scripts/importar_rede_cemaden.py caminho/Rede_Observacional_Santa_Catarina___SC.xlsx
python -m unittest discover -s scripts -p 'teste_*cemaden.py'
```

O importador usa apenas a biblioteca padrão, valida cabeçalhos, campos, códigos
únicos, tipos e coordenadas e grava o JSON somente após validar toda a planilha.
Revisar o diff antes de aceitar uma nova versão do cadastro.
