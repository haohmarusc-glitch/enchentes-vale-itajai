import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import indice from '@dados/manchas/index.json'
import { coresPorRotulo, legenda, ordenar, rotuloEvento } from '../logica/manchas'
import type { Mancha } from '../logica/manchas'
import { dentroDaColecao } from '../logica/pontoNaMancha'
import type { Coordenada } from '../logica/pontoNaMancha'
import { metros } from '../logica/formato'
import estilos from './MapaManchas.module.css'

/**
 * Os GeoJSON entram como URL, não como import de dado.
 *
 * São 1,6 MB somados. Embutidos no pacote, cada visita durante uma chuva
 * baixaria todos os nove eventos para ver um. Como URL, o Vite os emite como
 * arquivos à parte e a tela busca só o que a pessoa escolheu.
 */
const ARQUIVOS = import.meta.glob('@dados/manchas/itajai/*.geojson', {
  query: '?url',
  import: 'default',
  eager: true,
}) as Record<string, string>

function urlDoArquivo(arquivo: string): string | undefined {
  const nome = arquivo.split('/').pop()
  const chave = Object.keys(ARQUIVOS).find((k) => k.endsWith(`/${nome}`))
  return chave ? ARQUIVOS[chave] : undefined
}

/** Itajaí, na foz. Enquadramento inicial; os dados reposicionam o mapa. */
const CENTRO: [number, number] = [-26.9, -48.67]

/**
 * Os três fundos do mapa. A ATRIBUIÇÃO é condição de licença das três fontes,
 * não cortesia: tem de estar visível enquanto a camada estiver ativa, e trocar
 * junto com ela — por isso vive aqui, colada na URL, e não num texto solto.
 *
 * Nada de Google Maps/Earth: a licença não permite embutir tiles em site
 * próprio (seria a Google Maps Platform, paga e com chave).
 */
const FUNDOS = {
  // Trocado do CARTO para o Esri em 04/09/2026: o `basemaps.cartocdn.com`
  // passou a servir os tiles com "API KEY REQUIRED" repetido por cima de tudo.
  // O Esri não pede chave e já é o provedor do Satélite aqui. Preço: teto de
  // zoom 16 (o CARTO ia a 19); quem precisa de mais perto usa o "Mapa".
  // Os "canvas" do Esri separam desenho e rótulo, daí o `rotulos`.
  escuro: {
    nome: 'Escuro',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    rotulos:
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
    atribuicao: 'Esri, HERE, Garmin, © colaboradores do OpenStreetMap',
    maxZoom: 16,
  },
  satelite: {
    nome: 'Satélite',
    // ⚠️ Esri inverte a ordem: {z}/{y}/{x}, não {z}/{x}/{y} como as outras.
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    atribuicao: 'Imagem: Esri, Maxar, Earthstar Geographics',
    maxZoom: 18,
  },
  mapa: {
    nome: 'Mapa',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    atribuicao: '© colaboradores do OpenStreetMap',
    maxZoom: 19,
  },
} as const

type ChaveFundo = keyof typeof FUNDOS

/**
 * Põe a camada de RÓTULOS por cima da base, quando o fundo tem uma.
 *
 * Vai no mesmo pane, adicionada depois, então fica acima da base e abaixo das
 * manchas. Fundo escuro sem nome de bairro é bonito e mudo — e aqui a pessoa
 * está procurando a rua dela.
 */
function porRotulos(
  escolha: (typeof FUNDOS)[ChaveFundo],
  mapa: L.Map,
): L.TileLayer | null {
  const url = 'rotulos' in escolha ? escolha.rotulos : null
  if (!url) return null
  return L.tileLayer(url, { pane: 'fundo', maxZoom: escolha.maxZoom }).addTo(mapa)
}

/**
 * O fundo padrão é escuro por FUNÇÃO, não por estética: qualquer fundo com
 * textura concorre com as manchas e com a legenda de lâmina d'água. Satélite e
 * mapa entram como escolha de quem está olhando — o satélite ajuda a reconhecer
 * a barra, os molhes e o bairro; o mapa ajuda a achar a rua.
 */
const FUNDO_PADRAO: ChaveFundo = 'escuro'
const CHAVE_LOCAL = 'enchentes:fundo-mapa'

/**
 * O traço da mancha, ajustado ao fundo.
 *
 * Sobre o satélite, o contorno fino de 0,6 px e o azul translúcido somem contra
 * telhado e mata — e a mancha é justamente o dado da tela. Sobre imagem, o
 * contorno engrossa e escurece, e o preenchimento ganha opacidade. É a mesma
 * ideia do contorno escuro sob as linhas de faixa no monitor: o fundo pode
 * mudar, a leitura do risco não pode piorar.
 */
function estiloDaMancha(cores: Map<string, string>, sobreSatelite: boolean) {
  return (f?: GeoJSON.Feature) => {
    const situa = (f?.properties as { situa?: string } | undefined)?.situa
    return {
      color: sobreSatelite ? '#04141f' : '#1f5f96',
      weight: sobreSatelite ? 1.4 : 0.6,
      fillColor: (situa ? cores.get(situa) : undefined) ?? '#6aa8db',
      fillOpacity: sobreSatelite ? 0.72 : 0.55,
    }
  }
}

function fundoSalvo(): ChaveFundo {
  // localStorage falha em navegador com dados de site bloqueados; a tela tem de
  // abrir mesmo assim, no padrão.
  try {
    const v = localStorage.getItem(CHAVE_LOCAL)
    if (v && v in FUNDOS) return v as ChaveFundo
  } catch {
    /* sem preferência salva: segue no padrão */
  }
  return FUNDO_PADRAO
}

export default function MapaManchas() {
  const manchas = useMemo(() => ordenar((indice as { manchas: Mancha[] }).manchas), [])
  const [escolhida, setEscolhida] = useState<Mancha | undefined>(manchas[0])
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)
  const divRef = useRef<HTMLDivElement>(null)
  const mapaRef = useRef<L.Map | null>(null)
  const [fundo, setFundo] = useState<ChaveFundo>(fundoSalvo)
  const fundoLayerRef = useRef<L.TileLayer | null>(null)
  /** Camada de nomes de rua/bairro, quando o fundo separa desenho e rótulo. */
  const rotulosLayerRef = useRef<L.TileLayer | null>(null)
  // O efeito que cria o mapa roda uma vez só (deps []), então não pode fechar
  // sobre o `fundo` do primeiro render — lê o ref, sempre atual.
  const fundoRef = useRef<ChaveFundo>(fundo)
  fundoRef.current = fundo
  const camadaRef = useRef<L.GeoJSON | null>(null)

  // "Este ponto ficou dentro de quais manchas?"
  const [ponto, setPonto] = useState<Coordenada | null>(null)
  const [atingido, setAtingido] = useState<Mancha[] | null>(null)
  const [consultando, setConsultando] = useState(false)
  const [erroConsulta, setErroConsulta] = useState<string | null>(null)
  const marcaRef = useRef<L.CircleMarker | null>(null)
  /** Os GeoJSON já baixados, para o segundo clique não repetir 1,6 MB. */
  const cacheRef = useRef(new Map<string, unknown>())

  useEffect(() => {
    if (!divRef.current || mapaRef.current) return
    const mapa = L.map(divRef.current, { scrollWheelZoom: false }).setView(CENTRO, 12)
    // Pane próprio para o fundo, abaixo do overlay (400). Sem ele, trocar de
    // camada exigiria `bringToBack()`, que joga a camada NOVA para trás das
    // tiles antigas que o Leaflet ainda mantém no DOM: o fundo novo carrega,
    // fica escondido, e a tela não muda. Com pane fixo, trocar é só remover uma
    // e adicionar a outra.
    mapa.createPane('fundo')
    const pane = mapa.getPane('fundo')
    if (pane) pane.style.zIndex = '180'
    const inicial = FUNDOS[fundoRef.current]
    fundoLayerRef.current = L.tileLayer(inicial.url, {
      pane: 'fundo',
      maxZoom: inicial.maxZoom,
      attribution: inicial.atribuicao,
    }).addTo(mapa)
    rotulosLayerRef.current = porRotulos(inicial, mapa)
    mapa.on('click', (e: L.LeafletMouseEvent) => {
      // GeoJSON guarda [longitude, latitude]; o Leaflet entrega o contrário.
      // Trocar os dois aqui e não em `dentroDaColecao` mantém a lógica pura
      // falando a língua do arquivo, que é onde o erro seria invisível.
      setPonto([e.latlng.lng, e.latlng.lat])
    })
    mapaRef.current = mapa
    return () => {
      mapa.remove()
      mapaRef.current = null
    }
  }, [])

  // Troca o fundo: remove a camada atual e põe a nova no mesmo pane. A
  // atribuição vai junto na própria camada, então o Leaflet a troca sozinho —
  // que é o que a licença exige.
  useEffect(() => {
    const mapa = mapaRef.current
    if (!mapa) return
    const escolha = FUNDOS[fundo]
    fundoLayerRef.current?.remove()
    rotulosLayerRef.current?.remove()
    fundoLayerRef.current = L.tileLayer(escolha.url, {
      pane: 'fundo',
      maxZoom: escolha.maxZoom,
      attribution: escolha.atribuicao,
    }).addTo(mapa)
    rotulosLayerRef.current = porRotulos(escolha, mapa)
    try {
      localStorage.setItem(CHAVE_LOCAL, fundo)
    } catch {
      /* sem espaço ou bloqueado: a escolha vale só nesta visita */
    }
    // Repinta a mancha para o novo fundo SEM rebaixar o GeoJSON: são até 651 kB
    // por evento, e trocar de fundo não pode custar outro download a quem está
    // numa rede ruim no meio da chuva.
    if (camadaRef.current && escolhida) {
      camadaRef.current.setStyle(
        estiloDaMancha(coresPorRotulo(escolhida.classes_lamina), fundo === 'satelite'),
      )
    }
  }, [fundo, escolhida])

  // A consulta do ponto: baixa os eventos que ainda faltam e responde em quais
  // ele caiu dentro. É um clique explícito da pessoa, por isso pode buscar
  // todos os arquivos — o seletor lá em cima continua baixando um por vez.
  useEffect(() => {
    const mapa = mapaRef.current
    if (!mapa || !ponto) return

    marcaRef.current?.remove()
    marcaRef.current = L.circleMarker([ponto[1], ponto[0]], {
      radius: 7,
      color: '#111827',
      weight: 2,
      fillColor: '#fbbf24',
      fillOpacity: 1,
    }).addTo(mapa)

    let vivo = true
    setConsultando(true)
    setErroConsulta(null)
    setAtingido(null)
    Promise.all(
      manchas.map(async (m) => {
        const cache = cacheRef.current
        if (!cache.has(m.arquivo)) {
          const url = urlDoArquivo(m.arquivo)
          if (!url) throw new Error(`arquivo de ${rotuloEvento(m.evento)} não está no pacote`)
          const r = await fetch(url)
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          cache.set(m.arquivo, await r.json())
        }
        return dentroDaColecao(ponto, cache.get(m.arquivo)) ? m : null
      }),
    )
      .then((achados) => {
        if (!vivo) return
        setAtingido(achados.filter((m): m is Mancha => m !== null))
      })
      .catch((e: Error) => vivo && setErroConsulta(e.message))
      .finally(() => vivo && setConsultando(false))

    return () => {
      vivo = false
    }
  }, [ponto, manchas])

  useEffect(() => {
    const mapa = mapaRef.current
    if (!mapa || !escolhida) return
    const url = urlDoArquivo(escolhida.arquivo)
    if (!url) {
      setErro('arquivo da mancha não encontrado no pacote')
      return
    }

    // Tirar a camada ANTES de buscar a nova, não depois que ela chega.
    // Do jeito anterior, entre escolher out/2015 e o arquivo chegar, o mapa
    // continuava com a água de set/2011 enquanto a legenda logo abaixo já era
    // a de 2015 — mancha de um ano com a legenda de outro. Mapa vazio por um
    // instante é melhor do que mapa errado com cara de certo.
    camadaRef.current?.remove()
    camadaRef.current = null

    let vivo = true
    setCarregando(true)
    setErro(null)
    fetch(url)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((geo) => {
        if (!vivo) return
        const cores = coresPorRotulo(escolhida.classes_lamina)
        const camada = L.geoJSON(geo as GeoJSON.GeoJsonObject, {
          style: estiloDaMancha(cores, fundoRef.current === 'satelite'),
          onEachFeature: (f, camadaDaFeicao) => {
            const situa = (f.properties as { situa?: string } | undefined)?.situa
            camadaDaFeicao.bindPopup(
              situa
                ? `Lâmina d'água: ${situa} m<br><small>${rotuloEvento(escolhida.evento)}</small>`
                : `Área atingida em ${rotuloEvento(escolhida.evento)}`,
            )
          },
        }).addTo(mapa)
        camadaRef.current = camada
        const limites = camada.getBounds()
        if (limites.isValid()) mapa.fitBounds(limites, { padding: [16, 16] })
      })
      .catch((e: Error) => vivo && setErro(e.message))
      .finally(() => vivo && setCarregando(false))

    return () => {
      vivo = false
    }
  }, [escolhida])

  // A mesma conta que pinta o mapa, para a legenda não divergir dele.
  const coresDaEscolhida = useMemo(
    () => coresPorRotulo(escolhida?.classes_lamina ?? []),
    [escolhida],
  )

  if (manchas.length === 0) return null

  return (
    <section className="cartao">
      <h2>Até onde a água chegou</h2>

      <p className={estilos.intro}>
        Áreas atingidas em nove enchentes de Itajaí, entre 1983 e 2015, publicadas pela{' '}
        <strong>própria prefeitura</strong> na organização GeoItajaí, sob licença MIT.
      </p>

      <label className={estilos.rotulo} htmlFor="mancha">
        Enchente
      </label>
      <select
        id="mancha"
        className={estilos.seletor}
        value={escolhida?.arquivo ?? ''}
        onChange={(e) => setEscolhida(manchas.find((m) => m.arquivo === e.target.value))}
      >
        {manchas.map((m) => (
          <option key={m.arquivo} value={m.arquivo}>
            {rotuloEvento(m.evento)} — {m.tem_lamina ? "profundidade da água" : 'área atingida'} (
            {m.feicoes} {m.feicoes === 1 ? 'polígono' : 'polígonos'})
          </option>
        ))}
      </select>

      <p className={estilos.rotulo} id="fundo-mapa">
        Fundo do mapa
      </p>
      <div className={estilos.fundos} role="group" aria-labelledby="fundo-mapa">
        {(Object.keys(FUNDOS) as ChaveFundo[]).map((k) => (
          <button
            key={k}
            type="button"
            className={estilos.botaoFundo}
            aria-pressed={fundo === k}
            onClick={() => setFundo(k)}
          >
            {FUNDOS[k].nome}
          </button>
        ))}
      </div>

      <div className={estilos.mapa} ref={divRef} role="img"
           aria-label={`Mapa das áreas atingidas em Itajaí na enchente de ${escolhida ? rotuloEvento(escolhida.evento) : ''}`} />

      <div className={estilos.consulta}>
        <p className={estilos.rotulo}>Toque num ponto do mapa</p>
        {ponto === null ? (
          <p className={estilos.estado}>
            O mapa responde <strong>em quais destas enchentes aquele ponto ficou dentro da
            área atingida</strong>. Não diz com quantos metros de rio — os arquivos não trazem
            cota.
          </p>
        ) : consultando ? (
          <p className={estilos.estado}>Conferindo o ponto nas nove enchentes…</p>
        ) : erroConsulta ? (
          <p className={estilos.erro}>
            Não deu para conferir este ponto ({erroConsulta}). O resto da página segue funcionando.
          </p>
        ) : atingido === null ? null : atingido.length === 0 ? (
          <p className={estilos.estado}>
            Este ponto <strong>não caiu dentro de nenhuma</strong> das manchas levantadas.{' '}
            <strong>Isso não quer dizer que ali não alaga</strong> — o levantamento cobre o que foi
            mapeado, e a cidade mudou desde 1983.
          </p>
        ) : (
          <>
            <p className={estilos.estado}>
              Este ponto ficou dentro da área atingida em{' '}
              <strong>
                {atingido.length} {atingido.length === 1 ? 'enchente' : 'enchentes'}
              </strong>
              :
            </p>
            <ul className={estilos.eventos}>
              {atingido.map((m) => (
                <li key={m.arquivo}>{rotuloEvento(m.evento)}</li>
              ))}
            </ul>
          </>
        )}
      </div>

      {carregando ? <p className={estilos.estado}>Carregando a mancha…</p> : null}
      {erro ? (
        <p className={estilos.erro}>
          Não deu para carregar esta mancha ({erro}). O resto da página segue funcionando.
        </p>
      ) : null}

      {escolhida && escolhida.classes_lamina.length > 0 ? (
        <>
          <p className={estilos.rotulo}>Profundidade da água</p>
          <ul className={estilos.legenda}>
            {legenda(escolhida).map((c) => (
              <li key={c.rotulo}>
                <span
                  className={estilos.amostra}
                  style={{ background: coresDaEscolhida.get(c.rotulo) ?? '#6aa8db' }}
                />
                {c.rotulo} m
              </li>
            ))}
          </ul>
          {escolhida.classes_sobrepostas ? (
            <p className={estilos.ressalva}>
              As faixas de profundidade desta enchente <strong>se sobrepõem na fonte</strong> (por
              exemplo “0,41 a 0,60” e “0,51 a 1”). Está assim no arquivo original e não foi
              corrigido aqui.
            </p>
          ) : null}
        </>
      ) : null}

      {escolhida ? (
        <p className={estilos.nivel}>
          {escolhida.pico_registrado?.pico_m != null ? (
            <>
              Nesta enchente o rio chegou a{' '}
              <strong>{metros(escolhida.pico_registrado.pico_m)}</strong> em Itajaí.
            </>
          ) : (
            <>
              <strong>Não sabemos com quantos metros de rio isto aconteceu.</strong> Os arquivos não
              trazem cota, e o pico de Itajaí nesta data ainda não está levantado — por isso o mapa
              não pode ser comparado com o nível de hoje.
            </>
          )}
        </p>
      ) : null}

      <ul className={estilos.avisos}>
        <li>
          <strong>Isto não é previsão.</strong> É onde a água chegou naquele evento, na cidade que
          existia naquele ano. Aterro, drenagem e construção mudaram o terreno desde então.
        </li>
        <li>
          <strong>Não estar na mancha não quer dizer que não alaga.</strong> O levantamento cobre o
          que foi mapeado, não tudo o que a água atingiu.
        </li>
        <li>
          Em emergência, ligue <strong>199</strong>. Quem sabe o que está acontecendo na sua rua é a
          Defesa Civil de Itajaí.
        </li>
      </ul>

      {/* O crédito do fundo acompanha a camada ativa: com o satélite ligado,
          "© colaboradores do OpenStreetMap" fixo aqui seria crédito à fonte
          errada — e a atribuição é condição de licença das três. */}
      <p className={estilos.credito}>
        Dados: GeoItajaí / Prefeitura de Itajaí (licença MIT) · Mapa base:{' '}
        {FUNDOS[fundo].atribuicao}
      </p>
    </section>
  )
}
