/**
 * Chat do histórico SEM IA e SEM API: roda todo no navegador e responde só com
 * os JSONs do site (`motor.ts`). Funciona no GitHub Pages sem backend.
 *
 * Os dados só são baixados quando a caixa chega perto da tela (IntersectionObserver);
 * numa noite de chuva, quem abriu o site para ver o nível do rio não paga por eles.
 *
 * Contagem das perguntas não entendidas (decisão de 04/10/2026,
 * `docs/TELEMETRIA-CHAT.md`): só quando o servidor diz que está contando E a
 * pessoa não desmarcou. Vai um evento agregado, nunca o texto digitado.
 *
 * Chat com IA (docs/CHAT-IA.md): só quando o servidor diz que está ligado. O
 * motor local responde primeiro, sempre; a pergunta só vai à IA quando a pessoa
 * aperta "Perguntar à IA" naquela resposta, com o aviso de envio à vista.
 *
 * Piloto do classificador (docs/PILOTO-CLASSIFICADOR.md): só para quem o servidor
 * diz que está no piloto. Quando o motor não entende (ou só palpita), a pergunta vai
 * ao classificador; a resposta continua saindo do motor, com "Entendi: …" e os botões
 * "Correto"/"Não era isso". Dúvida, demora ou falha: "não consegui interpretar" — o
 * palpite (a maior cheia da cidade citada) não sai mais para quem está no piloto.
 *
 * Pergunta sobre o presente que cita uma cidade ("como está Blumenau?", 05/10/2026): a
 * última leitura ao vivo, com as regras do cartão "Agora", a chuva e o 199
 * (`situacaoAgora.ts`). Previsão e conselho continuam só com o aviso.
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { EXEMPLOS, citaRua, responder, type Dados } from './motor'
import { carregarBase, carregarCotasAna, carregarCotasRuas } from './carregar'
import { contagemChatPermitida, gravarContagemChat } from '../logica/preferencias'
import { RETENCAO_DIAS, criarEnviador, idsDoCadastro, montarEvento, servidorContando } from '../logica/telemetriaChat'
import { AVISO_ENVIO, iaLigada, perguntarIA } from '../chat-ia/cliente'
import { AVISO_PILOTO, TEXTO_NAO_ERA_ISSO, classificarPergunta, enviarCorrecao, mensagemDoPiloto, pilotoLigado, type Correcao, type Origem } from '../chat-ia/clienteClassificador'
import { estacoes } from '../dados/carregar'
import type { AoVivo } from '../dados/usarAoVivo'
import { respostaDoPresente } from './situacaoAgora'
import estilos from './ChatLocal.module.css'

/** Trocado pelo Vite no build (`vite.config.ts`); fora dele, "dev". */
declare const __VERSAO_SITE__: string | undefined
const VERSAO_SITE = typeof __VERSAO_SITE__ === 'string' ? __VERSAO_SITE__ : 'dev'

/** Um enviador por página aberta: o teto de eventos vale para a página toda. */
const enviarContagem = criarEnviador({
  beacon: (url, corpo) => typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function' && navigator.sendBeacon(url, corpo),
  fetch: typeof fetch === 'function' ? (url, init) => fetch(url, init) : undefined,
})

type Msg = {
  papel: 'usuario' | 'assistente'
  texto: string
  sugestoes?: string[]
  /** Resposta do motor local que pode ir à IA: a pergunta que a gerou. */
  paraIA?: string
  /** Veio da IA (rótulo próprio na tela). */
  ia?: boolean
  /** Piloto do classificador: o que foi entendido, e o id para os botões. */
  entendido?: string
  idCorrecao?: string
  corrigido?: Correcao
  /** Atalho para uma página do site ("Ver Blumenau agora →"). */
  link?: { texto: string; para: string }
}

const INICIO: Record<'itajai-acu' | 'itajai-mirim', string[]> = {
  'itajai-acu': [
    'Qual foi a maior cheia de Rio do Sul?',
    'Quanto choveu antes da enchente de novembro de 2008?',
    'Quanto tempo a cheia leva de Rio do Sul até Blumenau?',
  ],
  'itajai-mirim': [
    'As 5 maiores cheias de Brusque',
    'Cota da ANA em Brusque em novembro de 2008',
    'Qual a antecedência do pico em Botuverá antes de Brusque?',
  ],
}

export default function ChatLocal({ rio, aoVivo = null }: { rio: 'itajai-acu' | 'itajai-mirim'; aoVivo?: AoVivo | null }) {
  const [dados, setDados] = useState<Dados | null>(null)
  const [falhou, setFalhou] = useState(false)
  const [visivel, setVisivel] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [texto, setTexto] = useState('')
  // O servidor está contando? Começa em "não": sem resposta, nada é contado nem prometido.
  const [contando, setContando] = useState(false)
  const [permitido, setPermitido] = useState(() => contagemChatPermitida())
  // A IA está ligada no servidor? Começa em "não": sem resposta, o botão não aparece.
  const [comIA, setComIA] = useState(false)
  const [esperandoIA, setEsperandoIA] = useState(false)
  // Piloto do classificador: começa em "não", como a IA.
  const [piloto, setPiloto] = useState(false)
  const [classificando, setClassificando] = useState(false)
  const cadastro = useMemo(() => (dados ? idsDoCadastro(dados.estacoes) : new Set<string>()), [dados])
  const caixa = useRef<HTMLElement>(null)
  const fim = useRef<HTMLDivElement>(null)

  // Só começa a baixar os JSONs quando a caixa chega a ~600 px da tela.
  useEffect(() => {
    const el = caixa.current
    if (!el || typeof IntersectionObserver === 'undefined') {
      setVisivel(true)
      return
    }
    const obs = new IntersectionObserver(
      (entradas) => {
        if (entradas.some((x) => x.isIntersecting)) {
          setVisivel(true)
          obs.disconnect()
        }
      },
      { rootMargin: '600px 0px' },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    if (!visivel) return
    let vivo = true
    servidorContando((url, init) => fetch(url, init)).then((sim) => {
      if (vivo) setContando(sim)
    })
    iaLigada(typeof fetch === 'function' ? (url, init) => fetch(url, init) : undefined).then((sim) => {
      if (vivo) setComIA(sim)
    })
    pilotoLigado(typeof fetch === 'function' ? (url, init) => fetch(url, init) : undefined).then((sim) => {
      if (vivo) setPiloto(sim)
    })
    carregarBase()
      .then((d) => {
        if (!vivo) return
        setDados(d)
        carregarCotasAna()
          .then((c) => {
            if (vivo) setDados((atual) => (atual ? { ...atual, cotasAna: c } : atual))
          })
          .catch(() => {
            /* sem as cotas o motor responde "carregando"; o resto funciona */
          })
      })
      .catch(() => {
        if (vivo) setFalhou(true)
      })
    return () => {
      vivo = false
    }
  }, [visivel])

  async function perguntar(p: string) {
    const q = p.trim()
    if (!q || !dados) return
    // Pergunta sobre rua: baixa as cotas (~3 MB) só agora, e responde quando chegam.
    let base = dados
    if (citaRua(q) && !base.cotasRuas) {
      try {
        const cotasRuas = await carregarCotasRuas()
        base = { ...base, cotasRuas }
        setDados((atual) => (atual ? { ...atual, cotasRuas } : atual))
      } catch {
        /* sem as cotas o motor responde "carregando" */
      }
    }
    const r = responder(q, base)
    if (contando && permitido) {
      // O texto `q` não entra aqui: só a intenção e o motivo que o motor classificou.
      const evento = montarEvento({ intencao: r.intencao, falha: r.falha, agora: new Date(), versao: VERSAO_SITE, cidadesDoCadastro: cadastro })
      if (evento) enviarContagem(evento)
    }
    // A barreira do presente vale igual na IA: essa resposta não ganha o botão.
    const paraIA = r.intencao === 'agora' ? undefined : q
    const presente = () => respostaDoPresente({ pergunta: q, dados: base, rios: estacoes.rios, aoVivo })
    if (r.intencao === 'agora') {
      setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }, { papel: 'assistente', ...presente() }])
      setTexto('')
      rolarAoFim()
      return
    }
    const origem: Origem | null = !piloto || classificando ? null : r.intencao === 'nao_entendi' ? 'nao_entendi' : r.palpite ? 'palpite' : null
    if (!origem) {
      setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }, { papel: 'assistente', texto: r.texto, sugestoes: r.sugestoes, paraIA }])
      setTexto('')
      rolarAoFim()
      return
    }
    // Piloto: o motor não entendeu (ou palpitou). Pergunta ao classificador; a resposta sai do motor.
    setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }])
    setTexto('')
    setClassificando(true)
    rolarAoFim()
    const c = await classificarPergunta((url, init) => fetch(url, init), q, origem)
    if (!('erro' in c) && c.decisao.tipo === 'ok' && c.decisao.classificacao.intencao === 'rua_historico' && !base.cotasRuas) {
      try {
        const cotasRuas = await carregarCotasRuas()
        base = { ...base, cotasRuas }
        setDados((atual) => (atual ? { ...atual, cotasRuas } : atual))
      } catch {
        /* sem as cotas o motor responde "carregando" */
      }
    }
    if (!('erro' in c) && c.decisao.tipo === 'agora') {
      setMsgs((atual) => [...atual, { papel: 'assistente', ...presente() }])
    } else {
      const m = mensagemDoPiloto(c, base)
      setMsgs((atual) => [...atual, { papel: 'assistente', ...m, ...(m.entendido ? {} : { paraIA }) }])
    }
    setClassificando(false)
    rolarAoFim()
  }

  function corrigir(indice: number, id: string, correcao: Correcao) {
    void enviarCorrecao((url, init) => fetch(url, init), id, correcao)
    setMsgs((atual) => {
      const novas = atual.map((m, i) => (i === indice ? { ...m, corrigido: correcao } : m))
      return correcao === 'nao_era_isso' ? [...novas, { papel: 'assistente' as const, texto: TEXTO_NAO_ERA_ISSO, sugestoes: EXEMPLOS }] : novas
    })
    rolarAoFim()
  }

  function rolarAoFim() {
    setTimeout(() => fim.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 30)
  }

  async function perguntarAIA(indice: number, q: string) {
    if (esperandoIA) return
    setEsperandoIA(true)
    // O botão some daquela resposta: uma pergunta, um envio.
    setMsgs((atual) => atual.map((m, i) => (i === indice ? { ...m, paraIA: undefined } : m)))
    rolarAoFim()
    // Contexto: as duas últimas trocas com a IA (pergunta da pessoa → resposta da IA).
    const anteriores = msgs.flatMap((m, i) => {
      const antes = msgs[i - 1]
      return m.ia && antes?.papel === 'usuario' ? [{ pergunta: antes.texto, resposta: m.texto }] : []
    })
    const r = await perguntarIA((url, init) => fetch(url, init), q, anteriores)
    setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }, { papel: 'assistente', texto: r.texto, ia: r.tipo === 'ia' }])
    setEsperandoIA(false)
    rolarAoFim()
  }

  return (
    <section ref={caixa} className="cartao" aria-label="Perguntas sobre o histórico de enchentes">
      <h2>Pergunte sobre o histórico</h2>
      <p className={estilos['chat-aviso']}>
        Respostas montadas só com os dados deste site, com a fonte de cada número. <strong>Não é alerta.</strong> Em
        emergência, ligue <strong>199</strong>.
      </p>

      {falhou ? (
        <p className={estilos['chat-erro']} role="alert">
          Não foi possível carregar os dados do chat.
        </p>
      ) : null}

      <div className={estilos['chat-mensagens']} role="log" aria-live="polite">
        {msgs.length === 0 ? (
          <div className={estilos['chat-sugestoes']}>
            {INICIO[rio].map((s) => (
              <button key={s} type="button" disabled={!dados} onClick={() => perguntar(s)}>
                {s}
              </button>
            ))}
          </div>
        ) : null}
        {msgs.map((msg, i) => (
          <div key={i} className={`${estilos['chat-msg']} ${msg.papel === 'usuario' ? estilos['chat-usuario'] : estilos['chat-assistente']}`}>
            {msg.ia ? <div className={estilos['chat-rotulo-ia']}>Resposta da IA com os dados do site — pode errar</div> : null}
            {msg.entendido ? (
              <div className={estilos['chat-entendido']}>
                <strong>Entendi:</strong> {msg.entendido}. <span>(interpretação automática, piloto)</span>
              </div>
            ) : null}
            <div className={msg.corrigido === 'nao_era_isso' ? estilos['chat-descartada'] : undefined}>{msg.texto}</div>
            {msg.idCorrecao ? (
              msg.corrigido ? (
                <div className={estilos['chat-corrigido']} role="status">
                  {msg.corrigido === 'correto' ? 'Obrigado pela confirmação.' : 'Marcado como entendido errado.'}
                </div>
              ) : (
                <div className={estilos['chat-correcao']} role="group" aria-label="A interpretação está certa?">
                  <button type="button" onClick={() => corrigir(i, msg.idCorrecao!, 'correto')}>
                    Correto
                  </button>
                  <button type="button" onClick={() => corrigir(i, msg.idCorrecao!, 'nao_era_isso')}>
                    Não era isso
                  </button>
                </div>
              )
            ) : null}
            {comIA && msg.paraIA ? (
              <button type="button" className={estilos['chat-botao-ia']} disabled={esperandoIA} onClick={() => perguntarAIA(i, msg.paraIA!)}>
                Perguntar à IA
              </button>
            ) : null}
            {msg.link ? (
              <Link className={estilos['chat-link']} to={msg.link.para}>
                {msg.link.texto}
              </Link>
            ) : null}
            {msg.sugestoes ? (
              <div className={estilos['chat-sugestoes']}>
                {msg.sugestoes.map((s) => (
                  <button key={s} type="button" onClick={() => perguntar(s)}>
                    {s}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        ))}
        {classificando ? (
          <div className={`${estilos['chat-msg']} ${estilos['chat-assistente']}`} role="status">
            Tentando entender a pergunta…
          </div>
        ) : null}
        {esperandoIA ? (
          <div className={`${estilos['chat-msg']} ${estilos['chat-assistente']}`} role="status">
            A IA está consultando os dados do site…
          </div>
        ) : null}
        <div ref={fim} />
      </div>

      <div className={estilos['chat-entrada']}>
        <input
          value={texto}
          maxLength={300}
          placeholder={dados ? 'Ex.: cheias de Gaspar em 2011' : falhou ? 'Dados indisponíveis' : 'Carregando dados…'}
          disabled={!dados}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') perguntar(texto)
          }}
          aria-label="Sua pergunta"
        />
        <button type="button" onClick={() => perguntar(texto)} disabled={!dados || !texto.trim() || classificando}>
          Perguntar
        </button>
      </div>

      {comIA ? <p className={estilos['chat-aviso-ia']}>{AVISO_ENVIO}</p> : null}
      {piloto ? <p className={estilos['chat-aviso-ia']}>{AVISO_PILOTO}</p> : null}

      {contando ? (
        <div className={estilos['chat-contagem']}>
          <label>
            <input
              type="checkbox"
              checked={permitido}
              onChange={(e) => {
                setPermitido(e.target.checked)
                gravarContagemChat(e.target.checked)
              }}
            />{' '}
            Contar as perguntas que o chat não entender
          </label>
          <p>
            Soma 1 num contador do dia com o tipo de pergunta, o motivo, a cidade citada e a versão do site.{' '}
            <strong>Não guarda o que você digitou</strong>, nem IP, nome, telefone ou qualquer identificador; por isso não
            há dado seu para apagar. Os contadores somem em {RETENCAO_DIAS} dias. Desmarcar para a contagem neste aparelho.
          </p>
        </div>
      ) : null}
    </section>
  )
}
