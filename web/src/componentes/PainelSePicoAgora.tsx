import type { Cidade, Trecho } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
import { ROTULO_CONFIANCA_TRECHO, dataHora, metros, rotuloCota } from '../logica/formato'
import { faixaHoras } from '../logica/transito'
import {
  MIN_AGORA,
  chegadasSePicoAgora,
  foraDeOrdem,
  frescor,
  idadeMin,
  primeiraCota,
  textoIdade,
} from '../logica/tempoReal'
import estilos from './PainelSePicoAgora.module.css'

/**
 * Quando a cheia chegaria a jusante SE o pico fosse agora.
 *
 * O "se" carrega o painel inteiro. O tempo de descida é medido de pico a pico:
 * saber que o rio está em 8,20 m não diz que 8,20 m é o pico — ele pode subir
 * por mais horas, e aí tudo se desloca. A conta responde a uma pergunta
 * condicional, e a tela precisa dizer isso com todas as letras em vez de
 * apresentar horários como se fossem previsão.
 *
 * Só roda com leitura fresca. Calcular chegada a partir de um número de horas
 * atrás produziria horários que já passaram, com cara de previsão.
 */
export default function PainelSePicoAgora({
  rioId,
  cidades,
  trechos,
  origem,
  leitura,
  agora,
}: {
  rioId: string
  cidades: Cidade[]
  trechos: Trecho[]
  origem: Cidade
  leitura: LeituraAoVivo
  agora: Date
}) {
  if (!leitura.medidoEm) return null

  const idade = idadeMin(leitura.medidoEm, agora)
  if (frescor(idade) !== 'agora') {
    return (
      <section className="cartao" aria-labelledby="pico-agora-titulo">
        <h2 id="pico-agora-titulo">Se o pico fosse agora</h2>
        <p className={estilos.recusa}>
          A última leitura de {origem.nome} é de <strong>{textoIdade(idade)}</strong>, e o cálculo
          de chegada só roda com leitura de até {MIN_AGORA} minutos. Com dado velho os horários
          sairiam já vencidos, com cara de previsão. Confira o nível direto na fonte oficial.
        </p>
      </section>
    )
  }

  const chegadas = chegadasSePicoAgora(trechos, rioId, cidades, origem, leitura.medidoEm)
  if (chegadas.length === 0) return null
  // Fontes de trânsito que não concordam entre si podem produzir uma cidade
  // recebendo a água antes de outra que fica acima dela. Isso é dito, não
  // escondido: empurrar horário para arrumar a ordem inventaria precisão.
  const desordenado = foraDeOrdem(chegadas)

  const cota = primeiraCota(origem)
  const acimaDaCota = cota !== null && leitura.nivel_m >= cota.valor

  return (
    <section className="cartao" aria-labelledby="pico-agora-titulo">
      <h2 id="pico-agora-titulo">Se o pico em {origem.nome} fosse agora</h2>

      <p className={estilos.condicao}>
        {origem.nome} está em <strong>{metros(leitura.nivel_m)}</strong> ({textoIdade(idade)}).{' '}
        {acimaDaCota && cota ? (
          <>
            Já passou da cota de {rotuloCota(cota.chave)} ({metros(cota.valor)}).
          </>
        ) : cota ? (
          <>Ainda abaixo da cota de {rotuloCota(cota.chave)} ({metros(cota.valor)}).</>
        ) : null}
      </p>

      <p className={estilos.se}>
        <strong>Isto é uma conta condicional.</strong> O tempo de descida é de pico a pico, e o
        rio pode continuar subindo por horas — nesse caso tudo abaixo se desloca junto. Os
        horários valem <em>se</em> o pico for este.
      </p>

      <ul className={estilos.lista}>
        {chegadas.map((c) => (
          <li key={c.cidade.id}>
            <span className={estilos.cidade}>{c.cidade.nome}</span>
            <span className={estilos.janela}>
              {c.trecho.horasMin === c.trecho.horasMax ? (
                <>por volta de {dataHora(c.inicio)}</>
              ) : (
                <>
                  entre {dataHora(c.inicio)} e {dataHora(c.fim)}
                </>
              )}
            </span>
            <span className={estilos.trecho}>
              {faixaHoras(c.trecho)}
              {!c.trecho.direto ? ` · soma de ${c.trecho.trechos.length} trechos` : ''}
              {` · ${ROTULO_CONFIANCA_TRECHO[c.trecho.confianca].toLowerCase()}`}
            </span>
          </li>
        ))}
      </ul>

      {desordenado ? (
        <p className={estilos.desordem} role="note">
          <strong>Os horários acima não estão em ordem de rio abaixo.</strong> Os tempos de
          descida vêm de fontes diferentes que não concordam entre si, e por isso alguma cidade
          aparece recebendo a água antes de outra que fica acima dela. Leia cada linha como a
          estimativa daquele trecho, não como uma sequência.
        </p>
      ) : null}

      <p className={estilos.ressalva}>
        A conta não prevê altura, só horário — e ignora a chuva que cair no caminho, manobra de
        barragem e, em Itajaí, a maré. Em emergência, ligue 199.
      </p>
    </section>
  )
}
