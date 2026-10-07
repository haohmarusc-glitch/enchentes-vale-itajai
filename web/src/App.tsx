import { useEffect, useLayoutEffect, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useLocation, useNavigationType } from 'react-router-dom'
import Municipal from './telas/Municipal'
import estilos from './App.module.css'
import AvisoLegal from './componentes/AvisoLegal'
import { AvisosDoAplicativo, FaixaTopo, FolhaAviso, NavPrincipal, useEscopoApp } from './componentes/Casca'
import FaixaEmergencia from './componentes/FaixaEmergencia'
import { useAvisoLido, useLetra } from './dados/usarPreferencias'
import LimiteDeErro from './componentes/LimiteDeErro'
import Rodape from './componentes/Rodape'
import ChatNoTopo from './componentes/ChatNoTopo'
import Inicio from './telas/Inicio'
import TelaCidade from './telas/TelaCidade'
import MonitorBacia from './telas/MonitorBacia'
import TelaItajai from './telas/TelaItajai'
import TelaRio from './telas/TelaRio'
import TelaPerguntas from './telas/TelaPerguntas'
import TelaAcessos from './telas/TelaAcessos'

const ABAS = [
  { para: '/', rotulo: 'Início', fim: true },
  { para: '/monitor', rotulo: 'Monitor', fim: false },
  { para: '/acu', rotulo: 'Itajaí-Açu', fim: false },
  { para: '/mirim', rotulo: 'Itajaí-Mirim', fim: false },
  { para: '/itajai', rotulo: 'Itajaí (foz)', fim: false },
]

/**
 * Rotas que ficam com a casca ANTIGA (decisão D2, opção ③, 03/10/2026): o
 * Monitor soma à mão a altura da faixa e do cabeçalho de antes para dimensionar
 * o mapa, e o piloto municipal não tem casca nenhuma. A trava
 * `testes-navegador/trava-monitor.mjs` reprova qualquer mudança aqui.
 */
export function cascaAntiga(caminho: string): boolean {
  return caminho === '/monitor' || caminho.startsWith('/monitor/') || caminho.startsWith('/municipal/ascurra')
}

export default function App() {
  const local = useLocation()
  const municipal = local.pathname.startsWith('/municipal/ascurra')
  const antiga = cascaAntiga(local.pathname)
  /**
   * Casca antiga no CELULAR (redesenho do Monitor, etapa 1 — docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md):
   * as abas saem do topo e viram este menu (☰), para o mapa ganhar a tela. No computador o CSS esconde o
   * botão e mostra as abas como sempre. Trocar de página fecha o menu.
   */
  const [menuPaginas, setMenuPaginas] = useState(false)
  useEffect(() => setMenuPaginas(false), [local.pathname])
  const paginaAtual = ABAS.find((a) => (a.fim ? local.pathname === a.para : local.pathname.startsWith(a.para)))?.rotulo ?? null
  const [letra] = useLetra()
  useEscopoApp(!antiga, letra)
  const [avisoLido, marcarAvisoLido] = useAvisoLido()
  // A folha do aviso completo abre sozinha na primeira visita e pelo "saiba mais".
  const [folhaPedida, setFolhaPedida] = useState(false)
  const folhaAberta = !antiga && (folhaPedida || !avisoLido)

  if (!antiga) {
    return (
      <>
        <a href="#conteudo" className={estilos.pularParaConteudo} onClick={(e) => {
            e.preventDefault()
            document.getElementById('conteudo')?.focus()
            document.getElementById('conteudo')?.scrollIntoView({ block: 'start' })
          }}>
          Pular para o conteúdo
        </a>
        <FaixaTopo aoSaberMais={() => setFolhaPedida(true)} />
        <NavPrincipal />
        <AvisosDoAplicativo />
        <main className="conteudo" id="conteudo" tabIndex={-1}>
          {/* O chat no topo de toda página, antes do conteúdo (docs/CHAT-GLOBAL-COMANDOS.md). No Monitor,
              ele fica dentro do bloco do topo do mapa, pela casca antiga. */}
          <ChatNoTopo variante="barra" />
          <LimiteDeErro oQue="esta tela">
            <RolarAoTopo />
            <Rotas />
          </LimiteDeErro>
          {/* O aviso completo continua em TODA tela (regra do CLAUDE.md, D1):
              no fim, para não tapar o nível, que é o que a pessoa veio ver. */}
          <AvisoLegal />
        </main>
        <Rodape />
        <FolhaAviso
          aberta={folhaAberta}
          aoFechar={() => setFolhaPedida(false)}
          aoEntender={() => {
            marcarAvisoLido()
            setFolhaPedida(false)
          }}
        />
      </>
    )
  }

  return (
    <>
      {/* Primeiro elemento focável da página: quem navega por teclado ou leitor
          de tela pula o cabeçalho e as cinco abas de uma vez. Fica invisível
          até receber foco. */}
      <a href="#conteudo" className={estilos.pularParaConteudo} onClick={(e) => {
          e.preventDefault()
          document.getElementById('conteudo')?.focus()
          document.getElementById('conteudo')?.scrollIntoView({ block: 'start' })
        }}>
        Pular para o conteúdo
      </a>
      {!municipal && <FaixaEmergencia />}
      {!municipal && <header className={estilos.cabecalho}>
        <div className={estilos.faixa}>
          <button
            type="button"
            className={estilos.botaoMenuPaginas}
            aria-label={menuPaginas ? 'Fechar o menu de páginas' : 'Menu de páginas'}
            aria-expanded={menuPaginas}
            aria-controls="menu-paginas"
            onClick={() => setMenuPaginas((v) => !v)}
          >
            <span aria-hidden="true">{menuPaginas ? '✕' : '☰'}</span>
          </button>
          <NavLink to="/" className={estilos.marca}>
            Enchentes do Vale do Itajaí
          </NavLink>
          {paginaAtual ? <span className={estilos.paginaAtual} aria-hidden="true">{paginaAtual}</span> : null}
          <nav aria-label="Rios" onKeyDown={(e) => { if (e.key === 'Escape') setMenuPaginas(false) }}>
            <ul id="menu-paginas" className={`${estilos.abas} ${menuPaginas ? estilos.abasAbertas : ''}`}>
              {ABAS.map((aba) => (
                <li key={aba.para}>
                  <NavLink
                    to={aba.para}
                    end={aba.fim}
                    className={({ isActive }) =>
                      isActive ? `${estilos.aba} ${estilos.abaAtiva}` : estilos.aba
                    }
                  >
                    {aba.rotulo}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>}

      <main className="conteudo" id="conteudo" tabIndex={-1} style={local.pathname === '/municipal/ascurra' ? { maxWidth: 'none', padding: 0, margin: 0 } : undefined}>
        {/* O limite fica AQUI, em volta do conteúdo — e não em volta do site
            inteiro. Se uma tela quebrar, é ela que cai: a FaixaEmergencia acima
            continua na tela com o 199, que é o motivo de ela existir. */}
        <LimiteDeErro oQue="esta tela">
          <Rotas />
        </LimiteDeErro>
      </main>

      {!municipal && <Rodape />}
    </>
  )
}

/**
 * Página nova começa no topo (04/10/2026).
 *
 * Achado no celular do Jefferson: na Início de Itajaí, "Minha rua alaga?" levava à
 * tela da foz, e ela abria na mesma rolagem da página anterior — parecia que o
 * botão só mexia a tela. Trocar de página (o caminho, não a aba `?aba=`) volta ao
 * topo. O "voltar" do navegador (POP) fica com a rolagem que o navegador guardar.
 * Só na casca nova: o Monitor (casca antiga) não muda (D2).
 *
 * `useLayoutEffect` de propósito: roda antes do `useEffect` das telas, então uma
 * tela que pede para rolar até uma seção (`/itajai?secao=manchas`) rola DEPOIS
 * deste topo, e não é desfeita por ele.
 */
function RolarAoTopo() {
  const { pathname } = useLocation()
  const tipo = useNavigationType()
  useLayoutEffect(() => {
    if (tipo !== 'POP') window.scrollTo(0, 0)
  }, [pathname, tipo])
  return null
}

function Rotas() {
  return (
    <Routes>
      <Route path="/municipal/ascurra" element={<MonitorBacia municipal />} />
      <Route path="/municipal/ascurra/dados" element={<Municipal />} />
      <Route path="/" element={<Inicio />} />
      <Route path="/monitor" element={<MonitorBacia />} />
      {/* O mesmo Monitor, aberto numa cidade. Rota própria para ser um
          endereço que se dita por telefone durante a chuva. */}
      <Route path="/monitor/:cidadeId" element={<MonitorBacia />} />
      <Route path="/acu" element={<TelaRio key="acu" rioId="itajai-acu" />} />
      {/* Uma página por cidade. `rioId` vem na URL para o endereço ser
          compartilhável: `/acu/gaspar` é um endereço; "abra o Açu e toque
          em Gaspar" não é. */}
      <Route path="/:rioId/:cidadeId" element={<TelaCidade />} />
      <Route path="/mirim" element={<TelaRio key="mirim" rioId="itajai-mirim" />} />
      <Route path="/itajai" element={<TelaItajai />} />
      <Route path="/perguntas" element={<TelaPerguntas />} />
      {/* Só para o admin; a API responde 404 a qualquer outro e a tela diz "não encontrada". */}
      <Route path="/admin/acessos" element={<TelaAcessos />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
