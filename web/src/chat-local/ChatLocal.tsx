/**
 * Chat do histórico SEM IA e SEM API: roda todo no navegador e responde só com
 * os JSONs do site (`motor.ts`). Funciona no GitHub Pages sem backend.
 *
 * Os dados só são baixados quando a caixa chega perto da tela (IntersectionObserver);
 * numa noite de chuva, quem abriu o site para ver o nível do rio não paga por eles.
 */
import { useEffect, useRef, useState } from 'react'
import { responder, type Dados } from './motor'
import { carregarBase, carregarCotasAna } from './carregar'
import estilos from './ChatLocal.module.css'

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
    </section>
  )
}
