import type { Cidade } from '../dados/tipos'
import { rotuloCota, numero } from '../logica/formato'
import { escalaDoMedidor } from '../logica/medidor'
import estilos from './MedidorCotas.module.css'

/** "6,0", "9,76": a cota como a Defesa Civil escreve, sem zero inventado. */
function curto(v: number): string {
  return v.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })
}

/**
 * A régua desenhada da cidade: as cotas DELA em segmentos coloridos e o nível
 * marcado. É a escala da própria cidade — o texto ao lado diz que os metros não
 * se comparam com os de outra.
 */
export default function MedidorCotas({ cidade, nivel }: { cidade: Cidade; nivel: number | null }) {
  const escala = escalaDoMedidor(cidade.cotas_m ?? {}, nivel)
  if (!escala) return null
  const nomes = cidade.cotas_nomes_na_fonte
  // Números de cotas muito próximas descem para uma segunda linha, alternando.
  const linhas: number[] = []
  escala.marcas.forEach((m, i) => {
    const anterior = escala.marcas[i - 1]
    linhas.push(anterior && m.pos - anterior.pos < 0.1 && linhas[i - 1] === 0 ? 1 : 0)
  })
  const descricao =
    `Régua de ${cidade.nome}` +
    (nivel !== null ? `: nível ${numero(nivel)} m` : '') +
    '; cotas: ' +
    escala.marcas.map((m) => `${rotuloCota(m.chave, nomes)} ${numero(m.valor)} m`).join(', ')
  return (
    <div className={estilos.medidor} role="img" aria-label={descricao}>
      <div className={estilos.trilho}>
        {escala.segmentos.map((s) => (
          <span
            key={`${s.faixa}-${s.de}`}
            className={`${estilos.segmento} ${estilos[s.faixa] ?? ''}`}
            style={{ left: `${s.de * 100}%`, width: `${(s.ate - s.de) * 100}%` }}
          />
        ))}
        {escala.nivel !== null && nivel !== null ? (
          <span className={estilos.marcador} style={{ left: `${escala.nivel * 100}%` }}>
            <span className={estilos.bolha}>{numero(nivel)}</span>
          </span>
        ) : null}
      </div>
      {/* Embaixo de cada marca, só o número (curto, não colide nem com letra
          grande); os nomes vêm na legenda, na mesma ordem e com a mesma cor. */}
      <div className={`${estilos.rotulos} ${linhas.includes(1) ? estilos.duasLinhas : ''}`} aria-hidden="true">
        {escala.marcas.map((m, i) => (
          <span
            key={m.chave}
            className={`${estilos.rotulo} ${linhas[i] ? estilos.linha2 : ''} ${
              m.pos < 0.06 ? estilos.aEsquerda : m.pos > 0.94 ? estilos.aDireita : ''
            }`}
            style={{ left: `${m.pos * 100}%` }}
          >
            {curto(m.valor)}
          </span>
        ))}
      </div>
      <ul className={estilos.legenda} aria-hidden="true">
        {escala.marcas.map((m) => (
          <li key={m.chave}>
            <span className={`${estilos.amostra} ${estilos[m.chave] ?? ''}`} />
            {rotuloCota(m.chave, nomes)} <strong>{curto(m.valor)}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}
