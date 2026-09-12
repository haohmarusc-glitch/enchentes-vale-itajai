import { useEffect, useMemo, useState } from 'react'
import historico from '@dados/manchas/index.json'
import ituporanga from '@dados/manchas/ituporanga/index.json'
import blumenau from '@dados/manchas/blumenau/index.json'
import { camadaBlumenau } from '../logica/camadaBlumenau'
import { cheiaMaisProxima, type EventoComparavel, type MedicaoComparavel } from '../logica/compararCheias'
import { rotuloEvento } from '../logica/manchas'

const RISCO_ASCURRA = 'manchas/ascurra/risco-inundacao-2015.geojson'
const urls = import.meta.glob('@dados/manchas/**/*.geojson', { query: '?url', import: 'default', eager: true }) as Record<string, string>
export type CamadaDesenhada = { geo: GeoJSON.FeatureCollection; rotulo: string } | null
interface Props {
  somenteDados?: boolean
  cidade: string
  leituras: readonly MedicaoComparavel[]
  agora: Date
  reproduzindo: boolean
  onCamada: (camada: CamadaDesenhada) => void
}
export default function CamadasMonitor({ cidade, leituras, agora, reproduzindo, onCamada, somenteDados = false }: Props) {
  const [modo, setModo] = useState(cidade === 'ascurra' ? RISCO_ASCURRA : 'auto')
  const [estado, setEstado] = useState('')
  const [tentativa, setTentativa] = useState(0)
  const eventos = useMemo(() => (historico.manchas as EventoComparavel[]).filter((m) => m.cidade === cidade), [cidade])
  const opcoes = useMemo(() => cidade === 'ascurra'
    ? [{ arquivo: RISCO_ASCURRA, rotulo: 'Setores de risco de inundação — CPRM, 2015 (referência estática)' }]
    : cidade === 'blumenau'
    ? blumenau.camadas.map(c => ({ arquivo: 'manchas/blumenau/' + c.arquivo, rotulo: `Simulação ${c.nivel_m.toFixed(2).replace('.', ',')} m — FURB 2025` }))
    : cidade === 'ituporanga'
    ? ituporanga.camadas.map((c) => ({ arquivo: 'manchas/ituporanga/' + c.arquivo, rotulo: `Camada ${c.nivel_m.toFixed(2).replace('.', ',')} m — consulta manual` }))
    : eventos.map((e) => ({ arquivo: e.arquivo, rotulo: `${rotuloEvento(e.evento)} — ${e.tipo ?? 'mancha histórica'}` })), [cidade, eventos])
  const proxima = reproduzindo ? null : cheiaMaisProxima(eventos, leituras, agora)
  const blu = cidade === 'blumenau'
  const cotaBlu = blu && !reproduzindo ? camadaBlumenau(blumenau.camadas, leituras, agora) : null
  const arquivo = modo === 'auto' ? (blu ? cotaBlu ? 'manchas/blumenau/' + cotaBlu.arquivo : undefined : proxima?.evento.arquivo) : modo === 'off' ? undefined : modo
  const escolha = opcoes.find((o) => o.arquivo === arquivo)
  const evento = eventos.find((e) => e.arquivo === arquivo)
  const chuva = evento?.chuva_7dias
  const risco = arquivo === RISCO_ASCURRA
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
  return <section className="cartao" style={{ minWidth: 0, maxWidth: '100%' }} aria-label="Camadas de cheia no Monitor">
    <h2>Camadas e comparação de cheias</h2>
    <label htmlFor="camada-monitor">Camada sobre o mapa</label>{' '}
    <select style={{ display: 'block', width: '100%', maxWidth: '100%', minWidth: 0, boxSizing: 'border-box' }} id="camada-monitor" value={modo} onChange={(e) => setModo(e.target.value)}>
      <option value="auto">{blu ? 'Automática — referência por cota (FURB 2025)' : 'Automática — cheia histórica mais próxima'}</option>
      <option value="off">Ocultar camadas</option>
      {opcoes.map((o) => <option value={o.arquivo} key={o.arquivo}>{o.rotulo}</option>)}
    </select>
    {blu && <p>Cartas de enchente FURB 2025, publicadas pelo <a href={blumenau.pagina} target="_blank" rel="noreferrer">AlertaBlu</a>. Simulações de 8 a 18 m; não representam alagamento observado nem picos de eventos históricos. A cor de aviso da régua é independente destas áreas.</p>}
    {blu && modo === 'auto' && <p role="status">{reproduzindo ? 'Camada automática pausada durante a reprodução.' : cotaBlu ? `Referência de ${cotaBlu.nivel_m.toFixed(2).replace('.', ',')} m: maior cota disponível que não supera a leitura recente. Sem interpolação; a área pode diferir da situação real.` : 'Sem camada automática: é necessária leitura compatível de pelo menos 8 m e de até duas horas. Você pode consultar as simulações manualmente.'}</p>}
    {!blu && modo === 'auto' && (proxima ? <p role="status">
      Comparação mais próxima: <strong>{rotuloEvento(proxima.evento.evento)}</strong>.{' '}
      O rio está {Math.abs(proxima.diferencaM).toFixed(2).replace('.', ',')} m{' '}
      {proxima.diferencaM < 0 ? 'abaixo' : 'acima'} do pico registrado naquela cheia, na mesma régua.
      Esta comparação não prevê que o rio chegará àquele nível.
    </p> : <p>{reproduzindo ? 'Comparação automática pausada durante a reprodução: não mistura nível atual com o passado.' :
      opcoes.length === 0 ? 'Ainda não há áreas de inundação cadastradas para esta cidade.' :
      'Ainda não é possível escolher a cheia mais próxima: faltam pico e régua documentados ou leitura recente compatível. Você pode consultar uma camada manualmente.'}</p>)}
    {risco && <p>Quatro setores de risco de inundação levantados em 25/06/2015. A área azul é uma referência estática: não é a extensão de uma cheia específica nem alagamento observado agora. Não muda com o nível atual. <a href="https://rigeo.sgb.gov.br/handle/doc/18496" target="_blank" rel="noreferrer">Fonte: SGB/CPRM · levantamento de Ascurra</a>. Ainda falta a relação entre polígonos e cotas da régua para selecionar uma mancha conforme a cheia.</p>}
    {escolha && !risco && <>
      <p><strong>{escolha.rotulo}</strong>. A área azul é a camada da fonte, não confirmação de alagamento agora.</p>
      {!blu && <><p>Chuva nos sete dias da cheia passada:{' '}{chuva && Number.isFinite(chuva.mm) && chuva.mm >= 0
        ? <>{chuva.mm} mm, de {chuva.inicio} a {chuva.fim}, estação {chuva.estacao}. <a href={chuva.fonte}>Fonte</a></>
        : 'não documentada para esta camada.'}</p>
      <p>Chuva nos sete dias da cheia em andamento: acumulado de sete dias ainda não disponível nesta comparação. Valores de 24 ou 48 horas não substituem a semana.</p></>}
    </>}
    <p role="status">{estado}</p>
    {estado.startsWith('Não foi possível') && <button onClick={() => setTentativa((n) => n + 1)}>Tentar novamente</button>}
    {somenteDados ? <p>Exibição restrita às camadas cadastradas deste município. Sem geometria ou referência compatível, o mapa permanece sem mancha automática.</p> : <p>Selecione a cidade no menu Cidades do Monitor para consultar suas camadas. Ausência de área desenhada não significa ausência de risco. Siga a Defesa Civil, 199.</p>}
  </section>
}
