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
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { responder, type Dados } from './motor'
import { carregarBase, carregarCotasAna } from './carregar'
import { contagemChatPermitida, gravarContagemChat } from '../logica/preferencias'
import { RETENCAO_DIAS, criarEnviador, idsDoCadastro, montarEvento, servidorContando } from '../logica/telemetriaChat'
import estilos from './ChatLocal.module.css'

/** Trocado pelo Vite no build (`vite.config.ts`); fora dele, "dev". */
declare const __VERSAO_SITE__: string | undefined
const VERSAO_SITE = typeof __VERSAO_SITE__ === 'string' ? __VERSAO_SITE__ : 'dev'

/** Um enviador por página aberta: o teto de eventos vale para a página toda. */
const enviarContagem = criarEnviador({
  beacon: (url, corpo) => typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function' && navigator.sendBeacon(url, corpo),
  fetch: typeof fetch === 'function' ? (url, init) => fetch(url, init) : undefined,
})

type Msg = { papel: 'usuario' | 'assistente'; texto: string; sugestoes?: string[] }

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

export default function ChatLocal({ rio }: { rio: 'itajai-acu' | 'itajai-mirim' }) {
  const [dados, setDados] = useState<Dados | null>(null)
  const [falhou, setFalhou] = useState(false)
  const [visivel, setVisivel] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [texto, setTexto] = useState('')
  // O servidor está contando? Começa em "não": sem resposta, nada é contado nem prometido.
  const [contando, setContando] = useState(false)
  const [permitido, setPermitido] = useState(() => contagemChatPermitida())
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

  function perguntar(p: string) {
    const q = p.trim()
    if (!q || !dados) return
    const r = responder(q, dados)
    if (contando && permitido) {
      // O texto `q` não entra aqui: só a intenção e o motivo que o motor classificou.
      const evento = montarEvento({ intencao: r.intencao, falha: r.falha, agora: new Date(), versao: VERSAO_SITE, cidadesDoCadastro: cadastro })
      if (evento) enviarContagem(evento)
    }
    setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }, { papel: 'assistente', texto: r.texto, sugestoes: r.sugestoes }])
    setTexto('')
    setTimeout(() => fim.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 30)
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
            <div>{msg.texto}</div>
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
        <button type="button" onClick={() => perguntar(texto)} disabled={!dados || !texto.trim()}>
          Perguntar
        </button>
      </div>

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
