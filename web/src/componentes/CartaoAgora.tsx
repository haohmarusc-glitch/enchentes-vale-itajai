import type { ReactNode } from 'react'
import type { Cidade } from '../dados/tipos'
import type { AoVivo, EstadoDaCidade } from '../dados/usarAoVivo'
import { tendencia as tendenciaDaSerie } from '../dados/serie'
import { distancia, rotuloDaFaixa, situacaoNasCotas, tendenciaDaLeitura, textoTendencia } from '../logica/agora'
import { metros, numero } from '../logica/formato'
import { faixaAscurra } from '../logica/municipal'
import { frescorDaCidade, idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
import { ROTULO_FAIXA } from './LegendaFaixas'
import MedidorCotas from './MedidorCotas'
import ReguasAgora from './ReguasAgora'
import { todasAsReguas } from '../logica/reguas'
import { estacoesTempoReal } from '../dados/carregar'
import { leiturasDaCidadeEmTodosOsRios } from '../dados/tempoReal'
import estilos from './CartaoAgora.module.css'

/** A classe do chip: inundação e emergência são o mesmo vermelho; sem leitura e várias réguas, cinza. */
export function classeDoChip(faixa: Faixa): string {
  if (faixa === 'inundacao' || faixa === 'emergencia') return estilos.chip_perigo!
  if (faixa === 'sem-dado' || faixa === 'varias') return estilos.chip_semDado!
  return estilos[`chip_${faixa}`] ?? ''
}

/** O nome da faixa no chip, com a palavra da Defesa Civil da cidade (D6). */
export function nomeDaFaixa(faixa: Faixa, cidade: Cidade): string {
  return rotuloDaFaixa(faixa, cidade, ROTULO_FAIXA[faixa])
}

/** Os nomes da escala da Defesa Civil de SC (`rio_alarmes`), como ela publica. */
const NOME_ESTADUAL: Partial<Record<Faixa, string>> = {
  normal: 'Normal',
  atencao: 'Atenção',
  alerta: 'Alerta',
  emergencia: 'Emergência',
}

/**
 * O chip da faixa. Com `estadual`, a faixa é a que a Defesa Civil de SC publica
 * para a estação dela — o chip diz isso no próprio texto e tem borda tracejada,
 * como o pino estadual do Monitor, para não passar por faixa da cidade.
 */
export function ChipFaixa({
  faixa,
  cidade,
  compacto = false,
  estadual = false,
}: {
  faixa: Faixa
  cidade: Cidade
  compacto?: boolean
  estadual?: boolean
}) {
  return (
    <span
      className={`${estilos.chip} ${classeDoChip(faixa)} ${compacto ? estilos.chipCompacto : ''} ${estadual ? estilos.chipEstadual : ''}`}
    >
      <span className={estilos.ponto} aria-hidden="true" />
      {estadual ? `${NOME_ESTADUAL[faixa] ?? ROTULO_FAIXA[faixa]} · Defesa Civil SC` : nomeDaFaixa(faixa, cidade)}
    </span>
  )
}

/**
 * O CARTÃO "AGORA" — o que a pessoa abriu o site para ver, na primeira tela.
 *
 * Ordem fixa, e cada linha só aparece quando se sustenta:
 *  1. a faixa (cor + NOME, nunca só cor) e a idade da medição, juntas;
 *  2. o número grande, com a seta de tendência só quando a série descreve
 *     ESTA leitura (D7);
 *  3. a frase em português simples, só com leitura de agora (`situacaoNasCotas`);
 *  4. a ressalva das cotas da cidade, ANTES dos números delas;
 *  5. a régua desenhada, na escala da própria cidade, e o lembrete de que os
 *     metros não se comparam com os de outra.
 *
 * Sem leitura, o cartão diz isso com todas as letras: cartão vazio parece
 * normalidade, e normalidade é a afirmação mais perigosa que o site pode fazer
 * sem medir. O número NÃO anima quando atualiza — no meio de uma animação ele
 * pode ser lido errado; troca seco, e o leitor de tela é avisado.
 */
export default function CartaoAgora({
  cidade,
  aoVivo,
  estado,
  titulo,
  children,
}: {
  cidade: Cidade
  aoVivo: AoVivo
  estado: EstadoDaCidade
  /** Título visível acima do número (no Início, o nome da cidade já está fora). */
  titulo?: ReactNode
  children?: ReactNode
}) {
  const { agora, tempoReal } = aoVivo
  const { leitura, faixa, bruto, varias, todas, serie, estadual, faixaEstadual } = estado
  const carregando = tempoReal.situacao === 'carregando' && !leitura && !bruto && todas.length === 0

  if (carregando) {
    return (
      <section className={`${estilos.cartao}`} aria-busy="true" aria-label={`Carregando o nível de ${cidade.nome}`}>
        <div className={estilos.topo}>
          <span className={`esqueleto ${estilos.esqChip}`} />
          <span className={estilos.medido}>buscando a leitura…</span>
        </div>
        <span className={`esqueleto ${estilos.esqNumero}`} />
        <span className={`esqueleto ${estilos.esqFrase}`} />
        <MedidorCotas cidade={cidade} nivel={null} />
        <p className={estilos.regua}>
          Na <strong>régua de {cidade.nome}</strong>. Metros de outra cidade não se comparam com estes.
        </p>
      </section>
    )
  }

  if (!leitura) {
    // Várias réguas (Itajaí): TODAS as da cidade, em qualquer curso — o Mirim e
    // os ribeirões também, não só as do rio por onde a cidade foi escolhida.
    const reguas = varias ? todasAsReguas(estacoesTempoReal, cidade.id) : []
    return (
      <section className={`${estilos.cartao} surge`} aria-label={`Agora em ${cidade.nome}`}>
        {titulo}
        <div className={estilos.topo}>
          {bruto && faixaEstadual ? (
            <ChipFaixa faixa={faixaEstadual} cidade={cidade} estadual />
          ) : (
            <ChipFaixa faixa={faixa} cidade={cidade} />
          )}
          {bruto ? (
            <span className={estilos.medido}>
              {bruto.medidoEm ? `medido ${textoIdade(idadeMin(bruto.medidoEm, agora))}` : 'sem horário de medição'}
              {' · '}
              {bruto.codigo ?? bruto.estacao}
            </span>
          ) : null}
        </div>
        {varias ? (
          <>
            {reguas.length > 0 ? (
              <ReguasAgora
                cidade={cidade}
                reguas={reguas}
                leituras={leiturasDaCidadeEmTodosOsRios(tempoReal, cidade.id)}
                agora={agora}
              />
            ) : (
              <p className={estilos.semLeitura}>
                {todas.length} réguas nesta cidade, cada uma com o seu zero — os metros não se
                comparam entre elas.
              </p>
            )}
          </>
        ) : bruto ? (
          <>
            <p className={estilos.linhaNumero} aria-live="polite">
              <span
                className={`${estilos.numero} ${
                  !bruto.medidoEm || frescorDaCidade(idadeMin(bruto.medidoEm, agora), cidade.id) === 'velha'
                    ? estilos.numeroVelho
                    : ''
                }`}
              >
                {numero(bruto.nivelBrutoM)}
              </span>
              <span className={estilos.unidade}>m</span>
            </p>
            <p className={estilos.estadual}>
              Nível da <strong>rede estadual</strong> ({bruto.estacao}), numa régua de{' '}
              <strong>zero próprio</strong>: não se compara com as cotas desta cidade.{' '}
              {faixaEstadual ? (
                <>A cor é a faixa que a própria Defesa Civil de SC publica para a estação.</>
              ) : (
                <>A Defesa Civil de SC não publica faixa para esta estação agora.</>
              )}
            </p>
          </>
        ) : (
          <p className={estilos.semLeitura}>
            <strong>Sem leitura ao vivo.</strong> Isto não quer dizer que o rio esteja baixo: quer
            dizer que não estamos medindo. Acompanhe pela Defesa Civil.
          </p>
        )}
        {children}
      </section>
    )
  }

  const idade = leitura.medidoEm ? idadeMin(leitura.medidoEm, agora) : null
  const estadoIdade = idade === null ? 'velha' : frescorDaCidade(idade, cidade.id)
  const seta = tendenciaDaLeitura(serie, leitura, agora)
  // Leitura que não é de agora com o rio SUBINDO: o número erra para baixo,
  // que é o lado que machuca. Vale a série mesmo sem casar com a leitura.
  const subia = estadoIdade !== 'agora' && tendenciaDaSerie(serie)?.rotulo === 'subindo'
  const situacao = situacaoNasCotas(cidade, leitura, agora)
  const c18 =
    cidade.id === 'ascurra' && leitura.codigo === 'DCSC-00003'
      ? faixaAscurra(
          { cidade: 'ascurra', codigo: leitura.codigo, estacao: leitura.estacao, nivelBrutoM: leitura.nivel_m, medidoEm: leitura.medidoEm },
          agora,
        )
      : null

  return (
    <section className={`${estilos.cartao} surge`} aria-label={`Agora em ${cidade.nome}`}>
      {titulo}
      <div className={estilos.topo}>
        <ChipFaixa faixa={faixa} cidade={cidade} />
        <span className={estilos.medido}>
          <span className={`${estilos.frescor} ${estilos[`frescor_${estadoIdade}`] ?? ''}`} aria-hidden="true" />
          {idade === null ? 'sem horário de medição' : `medido ${textoIdade(idade)}`}
          {leitura.estacao ? ` · ${leitura.estacao}` : ''}
        </span>
      </div>

      <p className={estilos.linhaNumero} aria-live="polite">
        <span className={`${estilos.numero} ${estadoIdade === 'velha' ? estilos.numeroVelho : ''}`}>
          {numero(leitura.nivel_m)}
        </span>
        <span className={estilos.unidade}>m</span>
        {seta && estadoIdade !== 'velha' ? (
          <span className={`${estilos.tendencia} ${estilos[`t_${seta.rotulo === 'estável' ? 'estavel' : seta.rotulo}`] ?? ''}`}>
            <span className={estilos.seta} aria-hidden="true">
              {seta.rotulo === 'subindo' ? '▲' : seta.rotulo === 'descendo' ? '▼' : '▶'}
            </span>{' '}
            {textoTendencia(seta)}
          </span>
        ) : null}
      </p>

      {estadoIdade === 'velha' ? (
        <p className={estilos.alertaLeitura}>Leitura antiga — não use como nível atual.</p>
      ) : null}
      {estadoIdade === 'velha' && estadual?.medidoEm &&
      frescorDaCidade(idadeMin(estadual.medidoEm, agora), cidade.id) !== 'velha' ? (
        <p className={estilos.estadual}>
          Agora, a <strong>rede estadual</strong> ({estadual.codigo ?? estadual.estacao}) marca{' '}
          <strong>{metros(estadual.nivelBrutoM)}</strong>, medido{' '}
          {textoIdade(idadeMin(estadual.medidoEm, agora))}. É outra régua, de zero próprio: mostra se o
          rio sobe ou desce, <strong>não</strong> se compara com as cotas abaixo.
          {faixaEstadual ? (
            <>
              {' '}Faixa da Defesa Civil de SC para essa estação:{' '}
              <ChipFaixa faixa={faixaEstadual} cidade={cidade} compacto estadual />
            </>
          ) : null}
        </p>
      ) : null}
      {subia ? (
        <p className={estilos.alertaLeitura}>
          Quando foi medido, o rio vinha <strong>subindo</strong>: agora pode estar mais alto.
        </p>
      ) : null}
      {c18 ? <p className={estilos.nota}>{c18.nome} · enquadramento C18, DCSC-00003</p> : null}

      {situacao ? (
        <p className={estilos.frase}>
          {situacao.acima ? (
            situacao.acima.cm === 0 ? (
              <>Está <strong>na cota de {situacao.acima.nome}</strong> ({metros(situacao.acima.valor)}). </>
            ) : (
              <>
                Está <strong>{distancia(situacao.acima.cm / 100)} acima</strong> da cota de{' '}
                {situacao.acima.nome} ({metros(situacao.acima.valor)}).{' '}
              </>
            )
          ) : null}
          {situacao.proxima ? (
            <>
              Faltam <strong>{distancia(situacao.proxima.faltam)}</strong> para a cota de{' '}
              {situacao.proxima.nome} ({metros(situacao.proxima.valor)}).
            </>
          ) : null}
        </p>
      ) : null}

      {cidade.cotas_aviso_publico ? (
        <p className={estilos.avisoCotas}>
          <strong>Atenção ao ler as cotas desta cidade.</strong> {cidade.cotas_aviso_publico}
        </p>
      ) : null}

      {cidade.id !== 'gaspar' && cidade.id !== 'ascurra' ? (
        <MedidorCotas cidade={cidade} nivel={estadoIdade === 'velha' ? null : leitura.nivel_m} />
      ) : null}

      <p className={estilos.regua}>
        Na <strong>régua de {cidade.nome}</strong>. Metros de outra cidade não se comparam com estes.
      </p>
      {children}
    </section>
  )
}
