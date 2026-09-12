# Registro do evento de chuva

`data/evento-ativo.json` identifica o evento em observação. O nome não determina
o início hidrológico da cheia. Para encerrar novas capturas, definir `evento: null`.

A publicação normal executa `registrar_evento.py` antes de substituir os dados
do site. São preservados todos os `ultimo*.json` disponíveis na VPS: nível, chuva,
barragens e os metadados e fontes que os coletores já fornecem. Arquivos ausentes
ou JSONs inválidos ficam registrados no índice. Falha de armazenamento aparece
no log sem bloquear a publicação do monitor. `--seco` não grava capturas.

Cada versão fica comprimida e identificada pelo SHA-256 dos bytes originais.
O índice `capturas.ndjson` registra a hora UTC da captura e o horário de coleta
de cada arquivo quando disponível. Repetições reutilizam o mesmo objeto;
correções da fonte produzem uma nova versão, sem apagar a anterior.
Os horários de medição continuam intactos. Um dado antigo continua antigo:
o horário da captura não é evidência de nova medição.

## Ativar na VPS após o merge

```bash
cd /opt/enchentes-vale-itajai &&
bash scripts/deploy.sh &&
python3 scripts/registrar_evento.py
```

As próximas execuções de `publicar_tempo_real.sh` continuam o registro.
O registro depende do cron existente; não instala agendamento nem acessa a VPS.
O arquivo fica em `/opt/enchentes-vale-itajai/data/eventos-registro/chuvas-vale-2026-09/`.

## Preservar também o histórico anterior

As séries mensais de nível e chuva já ficam em `data/tempo-real/*.ndjson`
(ou `.ndjson.gz`). Guardar uma cópia delas junto ao arquivo do evento:

```bash
cd /opt/enchentes-vale-itajai &&
tar -czf "/root/registro-chuvas-$(date -u +%Y%m%dT%H%M%SZ).tar.gz" data/tempo-real data/eventos-registro
```

Copiar esse backup para outra máquina: o arquivo do evento e as séries na mesma
VPS não protegem contra perda do servidor. O registro não recupera medições
que nunca foram coletadas e não constitui coleta de todas as fontes governamentais.

Na análise posterior, calcular picos por estação e referência de régua e
conferir lacunas antes de chamar um valor de pico do evento. Não somar chuva
de 24 h ou 168 h entre capturas: são janelas sobrepostas. Não inserir picos
automaticamente em `enchentes.json` sem conferir fonte, período e referência.
