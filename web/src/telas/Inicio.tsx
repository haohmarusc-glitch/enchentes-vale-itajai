import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { BotaoLetra } from '../componentes/BotoesPreferencia'
import CartaoAgora, { nomeDaFaixa } from '../componentes/CartaoAgora'
import { AcoesDaCidade, LinhaDeCidade, eixoDoRio, rioDaUrl } from '../componentes/CartoesDaCidade'
import { barragensDoRio, cidadesDoRio, eventosDoRio, rio as rioDoCadastro, topologiaDoRio } from '../dados/carregar'
import type { Cidade } from '../dados/tipos'
import { estadoDaCidade, useAoVivo, type AoVivo } from '../dados/usarAoVivo'
import { useCidadesSeguidas } from '../dados/usarPreferencias'
import { useInstalar } from '../dados/modoAplicativo'
import { vizinhasNoEixo } from '../logica/agora'
import { descricaoDoRio } from '../logica/descricaoDoRio'
import estilos from './Inicio.module.css'

/**
 * O INÍCIO DA VERSÃO 2 (03/10/2026): "Minha cidade".
 *
 * Quem abre o site na chuva quer saber da cidade DELE, e antes precisava de
 * dois toques e de saber em que rio ela fica. Agora:
 *  - na primeira visita, a pessoa escolhe a cidade (busca ou toque no nome);
 *  - dali em diante, o Início abre direto no cartão "Agora" dela, com a cidade
 *    de cima do rio logo abaixo — é de lá que a água vem;
 *  - as outras que ela segue aparecem em "Outras que sigo".
 * A escolha fica só neste aparelho (`logica/preferencias.ts`). Sem
 * armazenamento, o seletor volta a cada visita — o lado seguro.
 *
 * A linha "de onde vem a água" de cada rio NÃO é texto fixo: sai do
 * `estacoes.json` por `descricaoDoRio`. Fonte de verdade é o cadastro.
 */
const RIOS = [
  { para: '/acu', id: 'itajai-acu', titulo: 'Rio Itajaí-Açu' },
  { para: '/mirim', id: 'itajai-mirim', titulo: 'Rio Itajaí-Mirim' },
] as const

interface CidadeDoInicio {
  id: string
  nome: string
  rio: string
  rioId: string
  cidade: Cidade
}

/**
 * Todas as cidades, em ordem ALFABÉTICA: quem chega sabe o nome da cidade
 * dele, não em que posição ela cai no curso. Itajaí entra uma vez só, apesar de
 * estar nos dois rios.
 */
function usarCidades(): CidadeDoInicio[] {
  return useMemo(() => {
    const vistas = new Map<string, CidadeDoInicio>()
    for (const [rioId, nomeRio] of [
      ['itajai-acu', 'Açu'],
      ['itajai-mirim', 'Mirim'],
    ] as const) {
      for (const c of cidadesDoRio(rioId)) {
        const existente = vistas.get(c.id)
        if (existente) {
          existente.rio = `${existente.rio} e ${nomeRio}`
          continue
        }
        vistas.set(c.id, { id: c.id, nome: c.nome, rio: nomeRio, rioId, cidade: c })
      }
    }
    return [...vistas.values()].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
  }, [])
}

/** Sem acento e sem caixa, para "itajai" achar "Itajaí". */
function normalizar(t: string): string {
  return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()
}

export default function Inicio() {
  const cidades = usarCidades()
  const aoVivo = useAoVivo()
  const { cidades: seguidas, tornarMinha } = useCidadesSeguidas()
  const [trocando, setTrocando] = useState(false)

  const porId = new Map(cidades.map((c) => [c.id, c]))
  const minha = seguidas.map((s) => porId.get(s.id)).find(Boolean)
  const outras = seguidas
    .slice(1)
    .map((s) => porId.get(s.id))
    .filter((c): c is CidadeDoInicio => Boolean(c))

  const escolher = (c: CidadeDoInicio) => {
    tornarMinha({ id: c.id, rio: rioDaUrl(c.rioId) })
    setTrocando(false)
    window.scrollTo({ top: 0 })
  }

  return (
    <>
      {minha && !trocando ? (
        <MinhaCidade item={minha} aoVivo={aoVivo} outras={outras} aoTrocar={() => setTrocando(true)} />
      ) : (
        <Seletor cidades={cidades} aoEscolher={escolher} aoCancelar={minha ? () => setTrocando(false) : undefined} />
      )}

      <h2 className={estilos.secao}>Escolha o rio</h2>
      <ul className={estilos.lista}>
        {RIOS.map((rio) => (
          <li key={rio.id}>
            <CartaoRio rioId={rio.id} para={rio.para} titulo={rio.titulo} aoVivo={aoVivo} />
          </li>
        ))}
        <li>
          <Link to="/itajai" className={estilos.cartaoRio}>
            <span className={estilos.tituloRio}>Itajaí (foz)</span>
            <span className={estilos.descricao}>
              Onde os dois rios se encontram, com influência da maré — onze réguas, uma por uma.
            </span>
          </Link>
        </li>
      </ul>

      <Instalar />

      <details className={`cartao ${estilos.comoLer}`}>
        <summary>Como ler este site</summary>
        <p>
          <strong>Cada cidade tem sua própria régua.</strong> O zero de cada uma foi cravado numa
          altura diferente, então os metros não se comparam entre cidades. O que se compara é a
          cidade com ela mesma, ao longo do tempo.
        </p>
        <p>
          <strong>A cor é a faixa da cidade, não o metro.</strong> Duas cidades na mesma cor não
          estão no mesmo nível. Cinza quer dizer sem leitura — nunca “está tudo bem”.
        </p>
        <p>
          <strong>Todo número mostra de onde veio.</strong> Onde a fonte é oficial ou acadêmica, o
          selo diz "confiança alta". Onde é imprensa ou compilação de internet, o selo avisa. Onde
          não existe dado, a tela diz que não existe — não preenchemos buraco com estimativa.
        </p>
        <p>
          <strong>Histórico não é previsão.</strong> As camadas mostram eventos passados. A
          comparação com a mesma régua não confirma alagamento atual nem prevê chegada.
        </p>
      </details>
    </>
  )
}

function MinhaCidade({
  item,
  aoVivo,
  outras,
  aoTrocar,
}: {
  item: CidadeDoInicio
  aoVivo: AoVivo
  outras: CidadeDoInicio[]
  aoTrocar: () => void
}) {
  const { cidade, rioId } = item
  const estado = estadoDaCidade(cidade, rioId, aoVivo)
  // Itajaí, na foz, recebe os DOIS rios: a água vem de Ilhota pelo Açu e de
  // Brusque pelo Mirim. As outras cidades têm um rio só.
  const rios = cidade.id === 'itajai' ? ['itajai-acu', 'itajai-mirim'] : [rioId]
  const deCima = rios.flatMap((r) => {
    const cidadesRio = cidadesDoRio(r)
    const { acima } = vizinhasNoEixo(eixoDoRio(cidadesRio, topologiaDoRio(r)), cidade.id)
    const c = cidadesRio.find((x) => x.id === acima)
    return c ? [{ rio: r, cidade: c }] : []
  })
  const para = cidade.id === 'itajai' ? '/itajai' : `/${rioDaUrl(rioId)}/${cidade.id}`
  return (
    <>
      <div className={estilos.cabeca}>
        <div>
          <p className={estilos.rotuloMinha}>Minha cidade</p>
          <h1 className={estilos.nomeMinha}>
            <Link to={para}>{cidade.nome}</Link>
          </h1>
        </div>
        <div className={estilos.botoes}>
          <button type="button" className={estilos.trocar} onClick={aoTrocar}>
            Trocar <span aria-hidden="true">▾</span>
          </button>
          <BotaoLetra />
        </div>
      </div>

      <CartaoAgora cidade={cidade} aoVivo={aoVivo} estado={estado}>
        <AcoesDaCidade cidade={cidade} rioId={rioId} aoVivo={aoVivo} estado={estado} />
      </CartaoAgora>

      {deCima.map((d) => (
        <LinhaDeCidade
          key={d.rio}
          rotulo={deCima.length > 1 ? (d.rio === 'itajai-mirim' ? 'Mirim acima' : 'Açu acima') : 'Rio acima'}
          cidade={d.cidade}
          rioId={d.rio}
          aoVivo={aoVivo}
        />
      ))}

      {outras.length > 0 ? (
        <>
          <h2 className={estilos.secao}>Outras que sigo</h2>
          {outras.map((o) => (
            <LinhaDeCidade key={o.id} cidade={o.cidade} rioId={o.rioId} aoVivo={aoVivo} />
          ))}
        </>
      ) : null}

      <p className={estilos.dica}>
        <Link to={para}>
          {cidade.id === 'itajai'
            ? 'Tudo sobre Itajaí: as onze réguas, a maré e o mapa das enchentes →'
            : `Tudo sobre ${cidade.nome}: minha rua, histórico e fontes →`}
        </Link>
      </p>
    </>
  )
}

/** A escolha da cidade: busca por nome e todos os nomes à mão. */
function Seletor({
  cidades,
  aoEscolher,
  aoCancelar,
}: {
  cidades: CidadeDoInicio[]
  aoEscolher: (c: CidadeDoInicio) => void
  aoCancelar?: () => void
}) {
  const [termo, setTermo] = useState('')
  const filtradas = cidades.filter((c) => normalizar(c.nome).includes(normalizar(termo)))
  return (
    <section className={`${estilos.seletor} surge`} aria-labelledby="titulo-seletor">
      <h1 id="titulo-seletor" className={estilos.tituloSeletor}>
        Qual é a sua cidade?
      </h1>
      <p className={estilos.instrucao}>
        O site abre nela daqui em diante, com o nível do rio na régua dela. Fica guardado só neste
        aparelho.
      </p>
      <label htmlFor="busca-cidade" className={estilos.rotuloBusca}>
        Buscar cidade
      </label>
      <input
        id="busca-cidade"
        type="search"
        className={estilos.busca}
        placeholder="Ex.: Blumenau, Brusque, Gaspar…"
        value={termo}
        onChange={(e) => setTermo(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && filtradas.length === 1) aoEscolher(filtradas[0]!)
        }}
        autoComplete="off"
      />
      <ul className={estilos.listaCidades}>
        {filtradas.map((c) => (
          <li key={c.id}>
            <button type="button" className={estilos.chipCidade} onClick={() => aoEscolher(c)}>
              <span className={estilos.nomeCidade}>{c.nome}</span>
              <span className={estilos.rioCidade}>{c.rio}</span>
            </button>
          </li>
        ))}
      </ul>
      {filtradas.length === 0 ? (
        <p className={estilos.instrucao}>Nenhuma cidade com esse nome no site ainda.</p>
      ) : null}
      {aoCancelar ? (
        <button type="button" className={estilos.cancelar} onClick={aoCancelar}>
          Manter a cidade atual
        </button>
      ) : null}
    </section>
  )
}

/**
 * O rio num cartão compacto: a descrição do curso e uma bolinha por cidade, na
 * ordem do rio, na cor da faixa de cada uma — cinza tracejado quando não há
 * leitura. É faixa, não metro: nada aqui compara cidades.
 */
function CartaoRio({ rioId, para, titulo, aoVivo }: { rioId: string; para: string; titulo: string; aoVivo: AoVivo }) {
  const cidades = cidadesDoRio(rioId)
  const cadastro = rioDoCadastro(rioId)
  const descricao = cadastro ? descricaoDoRio(cadastro, barragensDoRio(rioId)) : null
  const registros = eventosDoRio(rioId).length
  const ordem = useMemo(() => {
    const topo = topologiaDoRio(rioId)
    if (!topo) return cidades
    // Cabeceiras, tronco e afluentes; o que não estiver na árvore vem no fim.
    const ids = [
      ...topo.cabeceiras_paralelas,
      ...topo.tronco_sequencia,
      ...topo.afluentes_laterais.map((a) => a.id),
      ...cidades.map((c) => c.id),
    ]
    const porId = new Map(cidades.map((c) => [c.id, c]))
    return [...new Set(ids)].map((id) => porId.get(id)).filter((c): c is Cidade => Boolean(c))
  }, [rioId, cidades])
  return (
    <Link to={para} className={estilos.cartaoRio}>
      <span className={estilos.tituloRio}>{titulo}</span>
      {descricao ? (
        <span className={estilos.descricao}>
          {descricao.cabeceiras ? <b className={estilos.rotulo}>Tronco: </b> : null}
          {descricao.tronco}
        </span>
      ) : null}
      <span className={estilos.bolinhas} aria-hidden="true">
        {ordem.map((c) => {
          const est = estadoDaCidade(c, rioId, aoVivo)
          return (
            <span
              key={c.id}
              className={`${estilos.bolinha} ${estilos[`b_${est.faixa}`] ?? ''}`}
              title={`${c.nome}: ${nomeDaFaixa(est.faixa, c)}`}
            />
          )
        })}
      </span>
      <span className={estilos.contagem}>
        {cidades.length} cidades · {registros} picos históricos registrados
      </span>
    </Link>
  )
}

/**
 * O convite para ter o site como aplicativo (D5). Só aparece quando o navegador
 * oferece a instalação, ou no iPhone, onde ela é pelo menu Compartilhar. Sem
 * nenhum dos dois, não ocupa espaço.
 */
function Instalar() {
  const { pode, iphone, instalar } = useInstalar()
  if (!pode && !iphone) return null
  return (
    <section className={`cartao ${estilos.instalar}`}>
      <h2 className={estilos.tituloInstalar}>Ter o site como aplicativo</h2>
      <p className={estilos.instrucao}>
        Abre com um toque, direto na sua cidade, e mostra a última leitura guardada mesmo sem
        internet — sempre com a hora da medição.
      </p>
      {pode ? (
        <button type="button" className={estilos.botaoInstalar} onClick={instalar}>
          Instalar no celular
        </button>
      ) : (
        <p className={estilos.instrucao}>
          No iPhone: toque em <strong>Compartilhar</strong> (o quadrado com a seta) e depois em{' '}
          <strong>Adicionar à Tela de Início</strong>.
        </p>
      )}
    </section>
  )
}
