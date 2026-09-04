import { Navigate, NavLink, Route, Routes } from 'react-router-dom'
import estilos from './App.module.css'
import FaixaEmergencia from './componentes/FaixaEmergencia'
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
  return (
    <>
      <FaixaEmergencia />
      <header className={estilos.cabecalho}>
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
      </header>

      <main className="conteudo">
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/monitor" element={<MonitorBacia />} />
          <Route path="/acu" element={<TelaRio rioId="itajai-acu" />} />
          {/* Uma página por cidade. `rioId` vem na URL para o endereço ser
              compartilhável: `/acu/gaspar` é um endereço; "abra o Açu e toque
              em Gaspar" não é. */}
          <Route path="/:rioId/:cidadeId" element={<TelaCidade />} />
          <Route path="/mirim" element={<TelaRio rioId="itajai-mirim" />} />
          <Route path="/itajai" element={<TelaItajai />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <Rodape />
    </>
  )
}
