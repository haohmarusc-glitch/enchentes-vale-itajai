import { useMemo } from 'react'
import { areaEmTexto, arvoreDaBacia, type BarragemNaArvore } from '../logica/arvoreDaBacia'
import { barragensBrutas, rio as rioDoCadastro } from '../dados/carregar'
import estilos from './ArvoreDaBacia.module.css'

/**
 * "De onde vem a água", na tela do Monitor: o que chega em cada barragem, as
 * três de contenção, e só então o tronco.
 *
 * O QUE ESTE BLOCO NÃO FAZ, de propósito: não mostra o nível de nenhuma
 * barragem. A cota do reservatório é outra escala (centenas de metros acima do
 * mar) e, posta ao lado da régua urbana, pinta emergência falsa — em Taió, 17 m
 * de lago convivem com 5 m no centro. O estado de OPERAÇÃO (comportas abertas
 * ou fechadas) tem bloco próprio, o `EstadoDasBarragens`, e o mapa. Aqui é só a
 * geografia: quem está acima de quem.
 */
function Barragem({ b }: { b: BarragemNaArvore }) {
  const ficha = [
    b.ano ? `${b.ano}` : null,
    b.volumeMm3 != null ? `${b.volumeMm3} hm³` : null,
    b.comportas != null
      ? `${b.comportas} ${b.comportas === 1 ? 'comporta' : 'comportas'}` +
        (b.semComporta ? ` + ${b.semComporta} sem comporta` : '')
      : null,
  ].filter(Boolean)
  const area = areaEmTexto(b)
  return (
    <div className={estilos.barragem}>
      <span className={estilos.parede} aria-hidden="true" />
      <div>
        <strong>{b.nome}</strong> · {b.municipio}
        {ficha.length ? <div className={estilos.ficha}>{ficha.join(' · ')}</div> : null}
        {area ? <div className={estilos.ficha}>{area}</div> : null}
        {b.chuvaEquivalenteMm != null ? (
          <div className={estilos.ficha}>
            enche com ~{b.chuvaEquivalenteMm} mm de chuva sobre a bacia dela
          </div>
        ) : null}
        <div className={estilos.ficha}>a régua de {b.acimaDe} fica abaixo dela</div>
      </div>
    </div>
  )
}

export default function ArvoreDaBacia({ rioId = 'itajai-acu' }: { rioId?: string }) {
  const arvore = useMemo(() => {
    const cadastro = rioDoCadastro(rioId)
    return cadastro ? arvoreDaBacia(rioId, cadastro, barragensBrutas) : null
  }, [rioId])
  if (!arvore) return null

  return (
    <section className={`cartao ${estilos.bloco}`}>
      <h2 className={estilos.titulo}>De onde vem a água</h2>
      <p className={estilos.entrada}>
        A bacia é uma árvore, não uma fila. Duas cabeceiras correm em paralelo e
        só viram Açu quando se encontram; um terceiro rio entra pelo lado, no
        meio do caminho. Cada um passa por uma barragem antes.
      </p>

      <ol className={estilos.ramos}>
        {arvore.cabeceiras.map((c) => (
          <li key={c.cidade} className={estilos.ramo}>
            <span className={estilos.rotulo}>Cabeceira{c.rio ? ` · ${c.rio}` : ''}</span>
            {c.barragem ? <Barragem b={c.barragem} /> : null}
            <div className={estilos.cidade}>{c.cidade}</div>
          </li>
        ))}
      </ol>

      {arvore.nasce ? (
        <p className={estilos.nasce}>
          As duas se encontram em <strong>{arvore.nasce.cidade}</strong> — é ali que
          nasce o rio
          {arvore.nasce.lat != null && arvore.nasce.lon != null ? (
            <span className={estilos.coord}>
              {' '}
              ({arvore.nasce.lat.toFixed(4)}, {arvore.nasce.lon.toFixed(4)})
            </span>
          ) : null}
          .
        </p>
      ) : null}

      <span className={estilos.rotulo}>Tronco — a única sequência que a água segue</span>
      <p className={estilos.tronco}>{arvore.tronco.join(' → ')}</p>

      {arvore.laterais.length ? (
        <>
          <span className={estilos.rotulo}>Entram pelo lado, por outros rios</span>
          <ul className={estilos.laterais}>
            {arvore.laterais.map((l) => (
              <li key={l.cidade}>
                {l.barragem ? <Barragem b={l.barragem} /> : null}
                <div className={estilos.cidade}>{l.cidade}</div>
                <div className={estilos.ficha}>
                  {l.rio}
                  {l.entraPertoDe ? <> · entra no tronco perto de {l.entraPertoDe}</> : null}
                </div>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {arvore.afluentesSemRegua.length ? (
        <>
          <span className={estilos.rotulo}>Entram no tronco sem régua no site</span>
          <ul className={estilos.locais}>
            {arvore.afluentesSemRegua.map((r) => (
              <li key={r.nome}>
                <strong>{r.nome}</strong>
                {r.entraPertoDe ? <> — entra perto de {r.entraPertoDe}</> : null}
                {r.pontoExato ? <div className={estilos.ficha}>{r.pontoExato}</div> : null}
              </li>
            ))}
          </ul>
          <p className={estilos.ficha}>
            Trazem água para o tronco e não têm pino no mapa: sem régua no cadastro,
            não há nível para mostrar. A ausência de pino não significa que não entra
            água por ali.
          </p>
        </>
      ) : null}

      {arvore.locaisPorCidade.length ? (
        <>
          <span className={estilos.rotulo}>Barragens locais, que não são de contenção</span>
          <ul className={estilos.locais}>
            {arvore.locaisPorCidade.map((g) => (
              <li key={g.cidade}>
                {g.barragens.map((b) => b.nome).join(' e ')} — em {g.cidade}
                {g.barragens[0] ? <>, no {g.barragens[0].rio}</> : null}
                {g.barragens.some((b) => b.localidade) ? (
                  <div className={estilos.ficha}>
                    {g.barragens
                      .filter((b) => b.localidade)
                      .map((b) => `${b.nome}: ${b.localidade}`)
                      .join(' · ')}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
          <p className={estilos.ficha}>
            Citadas pelo Plano de Contingência do município. Não amortecem a cheia do
            Açu como as três acima, e a operação delas não é publicada — por isso
            entram sem ficha e sem posição em relação à régua da cidade.
          </p>
        </>
      ) : null}

      {arvore.barragensSoltas.length ? (
        <ul className={estilos.laterais}>
          {arvore.barragensSoltas.map((b) => (
            <li key={b.nome}>
              <Barragem b={b} />
            </li>
          ))}
        </ul>
      ) : null}

      <p className={estilos.ressalva}>
        <strong>A barragem não é o rio da cidade.</strong> O nível do reservatório é
        cota de lago, medida em altura acima do mar, e não se compara com a régua da
        cidade logo abaixo da parede. Nenhum número de barragem pinta pino nem faixa
        neste mapa. Fechar comporta na Oeste ou na Sul muda o que nasce em Rio do Sul;
        fechar na Norte muda o que entra no meio do tronco, e é o que Blumenau vê. São
        manivelas diferentes.
      </p>
    </section>
  )
}
