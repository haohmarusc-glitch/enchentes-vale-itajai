/**
 * A caixa de chat no topo das páginas e no bloco do topo do Monitor (docs/CHAT-GLOBAL-COMANDOS.md).
 *
 * O motor do chat é pesado e carrega à parte: até ele chegar, aparece a mesma barra, parada, para a página
 * não pular. Com um chat de página na tela (/perguntas, aba Histórico), a barra some: a caixa aparece uma vez.
 * Tem o próprio limite de erro: um defeito no chat não derruba a página, nem o mapa do Monitor.
 */
import { lazy, Suspense } from 'react'
import { useLocation } from 'react-router-dom'
import { useConversa } from '../chat-local/conversa'
import estilos from '../chat-local/ChatLocal.module.css'
import LimiteDeErro from './LimiteDeErro'

const ChatLocal = lazy(() => import('../chat-local/ChatLocal'))

function BarraParada({ monitor }: { monitor: boolean }) {
  return (
    <section className={`${estilos.global} ${monitor ? estilos['global-monitor'] : ''}`} aria-label="Chat: perguntas e pedidos">
      <div className={estilos['global-barra']}>
        <input disabled placeholder="Carregando o chat…" aria-label="Pergunte ou peça" />
        <button type="button" disabled>
          Enviar
        </button>
      </div>
    </section>
  )
}

export default function ChatNoTopo({ variante }: { variante: 'barra' | 'monitor' }) {
  const { chatsDePagina } = useConversa()
  const { pathname } = useLocation()
  if (variante === 'barra' && chatsDePagina > 0) return null
  const rio = pathname.startsWith('/mirim') ? 'itajai-mirim' : 'itajai-acu'
  return (
    <LimiteDeErro oQue="o chat">
      <Suspense fallback={<BarraParada monitor={variante === 'monitor'} />}>
        <ChatLocal rio={rio} variante={variante} />
      </Suspense>
    </LimiteDeErro>
  )
}
