/**
 * O painel da cidade no celular, em dois tamanhos (redesenho do Monitor, etapa 2 —
 * docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md, correção 2 do Jefferson): ao tocar no pino abre a versão
 * COMPACTA — nível, horário e tendência —; "Mais detalhes" abre a EXPANDIDA, com chuva, cota e tudo o que
 * o painel já mostrava.
 *
 * Aqui ficam os textos que a versão compacta escreve, puros e testáveis. Regras:
 *  - a hora da medição aparece sempre, por extenso; leitura velha é dita "antiga", nunca passa por atual;
 *  - tendência só quando `tendenciaDaLeitura` a devolve (D7: o último ponto da série É a leitura mostrada
 *    e é de agora); senão a tela diz que não há tendência para esta leitura — não inventa seta;
 *  - a cota mostrada é a da faixa de agora, na régua da própria cidade; sem faixa, a primeira cota da
 *    régua, dita como "primeira cota" e nunca como "faixa"; sem cota, dito como sem cota. Nada de "sem
 *    faixa oficial vinculada" numa cidade em atenção (era o erro da maquete).
 */
import type { Cidade } from '../dados/tipos'
import type { Tendencia } from '../dados/serie'
import { textoTendencia } from './agora'
import { cotasOperacionais } from './cotasOperacionais'
import { dataHora, metros, rotuloCota } from './formato'
import { frescorDaCidade, idadeMin, textoIdade, type Faixa } from './tempoReal'
import { textoSemCota, type OrigemDaCor } from './textosDoPainel'

export type EstadoDaLeitura =
  | { tipo: 'agora' | 'atrasada' | 'velha'; texto: string }
  | { tipo: 'sem'; texto: string }

/**
 * "Leitura: há 17 min · 07/10, 03:58" — ou "Leitura antiga" quando o frescor é `velha`. `rotulo` troca a
 * palavra inicial ("Leitura estadual" quando o número é o da rede estadual, com zero próprio).
 */
export function estadoDaLeitura(medidoEm: Date | null, agora: Date, cidadeId: string, rotulo = 'Leitura'): EstadoDaLeitura {
  if (!medidoEm) return { tipo: 'sem', texto: 'Sem leitura fresca nesta régua' }
  const idade = idadeMin(medidoEm, agora)
  const frescor = frescorDaCidade(idade, cidadeId)
  const quando = `${textoIdade(idade)} · ${dataHora(medidoEm)}`
  if (frescor === 'velha') return { tipo: 'velha', texto: `${rotulo} antiga: ${quando} — não é a de agora` }
  return { tipo: frescor, texto: `${rotulo}: ${quando}` }
}

/** Cidade de várias réguas (Itajaí): não há UMA hora de leitura; cada régua tem a sua. */
export const LEITURA_VARIAS_REGUAS: EstadoDaLeitura = {
  tipo: 'sem',
  texto: 'Várias réguas: cada uma com a própria leitura e hora, em Mais detalhes',
}

/** A tendência da linha compacta: seta + texto, ou a ausência dita. */
export function textoTendenciaCompacta(t: Tendencia | null): { seta: string; texto: string; nota: string } {
  if (!t) return { seta: '—', texto: 'sem tendência', nota: 'só com leitura de agora e série desta régua' }
  const seta = t.rotulo === 'subindo' ? '▲' : t.rotulo === 'descendo' ? '▼' : '→'
  return { seta, texto: textoTendencia(t), nota: 'última hora, nesta régua' }
}

export interface CotaCompacta {
  titulo: string
  /** O valor em metros, ou null quando não há cota a mostrar. */
  valor: string | null
  nota: string
}

/**
 * A cota que acompanha a faixa de agora. `faixa` é a do pino (já válida: cota do cadastro + leitura fresca);
 * `origem` diz de onde veio a cor (municipal, estadual ou várias réguas).
 */
export function cotaDaFaixa(cidade: Cidade, faixa: Faixa, origem: OrigemDaCor): CotaCompacta {
  if (origem === 'varias') {
    return { titulo: 'Cotas', valor: null, nota: 'cada régua tem as próprias cotas; estão em Mais detalhes' }
  }
  if (origem === 'estadual') {
    return { titulo: 'Cota', valor: null, nota: textoSemCota('estadual') }
  }
  const cotas = cotasOperacionais(cidade.cotas_m ?? {})
  if (cotas.length === 0) {
    return { titulo: 'Cota', valor: null, nota: 'sem cota cadastrada para esta régua' }
  }
  const nomes = cidade.cotas_nomes_na_fonte
  const daFaixa = faixa !== 'sem-dado' && faixa !== 'normal' && faixa !== 'varias' ? cotas.find(([k]) => k === faixa) : undefined
  if (daFaixa) {
    return { titulo: `Cota de ${rotuloCota(daFaixa[0], nomes)}`, valor: metros(daFaixa[1]), nota: 'faixa de agora, na régua desta cidade' }
  }
  const [chave, valor] = cotas[0]!
  return {
    titulo: `Primeira cota (${rotuloCota(chave, nomes)})`,
    valor: metros(valor),
    nota: faixa === 'sem-dado' ? 'sem faixa para esta leitura' : 'nível abaixo desta cota',
  }
}
