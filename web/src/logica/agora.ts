/**
 * AS FRASES DO CARTÃO "AGORA" (versão 2, 03/10/2026).
 *
 * O cartão diz em português simples onde o rio está em relação às cotas da
 * própria cidade: "Está 40 cm acima da cota de Alerta (6,00 m). Faltam 1,60 m
 * para a cota de Alerta Máximo (8,00 m)." Tudo aqui é conta sobre o que já está
 * no cadastro — nada é previsão — e cada função devolve `null` quando a conta
 * não se sustenta. Sem dado, a frase não aparece; nunca se estima.
 *
 * ONDE NÃO HÁ FRASE, e por quê:
 *  - Gaspar: a legenda da estação 21 usa "maior que" e deixa 5 m exatos
 *    indefinidos; uma frase "na cota de" afirmaria o que a fonte não define.
 *  - Ascurra: a faixa vem do enquadramento C18 da DCSC-00003, não das cotas
 *    do cadastro — misturar os dois daria duas escalas na mesma tela.
 *  - Cidade de várias réguas (Itajaí): não existe "o nível da cidade".
 *  - Cidade sem cota de acionamento, leitura que não é de agora.
 * Nesses casos o cartão mostra só a faixa e o número com a idade.
 */
import type { Cidade } from '../dados/tipos'
import type { PontoSerie, Tendencia } from '../dados/serie'
import { tendencia } from '../dados/serie'
import { metros, rotuloCota } from './formato'
import {
  cotaAlcancadaEntre,
  frescor,
  frescorDaCidade,
  idadeMin,
  proximaCotaEntre,
  textoIdade,
  type Faixa,
} from './tempoReal'

/** Cidades cuja faixa NÃO sai das cotas do cadastro — sem frase de cota. */
export const SEM_FRASE_DE_COTA = new Set(['gaspar', 'ascurra', 'itajai'])

export interface SituacaoNasCotas {
  /** A cota mais alta já alcançada, e quantos centímetros acima dela. */
  acima: { nome: string; valor: number; cm: number } | null
  /** A próxima cota acima do nível, e quanto falta até ela. */
  proxima: { nome: string; valor: number; faltam: number } | null
}

/**
 * Onde o nível está entre as cotas da cidade, ou `null` quando a frase não se
 * sustenta (ver o topo do arquivo).
 */
export function situacaoNasCotas(
  cidade: Cidade,
  leitura: { nivel_m: number; medidoEm: Date | null } | null,
  agora: Date,
): SituacaoNasCotas | null {
  if (!leitura || !leitura.medidoEm || !Number.isFinite(leitura.nivel_m)) return null
  if (SEM_FRASE_DE_COTA.has(cidade.id)) return null
  // Só leitura de AGORA: "40 cm acima" sobre um número de duas horas atrás
  // descreve o rio de duas horas atrás com a voz do presente.
  if (frescorDaCidade(idadeMin(leitura.medidoEm, agora), cidade.id) !== 'agora') return null
  const cotas = Object.entries(cidade.cotas_m ?? {})
  const nivel = leitura.nivel_m
  const alcancada = cotaAlcancadaEntre(cotas, nivel)
  const proxima = proximaCotaEntre(cotas, nivel)
  if (!alcancada && !proxima) return null
  const nomes = cidade.cotas_nomes_na_fonte
  return {
    acima: alcancada
      ? {
          nome: rotuloCota(alcancada.chave, nomes),
          valor: alcancada.valor,
          cm: Math.round((nivel - alcancada.valor) * 100),
        }
      : null,
    proxima: proxima
      ? {
          nome: rotuloCota(proxima.chave, nomes),
          valor: proxima.valor,
          faltam: Math.round((proxima.valor - nivel) * 100) / 100,
        }
      : null,
  }
}

/** "37 cm" abaixo de 1 m (é como se fala de um palmo); "1,60 m" a partir dele. */
export function distancia(m: number): string {
  return m < 1 ? `${Math.round(m * 100)} cm` : metros(m)
}

/**
 * O nome da faixa no chip, com a palavra da Defesa Civil da cidade quando ela
 * existe (decisão D6, 03/10/2026): em Blumenau o topo da escada é "Alerta
 * Máximo", não "Emergência"; em Ilhota o alerta é "Prontidão". A cor continua
 * a da faixa — muda só o nome, nunca a posição na escada.
 */
export function rotuloDaFaixa(faixa: Faixa, cidade: Cidade, padrao: string): string {
  if (SEM_FRASE_DE_COTA.has(cidade.id)) return padrao
  // A faixa tem o mesmo nome da chave de cota que a acendeu.
  if (!(faixa in (cidade.cotas_m ?? {}))) return padrao
  const daFonte = cidade.cotas_nomes_na_fonte?.[faixa]
  return typeof daFonte === 'string' && daFonte.trim() ? daFonte.trim() : padrao
}

/**
 * A tendência só ao lado de um número que ela de fato descreve (D7).
 *
 * `tendencia()` olha a SÉRIE; o cartão mostra a LEITURA. Os dois chegam por
 * arquivos diferentes e podem estar desencontrados — a série de uma hora atrás
 * ao lado da leitura de agora, ou de outra publicação. A seta só aparece quando
 * o último ponto da série É a leitura mostrada (mesmo instante, mesmo nível) e
 * é de agora; senão some, e a tela fica com "medido há N min".
 */
export function tendenciaDaLeitura(
  serie: PontoSerie[],
  leitura: { nivel_m: number; medidoEm: Date | null } | null,
  agora: Date,
): Tendencia | null {
  if (!leitura?.medidoEm || serie.length < 2) return null
  const ultimo = serie[serie.length - 1]!
  if (Math.abs(ultimo.medidoEm.getTime() - leitura.medidoEm.getTime()) > 60_000) return null
  if (Math.abs(ultimo.nivel_m - leitura.nivel_m) >= 0.005) return null
  if (frescor(idadeMin(ultimo.medidoEm, agora)) !== 'agora') return null
  return tendencia(serie)
}

/** "▲ subindo 12 cm/h", "▼ baixando 4 cm/h", "estável". */
export function textoTendencia(t: Tendencia): string {
  if (t.rotulo === 'subindo') return `subindo ${Math.abs(t.cmh)} cm/h`
  if (t.rotulo === 'descendo') return `baixando ${Math.abs(t.cmh)} cm/h`
  return 'estável'
}

const FUSO = 'America/Sao_Paulo'

function horaDeBrasilia(d: Date): string {
  return d.toLocaleString('pt-BR', {
    timeZone: FUSO,
    hour: '2-digit',
    minute: '2-digit',
  })
}

function diaDeBrasilia(d: Date): string {
  return d.toLocaleString('pt-BR', { timeZone: FUSO, day: '2-digit', month: '2-digit' })
}

/**
 * O texto para mandar no WhatsApp (decisão D4: SEM o endereço do site, que está
 * atrás do Cloudflare Access e pediria login a quem recebe).
 *
 * Só monta com leitura que não é velha — um número de horas atrás repassado
 * de celular em celular vira "o nível de agora" na segunda mensagem. Leva a
 * hora da medição sempre, nunca nível de outra cidade, nunca ordem de ação:
 * só "Siga a Defesa Civil" e "ligue 199".
 */
export function textoParaCompartilhar(args: {
  cidade: Cidade
  leitura: { nivel_m: number; medidoEm: Date | null; estacao?: string }
  rotuloFaixa: string | null
  tendencia: Tendencia | null
  agora: Date
}): string | null {
  const { cidade, leitura, rotuloFaixa, agora } = args
  if (!leitura.medidoEm || !Number.isFinite(leitura.nivel_m)) return null
  const idade = idadeMin(leitura.medidoEm, agora)
  if (frescorDaCidade(idade, cidade.id) === 'velha') return null
  const linhas = [
    `${cidade.nome} — ${metros(leitura.nivel_m)}` +
      (rotuloFaixa ? ` (faixa ${rotuloFaixa}, na régua de ${cidade.nome})` : ` (na régua de ${cidade.nome})`),
  ]
  if (args.tendencia && args.tendencia.rotulo !== 'estável') {
    linhas.push(`${args.tendencia.rotulo === 'subindo' ? '▲' : '▼'} ${textoTendencia(args.tendencia)}`)
  }
  linhas.push(
    `Medido às ${horaDeBrasilia(leitura.medidoEm)} de ${diaDeBrasilia(leitura.medidoEm)} (${textoIdade(idade)})` +
      (leitura.estacao ? ` · ${leitura.estacao}` : ''),
  )
  linhas.push('', 'Não é alerta oficial. Em emergência, ligue 199. Siga a Defesa Civil.')
  return linhas.join('\n')
}

/** A cidade imediatamente acima e abaixo NO EIXO por onde a água desce. */
export function vizinhasNoEixo(
  eixo: string[],
  cidadeId: string,
): { acima: string | null; abaixo: string | null } {
  const i = eixo.indexOf(cidadeId)
  if (i < 0) return { acima: null, abaixo: null }
  return { acima: i > 0 ? eixo[i - 1]! : null, abaixo: i < eixo.length - 1 ? eixo[i + 1]! : null }
}
