import { useCallback, useEffect, useState } from 'react'
import {
  avisoLido,
  cidadesSeguidas,
  deixarDeSeguir,
  gravarLetra,
  letra,
  marcarAvisoLido,
  tornarMinha,
  type CidadeSeguida,
  type Letra,
} from '../logica/preferencias'

/**
 * As preferências do aparelho como estado do React, iguais em todos os
 * componentes que as usam (a estrela da cidade, o Início, a casca). Uma
 * mudança em qualquer um avisa os outros pelo evento abaixo — sem isso, marcar
 * ★ na página da cidade não mudaria o Início até recarregar.
 */
const EVENTO = 'enchentes:preferencias'

function avisar() {
  window.dispatchEvent(new Event(EVENTO))
}

/** Para quem muda a preferência fora destes ganchos (o chat): as telas abertas se atualizam. */
export const avisarPreferencias = avisar

function useAtualizar<T>(ler: () => T): T {
  const [valor, setValor] = useState(ler)
  useEffect(() => {
    const atualizar = () => setValor(ler())
    window.addEventListener(EVENTO, atualizar)
    window.addEventListener('storage', atualizar)
    return () => {
      window.removeEventListener(EVENTO, atualizar)
      window.removeEventListener('storage', atualizar)
    }
    // `ler` é uma função de módulo, estável: basta assinar uma vez.
  }, [])
  return valor
}

export function useCidadesSeguidas() {
  const cidades = useAtualizar(cidadesSeguidas)
  const minha = useCallback((c: CidadeSeguida) => {
    tornarMinha(c)
    avisar()
  }, [])
  const tirar = useCallback((id: string) => {
    deixarDeSeguir(id)
    avisar()
  }, [])
  return { cidades, tornarMinha: minha, deixarDeSeguir: tirar }
}

export function useLetra(): [Letra, (l: Letra) => void] {
  const atual = useAtualizar(letra)
  const trocar = useCallback((l: Letra) => {
    gravarLetra(l)
    // Sem armazenamento a troca ainda vale nesta visita.
    document.documentElement.dataset.letra = l
    avisar()
  }, [])
  return [atual, trocar]
}

export function useAvisoLido(): [boolean, () => void] {
  const [lido, setLido] = useState(avisoLido)
  const marcar = useCallback(() => {
    marcarAvisoLido()
    setLido(true)
  }, [])
  return [lido, marcar]
}
