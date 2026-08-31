import { useMemo, useState } from 'react'
import type { Cidade } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
// A tabela vem daqui, e não por propriedade: assim ela viaja no mesmo pedaço
// que este componente, que só é carregado quando a busca aparece na tela.
import { avisosCotasRuas, cotasRuas } from '../dados/cotasRuas'
import {
  atingidas,
  buscar,
  daCidade,
  faixaDaCidade,
  faltaPara,
  nomeCompleto,
  proximas,
} from '../logica/cotasRuas'
import { metros } from '../logica/formato'
import estilos from './CotasDeRua.module.css'

interface Props {
  cidade: Cidade
  /** Nível ao vivo da cidade, quando existe uma régua só. */
  leitura: LeituraAoVivo | null
}

/**
 * "A minha rua alaga com quantos metros?"
 *
 * É a pergunta que a pessoa realmente faz. Todo o resto do site responde em
 * metros de régua, que é a linguagem de quem opera o rio, não de quem mora
 * perto dele.
 *
 * Duas partes: busca pelo nome da rua, e um controle deslizante para ver a
 * cidade em qualquer nível — inclusive acima do atual, que é a pergunta
 * "e se continuar subindo".
 *
 * O que este componente NÃO faz, e não deve passar a fazer: prever se o rio vai
 * chegar naquele nível. Ele lê uma tabela. A tabela diz o que acontece SE o rio
 * chegar lá; quem diz se vai chegar é a Defesa Civil.
 */
export default function CotasDeRua({ cidade, leitura }: Props) {
  const cotas = cotasRuas
  const avisos = avisosCotasRuas
  const dela = useMemo(() => daCidade(cotas, cidade.id), [cotas, cidade.id])
  const faixa = useMemo(() => faixaDaCidade(cotas, cidade.id), [cotas, cidade.id])
  const [termo, setTermo] = useState('')
  const [simulado, setSimulado] = useState<number | null>(null)

  if (dela.length === 0) return null

  const nivelAtual = leitura?.nivel_m ?? null
  // O controle começa no nível de agora quando ele existe; sem leitura ao vivo,
  // na cota mais baixa levantada — o primeiro ponto em que algo acontece.
  const nivel = simulado ?? nivelAtual ?? faixa?.min ?? 0
  const achadas = buscar(cotas, cidade.id, termo)
  const jaAlagam = atingidas(cotas, cidade.id, nivel)
  const seguintes = proximas(cotas, cidade.id, nivel, 4)
  const semCota = dela.filter((c) => c.cota_m === null)

  const piso = faixa ? Math.max(0, Math.floor((faixa.min - 1) * 10) / 10) : 0
  const teto = faixa ? Math.ceil((faixa.max + 1) * 10) / 10 : 10

  return (
    <section className="cartao">
      <h2>A minha rua alaga com quantos metros? — {cidade.nome}</h2>

      <p className={estilos.regua}>
        Os números abaixo são o nível na régua de {cidade.nome}
        {cidade.regua ? ` (${cidade.regua})` : ''}. <strong>Não se comparam</strong> com os de
        outra cidade.
      </p>

      <label className={estilos.rotulo} htmlFor={`busca-${cidade.id}`}>
        Procure a sua rua
      </label>
      <input
        id={`busca-${cidade.id}`}
        className={estilos.busca}
        type="search"
        value={termo}
        placeholder="nome da rua ou do bairro"
        autoComplete="off"
        onChange={(e) => setTermo(e.target.value)}
      />

      {termo.trim().length >= 2 ? (
        achadas.length > 0 ? (
          <ul className={estilos.resultados}>
            {achadas.map((c, i) => (
              <li key={`${c.rua}-${c.ponto ?? i}`} className={estilos.resultado}>
                <span className={estilos.nomeRua}>{nomeCompleto(c)}</span>
                {c.bairro ? <span className={estilos.bairro}>{c.bairro}</span> : null}
                {c.cota_m !== null ? (
                  <>
                    <span className={estilos.cota}>
                      alaga a partir de {metros(c.cota_m)}
                      {/* A máxima é informação, não gatilho: quem decide sair
                          de casa decide pela mínima, que é quando a água
                          chega. */}
                      {c.cota_max_m !== undefined
                        ? ` · toda a rua a ${metros(c.cota_max_m)}`
                        : ''}
                    </span>
                    {/* Registro marcado para não mover aviso não vira "já foi
                        alcançado": seria uma frase assustadora tirada de um
                        número que o próprio registro diz não estar conferido. */}
                    {nivelAtual !== null && c.usar_para_aviso !== false ? (
                      <span className={estilos.falta}>
                        {faltaPara(c.cota_m, nivelAtual) > 0
                          ? `faltam ${metros(faltaPara(c.cota_m, nivelAtual))} de subida`
                          : 'este nível já foi alcançado'}
                      </span>
                    ) : null}
                    {/* A nota sai JUNTO do número, e não só quando ele falta.
                        Rio do Sul publica ruas alagando abaixo da menor cota
                        da cidade: sem a ressalva ao lado, "este nível já foi
                        alcançado" apareceria num dia de sol. */}
                    {c.nota ? <span className={estilos.ressalva}>{c.nota}</span> : null}
                  </>
                ) : (
                  <span className={estilos.semNumero}>{c.nota ?? 'cota não publicada'}</span>
                )}
                <span className={estilos.fonte}>
                  {c.fonte} · {c.data_fonte} · confiança {c.confianca}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className={estilos.vazio}>
            Nenhuma rua com esse nome entre as {dela.length} levantadas em {cidade.nome}.{' '}
            <strong>Isso não quer dizer que a sua rua não alaga</strong> — quer dizer que ela não
            está nesta lista, que está longe de completa.
          </p>
        )
      ) : null}

      <hr className={estilos.divisor} />

      <label className={estilos.rotulo} htmlFor={`simulador-${cidade.id}`}>
        E se o rio estivesse em…
      </label>
      <div className={estilos.controle}>
        <input
          id={`simulador-${cidade.id}`}
          type="range"
          min={piso}
          max={teto}
          step={0.05}
          value={nivel}
          onChange={(e) => setSimulado(Number(e.target.value))}
        />
        <output className={estilos.valor}>{metros(nivel)}</output>
      </div>
      {simulado !== null && nivelAtual !== null ? (
        <button type="button" className={estilos.voltar} onClick={() => setSimulado(null)}>
          voltar para o nível de agora ({metros(nivelAtual)})
        </button>
      ) : null}

      <p className={estilos.contagem}>
        A {metros(nivel)}, <strong>{jaAlagam.length}</strong> de {dela.length} ruas conhecidas
        {jaAlagam.length === 1 ? ' já estaria alagada' : ' já estariam alagadas'} em {cidade.nome}.
      </p>

      {jaAlagam.length > 0 ? (
        <ul className={estilos.lista}>
          {jaAlagam.map((c, i) => (
            <li key={`a-${c.rua}-${c.ponto ?? i}`}>
              <span className={estilos.nomeRua}>{nomeCompleto(c)}</span>
              <span className={estilos.cota}>{metros(c.cota_m!)}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {seguintes.length > 0 ? (
        <>
          <p className={estilos.rotuloLista}>As próximas, se continuar subindo:</p>
          <ul className={estilos.lista}>
            {seguintes.map((c, i) => (
              <li key={`p-${c.rua}-${c.ponto ?? i}`} className={estilos.proxima}>
                <span className={estilos.nomeRua}>{nomeCompleto(c)}</span>
                <span className={estilos.cota}>
                  {metros(c.cota_m!)} · faltam {metros(faltaPara(c.cota_m!, nivel))}
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {semCota.length > 0 ? (
        <p className={estilos.semNumeroBloco}>
          Outras {semCota.length} ruas de {cidade.nome} são citadas pela fonte sem cota exata, e por
          isso ficam fora destas contas. Elas aparecem na busca acima.
        </p>
      ) : null}

      <ul className={estilos.avisos}>
        {avisos.map((a) => (
          <li key={a}>{a}</li>
        ))}
      </ul>
    </section>
  )
}
