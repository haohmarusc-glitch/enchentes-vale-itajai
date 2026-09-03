import { useState } from 'react'
import { abrigosItajai, avisoAbrigos } from '../dados/carregar'
import { maisProximos } from '../logica/abrigos'
import type { AbrigoProximo } from '../logica/abrigos'
import estilos from './AbrigoMaisProximo.module.css'

type Estado =
  | { fase: 'inicio' }
  | { fase: 'buscando' }
  | { fase: 'ok'; perto: AbrigoProximo[] }
  | { fase: 'erro'; motivo: string }

/** Distância curta em texto: metros abaixo de 1 km, senão km com uma casa. */
function distancia(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`
}

/**
 * "Abrigo cadastrado mais próximo" para Itajaí, por distância real.
 *
 * A ressalva vem PRIMEIRO e sempre: a lista é cadastro, não estado atual. O site
 * não diz que o abrigo está aberto nem manda ninguém ir por conta própria —
 * quem ativa abrigo e manda evacuar é a Defesa Civil (199). A distância é em
 * linha reta, não a pé: serve para saber qual é o mais perto, não como rota.
 */
export default function AbrigoMaisProximo() {
  const [estado, setEstado] = useState<Estado>({ fase: 'inicio' })

  function localizar() {
    if (!('geolocation' in navigator)) {
      setEstado({ fase: 'erro', motivo: 'Este aparelho não permite localização pelo navegador.' })
      return
    }
    setEstado({ fase: 'buscando' })
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const perto = maisProximos(abrigosItajai, pos.coords.latitude, pos.coords.longitude, 3)
        setEstado({ fase: 'ok', perto })
      },
      (err) => {
        const motivo =
          err.code === err.PERMISSION_DENIED
            ? 'Você não permitiu o acesso à localização. Pode ligar nas configurações do navegador e tentar de novo.'
            : 'Não foi possível obter sua localização agora.'
        setEstado({ fase: 'erro', motivo })
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    )
  }

  return (
    <section className="cartao">
      <h2>Abrigo cadastrado mais próximo</h2>

      <p className={estilos.aviso}>
        <strong>Atenção:</strong> esta é a lista de abrigos <strong>cadastrados</strong> pela Defesa
        Civil de Itajaí — <strong>não</strong> quer dizer que estão abertos agora. Quem ativa um
        abrigo e manda evacuar é a <strong>Defesa Civil (199)</strong>. Confirme antes de sair, e não
        vá por conta própria. A distância é em <strong>linha reta</strong>, não a pé.
      </p>

      {estado.fase === 'inicio' ? (
        <button type="button" className={estilos.botao} onClick={localizar}>
          Ver os mais próximos de mim
        </button>
      ) : null}

      {estado.fase === 'buscando' ? <p className={estilos.status}>Localizando…</p> : null}

      {estado.fase === 'erro' ? (
        <>
          <p className={estilos.status}>{estado.motivo}</p>
          <button type="button" className={estilos.botao} onClick={localizar}>
            Tentar de novo
          </button>
        </>
      ) : null}

      {estado.fase === 'ok' ? (
        estado.perto.length === 0 ? (
          <p className={estilos.status}>Nenhum abrigo cadastrado com nome foi encontrado.</p>
        ) : (
          <ol className={estilos.lista}>
            {estado.perto.map(({ abrigo, distanciaKm }, i) => (
              // Índice no fim garante chave única mesmo se dois abrigos da fonte
              // caírem na mesma coordenada (a lista é curta e recomputada inteira).
              <li key={`${abrigo.lat},${abrigo.lon}#${i}`} className={estilos.item}>
                <span className={estilos.nome}>{abrigo.nome}</span>
                <span className={estilos.dist}>a {distancia(distanciaKm)} em linha reta</span>
                {abrigo.endereco ? <span className={estilos.endereco}>{abrigo.endereco}</span> : null}
                <span className={estilos.meta}>
                  {abrigo.capacidade != null ? `Capacidade cadastrada: ${abrigo.capacidade}` : ''}
                  {abrigo.capacidade != null && abrigo.zona_defesa_civil ? ' · ' : ''}
                  {abrigo.zona_defesa_civil ? `Zona ${abrigo.zona_defesa_civil}` : ''}
                </span>
              </li>
            ))}
          </ol>
        )
      ) : null}

      <p className={estilos.fonte}>
        {avisoAbrigos ? avisoAbrigos : ''}
      </p>
      <p className={estilos.fonte}>
        Fonte: Defesa Civil de Itajaí (ArcGIS da Prefeitura), {abrigosItajai.length} abrigos
        cadastrados. Sua localização fica no seu aparelho — o site não a envia a lugar nenhum.
      </p>
    </section>
  )
}
