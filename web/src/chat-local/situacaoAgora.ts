/**
 * "COMO ESTÁ BLUMENAU?" — a resposta do chat para pergunta sobre o PRESENTE que cita
 * uma cidade (decisão do Jefferson de 05/10/2026, opção A; `docs/CHAT-LOCAL.md`).
 *
 * Antes, toda pergunta sobre o presente recebia só o aviso da Defesa Civil. Agora, quando
 * a pergunta pede a SITUAÇÃO de uma cidade, o chat mostra o que o site já mostra no cartão
 * "Agora", com as MESMAS regras (nada de novo é calculado aqui):
 *  - o nível sai de `textoParaCompartilhar` (D4): só leitura que não é velha, sempre com a
 *    hora da medição, a faixa com o nome da Defesa Civil da cidade, nunca ordem de ação;
 *  - cidade de várias réguas (Itajaí) não tem "um número": manda para a página dela;
 *  - sem leitura municipal de agora, a régua da Defesa Civil de SC aparece com o zero
 *    próprio escrito; sem nenhuma leitura recente, o chat diz que não há — nunca mostra
 *    número velho como se fosse de agora;
 *  - a chuva vem do mesmo resumo do painel de chuva (`chuvaDaCidade`): 1 h, 12 h e 24 h.
 *    A fonte NÃO publica 6 h, e o site não inventa (somar janelas não dá o acumulado).
 *
 * Pergunta de PREVISÃO ou de CONSELHO ("vai encher?", "devo sair de casa?") continua só com
 * o aviso: um número ao lado de "devo sair?" soa como resposta. Ganha apenas o atalho para
 * a página da cidade. Nada aqui é IA.
 */
import faixas from '../../../data/faixas.json'
import type { Cidade } from '../dados/tipos'
import type { ChuvaAoVivo } from '../dados/tempoReal'
import { estadoDaCidade, type AoVivo } from '../dados/usarAoVivo'
import { diaDeBrasilia, horaDeBrasilia, rotuloDaFaixa, tendenciaDaLeitura, textoParaCompartilhar } from '../logica/agora'
import { chuvaDaCidade, textoFaixa, type Janela } from '../logica/chuva'
import { metros } from '../logica/formato'
import { frescorDaCidade, idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
import { TEXTO_ALERTA, extrair, norm, type Dados } from './motor'

const ROTULO = (faixas as unknown as { faixas: Record<Faixa, { rotulo: string }> }).faixas
const ROTULO_ESTADUAL: Record<string, string> = { normal: 'Normal', atencao: 'Atenção', alerta: 'Alerta', emergencia: 'Emergência' }

/** Previsão, futuro ou pedido de conselho: aí o chat não mostra número, só o aviso. */
const PREVISAO_OU_CONSELHO = [
  /\b(vai|vao|pode|podem|deve|devem|ira|irao)\s+(encher|subir|transbordar|alagar|inundar|chover|baixar|descer|passar|chegar)\b/,
  /\bprevis/,
  /\b(amanha|proximas horas|proximos dias|mais tarde|logo mais|daqui a pouco|esta noite|essa noite|madrugada|fim de semana)\b/,
  /\b(devo|devemos|preciso|precisamos|tenho que|temos que|compensa|vale a pena|e seguro|posso|podemos|da para|da pra|e para|e pra|melhor)\b/,
  /\b(sair de casa|evacuar|moveis|tirar o carro|o que (voce|vc) acha|o que fa[cz]o|o que fazer)\b/,
]
export const pedePrevisaoOuConselho = (pergunta: string) => {
  const t = norm(pergunta)
  return PREVISAO_OU_CONSELHO.some((r) => r.test(t))
}

export interface RespostaDoPresente {
  texto: string
  /** Atalho para a página da cidade ("Ver Blumenau agora →"). */
  link?: { texto: string; para: string }
}

export const RODAPE_PRESENTE = 'É a última medição, não previsão. Para saber o que fazer, siga a Defesa Civil: ligue 199 (ou 193, Bombeiros, em emergência).'

const JANELAS_CHAT: Janela[] = ['h1', 'h12', 'h24']

function textoChuva(nome: string, cidadeId: string, chuva: ChuvaAoVivo[], agora: Date): string | null {
  const r = chuvaDaCidade(chuva, cidadeId)
  if (!r || !r.pluviometros || !r.medidoEm) return null
  if (frescorDaCidade(idadeMin(r.medidoEm, agora), cidadeId) === 'velha') return null
  const partes = JANELAS_CHAT.filter((j) => r.porJanela[j]).map((j) => `${j.slice(1)} h: ${textoFaixa(r.porJanela[j]!)}`)
  if (!partes.length) return null
  const quantos = r.pluviometros === 1 ? '1 pluviômetro' : `${r.pluviometros} pluviômetros`
  return `Chuva acumulada em ${nome} (${quantos}, medida até ${horaDeBrasilia(r.medidoEm)}): ${partes.join(' · ')}.`
}

/**
 * A resposta para uma pergunta que a barreira do presente pegou (ou que o classificador
 * marcou `situacao_atual`). Sem cidade, sem dado ao vivo ou com pedido de previsão/conselho:
 * o aviso de sempre.
 */
export function respostaDoPresente(args: {
  pergunta: string
  dados: Dados
  /** As cidades do cadastro, por rio (`estacoes.rios`). */
  rios: Record<string, { cidades: Cidade[] }>
  aoVivo: AoVivo | null
}): RespostaDoPresente {
  const conhecida = extrair(args.pergunta, args.dados).cidade
  if (!conhecida) return { texto: TEXTO_ALERTA }
  const achada = Object.entries(args.rios)
    .flatMap(([rioId, r]) => r.cidades.map((c) => ({ rioId, c })))
    .find((x) => x.c.id === conhecida.id)
  if (!achada) return { texto: `${conhecida.nome} não tem régua de rio neste site.\n${TEXTO_ALERTA}` }
  const { rioId, c: cidade } = achada
  const link = { texto: `Ver ${cidade.nome} agora →`, para: cidade.id === 'itajai' ? '/itajai' : `/${rioId === 'itajai-mirim' ? 'mirim' : 'acu'}/${cidade.id}` }
  if (pedePrevisaoOuConselho(args.pergunta) || !args.aoVivo) return { texto: TEXTO_ALERTA, link }

  const v = args.aoVivo
  const e = estadoDaCidade(cidade, rioId, v)
  const linhas: string[] = []
  if (e.varias) {
    linhas.push(`${cidade.nome} tem várias réguas, cada uma com o seu zero: não há um número só para a cidade. A leitura de cada régua está na página de ${cidade.nome}.`)
  } else {
    const texto = e.leitura
      ? textoParaCompartilhar({
          cidade,
          leitura: e.leitura,
          rotuloFaixa: e.faixa === 'sem-dado' || e.faixa === 'varias' ? null : rotuloDaFaixa(e.faixa, cidade, ROTULO[e.faixa].rotulo),
          tendencia: tendenciaDaLeitura(e.serie, e.leitura, v.agora),
          agora: v.agora,
        })
      : null
    const est = e.estadual
    if (texto) {
      // O texto do WhatsApp (D4) sem o rodapé dele: o rodapé daqui vem no fim.
      linhas.push(`Última leitura da régua de ${cidade.nome}:`, texto.split('\n\n')[0]!)
    } else if (est?.medidoEm && Number.isFinite(est.nivelBrutoM) && frescorDaCidade(idadeMin(est.medidoEm, v.agora), cidade.id) !== 'velha') {
      linhas.push(
        `O site não tem leitura recente da régua da Defesa Civil de ${cidade.nome}. Na rede da Defesa Civil de SC (${est.estacao}): ${metros(est.nivelBrutoM)}, medido às ${horaDeBrasilia(est.medidoEm)} de ${diaDeBrasilia(est.medidoEm)} (${textoIdade(idadeMin(est.medidoEm, v.agora))}).`,
        'Essa régua tem zero próprio: não compare com as cotas da cidade.' +
          (e.faixaEstadual ? ` Faixa publicada pela Defesa Civil de SC: ${ROTULO_ESTADUAL[e.faixaEstadual] ?? e.faixaEstadual}.` : ''),
      )
    } else {
      linhas.push(`O site não tem leitura recente da régua de ${cidade.nome} agora.`)
    }
  }
  const chuva = v.tempoReal.chuvaOk === false ? null : textoChuva(cidade.nome, cidade.id, v.tempoReal.chuva ?? [], v.agora)
  if (chuva) linhas.push(chuva)
  linhas.push(RODAPE_PRESENTE)
  return { texto: linhas.join('\n'), link }
}
