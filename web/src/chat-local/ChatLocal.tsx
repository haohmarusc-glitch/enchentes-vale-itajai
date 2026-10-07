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
 *
 * Chat no topo de todas as páginas e comandos (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026). Três variantes,
 * a mesma conversa (`conversa.ts`, só na memória da aba):
 *  - `cartao`: a caixa de sempre, em /perguntas e na aba Histórico; com ela na tela, a barra do topo some;
 *  - `barra`: uma linha no topo das páginas, que abre a conversa ao tocar;
 *  - `monitor`: a mesma linha, dentro do bloco do topo do Monitor (decisão do Jefferson: o mapa não muda).
 * Antes do motor, o texto é tentado como PEDIDO (`comandos/`): "mostrar Blumenau", "zoom na régua DC-05".
 * Só comandos do registro executam, e o chat diz o resultado real de cada um.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { EXEMPLOS, cidadesConhecidas, citaRua, responder, type Dados } from './motor'
import { corrigirCidade, textoDaCorrecao } from '../comandos/corrigir'
import { carregarBase, carregarCotasAna, carregarCotasRuas, carregarRuasManchaItajai } from './carregar'
import { contagemChatPermitida, gravarContagemChat } from '../logica/preferencias'
import { RETENCAO_DIAS, criarEnviador, idsDoCadastro, montarEvento, servidorContando } from '../logica/telemetriaChat'
import { AVISO_ENVIO, iaLigada, perguntarIA } from '../chat-ia/cliente'
import { AVISO_PILOTO, TEXTO_NAO_ERA_ISSO, classificarPergunta, enviarCorrecao, mensagemDoPiloto, pilotoLigado, type Correcao, type Origem } from '../chat-ia/clienteClassificador'
import { estacoes } from '../dados/carregar'
import type { AoVivo } from '../dados/usarAoVivo'
import { respostaDoPresente } from './situacaoAgora'
import { abrirPainel, lerConversa, limparConversa, mudarMsgs, registrarChatDePagina, useConversa, type Msg } from './conversa'
import { useComandos } from '../comandos/usarComandos'
import { contextoComConversa, decidirContinuacao, memoriaDaConversa } from '../comandos/conversa'
import AoVivoDoChat from './AoVivoDoChat'
import estilos from './ChatLocal.module.css'

/** Trocado pelo Vite no build (`vite.config.ts`); fora dele, "dev". */
declare const __VERSAO_SITE__: string | undefined
const VERSAO_SITE = typeof __VERSAO_SITE__ === 'string' ? __VERSAO_SITE__ : 'dev'

/** Um enviador por página aberta: o teto de eventos vale para a página toda. */
const enviarContagem = criarEnviador({
  beacon: (url, corpo) => typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function' && navigator.sendBeacon(url, corpo),
  fetch: typeof fetch === 'function' ? (url, init) => fetch(url, init) : undefined,
})

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

export type Variante = 'cartao' | 'barra' | 'monitor'

/** As cidades do cadastro, para "e Gaspar?" antes de os dados do motor carregarem. */
const nomesDoCadastro = Object.values(estacoes.rios).flatMap((r) => r.cidades.map((c) => ({ id: c.id, nome: c.nome })))

export default function ChatLocal({ rio, aoVivo: aoVivoDaPagina = null, variante = 'cartao' }: {
  rio: 'itajai-acu' | 'itajai-mirim'
  aoVivo?: AoVivo | null
  variante?: Variante
}) {
  const compacto = variante !== 'cartao'
  const [dados, setDados] = useState<Dados | null>(null)
  const [falhou, setFalhou] = useState(false)
  // Compacto: os dados só descem quando a pessoa toca na caixa (no Monitor, numa noite de chuva, quem abriu
  // o mapa não paga pelo chat).
  const [visivel, setVisivel] = useState(false)
  const conversa = useConversa()
  const msgs = conversa.msgs
  const setMsgs = mudarMsgs
  const [texto, setTexto] = useState('')
  const [aoVivoProprio, setAoVivoProprio] = useState<AoVivo | null>(null)
  const aoVivo = aoVivoDaPagina ?? aoVivoProprio
  // Os pedidos da 2ª entrega ("quais leituras estão atrasadas?") leem as leituras ao vivo: esperam a primeira
  // busca terminar, com limite, em vez de responder com dado que ainda não chegou.
  const aoVivoRef = useRef<AoVivo | null>(null)
  aoVivoRef.current = aoVivo
  const esperasAoVivo = useRef(new Set<() => void>())
  useEffect(() => {
    esperasAoVivo.current.forEach((f) => f())
  }, [aoVivo])
  const obterAoVivo = useCallback(
    () =>
      new Promise<AoVivo | null>((resolver) => {
        const pronto = () => {
          const v = aoVivoRef.current
          return v && v.tempoReal.situacao !== 'carregando' && v.serie.situacao !== 'carregando' ? v : null
        }
        const ja = pronto()
        if (ja) return resolver(ja)
        setVisivel(true)
        const ouvir = () => {
          const v = pronto()
          if (!v) return
          esperasAoVivo.current.delete(ouvir)
          clearTimeout(limite)
          resolver(v)
        }
        const limite = setTimeout(() => {
          esperasAoVivo.current.delete(ouvir)
          const v = aoVivoRef.current
          resolver(v && v.tempoReal.situacao !== 'carregando' ? v : null)
        }, 12_000)
        esperasAoVivo.current.add(ouvir)
      }),
    [],
  )
  const comandos = useComandos(obterAoVivo)
  const [copiados, setCopiados] = useState<Record<number, 'ok' | 'falhou'>>({})
  // "Limpar" zera a conversa: o "Copiado." de uma mensagem antiga não pode aparecer numa nova.
  useEffect(() => {
    if (msgs.length === 0) setCopiados({})
  }, [msgs.length])
  useLocation() // redesenha ao navegar: o contexto (cidade, Monitor) vem do endereço
  const pendente = useRef<string | null>(null)
  // O servidor está contando? Começa em "não": sem resposta, nada é contado nem prometido.
  const [contando, setContando] = useState(false)
  const [permitido, setPermitido] = useState(() => contagemChatPermitida())
  // A escolha também muda pelo chat ("não contar minhas perguntas"): a caixa acompanha.
  useEffect(() => {
    const atualizar = () => setPermitido(contagemChatPermitida())
    window.addEventListener('enchentes:preferencias', atualizar)
    return () => window.removeEventListener('enchentes:preferencias', atualizar)
  }, [])
  // A IA está ligada no servidor? Começa em "não": sem resposta, o botão não aparece.
  const [comIA, setComIA] = useState(false)
  const [esperandoIA, setEsperandoIA] = useState(false)
  // Piloto do classificador: começa em "não", como a IA.
  const [piloto, setPiloto] = useState(false)
  const [classificando, setClassificando] = useState(false)
  const cadastro = useMemo(() => (dados ? idsDoCadastro(dados.estacoes) : new Set<string>()), [dados])
  const caixa = useRef<HTMLElement>(null)
  const fim = useRef<HTMLDivElement>(null)

  // Chat de página: a barra do topo some enquanto ele estiver montado (a caixa aparece uma vez só).
  useEffect(() => (compacto ? undefined : registrarChatDePagina()), [compacto])

  // Só começa a baixar os JSONs quando a caixa chega a ~600 px da tela (cartão) ou é tocada (compacto).
  useEffect(() => {
    if (compacto) return
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
  }, [compacto])

  // Pergunta feita antes de os dados chegarem: responde assim que chegarem.
  useEffect(() => {
    if (dados && pendente.current) {
      const q = pendente.current
      pendente.current = null
      void perguntar(q, true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dados])

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

  /** Baixa (uma vez) as cotas de rua e a tabela ruas × manchas de Itajaí. Falha: o motor diz "carregando". */
  async function comDadosDeRua(base: Dados): Promise<Dados> {
    const [cotasRuas, ruasManchaItajai] = await Promise.all([
      base.cotasRuas ?? carregarCotasRuas().catch(() => undefined),
      base.ruasManchaItajai ?? carregarRuasManchaItajai().catch(() => undefined),
    ])
    const novo = { ...base, ...(cotasRuas ? { cotasRuas } : {}), ...(ruasManchaItajai ? { ruasManchaItajai } : {}) }
    setDados((atual) => (atual ? { ...atual, ...(cotasRuas ? { cotasRuas } : {}), ...(ruasManchaItajai ? { ruasManchaItajai } : {}) } : atual))
    return novo
  }

  async function perguntar(p: string, jaMostrada = false, refeito = false) {
    const q = p.trim()
    if (!q) return
    setVisivel(true)
    abrirPainel(true)
    // 10ª entrega: "e Gaspar?", "e em 2011?", "de novo" refazem o último pedido com uma troca só, e a tela diz
    // "Entendi como: …" antes de responder. Sem pedido anterior (ou com duas cidades nele), pergunta.
    // 19ª entrega: a memória da conversa (a última cidade citada, o último pedido como foi entendido) é separada da
    // tela; uma continuação que MUDARIA A TELA ("mostrar Blumenau" → "e Gaspar?") pede confirmação em vez de navegar.
    const nomes = dados ? cidadesConhecidas(dados) : nomesDoCadastro
    const memoria = memoriaDaConversa(lerConversa().msgs.filter((m) => m.papel === 'usuario').map((m) => m.entendidoComo ?? m.texto), nomes)
    if (!jaMostrada) {
      const d = decidirContinuacao(q, memoria, nomes, comandos.catalogo, contextoComConversa(comandos.contexto(), memoria))
      if (d && d.tipo === 'perguntar') {
        setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }, { papel: 'assistente', texto: d.texto, sugestoes: d.sugestoes }])
        setTexto('')
        rolarAoFim()
        return
      }
      if (d && d.tipo === 'confirmar') {
        setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }, { papel: 'assistente', texto: d.pergunta, sugestoes: d.sugestoes, comando: true }])
        setTexto('')
        rolarAoFim()
        return
      }
      if (d) {
        setMsgs((atual) => [...atual, { papel: 'usuario', texto: q, entendidoComo: d.texto }, { papel: 'assistente', texto: `Entendi como: "${d.texto}".` }])
        setTexto('')
        return perguntar(d.texto, true, true)
      }
    }
    // Pedido ("mostrar Blumenau", "zoom na régua DC-05"): executa e diz o resultado. Não depende dos dados.
    if ((!jaMostrada && comandos.tentar(q, true, memoria)) || (refeito && comandos.tentar(q, false, memoria))) {
      setTexto('')
      rolarAoFim()
      return
    }
    if (!dados) {
      // Ainda carregando: guarda e responde quando os dados chegarem, em vez de engolir a pergunta.
      pendente.current = q
      if (!jaMostrada) setMsgs((atual) => [...atual, { papel: 'usuario', texto: q }])
      setTexto('')
      rolarAoFim()
      return
    }
    // Pergunta sobre rua: baixa as cotas (~3 MB) e as ruas × manchas de Itajaí só agora.
    let base = citaRua(q) ? await comDadosDeRua(dados) : dados
    const r = responder(q, base)
    if (contando && permitido) {
      // O texto `q` não entra aqui: só a intenção e o motivo que o motor classificou.
      const evento = montarEvento({ intencao: r.intencao, falha: r.falha, agora: new Date(), versao: VERSAO_SITE, cidadesDoCadastro: cadastro })
      if (evento) enviarContagem(evento)
    }
    // A barreira do presente vale igual na IA: essa resposta não ganha o botão.
    const paraIA = r.intencao === 'agora' ? undefined : q
    // 9ª entrega: nome de cidade com erro de digitação ("Blumenal") vira "Você quis dizer…?" antes da resposta,
    // com a frase corrigida como sugestão. O motor continua respondendo o que foi escrito; nada é trocado sozinho.
    const dica = corrigirCidade(q, cidadesConhecidas(base))
    const comDica = <T extends { texto: string; sugestoes?: string[] }>(m: T): T =>
      dica ? { ...m, texto: `${textoDaCorrecao(dica, 'pergunta')}\n\n${m.texto}`, sugestoes: [dica.texto, ...(m.sugestoes ?? [])].slice(0, 4) } : m
    const presente = () => respostaDoPresente({ pergunta: q, dados: base, rios: estacoes.rios, aoVivo })
    const doUsuario: Msg[] = jaMostrada ? [] : [{ papel: 'usuario', texto: q }]
    if (r.intencao === 'agora') {
      setMsgs((atual) => [...atual, ...doUsuario, { papel: 'assistente', ...comDica(presente()) }])
      setTexto('')
      rolarAoFim()
      return
    }
    const origem: Origem | null = !piloto || classificando ? null : r.intencao === 'nao_entendi' ? 'nao_entendi' : r.palpite ? 'palpite' : null
    if (!origem) {
      setMsgs((atual) => [...atual, ...doUsuario, { papel: 'assistente', ...comDica({ texto: r.texto, sugestoes: r.sugestoes }), paraIA, ...(r.link ? { link: r.link } : {}) }])
      setTexto('')
      rolarAoFim()
      return
    }
    // Piloto: o motor não entendeu (ou palpitou). Pergunta ao classificador; a resposta sai do motor.
    setMsgs((atual) => [...atual, ...doUsuario])
    setTexto('')
    setClassificando(true)
    rolarAoFim()
    const c = await classificarPergunta((url, init) => fetch(url, init), q, origem)
    if (!('erro' in c) && c.decisao.tipo === 'ok' && c.decisao.classificacao.intencao === 'rua_historico') base = await comDadosDeRua(base)
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

  /** Copia o texto preparado (resumo, link). Sem permissão de área de transferência, diz para selecionar. */
  async function copiar(indice: number, texto: string) {
    let ok = false
    try {
      await navigator.clipboard.writeText(texto)
      ok = true
    } catch {
      try {
        const area = document.createElement('textarea')
        area.value = texto
        area.setAttribute('readonly', '')
        area.style.position = 'fixed'
        area.style.opacity = '0'
        document.body.appendChild(area)
        area.select()
        ok = document.execCommand('copy')
        area.remove()
      } catch {
        ok = false
      }
    }
    setCopiados((c) => ({ ...c, [indice]: ok ? 'ok' : 'falhou' }))
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

  const ctx = comandos.contexto()
  const nomeCidade = comandos.nomeDaCidadeAtual()
  const iniciais = compacto
    ? [
        { rotulo: nomeCidade ? `Situação de ${nomeCidade}` : 'Situação de Blumenau', texto: `como está ${nomeCidade ?? 'Blumenau'}?` },
        ctx.naMonitor
          ? { rotulo: 'Aproximar a régua', texto: ctx.cidadeAtual ? 'aproximar a régua' : 'ver a bacia toda' }
          : { rotulo: `Mostrar ${nomeCidade ?? 'Blumenau'} no mapa`, texto: `mostrar ${nomeCidade ?? 'Blumenau'}` },
        { rotulo: 'O que posso pedir?', texto: 'o que posso pedir?' },
      ]
    : INICIO[rio].map((t) => ({ rotulo: t, texto: t }))
  const exemploPedido = ctx.naMonitor ? 'aproximar a régua' : `mostrar ${nomeCidade ?? 'Blumenau'}`
  const textoContexto = [
    ctx.naMonitor ? 'Monitor' : 'Página',
    nomeCidade ?? (ctx.naMonitor ? 'bacia inteira' : null),
    ctx.reguaAtual ? `régua ${ctx.reguaAtual}` : null,
  ].filter(Boolean).join(' · ')

  const log = (
      <div className={estilos['chat-mensagens']} role="log" aria-live="polite">
        {msgs.length === 0 ? (
          <div className={estilos['chat-sugestoes']}>
            {iniciais.map((s) => (
              <button key={s.rotulo} type="button" disabled={!dados && !compacto} onClick={() => perguntar(s.texto)}>
                {s.rotulo}
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
            {msg.copiar ? (
              <div className={estilos['chat-copiar']}>
                <button type="button" onClick={() => void copiar(i, msg.copiar!)}>
                  Copiar
                </button>
                {copiados[i] ? (
                  <span role="status">{copiados[i] === 'ok' ? 'Copiado.' : 'Não consegui copiar: selecione o texto acima.'}</span>
                ) : null}
              </div>
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
        {conversa.ocupado ? (
          <div className={`${estilos['chat-msg']} ${estilos['chat-assistente']}`} role="status">
            Executando o pedido…
          </div>
        ) : null}
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
  )

  const avisos = (
    <>
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
    </>
  )

  if (compacto) {
    const aberto = conversa.aberto
    const ultimaMsg = msgs.at(-1)
    const ultima = ultimaMsg && ultimaMsg.papel === 'assistente' ? ultimaMsg : null
    return (
      <section
        ref={caixa}
        className={`${estilos.global} ${variante === 'monitor' ? estilos['global-monitor'] : ''}`}
        aria-label="Chat: perguntas e pedidos"
      >
        <form
          className={estilos['global-barra']}
          onSubmit={(e) => {
            e.preventDefault()
            void perguntar(texto)
          }}
        >
          <input
            id={variante === 'monitor' ? 'chat-monitor' : 'chat-global'}
            value={texto}
            maxLength={300}
            enterKeyHint="send"
            autoComplete="off"
            // No Monitor, a caixa é a pílula da maquete (07/10/2026): "Cidade, régua ou pergunta" — o que ela
            // aceita, numa linha que cabe no celular. Fora dele, o convite com o exemplo de pedido.
            placeholder={variante === 'monitor' ? 'Cidade, régua ou pergunta' : nomeCidade ? `Pergunte sobre ${nomeCidade} ou peça: ${exemploPedido}` : `Pergunte ou peça: ${exemploPedido}`}
            onFocus={() => {
              setVisivel(true)
              abrirPainel(true)
            }}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') abrirPainel(false)
            }}
            aria-label="Pergunte ou peça"
            aria-controls="chat-painel"
            aria-expanded={aberto}
          />
          <button type="submit" disabled={!texto.trim() || conversa.ocupado || classificando}>
            Enviar
          </button>
        </form>
        {visivel && !aoVivoDaPagina ? <AoVivoDoChat aoMudar={setAoVivoProprio} /> : null}
        {!aberto && ultima ? (
          <div className={estilos['global-ultima']}>
            <p role="status">{ultima.texto}</p>
            <button type="button" onClick={() => abrirPainel(true)}>
              Ver conversa ({msgs.length})
            </button>
          </div>
        ) : null}
        {aberto ? (
          <div id="chat-painel" className={estilos['global-painel']}>
            <div className={estilos['global-cabeca']}>
              <span className={estilos['global-contexto']}>{textoContexto}</span>
              <span className={estilos['global-aviso']}>
                Não é alerta. Emergência: <strong>199</strong>.
              </span>
              <span className={estilos['global-acoes']}>
                {msgs.length > 0 ? (
                  <button type="button" onClick={limparConversa}>
                    Limpar
                  </button>
                ) : null}
                <button type="button" onClick={() => abrirPainel(false)} aria-label="Recolher a conversa">
                  Recolher
                </button>
              </span>
            </div>
            {falhou ? (
              <p className={estilos['chat-erro']} role="alert">
                Não foi possível carregar os dados das perguntas. Os pedidos de mapa continuam funcionando.
              </p>
            ) : null}
            {log}
            {avisos}
          </div>
        ) : null}
      </section>
    )
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

      {log}

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

      {avisos}
    </section>
  )
}
