import { useEffect, useMemo, useState } from 'react'
import historico from '@dados/manchas/index.json'
import ituporanga from '@dados/manchas/ituporanga/index.json'
import { cheiaMaisProxima, type EventoComparavel, type MedicaoComparavel } from '../logica/compararCheias'
import { rotuloEvento } from '../logica/manchas'

const urls = import.meta.glob('@dados/manchas/**/*.geojson', { query: '?url', import: 'default', eager: true }) as Record<string, string>
export type CamadaDesenhada = { geo: GeoJSON.FeatureCollection; rotulo: string } | null
interface Props {
  cidade: string
  leituras: readonly MedicaoComparavel[]
  agora: Date
  reproduzindo: boolean
  onCamada: (camada: CamadaDesenhada) => void
}
export default function CamadasMonitor({ cidade, leituras, agora, reproduzindo, onCamada }: Props) {
  const [modo, setModo] = useState('auto')
  const [estado, setEstado] = useState('')
  const [tentativa, setTentativa] = useState(0)
  const eventos = useMemo(() => (historico.manchas as EventoComparavel[]).filter((m) => m.cidade === cidade), [cidade])
  const opcoes = useMemo(() => cidade === 'ituporanga'
    ? ituporanga.camadas.map((c) => ({ arquivo: 'manchas/ituporanga/' + c.arquivo, rotulo: `Camada ${c.nivel_m.toFixed(2).replace('.', ',')} m — consulta manual` }))
    : eventos.map((e) => ({ arquivo: e.arquivo, rotulo: `${rotuloEvento(e.evento)} — ${e.tipo ?? 'mancha histórica'}` })), [cidade, eventos])
  const proxima = reproduzindo ? null : cheiaMaisProxima(eventos, leituras, agora)
  const arquivo = modo === 'auto' ? proxima?.evento.arquivo : modo === 'off' ? undefined : modo
  const escolha = opcoes.find((o) => o.arquivo === arquivo)
  const evento = eventos.find((e) => e.arquivo === arquivo)
  const chuva = evento?.chuva_7dias
  const rotulo = escolha?.rotulo
  useEffect(() => {
    onCamada(null)
    if (!arquivo || !rotulo) { setEstado(''); return }
    const url = Object.entries(urls).find(([k]) => k.endsWith('/' + arquivo))?.[1]
    if (!url) { setEstado('Arquivo da camada indisponível.'); return }
    let vivo = true
    const controller = new AbortController()
    setEstado('Carregando camada…')
    fetch(url, { signal: controller.signal }).then((r) => { if (!r.ok) throw new Error(); return r.json() })
      .then((geo) => { if (vivo) { onCamada({ geo, rotulo }); setEstado('Camada desenhada no Monitor.') } })
      .catch(() => { if (vivo) setEstado('Não foi possível carregar a camada.') })
    return () => { vivo = false; controller.abort(); onCamada(null) }
  }, [arquivo, rotulo, onCamada, tentativa])
  return <section className="cartao" aria-label="Camadas de cheia no Monitor">
    <h2>Camadas e comparação de cheias</h2>
    <label htmlFor="camada-monitor">Camada sobre o mapa</label>{' '}
    <select id="camada-monitor" value={modo} onChange={(e) => setModo(e.target.value)}>
      <option value="auto">Automática — cheia histórica mais próxima</option>
      <option value="off">Ocultar camadas</option>
      {opcoes.map((o) => <option value={o.arquivo} key={o.arquivo}>{o.rotulo}</option>)}
    </select>
    {modo === 'auto' && (proxima ? <p role="status">
      Comparação mais próxima: <strong>{rotuloEvento(proxima.evento.evento)}</strong>.{' '}
      O rio está {Math.abs(proxima.diferencaM).toFixed(2).replace('.', ',')} m{' '}
      {proxima.diferencaM < 0 ? 'abaixo' : 'acima'} do pico registrado naquela cheia, na mesma régua.
      Esta comparação não prevê que o rio chegará àquele nível.
    </p> : <p>{reproduzindo ? 'Comparação automática pausada durante a reprodução: não mistura nível atual com o passado.' :
      opcoes.length === 0 ? 'Ainda não há áreas de inundação cadastradas para esta cidade.' :
      'Ainda não é possível escolher a cheia mais próxima: faltam pico e régua documentados ou leitura recente compatível. Você pode consultar uma camada manualmente.'}</p>)}
    {escolha && <>
      <p><strong>{escolha.rotulo}</strong>. A área azul é a camada da fonte, não confirmação de alagamento agora.</p>
      <p>Chuva nos sete dias da cheia passada:{' '}{chuva && Number.isFinite(chuva.mm) && chuva.mm >= 0
        ? <>{chuva.mm} mm, de {chuva.inicio} a {chuva.fim}, estação {chuva.estacao}. <a href={chuva.fonte}>Fonte</a></>
        : 'não documentada para esta camada.'}</p>
      <p>Chuva nos sete dias da cheia em andamento: acumulado de sete dias ainda não disponível nesta comparação. Valores de 24 ou 48 horas não substituem a semana.</p>
    </>}
    <p role="status">{estado}</p>
    {estado.startsWith('Não foi possível') && <button onClick={() => setTentativa((n) => n + 1)}>Tentar novamente</button>}
    <p>Selecione a cidade no menu Cidades do Monitor para consultar suas camadas. Ausência de área desenhada não significa ausência de risco. Siga a Defesa Civil, 199.</p>
  </section>
}
