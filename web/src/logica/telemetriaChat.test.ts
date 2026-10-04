/**
 * Contagem das perguntas que o chat não entende (decisão de 04/10/2026).
 * Trava a privacidade: o evento tem EXATAMENTE as cinco chaves, nunca leva
 * pedaço do texto digitado, cidade só do cadastro e só citada, dia sem hora.
 * As perguntas passam pelo motor de verdade, com os dados reais.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { responder } from '../chat-local/motor'
import { dados } from '../chat-local/testes/carregar'
import {
  CHAVES_EVENTO,
  LIMITE_POR_PAGINA,
  ROTA_CONTAGEM,
  chaveContador,
  criarEnviador,
  diaDeBrasilia,
  idsDoCadastro,
  montarEvento,
  serializarEvento,
  servidorContando,
  validarEvento,
  type EventoNaoEntendi,
} from './telemetriaChat'
import {
  CHAVE_CONTAGEM_CHAT,
  contagemChatPermitida,
  gravarContagemChat,
  navegadorPedeNaoRastrear,
  type Armazem,
} from './preferencias'

const CADASTRO = idsDoCadastro(dados.estacoes)
const AGORA = new Date('2026-10-04T15:42:17Z')
const VERSAO = '0.1.0+abc1234'

function eventoDe(pergunta: string, agora = AGORA): EventoNaoEntendi | null {
  const r = responder(pergunta, dados)
  return montarEvento({ intencao: r.intencao, falha: r.falha, agora, versao: VERSAO, cidadesDoCadastro: CADASTRO })
}

/** Todo trecho de `n` caracteres do texto (minúsculo, sem acento) que tenha letra ou dígito. */
function trechos(texto: string, n: number): string[] {
  const t = texto
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
  const out: string[] = []
  for (let i = 0; i + n <= t.length; i++) {
    const s = t.slice(i, i + n)
    if (/[a-z0-9]/.test(s) && !/^\s|\s$/.test(s)) out.push(s)
  }
  return out
}

function semPedacoDoTexto(evento: EventoNaoEntendi, pergunta: string, permitido: string[] = []) {
  const serial = serializarEvento(evento).toLowerCase()
  const livre = permitido.reduce((s, p) => s.split(p).join('#'), serial)
  for (const t of trechos(pergunta, 4)) assert.ok(!livre.includes(t), `o evento contém "${t}", pedaço da pergunta: ${serial}`)
}

test('pergunta não entendida vira evento com exatamente as cinco chaves e nada do texto', () => {
  const pergunta = 'Me conta uma piada do Joaquim Pereira, telefone 47 99999-0000, rua XV de Novembro 812'
  const r = responder(pergunta, dados)
  assert.equal(r.intencao, 'nao_entendi')
  const ev = eventoDe(pergunta)
  assert.ok(ev)
  assert.deepEqual(Object.keys(ev), [...CHAVES_EVENTO])
  assert.deepEqual(ev, { categoria: 'desconhecida', motivo: 'sem_intencao', cidade: null, dia: '2026-10-04', versao: VERSAO })
  semPedacoDoTexto(ev, pergunta)
  assert.deepEqual(Object.keys(JSON.parse(serializarEvento(ev))), [...CHAVES_EVENTO])
})

test('várias perguntas não entendidas: nenhum pedaço de 4 letras do texto vai no evento', () => {
  const perguntas = [
    'me conta uma piada',
    'Quem ganhou o jogo ontem?',
    'meu e-mail é fulano.silva@exemplo.com e meu CPF 123.456.789-00',
    'Moro na Rua Hermann Hering, 1500 apto 32, ligue 47988887777',
    'qwerty asdfgh zxcvbn',
  ]
  for (const p of perguntas) {
    const ev = eventoDe(p)
    assert.ok(ev, p)
    assert.equal(ev.motivo, 'sem_intencao', p)
    assert.equal(ev.cidade, null, p)
    semPedacoDoTexto(ev, p)
  }
})

test('intenção reconhecida sem o ano: categoria, motivo e a cidade do cadastro — e só ela do texto', () => {
  const pergunta = 'Quantos desabrigados teve Blumenau naquela enchente terrível?'
  const ev = eventoDe(pergunta)
  assert.deepEqual(ev, { categoria: 'atlas', motivo: 'faltou_ano', cidade: 'blumenau', dia: '2026-10-04', versao: VERSAO })
  semPedacoDoTexto(ev!, pergunta, ['blumenau'])
})

test('intenção reconhecida sem a cidade', () => {
  const ev = eventoDe('qual foi a maior enchente de todas?')
  assert.deepEqual(ev, { categoria: 'maiores_cheias', motivo: 'faltou_cidade', cidade: null, dia: '2026-10-04', versao: VERSAO })
  assert.equal(eventoDe('quanto choveu na enchente?')?.motivo, 'faltou_ano')
  assert.equal(eventoDe('quanto choveu na enchente?')?.categoria, 'chuva')
})

test('cidade fora do cadastro (só no Atlas) não vai no evento', () => {
  assert.ok(!CADASTRO.has('navegantes'))
  const ev = eventoDe('desabrigados em Navegantes')
  assert.equal(ev?.motivo, 'faltou_ano')
  assert.equal(ev?.cidade, null)
})

test('pergunta entendida não gera evento', () => {
  for (const p of ['Qual foi a maior cheia de Rio do Sul?', 'Cheias de Gaspar em 2011', 'vai encher hoje?', 'oi'])
    assert.equal(eventoDe(p), null, p)
})

test('o dia é o de Brasília e a hora some', () => {
  // 02:30 UTC de 04/10 = 23:30 de 03/10 em Brasília.
  assert.equal(diaDeBrasilia(new Date('2026-10-04T02:30:00Z')), '2026-10-03')
  assert.equal(diaDeBrasilia(new Date('2026-10-04T03:00:00Z')), '2026-10-04')
  const ev = eventoDe('me conta uma piada', new Date('2026-10-04T02:30:00Z'))
  assert.equal(ev?.dia, '2026-10-03')
  assert.doesNotMatch(serializarEvento(ev!), /T\d|:\d\d/)
})

test('versão estranha vira "desconhecida"; intenção fora da lista vira "desconhecida"', () => {
  const ev = montarEvento({
    intencao: 'inventada',
    falha: { motivo: 'sem_intencao' },
    agora: AGORA,
    versao: 'texto livre com espaço',
    cidadesDoCadastro: CADASTRO,
  })
  assert.equal(ev?.categoria, 'desconhecida')
  assert.equal(ev?.versao, 'desconhecida')
  // Motivo fora do enum: não há evento.
  assert.equal(
    montarEvento({ intencao: 'atlas', falha: { motivo: 'outro' as never }, agora: AGORA, versao: VERSAO, cidadesDoCadastro: CADASTRO }),
    null,
  )
})

test('o servidor aceita o evento montado e recusa tudo que fuja do esquema', () => {
  const ok = eventoDe('desabrigados em Blumenau')!
  const op = { cidadesDoCadastro: CADASTRO, agora: AGORA }
  assert.deepEqual(validarEvento(JSON.parse(serializarEvento(ok)), op), ok)
  const recusa = (corpo: unknown, por: string) => assert.equal(validarEvento(corpo, op), null, por)
  recusa({ ...ok, texto: 'me conta uma piada' }, 'campo a mais')
  recusa({ ...ok, ip: '1.2.3.4' }, 'campo a mais')
  const { versao: _v, ...semVersao } = ok
  recusa(semVersao, 'campo a menos')
  recusa({ ...ok, categoria: 'qualquer' }, 'categoria fora do enum')
  recusa({ ...ok, motivo: 'qualquer' }, 'motivo fora do enum')
  recusa({ ...ok, cidade: 'navegantes' }, 'cidade fora do cadastro')
  recusa({ ...ok, cidade: 'Rua XV de Novembro' }, 'cidade com texto livre')
  recusa({ ...ok, dia: '2026-10-04T15:42' }, 'dia com hora')
  recusa({ ...ok, dia: '2026-09-01' }, 'dia longe de hoje')
  recusa({ ...ok, versao: 'a b' }, 'versão com espaço')
  recusa([ok], 'lista')
  recusa(null, 'nulo')
  recusa('texto', 'texto')
  // Ontem e amanhã passam (relógio torto, virada do dia).
  assert.ok(validarEvento({ ...ok, dia: '2026-10-03' }, op))
  assert.ok(validarEvento({ ...ok, dia: '2026-10-05' }, op))
})

test('chave do contador: dia|categoria|motivo|cidade', () => {
  assert.equal(chaveContador(eventoDe('desabrigados em Blumenau')!), '2026-10-04|atlas|faltou_ano|blumenau')
  assert.equal(chaveContador(eventoDe('me conta uma piada')!), '2026-10-04|desconhecida|sem_intencao|-')
})

test('envio: beacon primeiro, fetch com keepalive se o beacon recusar, uma tentativa só e teto por página', async () => {
  const ev = eventoDe('me conta uma piada')!
  const beacons: string[] = []
  const fetches: { url: string; init?: RequestInit }[] = []
  const enviar = criarEnviador({
    beacon: (url, corpo) => {
      beacons.push(`${url} ${corpo}`)
      return false // recusou
    },
    fetch: async (url, init) => {
      fetches.push({ url, init })
      throw new Error('sem rede')
    },
  })
  enviar(ev)
  await new Promise((r) => setTimeout(r, 0))
  assert.equal(beacons.length, 1)
  assert.equal(fetches.length, 1, 'falhou: não tenta de novo')
  assert.equal(fetches[0]?.url, ROTA_CONTAGEM)
  assert.equal(fetches[0]?.init?.keepalive, true)
  assert.equal(fetches[0]?.init?.body, serializarEvento(ev))
  for (let i = 0; i < 50; i++) enviar(ev)
  assert.equal(beacons.length, LIMITE_POR_PAGINA)
})

test('envio: beacon aceito não chama fetch; erro do beacon não quebra', () => {
  const ev = eventoDe('me conta uma piada')!
  let fetches = 0
  criarEnviador({ beacon: () => true, fetch: async () => (fetches++, new Response(null)) })(ev)
  assert.equal(fetches, 0)
  assert.doesNotThrow(() =>
    criarEnviador({
      beacon: () => {
        throw new Error('x')
      },
      fetch: () => {
        throw new Error('y')
      },
    })(ev),
  )
})

test('o site só conta quando o servidor diz, em JSON e sem desvio, que está contando', async () => {
  const json = (corpo: unknown, extra: ResponseInit = {}) =>
    new Response(JSON.stringify(corpo), { status: 200, headers: { 'content-type': 'application/json' }, ...extra })
  assert.equal(await servidorContando(async () => json({ contando: true })), true)
  assert.equal(await servidorContando(async () => json({ contando: false })), false)
  assert.equal(await servidorContando(async () => json({ contando: 'true' })), false)
  // Pages sem a função devolve o index.html; o Access, a tela de login.
  assert.equal(await servidorContando(async () => new Response('<html>', { headers: { 'content-type': 'text/html' } })), false)
  assert.equal(await servidorContando(async () => new Response('', { status: 404 })), false)
  const desviada = json({ contando: true })
  Object.defineProperty(desviada, 'redirected', { value: true })
  assert.equal(await servidorContando(async () => desviada), false)
  assert.equal(
    await servidorContando(async () => {
      throw new Error('sem rede')
    }),
    false,
  )
})

function armazem(inicial: Record<string, string> = {}): Armazem & { dados: Record<string, string> } {
  const dados = { ...inicial }
  return {
    dados,
    getItem: (k) => dados[k] ?? null,
    setItem: (k, v) => {
      dados[k] = v
    },
    removeItem: (k) => {
      delete dados[k]
    },
  }
}

test('preferência: conta por padrão, para com o "não", respeita Não Rastrear e aparelho sem memória', () => {
  assert.equal(contagemChatPermitida(armazem(), false), true)
  assert.equal(contagemChatPermitida(armazem(), true), false, 'GPC/DNT: não conta sem escolha')
  assert.equal(contagemChatPermitida(null, false), false, 'sem armazenamento: não conta')
  const quebrado: Armazem = {
    getItem: () => {
      throw new Error('bloqueado')
    },
    setItem: () => {
      throw new Error('bloqueado')
    },
    removeItem: () => {},
  }
  assert.equal(contagemChatPermitida(quebrado, false), false)
  assert.equal(gravarContagemChat(false, quebrado), false)

  const a = armazem()
  assert.equal(gravarContagemChat(false, a), true)
  assert.equal(a.dados[CHAVE_CONTAGEM_CHAT], 'nao')
  assert.equal(contagemChatPermitida(a, false), false)
  gravarContagemChat(true, a)
  assert.equal(contagemChatPermitida(a, true), true, 'escolha gravada vence o sinal do navegador')

  assert.equal(navegadorPedeNaoRastrear({ globalPrivacyControl: true }), true)
  assert.equal(navegadorPedeNaoRastrear({ doNotTrack: '1' }), true)
  assert.equal(navegadorPedeNaoRastrear({ doNotTrack: 'unspecified' }), false)
  assert.equal(navegadorPedeNaoRastrear(undefined), false)
})
