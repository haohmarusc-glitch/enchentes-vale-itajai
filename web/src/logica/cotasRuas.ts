/**
 * Cotas de rua: a partir de que nível do rio cada rua começa a alagar.
 *
 * É o dado mais direto do projeto — não passa por modelo nenhum, é leitura de
 * tabela — e por isso o mais fácil de estragar sem que ninguém perceba. Um
 * número errado aqui não destoa de nada na tela: só manda a pessoa para o lado
 * errado.
 *
 * Três regras que este módulo mantém:
 *
 * 1. **Nunca comparar entre cidades.** 7 m em Gaspar não é 7 m em Blumenau.
 *    Toda função recebe a cidade e só olha para as cotas dela.
 * 2. **Cota nula não é zero.** A fonte cita a rua e não publica o número; a
 *    rua aparece na busca com a nota, e fica fora de qualquer conta.
 * 3. **A rua é o par (nome, ponto).** A São Rafael alaga a 7,40 m no final e a
 *    7,75 m perto do nº 169. Agrupar por nome perderia a cota mais baixa —
 *    justamente a que importa.
 */
import type { Confianca, CotaRua } from '../dados/tipos'

/** Compara ignorando acento e caixa: quem digita no celular não acentua. */
/**
 * Minúsculas, sem acento e SEM HÍFEN, para a busca de rua casar.
 *
 * O hífen entrou em 06/09/2026, achado por acidente: quem digita "Beira-Rio" —
 * que é como a avenida é escrita na placa — não achava a "Av. Beira Rio" do
 * cadastro, que a fonte grafou sem hífen, e lia "nenhuma rua com esse nome
 * entre as levantadas" para uma rua que ESTÁ levantada. Mesma correção no
 * `sem_acento` do bot, que tem a mesma busca.
 *
 * O hífen vira espaço, e não some: "Beira-Rio" e "Beira Rio" passam a ser o
 * mesmo termo, mas "BeiraRio" continua sendo outro.
 */
export function normalizar(texto: string): string {
  return texto
    .replace(/[-–—]/g, ' ')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
}

export function daCidade(cotas: CotaRua[], cidadeId: string): CotaRua[] {
  return cotas.filter((c) => c.cidade === cidadeId)
}

/** Cidades que têm alguma cota de rua levantada, para a tela saber o que oferecer. */
export function cidadesComCotas(cotas: CotaRua[]): string[] {
  return [...new Set(cotas.map((c) => c.cidade))].sort()
}

/**
 * Ruas da cidade que casam com o que a pessoa digitou.
 *
 * Ordena as que têm cota primeiro, da mais baixa para a mais alta: a rua que
 * alaga antes é a que a pessoa precisa ver antes.
 */
/**
 * Quantas ruas a busca mostra de uma vez.
 *
 * POR QUE EXISTE (14/09/2026). Digitar "Rua" em Blumenau devolvia 1.894
 * resultados numa página só — no celular, no meio da chuva, é rolagem que não
 * acaba, e quem procura a própria rua desiste antes. O corte mantém as que
 * alagam PRIMEIRO (a lista já vem ordenada pela cota mais baixa), que são as
 * que importam a quem está decidindo sair de casa, e a tela diz quantas ficaram
 * de fora e o que fazer para achar a sua.
 */
export const MAX_RESULTADOS_BUSCA = 12

export function buscar(cotas: CotaRua[], cidadeId: string, termo: string): CotaRua[] {
  const alvo = normalizar(termo)
  if (alvo.length < 2) return []
  return daCidade(cotas, cidadeId)
    .filter((c) => normalizar(c.rua).includes(alvo) || normalizar(c.bairro ?? '').includes(alvo))
    .sort((a, b) => {
      if (a.cota_m === null && b.cota_m === null) return a.rua.localeCompare(b.rua, 'pt-BR')
      if (a.cota_m === null) return 1
      if (b.cota_m === null) return -1
      return a.cota_m - b.cota_m
    })
}

/**
 * Um ponto pode virar afirmação de alcance ("já alagou")?
 *
 * `usar_para_aviso: false` é o cadastro dizendo que aquele número NÃO está
 * conferido o bastante para mover aviso. Em Rio do Sul são dois — Pouso Redondo
 * (3,11 m) e SD 1604 (3,26 m) —, publicados ABAIXO do nível normal do rio: com
 * tempo bom eles já estão "alagados" pela aritmética, e nunca deixam de estar.
 *
 * ACHADO por auditoria externa em 19/09/2026: a busca individual já respeitava
 * o bloqueio para a frase "este nível já foi alcançado", mas o RESUMO não. Com
 * o rio em 3,76 m, o cartão afirmava "2 de 555 ruas já estariam alagadas" e
 * listava exatamente esses dois. O produto transformava em afirmação de água na
 * rua dois números que ele próprio marca como não conferidos.
 */
export function podeAfirmarAlcance(c: CotaRua): boolean {
  return c.usar_para_aviso !== false
}

/** Ruas já alagadas com o rio neste nível, da mais funda para a mais rasa. */
/**
 * As ruas da cidade que TÊM cota E podem ser afirmadas — as únicas contáveis.
 *
 * O cartão dizia "3 de 23 ruas conhecidas já estariam alagadas" usando o total
 * da cidade no denominador. Em Gaspar, 18 das 23 ruas não têm cota: a fonte as
 * cita sem número. Elas nunca podem entrar no numerador, então incluí-las
 * embaixo faz o alagamento parecer quase cinco vezes menos espalhado do que o
 * próprio dado diz — e erra para o lado de quem lê achando que está seguro.
 * As sem cota continuam na tela, contadas à parte.
 *
 * A MESMA razão vale para os bloqueados (`usar_para_aviso: false`), e é por isso
 * que eles saem daqui também: nunca podem entrar no numerador, então mantê-los
 * no denominador afundaria a proporção com pontos que jamais a compõem. Saem da
 * conta e continuam na tela, com a ressalva deles.
 */
export function comCota(cotas: CotaRua[], cidadeId: string): CotaRua[] {
  return daCidade(cotas, cidadeId).filter((c) => c.cota_m !== null && podeAfirmarAlcance(c))
}

export function atingidas(cotas: CotaRua[], cidadeId: string, nivelM: number): CotaRua[] {
  return daCidade(cotas, cidadeId)
    .filter((c) => c.cota_m !== null && c.cota_m <= nivelM && podeAfirmarAlcance(c))
    .sort((a, b) => (a.cota_m ?? 0) - (b.cota_m ?? 0))
}

/**
 * Os pontos BLOQUEADOS cuja cota o nível já passou. Não entram na contagem nem
 * em nenhuma frase de alcance — existem para a tela poder dizer que eles estão
 * ali, em vez de sumir com eles em silêncio. Sumir calado daria a MESMA tela de
 * uma cidade sem pendência nenhuma, e as duas situações pedem decisões
 * diferentes de quem lê.
 */
export function pendentesAbaixoDoNivel(
  cotas: CotaRua[],
  cidadeId: string,
  nivelM: number,
): CotaRua[] {
  return daCidade(cotas, cidadeId)
    .filter((c) => c.cota_m !== null && c.cota_m <= nivelM && !podeAfirmarAlcance(c))
    .sort((a, b) => (a.cota_m ?? 0) - (b.cota_m ?? 0))
}

/** As próximas a alagar se o rio continuar subindo. */
export function proximas(
  cotas: CotaRua[],
  cidadeId: string,
  nivelM: number,
  quantas = 5,
): CotaRua[] {
  return daCidade(cotas, cidadeId)
    .filter((c) => c.cota_m !== null && c.cota_m > nivelM)
    .sort((a, b) => (a.cota_m ?? 0) - (b.cota_m ?? 0))
    .slice(0, quantas)
}

/** A menor e a maior cota levantada na cidade, para o alcance do simulador. */
export function faixaDaCidade(
  cotas: CotaRua[],
  cidadeId: string,
): { min: number; max: number } | null {
  const valores = daCidade(cotas, cidadeId)
    .map((c) => c.cota_m)
    .filter((v): v is number => v !== null)
  if (valores.length === 0) return null
  return { min: Math.min(...valores), max: Math.max(...valores) }
}

/**
 * Quanto falta o rio subir para chegar nesta rua.
 *
 * Negativo quando a rua já está abaixo do nível — e nesse caso quem chama diz
 * "já alaga", não "faltam -0,40 m".
 */
export function faltaPara(cotaM: number, nivelM: number): number {
  return Math.round((cotaM - nivelM) * 100) / 100
}

/**
 * O `ponto` que é NOME DE RUA é uma transversal, e o parêntese escondia isso.
 *
 * MEDIDO em 17/09/2026 sobre `cotas-ruas.json`: dos 1.615 pontos de Gaspar, 454
 * (28%) trazem um nome de rua em `ponto`. Saía "Rua Luiz Franzói (Rua Gertrudes
 * Seberino da Silva)", que se lê como se a segunda fosse outro nome da primeira
 * — quando é a esquina. Quem procura a própria rua precisa reconhecer o lugar.
 *
 * A fonte diz o que o campo é: no KML de Gaspar ele se chama `esquina`, e o
 * `importar_cotas_gaspar.py` registra que traz "a transversal, o número da casa
 * ou o ponto de referência". Por isso só o caso de RUA muda de forma — "47"
 * continua entre parênteses, porque escrever "nº 47" afirmaria que é número de
 * casa, e a fonte não garante isso.
 *
 * Blumenau e Rio do Sul não mudam (0% de nomes de rua em `ponto`).
 * O `bot.py` tem a mesma regra, em `nome_do_ponto`.
 */
const RUA_NO_PONTO = /^(rua|r\.|av\.|avenida|travessa|tv\.|estrada|rod\.|rodovia|servidão)(\s|$)/i

/** `Rua São Rafael (final da rua)` — o ponto faz parte da identidade. */
export function nomeCompleto(c: CotaRua): string {
  const ponto = c.ponto?.trim()
  if (!ponto || ponto === c.rua) return c.rua
  return RUA_NO_PONTO.test(ponto) ? `${c.rua} — esquina com ${ponto}` : `${c.rua} (${ponto})`
}

/* -------------------------------------------------------------------------- *
 * O QUE VALE COMO COTA — o filtro de entrada.
 * -------------------------------------------------------------------------- */

const CONFIANCAS: Confianca[] = ['alta', 'media', 'baixa']

function ehConfianca(v: unknown): v is Confianca {
  return typeof v === 'string' && (CONFIANCAS as string[]).includes(v)
}

function descarta(motivo: string, registro: unknown): void {
  console.warn(`[dados] registro descartado — ${motivo}`, registro)
}

/**
 * Este registro pode virar resposta na tela?
 *
 * VIVE AQUI, e não em `dados/cotasRuas.ts`, porque aquele módulo importa o JSON
 * pelo alias `@dados`, que só existe no Vite: teste nenhum o carrega. A regra
 * mais severa deste arquivo estava lá, e por isso ninguém podia falsificá-la —
 * e ela estava errada.
 */
export function cotaRuaValida(c: CotaRua): boolean {
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
  //
  // CORRIGIDO em 06/09/2026. A condição era `c.referencia !== undefined &&
  // c.referencia !== 'régua'`: uma cota SEM O CAMPO passava direto, comparada
  // como se fosse régua. Ausência virava permissão — o oposto do que o projeto
  // faz em todo lugar, onde `null` é "ninguém conferiu ainda". Eram 39 cotas.
  // O buraco não era sobre elas: era sobre a próxima linha a entrar sem o campo,
  // num arquivo que cresce por importação.
  if (c.referencia !== 'régua') {
    descarta('cota de rua sem referência declarada, ou fora da régua', c)
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
