# Gaspar: coleta pelo PC e entrega à VPS

O portal municipal responde no PC, mas a VPS não estabelece TCP com
186.250.184.3:443. DNS funciona; a falha precede TLS. A causa de rede não foi
determinada. Esta ponte transporta somente a leitura municipal da estação 21.

No PC, com Python, dependências do coletor e acesso SSH já configurado:

```powershell
python scripts/enviar_gaspar_pc.py --vps root@65.108.154.111
```

O envio confirma acesso ao portal, confere o título da estação 21 e envia JSON
pelo stdin do SSH. A chave e a senha não entram no código. Exige chave do host
já conhecida e autenticação não interativa. O arquivo é escrito atomicamente
em `/opt/enchentes-vale-itajai/data/tempo-real/gaspar-pc.json`.

O coletor da VPS aceita esse arquivo quando a consulta pelo PC tem até 30 min
e a medição municipal tem até 3 h (limite geral de leitura velha do monitor).
Datas futuras, estação/cidade/rio/fonte diferentes, números inválidos e arquivo
ilegível são recusados. A medição conserva o horário de Brasília sem fuso;
o horário da consulta é UTC. A idade nunca é renovada pelo envio.

Enquanto o arquivo for válido, o coletor evita a tentativa de rede que expira
na VPS. A leitura entra pelo fluxo existente em `ultimo.json`, série mensal,
linha do tempo e registro do evento. Sem arquivo válido, tenta a fonte direta.
O envio sozinho não altera `ultimo.json` nem publica um snapshot parcial.

Executar o envio a cada 15 min com o PC ligado e conectado. O cron existente
da VPS continua responsável pela coleta e publicação. É necessário integrar
esta alteração no main e atualizar a VPS antes de o arquivo ser consumido.

Em 12/09 às 21h38, o transporte foi confirmado, mas o portal só publicava
4,02 m de 19h04: dado atrasado, não uma medição feita às 21h38. Se o município
não renovar a medição, a ponte para de aceitá-la ao ultrapassar três horas.

Testes verificam identidade, carimbos, expiração, valores inválidos, arquivo
ausente/corrompido e uso pelo coletor sem tentar o host inacessível.
