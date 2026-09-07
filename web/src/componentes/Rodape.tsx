import { fontesGerais, fontesGeraisEstado } from '../dados/carregar'
import { comoMostrar } from '../logica/fontesDoRodape'
import estilos from './Rodape.module.css'

const ROTULOS: Record<string, string> = {
  ana_hidroweb: 'ANA / HidroWeb — séries históricas',
  defesa_civil_sc: 'Defesa Civil de SC — monitoramento',
  ceops_furb_acervo: 'CEOPS/FURB — acervo de picos',
  epagri_ciram: 'Epagri/Ciram — rios',
  mare_itajai: 'Maré em Itajaí',
  ana_api_acesso: 'Acesso à API da ANA',
}

export default function Rodape() {
  return (
    <footer className={estilos.rodape}>
      <div className={estilos.dentro}>
        <h2 className={estilos.titulo}>Fontes dos dados</h2>
        <ul className={estilos.lista}>
          {Object.entries(fontesGerais).map(([chave, valor]) => {
            const mostrar = comoMostrar(chave, valor, fontesGeraisEstado)
            return (
              <li key={chave}>
                {ROTULOS[chave] ?? chave}:{' '}
                {mostrar.tipo === 'link' ? (
                  <a href={mostrar.href} target="_blank" rel="noreferrer">
                    {mostrar.href}
                  </a>
                ) : mostrar.tipo === 'fora_do_ar' ? (
                  <span className={estilos.foraDoAr}>
                    <span className={estilos.endereco}>{mostrar.endereco}</span>{' '}
                    <strong>— fora do ar</strong>
                    <span className={estilos.motivo}>{mostrar.observado}</span>
                  </span>
                ) : (
                  valor
                )}
              </li>
            )
          })}
        </ul>
        <p className={estilos.nota}>
          Projeto aberto e não oficial. Os dados vêm dos arquivos em <code>data/</code> do
          repositório; cada número na tela mostra sua fonte e seu grau de confiança. Encontrou um
          valor errado? Ele provavelmente está errado no arquivo — corrigir lá corrige o site.
        </p>
      </div>
    </footer>
  )
}
