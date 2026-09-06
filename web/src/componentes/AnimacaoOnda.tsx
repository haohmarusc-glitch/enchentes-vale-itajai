import { useEffect, useMemo, useState } from 'react'
import type { Cidade } from '../dados/tipos'
import type { EstadoSerie } from '../dados/serie'
import { leituraEm, serieDaCidade } from '../dados/serie'
import { faixaDaCidade, type Faixa } from '../logica/tempoReal'
import { linhaDaReproducao, vinculoDeResgate } from '../logica/reproducaoPorCidade'
import { dataHora, metros } from '../logica/formato'
import { ROTULO_FAIXA } from './LegendaFaixas'
import estilos from './AnimacaoOnda.module.css'

/**
 * A onda descendo, no espírito do Kikikuru: reproduz as últimas horas e, a cada
 * instante, pinta cada cidade pela faixa da régua DELA naquele momento. Como a
 * faixa é normalizada por cidade (nunca metro absoluto comparado), ver a cor
 * acender de montante a jusante é ver a cheia caminhar — sem sugerir que uma
 * cidade "enche mais" que a outra.
 *
 * É reprodução do que foi MEDIDO, não previsão. Cidade sem leitura fresca
 * naquele instante fica cinza — nunca verde sobre buraco.
 */
const COR_FAIXA: Record<Faixa, string> = {
  normal: '#2e7d32',
  monitoramento: '#a3c93a',
  atencao: '#e6a700',
  alerta: '#e2661a',
  inundacao: '#c62828',
  emergencia: '#c62828',
  'sem-dado': '#9aa7b2',
  varias: '#1c6ea4',
}

const PASSO_MIN = 30
const JANELA_H = 24
const MS_POR_QUADRO = 450

export default function AnimacaoOnda({
  rioId,
  cidades,
  serie,
  leituras = [],
}: {
  rioId: string
  cidades: Cidade[]
  serie: EstadoSerie
  /**
   * As leituras ao vivo, só para saber quais títulos são RESGATE de qual
   * primária. Sem isso, Blumenau (primária + AlertaBlu da mesma régua ANA)
   * passaria por duas réguas e perderia o número.
   */
  leituras?: readonly { estacao: string; resgateDe: string | null }[]
}) {
  const grade = useMemo(() => {
    let min = Infinity
    let max = -Infinity
    for (const c of cidades) {
      for (const p of serieDaCidade(serie, rioId, c.id)) {
        const t = p.medidoEm.getTime()
        if (t < min) min = t
        if (t > max) max = t
      }
    }
    if (!Number.isFinite(min)) return [] as number[]
    const inicio = Math.max(min, max - JANELA_H * 3_600_000)
    const passos: number[] = []
    for (let t = inicio; t < max; t += PASSO_MIN * 60_000) passos.push(t)
    passos.push(max)
    return passos
  }, [rioId, cidades, serie])

  const [indice, setIndice] = useState(0)
  const [tocando, setTocando] = useState(false)

  // Sempre que a série muda, começa no instante mais recente (a cena "agora").
  useEffect(() => {
    setIndice(grade.length > 0 ? grade.length - 1 : 0)
    setTocando(false)
  }, [grade.length])

  useEffect(() => {
    if (!tocando || grade.length === 0) return
    const id = setInterval(() => setIndice((x) => (x + 1 >= grade.length ? x : x + 1)), MS_POR_QUADRO)
    return () => clearInterval(id)
  }, [tocando, grade.length])

  // Chegou ao fim: para (não fica batendo no último quadro).
  useEffect(() => {
    if (tocando && indice >= grade.length - 1) setTocando(false)
  }, [indice, tocando, grade.length])

  if (grade.length === 0) {
    return (
      <p className={estilos.vazio}>
        Ainda não há série publicada para animar este rio. A coleta acumula a cada
        15 minutos — quando houver leituras, a reprodução aparece aqui.
      </p>
    )
  }

  const t = grade[Math.min(indice, grade.length - 1)]!
  const instante = new Date(t)

  const vinculo = vinculoDeResgate(leituras)
  const linhas = cidades.map((c) => {
    const pontos = serieDaCidade(serie, rioId, c.id)
    const atual = leituraEm(pontos, t)
    const faixa = faixaDaCidade(
      c,
      atual ? { nivel_m: atual.nivel_m, medidoEm: atual.medidoEm } : null,
      false,
      instante,
    )
    // A série de uma cidade com VÁRIAS RÉGUAS é a costura delas: o ponto mais
    // próximo do instante pode ser de qualquer uma, e o metro salta com a
    // troca de zero, não com o rio. Ver `logica/reproducaoPorCidade`.
    return { c, atual, faixa, linha: linhaDaReproducao(pontos, atual, vinculo) }
  })

  const noFim = indice >= grade.length - 1
  const aoTocar = () => {
    if (noFim) setIndice(0) // recomeça do início da janela
    setTocando((v) => !v)
  }

  return (
    <div>
      <div className={estilos.controles}>
        <button type="button" className={estilos.botao} onClick={aoTocar}>
          {tocando ? '⏸ Pausar' : noFim ? '▶ Rever' : '▶ Reproduzir'}
        </button>
        <input
          className={estilos.barra}
          type="range"
          min={0}
          max={grade.length - 1}
          value={Math.min(indice, grade.length - 1)}
          onChange={(e) => {
            setTocando(false)
            setIndice(Number(e.target.value))
          }}
          aria-label="Instante da reprodução"
        />
        <span className={estilos.instante}>{dataHora(instante)}</span>
      </div>

      <ul className={estilos.cidades}>
        {linhas.map(({ c, faixa, linha }) => (
          <li key={c.id} className={estilos.cidade}>
            <span className={estilos.ponto} style={{ background: COR_FAIXA[faixa] }} aria-hidden />
            <span className={estilos.nome}>{c.nome}</span>
            <span className={estilos.faixa}>
              {linha.tipo === 'varias-reguas'
                ? `${linha.quantas} réguas nesta cidade`
                : ROTULO_FAIXA[faixa]}
            </span>
            <span className={estilos.nivel}>
              {linha.tipo === 'leitura' ? metros(linha.nivel_m) : '—'}
            </span>
          </li>
        ))}
      </ul>

      <p className={estilos.nota}>
        Reprodução do que foi <strong>medido</strong> nas últimas horas — cada cidade
        na cor da faixa da régua dela naquele instante. Não é previsão. Cinza = sem
        leitura fresca naquele momento. Cidade com <strong>mais de uma régua</strong>
        não mostra metro aqui: as réguas têm zeros diferentes, e um número só
        saltaria com a troca de régua em vez do rio — a leitura de cada uma está
        na lista da cidade. Para a projeção de chegada a jusante, veja o painel
        “Se o pico fosse agora”.
      </p>
    </div>
  )
}
