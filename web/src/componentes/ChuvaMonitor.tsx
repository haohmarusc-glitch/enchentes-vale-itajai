import type { ChuvaAoVivo } from '../dados/tempoReal'
import { chuvaMonitor, mmChuva } from '../logica/chuvaMonitor'
import { dataHora } from '../logica/formato'
import { idadeMin, textoIdade } from '../logica/tempoReal'

export default function ChuvaMonitor({ cidades, chuva, agora }: {
  cidades: { id: string; nome: string }[]; chuva: ChuvaAoVivo[]; agora: Date
}) {
  return <>
    <table style={{ width: '100%', fontSize: '0.85rem', borderSpacing: '4px 8px' }}>
      <caption>Chuva acumulada (mm)</caption>
      <thead><tr><th>Cidade / estação</th><th>1 h</th><th>12 h</th><th>24 h</th></tr></thead>
      <tbody>{[...new Map(cidades.map(c => [c.id, c])).values()].map(cidade => {
        const c = chuvaMonitor(chuva, cidade.id)
        return <tr key={cidade.id}>
          <th scope="row" style={{ textAlign: 'left', fontWeight: 400 }}>
            <strong>{cidade.nome}</strong>
            <small style={{ display: 'block' }}>{c?.estacao ?? 'Sem leitura válida'}</small>
            {c?.medidoEm && <small style={{ display: 'block' }}>{dataHora(c.medidoEm)} · {textoIdade(idadeMin(c.medidoEm, agora))}</small>}
          </th>
          <td>{mmChuva(c?.mm.h1)}</td><td>{mmChuva(c?.mm.h12)}</td><td>{mmChuva(c?.mm.h24)}</td>
        </tr>
      })}</tbody>
    </table>
    <p>— = indisponível. Pluviômetro com leitura válida mais recente; não é média da cidade. Horários de Brasília.</p>
  </>
}
