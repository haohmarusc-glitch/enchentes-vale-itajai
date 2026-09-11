import { Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Municipal from './telas/Municipal'
import estilos from './App.module.css'
import FaixaEmergencia from './componentes/FaixaEmergencia'
import LimiteDeErro from './componentes/LimiteDeErro'
import Rodape from './componentes/Rodape'
import Inicio from './telas/Inicio'
import TelaCidade from './telas/TelaCidade'
import MonitorBacia from './telas/MonitorBacia'
import TelaItajai from './telas/TelaItajai'
import TelaRio from './telas/TelaRio'

const ABAS = [
  { para: '/', rotulo: 'Início', fim: true },
  { para: '/monitor', rotulo: 'Monitor', fim: false },
  { para: '/acu', rotulo: 'Itajaí-Açu', fim: false },
  { para: '/mirim', rotulo: 'Itajaí-Mirim', fim: false },
  { para: '/itajai', rotulo: 'Itajaí (foz)', fim: false },
]

export default function App() {
  const local = useLocation()
  const municipal = local.pathname.startsWith('/municipal/ascurra')
  return (
    <>
      {/* Primeiro elemento focável da página: quem navega por teclado ou leitor
          de tela pula o cabeçalho e as cinco abas de uma vez. Fica invisível
          até receber foco. */}
      <a href="#conteudo" className={estilos.pularParaConteudo}>
        Pular para o conteúdo
      </a>
      {!municipal && <FaixaEmergencia />}
      {!municipal && <header className={estilos.cabecalho}>
        <div className={estilos.faixa}>
          <NavLink to="/" className={estilos.marca}>
            Enchentes do Vale do Itajaí
          </NavLink>
          <nav aria-label="Rios">
            <ul className={estilos.abas}>
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
          <Routes>
            <Route path="/municipal/ascurra" element={<MonitorBacia municipal />} />
            <Route path="/municipal/ascurra/dados" element={<Municipal />} />
            <Route path="/" element={<Inicio />} />
            <Route path="/monitor" element={<MonitorBacia />} />
            {/* O mesmo Monitor, aberto numa cidade. Rota própria para ser um
                endereço que se dita por telefone durante a chuva. */}
            <Route path="/monitor/:cidadeId" element={<MonitorBacia />} />
            <Route path="/acu" element={<TelaRio rioId="itajai-acu" />} />
            {/* Uma página por cidade. `rioId` vem na URL para o endereço ser
                compartilhável: `/acu/gaspar` é um endereço; "abra o Açu e toque
                em Gaspar" não é. */}
            <Route path="/:rioId/:cidadeId" element={<TelaCidade />} />
            <Route path="/mirim" element={<TelaRio rioId="itajai-mirim" />} />
            <Route path="/itajai" element={<TelaItajai />} />
              <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </LimiteDeErro>
      </main>

      {!municipal && <Rodape />}
    </>
  )
}
