import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import indice from '@dados/manchas/index.json'
import { coresPorRotulo, legenda, ordenar, rotuloEvento } from '../logica/manchas'
import type { Mancha } from '../logica/manchas'
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

export default function MapaManchas() {
  const manchas = useMemo(() => ordenar((indice as { manchas: Mancha[] }).manchas), [])
  const [escolhida, setEscolhida] = useState<Mancha | undefined>(manchas[0])
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)
  const divRef = useRef<HTMLDivElement>(null)
  const mapaRef = useRef<L.Map | null>(null)
  const camadaRef = useRef<L.GeoJSON | null>(null)

  useEffect(() => {
    if (!divRef.current || mapaRef.current) return
    const mapa = L.map(divRef.current, { scrollWheelZoom: false }).setView(CENTRO, 12)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© colaboradores do OpenStreetMap',
    }).addTo(mapa)
    mapaRef.current = mapa
    return () => {
      mapa.remove()
      mapaRef.current = null
    }
  }, [])

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
          style: (f) => {
            const situa = (f?.properties as { situa?: string } | undefined)?.situa
            return {
              color: '#1f5f96',
              weight: 0.6,
              fillColor: (situa ? cores.get(situa) : undefined) ?? '#6aa8db',
              fillOpacity: 0.55,
            }
          },
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

      <div className={estilos.mapa} ref={divRef} role="img"
           aria-label={`Mapa das áreas atingidas em Itajaí na enchente de ${escolhida ? rotuloEvento(escolhida.evento) : ''}`} />

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

      <p className={estilos.credito}>
        Dados: GeoItajaí / Prefeitura de Itajaí (licença MIT) · Mapa base: © colaboradores do
        OpenStreetMap
      </p>
    </section>
  )
}
