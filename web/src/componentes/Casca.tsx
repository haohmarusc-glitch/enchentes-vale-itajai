import { useEffect, useLayoutEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import AvisoLegal from './AvisoLegal'
import { useConexao, useNovaVersao } from '../dados/modoAplicativo'
import estilos from './Casca.module.css'

/**
 * A CASCA DA VERSÃO 2 (03/10/2026) — tudo o que envolve as telas que não são o
 * Monitor. O Monitor mantém a casca antiga (decisão D2, opção ③), porque a
 * altura do mapa dele é somada à mão com a altura dessa casca.
 *
 * Três peças, e as três existem por segurança antes de estética:
 *  - a FAIXA do topo, presa na tela, com o 199 e a frase de que o site não
 *    substitui a Defesa Civil (D1: a regra do CLAUDE.md fica — a faixa curta
 *    também diz isso, e o texto completo continua no fim de toda página);
 *  - a FOLHA da primeira visita, com o aviso completo, que só sai com
 *    "Entendi" (e volta se o aparelho não conseguir lembrar);
 *  - a NAVEGAÇÃO embaixo, ao alcance do polegar, no lugar das cinco abas que
 *    não cabiam na largura do celular.
 */

export function FaixaTopo({ aoSaberMais }: { aoSaberMais: () => void }) {
  // A altura da faixa muda com a largura (quebra em duas linhas no celular) e
  // com a letra maior: quem gruda logo abaixo dela (as abas da cidade) lê daqui.
  const ref = useRef<HTMLDivElement | null>(null)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const raiz = document.documentElement
    const medir = () => raiz.style.setProperty('--altura-faixa', `${el.offsetHeight}px`)
    medir()
    const obs = new ResizeObserver(medir)
    obs.observe(el)
    return () => {
      obs.disconnect()
      raiz.style.removeProperty('--altura-faixa')
    }
  }, [])
  return (
    <div ref={ref} className={estilos.faixa} role="note">
      <span>
        Emergência: <strong className={estilos.numero}>199</strong>
        <span aria-hidden="true"> · </span>
        <span className={estilos.naoSubstitui}>não substitui a Defesa Civil</span>
      </span>{' '}
      <button type="button" className={estilos.saibaMais} onClick={aoSaberMais}>
        saiba mais
      </button>
    </div>
  )
}

/**
 * O aviso completo numa folha que sobe de baixo. Abre sozinha na primeira
 * visita e pelo "saiba mais" da faixa. `<dialog>` nativo: foco preso dentro,
 * Esc fecha, leitor de tela anuncia — sem biblioteca.
 */
export function FolhaAviso({
  aberta,
  aoFechar,
  aoEntender,
}: {
  aberta: boolean
  aoFechar: () => void
  aoEntender: () => void
}) {
  const ref = useRef<HTMLDialogElement | null>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (aberta && !d.open) {
      // `showModal` não existe em navegador muito antigo: o texto aparece como
      // bloco aberto, que é o lado seguro.
      if (typeof d.showModal === 'function') d.showModal()
      else d.setAttribute('open', '')
    } else if (!aberta && d.open) d.close()
  }, [aberta])
  return (
    <dialog
      ref={ref}
      className={estilos.folha}
      aria-labelledby="aviso-folha-titulo"
      onClose={aoFechar}
      onClick={(e) => {
        // Toque fora da folha (no fundo escurecido) fecha, como nos apps.
        if (e.target === ref.current) aoFechar()
      }}
    >
      <div className={estilos.alca} aria-hidden="true" />
      <AvisoLegal idTitulo="aviso-folha-titulo" plano />
      {/* O foco vai para "Entendi", não para o primeiro link do texto: quem
          navega por teclado lê o aviso e confirma, sem sair da folha por engano. */}
      <button type="button" className={estilos.entendi} onClick={aoEntender} autoFocus>
        Entendi
      </button>
      <p className={estilos.notaFolha}>
        Este aviso também fica no fim de cada página e volta pelo “saiba mais”, na faixa de cima.
      </p>
    </dialog>
  )
}

const ITENS = [
  { para: '/', rotulo: 'Minha cidade', icone: 'local' as const },
  { para: '/acu', rotulo: 'Rios', icone: 'rios' as const },
  { para: '/monitor', rotulo: 'Monitor', icone: 'mapa' as const },
  { para: '/itajai', rotulo: 'Itajaí', icone: 'mare' as const },
]

/** "Rios" fica aceso no Açu, no Mirim e nas páginas de cidade deles. */
function ativo(para: string, caminho: string): boolean {
  if (para === '/') return caminho === '/'
  if (para === '/acu') return /^\/(acu|mirim)(\/|$)/.test(caminho)
  return caminho === para || caminho.startsWith(`${para}/`)
}

export function NavPrincipal() {
  const { pathname } = useLocation()
  return (
    <nav aria-label="Principal" className={estilos.nav}>
      <span className={estilos.marca}>Enchentes do Vale do Itajaí</span>
      <ul className={estilos.itens}>
        {ITENS.map((item) => {
          const aceso = ativo(item.para, pathname)
          return (
            <li key={item.para}>
              <NavLink
                to={item.para}
                className={aceso ? `${estilos.item} ${estilos.itemAtivo}` : estilos.item}
                aria-current={aceso ? 'page' : undefined}
              >
                <Icone nome={item.icone} />
                <span>{item.rotulo}</span>
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

/** Quatro ícones desenhados aqui: uma biblioteca inteira por quatro traços não vale a rede. */
function Icone({ nome }: { nome: 'local' | 'rios' | 'mapa' | 'mare' }) {
  const comum = {
    width: 24,
    height: 24,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
    className: estilos.icone,
  }
  switch (nome) {
    case 'local':
      return (
        <svg {...comum}>
          <path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0C18.5 15.4 12 21 12 21z" />
          <circle cx="12" cy="10" r="2.4" />
        </svg>
      )
    case 'rios':
      return (
        <svg {...comum}>
          <path d="M3 7c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0" />
          <path d="M3 12c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0" />
          <path d="M3 17c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0" />
        </svg>
      )
    case 'mapa':
      return (
        <svg {...comum}>
          <path d="M9 4 3 6.5v13L9 17l6 2.5 6-2.5v-13L15 6.5 9 4z" />
          <path d="M9 4v13M15 6.5v13" />
        </svg>
      )
    case 'mare':
      return (
        <svg {...comum}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 7.5V12l3 2" />
        </svg>
      )
  }
}

/**
 * Liga o escopo `data-app` no `<html>` enquanto a casca nova está na tela.
 * Tema escuro e letra maior só valem dentro dele — o Monitor fica de fora.
 */
export function useEscopoApp(ligado: boolean, letra: string) {
  // Antes da pintura: ao entrar no Monitor vindo de outra tela, nem um quadro
  // dele pode sair com a letra ou o tema da versão 2.
  useLayoutEffect(() => {
    const raiz = document.documentElement
    if (ligado) {
      raiz.dataset.app = 'v2'
      raiz.dataset.letra = letra
    } else {
      delete raiz.dataset.app
      delete raiz.dataset.letra
    }
  }, [ligado, letra])
}

/**
 * Os dois avisos do modo aplicativo (D5), logo abaixo da faixa do 199:
 *  - SEM CONEXÃO: o que está na tela é o que o aparelho guardou. Cada número
 *    continua com a hora da medição, e o site já marca o que é velho — o aviso
 *    diz por que pode estar velho.
 *  - VERSÃO NOVA: o service worker mudou; esta aba roda o código anterior até
 *    recarregar, e regra de segurança velha não fica na tela sem aviso.
 */
export function AvisosDoAplicativo() {
  const online = useConexao()
  const nova = useNovaVersao()
  if (online && !nova) return null
  return (
    <div className={estilos.avisos}>
      {!online ? (
        <p className={estilos.semConexao} role="status">
          <strong>Sem conexão.</strong> Você está vendo o que este aparelho guardou — confira a hora de
          cada medição. Ligar para o 199 funciona sem internet.
        </p>
      ) : null}
      {nova ? (
        <p className={estilos.novaVersao} role="status">
          Há uma versão nova do site.{' '}
          <button type="button" className={estilos.atualizar} onClick={() => window.location.reload()}>
            Atualizar agora
          </button>
        </p>
      ) : null}
    </div>
  )
}
