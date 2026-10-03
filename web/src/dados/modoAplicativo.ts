import { useCallback, useEffect, useState } from 'react'

/**
 * MODO APLICATIVO (decisão D5, 03/10/2026) — o lado do site.
 *
 * Registra o service worker (`public/sw.js`) e expõe três estados para a tela:
 *  - sem conexão: o site está mostrando o que o aparelho guardou;
 *  - versão nova: o service worker mudou — a aba aberta roda código velho e
 *    precisa recarregar (regra de segurança velha não pode ficar na tela);
 *  - instalar: o navegador ofereceu instalar, ou é um iPhone, onde a
 *    instalação é pelo menu Compartilhar.
 * Nada disso existe no modo de desenvolvimento nem fora de HTTPS.
 */

const EVENTO_NOVA_VERSAO = 'enchentes:nova-versao'
/** Uma aba aberta a noite toda confere se há versão nova de meia em meia hora. */
const INTERVALO_ATUALIZACAO_MS = 30 * 60_000

export function registrarModoAplicativo(): void {
  if (!import.meta.env?.PROD) return
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return
  if (!window.isSecureContext) return
  const tinhaControle = Boolean(navigator.serviceWorker.controller)
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    // Primeira instalação não é "versão nova": só a troca de um que já mandava.
    if (tinhaControle) window.dispatchEvent(new Event(EVENTO_NOVA_VERSAO))
  })
  // Depois do carregamento: o service worker não disputa a rede com a primeira tela.
  // Antes, o interruptor (`pwa.json`): desligado, nada se registra e o que
  // estiver registrado sai — senão o recarregamento que o service worker faz
  // ao se desligar o registraria de novo.
  const registrar = () => {
    fetch('./pwa.json', { cache: 'no-store' })
      .then((r) => (r.ok && !r.redirected ? r.json() : null))
      .catch(() => null)
      .then((corpo: unknown) => {
        if (corpo && typeof corpo === 'object' && (corpo as { ativo?: unknown }).ativo === false) {
          return navigator.serviceWorker
            .getRegistrations()
            .then((rs) => Promise.all(rs.map((r) => r.unregister())))
            .then(() => undefined)
        }
        return registrarDeVez()
      })
      .catch(() => {})
  }
  const registrarDeVez = () =>
    navigator.serviceWorker
      .register('./sw.js', { scope: './' })
      .then((registro) => {
        setInterval(() => {
          registro.update().catch(() => {})
        }, INTERVALO_ATUALIZACAO_MS)
      })
      .catch(() => {
        // Sem service worker o site funciona como sempre funcionou.
      })
  if (document.readyState === 'complete') registrar()
  else window.addEventListener('load', registrar, { once: true })
}

export function useConexao(): boolean {
  const [online, setOnline] = useState(() => (typeof navigator === 'undefined' ? true : navigator.onLine))
  useEffect(() => {
    const ligar = () => setOnline(true)
    const desligar = () => setOnline(false)
    window.addEventListener('online', ligar)
    window.addEventListener('offline', desligar)
    return () => {
      window.removeEventListener('online', ligar)
      window.removeEventListener('offline', desligar)
    }
  }, [])
  return online
}

export function useNovaVersao(): boolean {
  const [nova, setNova] = useState(false)
  useEffect(() => {
    const marcar = () => setNova(true)
    window.addEventListener(EVENTO_NOVA_VERSAO, marcar)
    return () => window.removeEventListener(EVENTO_NOVA_VERSAO, marcar)
  }, [])
  return nova
}

/** O evento que o Chrome dispara quando o site pode ser instalado. */
interface PedidoDeInstalacao extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

let pedidoGuardado: PedidoDeInstalacao | null = null
if (typeof window !== 'undefined') {
  // Escuta desde o carregamento: o evento chega uma vez, às vezes antes de a tela montar.
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    pedidoGuardado = e as PedidoDeInstalacao
    window.dispatchEvent(new Event('enchentes:pode-instalar'))
  })
}

export function jaInstalado(): boolean {
  if (typeof window === 'undefined') return false
  const nav = navigator as Navigator & { standalone?: boolean }
  return window.matchMedia?.('(display-mode: standalone)').matches === true || nav.standalone === true
}

export function ehIphone(): boolean {
  if (typeof navigator === 'undefined') return false
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

export function useInstalar(): { pode: boolean; iphone: boolean; instalar: () => void } {
  const [pode, setPode] = useState(() => pedidoGuardado !== null)
  useEffect(() => {
    const atualizar = () => setPode(pedidoGuardado !== null)
    const instalado = () => {
      pedidoGuardado = null
      atualizar()
    }
    window.addEventListener('enchentes:pode-instalar', atualizar)
    window.addEventListener('appinstalled', instalado)
    return () => {
      window.removeEventListener('enchentes:pode-instalar', atualizar)
      window.removeEventListener('appinstalled', instalado)
    }
  }, [])
  const instalar = useCallback(() => {
    const p = pedidoGuardado
    if (!p) return
    p.prompt()
      .then(() => p.userChoice)
      .finally(() => {
        pedidoGuardado = null
        setPode(false)
      })
  }, [])
  return { pode: pode && !jaInstalado(), iphone: ehIphone() && !jaInstalado(), instalar }
}
