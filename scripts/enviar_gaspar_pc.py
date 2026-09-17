"""Coleta no PC e envia somente Gaspar por SSH. Executar uma vez por rodada."""
import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone

import coleta_gaspar as cg
from gaspar_pc import FONTE, validar

FUSO_BRASILIA = timezone(timedelta(hours=-3))

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



def porque_recusou(leitura, agora=None) -> str:
    """Por que esta leitura não foi enviada — em uma frase que o log responde sozinho.

    POR QUE EXISTE (17/09/2026). A tarefa agendada no PC roda de 15 em 15 min e
    escreve num log. Durante uma madrugada inteira ele repetiu a MESMA linha,
    "sem leitura municipal recente e válida" — verdadeira e inútil: não dá para
    saber se o portal parou de publicar a régua do Açu, se o número veio
    implausível ou se a leitura está lá, só velha. São três problemas diferentes,
    com três donos diferentes, e a única forma de distinguir era abrir o site na
    mão. Num dia de chuva, essa diferença é o que decide se vale correr atrás.
    """
    if leitura is None:
        return ('a tabela do portal não trouxe a régua do Açu com nível plausível E '
                'horário — ou a linha sumiu, ou veio sem carimbo, ou o número está '
                'fora da faixa de um rio')
    quando = leitura.get('medido_em')
    try:
        medicao = datetime.fromisoformat(str(quando)).replace(tzinfo=FUSO_BRASILIA)
    except (TypeError, ValueError):
        return f'a leitura veio com horário ilegível ({quando!r})'
    horas = ((agora or datetime.now(timezone.utc)) - medicao).total_seconds() / 3600
    nivel = leitura.get('nivel_m')
    if horas > 3:
        return (f'a leitura mais recente do portal é de {quando} ({horas:.1f} h atrás), '
                f'e o teto é 3 h — a estação do município parou de atualizar, '
                f'não o envio. Último valor visto: {nivel} m')
    if horas < 0:
        return f'a leitura está {abs(horas):.1f} h no futuro ({quando}) — relógio fora de hora'
    return f'a leitura de {quando} ({nivel} m) não passou na validação de formato ou faixa'


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
        raise SystemExit('Nada enviado: ' + porque_recusou(leitura))
    # aspas simples POSIX no comando remoto; o JSON vai pelo stdin, nunca pelo shell.
    comando = "python3 -c '" + RECEBER.replace("'", "'\"'\"'") + "'"
    subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                    '-o', 'ConnectTimeout=10', args.vps, comando],
                   input=json.dumps(corpo, ensure_ascii=False).encode('utf-8'), check=True, timeout=30)
    print(f"Enviado: {leitura['nivel_m']:.2f} m, medido em {leitura['medido_em']} (Brasília)")


if __name__ == '__main__':
    main()
