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
import type { CotaRua, CotasRuas } from './tipos'
import { cotaRuaValida } from '../logica/cotasRuas'

// O QUE VALE COMO COTA vive em `logica/cotasRuas`, não aqui.
//
// Este módulo importa o JSON pelo alias `@dados`, que SÓ EXISTE NO VITE — teste
// nenhum consegue carregá-lo. Enquanto o predicado morava aqui, a regra
// bloqueante da referência (CLAUDE.md item 4) era prosa que ninguém podia
// falsificar; e de fato ela estava errada, aceitando cota sem o campo. Agora a
// decisão está na camada pura, com sabotagem que reprova.
const cotasBrutas = cotasRuasJson as unknown as CotasRuas

export const cotasRuas: CotaRua[] = (cotasBrutas.cotas ?? []).filter(cotaRuaValida)

/** Os avisos que a tela é obrigada a mostrar junto das cotas. */
export const avisosCotasRuas: string[] = cotasBrutas._meta?.aviso ?? []
