import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App'
import './estilos/global.css'

const raiz = document.getElementById('root')
if (!raiz) throw new Error('Elemento #root não encontrado.')

createRoot(raiz).render(
  <StrictMode>
    {/* HashRouter: o site é estático (GitHub Pages), sem servidor para reescrever rotas. */}
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>,
)
