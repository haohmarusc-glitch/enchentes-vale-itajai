"""Coleta no PC e envia somente Gaspar por SSH. Executar uma vez por rodada."""
import argparse
import json
import subprocess
from datetime import datetime, timezone

import coleta_gaspar as cg
from gaspar_pc import FONTE, validar

# Destino fixo; nenhuma interpolação de conteúdo remoto ou de caminho do usuário.
RECEBER = """import sys,os,tempfile,pathlib
p=pathlib.Path('/opt/enchentes-vale-itajai/data/tempo-real/gaspar-pc.json')
d=sys.stdin.buffer.read(16385)
if len(d)>16384: raise SystemExit('arquivo excede limite')
p.parent.mkdir(parents=True,exist_ok=True)
fd,n=tempfile.mkstemp(prefix='.gaspar-pc-',dir=p.parent)
with os.fdopen(fd,'wb') as f: f.write(d)
os.replace(n,p)
print('Gaspar recebido na VPS')
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vps', required=True, help='destino SSH já autorizado, usuário@host')
    args = ap.parse_args()
    if args.vps.startswith('-') or any(c.isspace() for c in args.vps):
        ap.error('destino SSH inválido')
    if not cg.permitido():
        raise SystemExit('Não foi possível confirmar acesso ao portal de Gaspar.')
    leitura = cg.leitura_da_cidade(cg.analisar_estacao(cg.baixar(cg.URL_ESTACAO)))
    corpo = {'fonte': FONTE, 'coletado_em': datetime.now(timezone.utc).isoformat(), 'leitura': leitura}
    if not validar(corpo):
        raise SystemExit('Sem leitura municipal recente e válida; nada enviado.')
    # aspas simples POSIX no comando remoto; o JSON vai pelo stdin, nunca pelo shell.
    comando = "python3 -c '" + RECEBER.replace("'", "'\"'\"'") + "'"
    subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                    '-o', 'ConnectTimeout=10', args.vps, comando],
                   input=json.dumps(corpo, ensure_ascii=False).encode('utf-8'), check=True, timeout=30)
    print(f"Enviado: {leitura['nivel_m']:.2f} m, medido em {leitura['medido_em']} (Brasília)")


if __name__ == '__main__':
    main()
