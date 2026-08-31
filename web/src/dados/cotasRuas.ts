/**
 * As cotas de rua, em módulo separado de propósito.
 *
 * São 611 registros e crescem: Rio do Sul sozinha publica 554 logradouros. No
 * pacote inicial, isso é um quarto de megabyte que todo mundo baixa e
 * interpreta — inclusive quem abriu o site no celular, no meio da chuva, só
 * para ver o nível do rio. Como só a busca "minha rua" usa esta tabela, e ela
 * vive num componente carregado à parte, o JSON viaja no mesmo pedaço: quem
 * não abre a busca não paga por ela.
 *
 * O filtro aqui é severo. Um registro malformado não destoaria de nada na
 * tela — só mandaria a pessoa para o lado errado.
 */
import cotasRuasJson from '@dados/cotas-ruas.json'
import type { Confianca, CotaRua, CotasRuas } from './tipos'

const CONFIANCAS: Confianca[] = ['alta', 'media', 'baixa']

function ehConfianca(v: unknown): v is Confianca {
  return typeof v === 'string' && (CONFIANCAS as string[]).includes(v)
}

function descarta(motivo: string, registro: unknown): void {
  console.warn(`[dados] registro descartado — ${motivo}`, registro)
}

const cotasBrutas = cotasRuasJson as unknown as CotasRuas

function cotaRuaValida(c: CotaRua): boolean {
  if (!c.cidade || !c.rua) {
    descarta('cota de rua sem cidade ou sem rua', c)
    return false
  }
  if (!ehConfianca(c.confianca) || !c.fonte) {
    descarta('cota de rua sem fonte ou com confiança inválida', c)
    return false
  }
  // REGRA BLOQUEANTE do CLAUDE.md, item 4: busca e simulador só em régua.
  // O nível ao vivo com que estas cotas são comparadas vem da Defesa Civil, que
  // é régua. Uma cota em outra referência produziria "faltam 2,30 m" com 20 cm
  // de erro embutido, sem nada na tela denunciando.
  if (c.referencia !== undefined && c.referencia !== 'régua') {
    descarta('cota de rua fora da referência régua', c)
    return false
  }
  if (c.cota_m === null) return true // legítimo: a fonte cita e não publica o número
  if (typeof c.cota_m !== 'number' || !Number.isFinite(c.cota_m)) {
    descarta('cota de rua com cota_m que não é número', c)
    return false
  }
  // Nenhuma régua da bacia chega perto de 25 m.
  if (c.cota_m <= 0 || c.cota_m >= 25) {
    descarta('cota de rua fora de faixa plausível', c)
    return false
  }
  return true
}

export const cotasRuas: CotaRua[] = (cotasBrutas.cotas ?? []).filter(cotaRuaValida)

/** Os avisos que a tela é obrigada a mostrar junto das cotas. */
export const avisosCotasRuas: string[] = cotasBrutas._meta?.aviso ?? []
