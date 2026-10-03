import { Link } from 'react-router-dom'
import type { Cidade, Topologia } from '../dados/tipos'
import { trechos } from '../dados/carregar'
import type { AoVivo, EstadoDaCidade } from '../dados/usarAoVivo'
import { estadoDaCidade } from '../dados/usarAoVivo'
import { rotuloDaFaixa, tendenciaDaLeitura, textoParaCompartilhar, vizinhasNoEixo } from '../logica/agora'
import { metros } from '../logica/formato'
import { frescorDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'
import { caminho, faixaHoras } from '../logica/transito'
import { ChipFaixa } from './CartaoAgora'
import { ROTULO_FAIXA } from './LegendaFaixas'
import SeloConfianca from './SeloConfianca'
import estilos from './CartoesDaCidade.module.css'

/** `acu`/`mirim` — a palavra da URL para o rio do cadastro. */
export function rioDaUrl(rioId: string): 'acu' | 'mirim' {
  return rioId === 'itajai-mirim' ? 'mirim' : 'acu'
}

/** A sequência que a água realmente segue: o tronco no Açu, a fila no Mirim. */
export function eixoDoRio(cidades: Cidade[], topologia?: Topologia): string[] {
  if (topologia?.tronco_sequencia?.length) return topologia.tronco_sequencia
  return cidades.map((c) => c.id)
}

/**
 * Os três botões do cartão "Agora": mandar no WhatsApp (sem link do site, D4),
 * a busca da rua e o mapa. O WhatsApp só aparece com leitura que não é velha.
 */
export function AcoesDaCidade({
  cidade,
  rioId,
  aoVivo,
  estado,
}: {
  cidade: Cidade
  rioId: string
  aoVivo: AoVivo
  estado: EstadoDaCidade
}) {
  const { leitura, faixa, serie } = estado
  const texto = leitura
    ? textoParaCompartilhar({
        cidade,
        leitura,
        rotuloFaixa: faixa === 'sem-dado' || faixa === 'varias' ? null : rotuloDaFaixa(faixa, cidade, ROTULO_FAIXA[faixa]),
        tendencia: tendenciaDaLeitura(serie, leitura, aoVivo.agora),
        agora: aoVivo.agora,
      })
    : null
  const rio = rioDaUrl(rioId)
  return (
    <div className={estilos.acoes}>
      {texto ? (
        <a
          className={estilos.zap}
          href={`https://wa.me/?text=${encodeURIComponent(texto)}`}
          target="_blank"
          rel="noreferrer"
        >
          <span aria-hidden="true">↗</span> Mandar no WhatsApp
        </a>
      ) : null}
      <div className={estilos.duas}>
        <Link className={estilos.botao} to={cidade.id === 'itajai' ? '/itajai' : `/${rio}/${cidade.id}?aba=rua`}>
          Minha rua alaga?
        </Link>
        <Link className={estilos.botao} to={`/monitor/${cidade.id}`}>
          Ver no mapa
        </Link>
      </div>
    </div>
  )
}

/**
 * "A água desce para Gaspar — cerca de 2 h": o tempo de referência até a
 * cidade de baixo, e de onde a água vem. Só ao longo do eixo; cabeceira e
 * afluente lateral dizem que não estão nele, em vez de encadear um tempo que a
 * geografia não sustenta. É referência de estudo, não previsão desta cheia.
 */
export function CartaoDescida({
  cidade,
  rioId,
  cidades,
  topologia,
}: {
  cidade: Cidade
  rioId: string
  cidades: Cidade[]
  topologia?: Topologia
}) {
  const eixo = eixoDoRio(cidades, topologia)
  const { acima, abaixo } = vizinhasNoEixo(eixo, cidade.id)
  const rio = rioDaUrl(rioId)
  const nome = (id: string | null) => cidades.find((c) => c.id === id)
  const deCima = nome(acima)
  const deBaixo = nome(abaixo)
  const paraBaixo = deBaixo ? caminho(trechos, rioId, cidade.id, deBaixo.id) : null
  const doAlto = deCima ? caminho(trechos, rioId, deCima.id, cidade.id) : null

  if (eixo.indexOf(cidade.id) < 0) {
    return (
      <section className={estilos.cartao}>
        <h2 className={estilos.titulo}>De onde a água vem</h2>
        <p className={estilos.texto}>
          {cidade.nome} não está na sequência do tronco — é{' '}
          {cidade.ramo ? <>uma cabeceira ou afluente ({cidade.ramo.replace(/_/g, ' ')})</> : 'um ponto fora do eixo'}.
          A cheia daqui <strong>não é a mesma</strong> que desce o rio principal, então não há tempo
          de descida a encadear por esta cidade. Veja a <Link to={`/${rio}`}>tela do rio</Link>.
        </p>
      </section>
    )
  }

  return (
    <section className={estilos.cartao}>
      {deBaixo ? (
        <>
          <h2 className={estilos.titulo}>
            A água desce para <Link to={`/${rio}/${deBaixo.id}`}>{deBaixo.nome}</Link>
          </h2>
          {paraBaixo ? (
            <>
              <p className={estilos.horas}>{faixaHoras(paraBaixo)}</p>
              <p className={estilos.texto}>
                <SeloConfianca nivel={paraBaixo.confianca} fonte={paraBaixo.fontes.join('; ')} tipo="trecho" />{' '}
                tempo de referência ({paraBaixo.fontes.join('; ')}). É um intervalo,{' '}
                <strong>não é previsão</strong> para esta cheia.
              </p>
            </>
          ) : (
            <p className={estilos.texto}>Tempo de descida ainda não levantado para este trecho.</p>
          )}
        </>
      ) : (
        <h2 className={estilos.titulo}>Fim do curso nesta tela</h2>
      )}
      {deCima ? (
        <p className={estilos.vem}>
          A água vem de <Link to={`/${rio}/${deCima.id}`}>{deCima.nome}</Link>
          {doAlto ? (
            <>
              {' '}— leva <strong>{faixaHoras(doAlto)}</strong> até aqui
            </>
          ) : (
            <> — tempo ainda não levantado</>
          )}
          .
        </p>
      ) : null}
    </section>
  )
}

/**
 * Uma linha de situação de outra cidade ("Rio acima: Indaial", "Outras que
 * sigo"): faixa, número e idade — ou, sem leitura, o aviso de que falta dado
 * não quer dizer que está tudo bem.
 */
export function LinhaDeCidade({
  rotulo,
  cidade,
  rioId,
  aoVivo,
}: {
  rotulo?: string
  cidade: Cidade
  rioId: string
  aoVivo: AoVivo
}) {
  const estado = estadoDaCidade(cidade, rioId, aoVivo)
  const { leitura } = estado
  const idade = leitura?.medidoEm ? idadeMin(leitura.medidoEm, aoVivo.agora) : null
  const velha = idade === null || frescorDaCidade(idade, cidade.id) === 'velha'
  const para = cidade.id === 'itajai' ? '/itajai' : `/${rioDaUrl(rioId)}/${cidade.id}`
  return (
    <Link to={para} className={estilos.linha}>
      <span className={estilos.linhaCorpo}>
        <span className={estilos.linhaNome}>
          {rotulo ? <span className={estilos.linhaRotulo}>{rotulo}: </span> : null}
          {cidade.nome}
        </span>
        <span className={estilos.linhaSub}>
          {leitura && !velha ? (
            <>
              {metros(leitura.nivel_m)} · medido {textoIdade(idade!)}
            </>
          ) : estado.varias ? (
            <>{estado.todas.length} réguas, uma por uma</>
          ) : estado.faixaEstadual && estado.estadual?.medidoEm ? (
            <>
              rede estadual: {metros(estado.estadual.nivelBrutoM)} · medido{' '}
              {textoIdade(idadeMin(estado.estadual.medidoEm, aoVivo.agora))}
            </>
          ) : (
            <>sem leitura recente · não conclua que está seguro</>
          )}
        </span>
      </span>
      {(leitura && !velha) || estado.varias || estado.faixa !== 'sem-dado' ? (
        <ChipFaixa faixa={estado.faixa} cidade={cidade} compacto />
      ) : estado.faixaEstadual ? (
        <ChipFaixa faixa={estado.faixaEstadual} cidade={cidade} compacto estadual />
      ) : null}
      <span className={estilos.abrir} aria-hidden="true">›</span>
    </Link>
  )
}
