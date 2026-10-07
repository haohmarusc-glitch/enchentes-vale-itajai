/**
 * 15ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): as cheias que o site já captou.
 *
 * O morador pergunta "qual foi a última cheia em Blumenau?", "como foi a cheia de setembro?", "quantas vezes o
 * rio passou da cota de alerta desde que o site acompanha?". A resposta sai de `data/eventos-captados.json`, o
 * resumo da série que a coleta grava (gerado por `scripts/eventos_captados.py`), e por isso toda frase diz:
 *  - "a maior leitura que o site CAPTOU", nunca "o pico": a série tem lacunas, e a maior delas é dita quando passa
 *    de 3 h;
 *  - a hora é a da MEDIÇÃO; em Blumenau, quando só o repasse (3 h atrasado) tinha a leitura, isso é dito;
 *  - cada número vale na régua da cidade (ou da estação, em Itajaí), e metros não se comparam entre cidades;
 *  - o episódio que JÁ foi conferido e gravado em `enchentes.json` ganha "conferido e registrado"; os outros são
 *    captura, não registro oficial. Para o histórico oficial, a Defesa Civil.
 * Nada aqui é previsão nem conselho; em emergência, 199.
 */
import faixas from '../../../data/faixas.json'
import type { Cidade } from '../dados/tipos'
import type { CoberturaCaptada, EpisodioCaptado, EventosCaptados, FaixaCaptada } from '../dados/eventosCaptados'
import { diaDeBrasilia, horaDeBrasilia, rotuloDaFaixa } from '../logica/agora'
import { metros } from '../logica/formato'

const ROTULO = (faixas as unknown as { faixas: Record<string, { rotulo: string }> }).faixas
const ORDEM: FaixaCaptada[] = ['monitoramento', 'atencao', 'alerta', 'inundacao', 'emergencia']
export const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

export const AVISO_CAPTADOS =
  'É o que a coleta do site captou, com lacunas; não é registro oficial nem pico conferido, e cada número vale na régua da própria cidade. Para o histórico oficial, siga a Defesa Civil; em emergência, ligue 199.'

const hd = (d: Date) => `${horaDeBrasilia(d)} de ${diaDeBrasilia(d)}`
const dia = (d: Date) => diaDeBrasilia(d)
const horas = (min: number) => (min < 60 ? `${Math.round(min)} min` : `${Math.round(min / 60)} h`)
const posicao = (f: FaixaCaptada | null) => (f ? ORDEM.indexOf(f) : -1)

export interface ContextoCaptados {
  dados: EventosCaptados
  cidade: (id: string) => Cidade | null
  nome: (id: string) => string
}

/** Rótulo curto da régua em Itajaí ("DC-11"); nas outras cidades, nada. */
const regua = (e: { regua: string; cidade: string }) => (e.cidade === 'itajai' ? ` (${e.regua.split(' ')[0]})` : '')
const antiga = (e: { no_cadastro: boolean; regua: string }) => (e.no_cadastro ? '' : ` — publicação antiga, "${e.regua}", fora do cadastro atual`)

function nomeFaixa(c: ContextoCaptados, cidadeId: string, f: FaixaCaptada | null): string {
  if (!f) return 'sem faixa'
  const cidade = c.cidade(cidadeId)
  const padrao = ROTULO[f]?.rotulo ?? f
  return cidade ? rotuloDaFaixa(f, cidade, padrao) : padrao
}

function linhaEpisodio(c: ContextoCaptados, e: EpisodioCaptado, comCidade: boolean): string {
  const quem = comCidade ? `${c.nome(e.cidade)}${regua(e)}: ` : `${regua(e).trim() ? regua(e).trim().replace(/[()]/g, '') + ': ' : ''}`
  const relogio = e.relogio_defasado ? ' (hora do repasse, que anda ~3 h atrasado)' : ''
  const lacuna = e.maior_lacuna_min >= 180 ? `; houve ${horas(e.maior_lacuna_min)} sem medição no meio` : ''
  const reg = e.registro_em_enchentes
  const registrado = reg
    ? ` Conferido e registrado no histórico: ${reg.pico_m != null ? metros(reg.pico_m) : 'sem número'}${reg.hora ? ` às ${reg.hora}` : ''}${reg.referencia ? `, ${reg.referencia}` : ''}.`
    : ''
  const dur = (e.fim.getTime() - e.inicio.getTime()) / 60_000
  return `• ${quem}${metros(e.maior_leitura_m)} (${nomeFaixa(c, e.cidade, e.faixa_alcancada)}) às ${hd(e.quando)}${relogio}; acima da cota de ${metros(e.cota_referencia.valor_m)} de ${hd(e.inicio)} a ${hd(e.fim)} (${horas(dur)})${lacuna}${antiga(e)}.${registrado}`
}

function cobertura(c: ContextoCaptados, cidadeId: string): CoberturaCaptada[] {
  return c.dados.cobertura.filter((x) => x.cidade === cidadeId)
}
function desde(c: ContextoCaptados, cidadeId: string): Date | null {
  const cs = cobertura(c, cidadeId)
  return cs.length ? new Date(Math.min(...cs.map((x) => x.de.getTime()))) : null
}
function ate(c: ContextoCaptados, cidadeId: string): Date | null {
  const cs = cobertura(c, cidadeId)
  return cs.length ? new Date(Math.max(...cs.map((x) => x.ate.getTime()))) : null
}
const episodiosDa = (c: ContextoCaptados, cidadeId: string) => c.dados.episodios.filter((e) => e.cidade === cidadeId)

function semCobertura(c: ContextoCaptados, cidadeId: string): string {
  return `O site ainda não tem série captada de ${c.nome(cidadeId)}: a coleta não acompanha essa régua, então não há cheia captada para contar. O histórico registrado está na aba Histórico de ${c.nome(cidadeId)}.`
}

/** "Quais cheias o site captou?": as ondas na bacia, agrupando episódios que se sobrepõem no tempo. */
export function textoListaCaptados(c: ContextoCaptados, cidadeId: string | null): string {
  if (cidadeId) {
    const cs = cobertura(c, cidadeId)
    if (!cs.length) return semCobertura(c, cidadeId)
    const eps = episodiosDa(c, cidadeId).slice().sort((a, b) => b.inicio.getTime() - a.inicio.getTime())
    const de = desde(c, cidadeId)!
    const f = cs[0]!.cota_referencia
    if (!eps.length) {
      const semFaixa = cs.find((x) => x.sem_faixa)
      return [
        `Desde ${dia(de)}, quando o site passou a acompanhar ${c.nome(cidadeId)}, a régua não passou da cota de referência${f ? ` (${nomeFaixa(c, cidadeId, f.chave as FaixaCaptada)}, ${metros(f.valor_m)})` : ''} em nenhuma medição captada.`,
        semFaixa ? `Esta régua não ganha faixa: ${semFaixa.sem_faixa}.` : '',
        AVISO_CAPTADOS,
      ].filter(Boolean).join('\n')
    }
    return [
      `Cheias que o site captou em ${c.nome(cidadeId)} desde ${dia(de)} (${eps.length}), da mais recente para a mais antiga:`,
      ...eps.map((e) => linhaEpisodio(c, e, false)),
      AVISO_CAPTADOS,
    ].join('\n')
  }
  const eps = c.dados.episodios
  if (!eps.length) return `A coleta do site ainda não captou nenhuma cheia acima da cota de referência. ${AVISO_CAPTADOS}`
  // Ondas: as cristas que caem a menos de 48 h uma da outra são a mesma chuva na bacia. Agrupar pelas janelas
  // acima da cota não serve: Rio do Sul ficou dez dias acima da atenção e emendaria duas chuvas numa só.
  const ondas: EpisodioCaptado[][] = []
  for (const e of eps.slice().sort((a, b) => a.quando.getTime() - b.quando.getTime())) {
    const atual = ondas[ondas.length - 1]
    const ultimaCrista = atual ? atual[atual.length - 1]!.quando.getTime() : -Infinity
    if (atual && e.quando.getTime() - ultimaCrista <= 48 * 3_600_000) atual.push(e)
    else ondas.push([e])
  }
  const inicioGeral = new Date(Math.min(...c.dados.cobertura.map((x) => x.de.getTime())))
  const linhas = [`Cheias que a coleta do site captou desde ${dia(inicioGeral)}, da mais recente para a mais antiga (cada número na régua da própria cidade; a data é a da maior leitura):`]
  for (const onda of ondas.reverse()) {
    const de = new Date(Math.min(...onda.map((x) => x.quando.getTime())))
    const fim = new Date(Math.max(...onda.map((x) => x.quando.getTime())))
    const porCidade = new Map<string, EpisodioCaptado[]>()
    for (const e of onda) porCidade.set(e.cidade, [...(porCidade.get(e.cidade) ?? []), e])
    // Dentro da onda, a faixa mais grave primeiro; na mesma faixa, a crista que veio antes.
    const grave = (lista: EpisodioCaptado[]) => Math.max(...lista.map((x) => posicao(x.faixa_alcancada)))
    const primeira = (lista: EpisodioCaptado[]) => Math.min(...lista.map((x) => x.quando.getTime()))
    const partes = [...porCidade.entries()]
      .sort((a, b) => grave(b[1]) - grave(a[1]) || primeira(a[1]) - primeira(b[1]))
      .map(([cid, lista]) => {
        const maior = lista.reduce((a, b) => (posicao(b.faixa_alcancada) > posicao(a.faixa_alcancada) || (posicao(b.faixa_alcancada) === posicao(a.faixa_alcancada) && b.maior_leitura_m > a.maior_leitura_m) ? b : a))
        return `${c.nome(cid)}${regua(maior)} ${metros(maior.maior_leitura_m)} (${nomeFaixa(c, cid, maior.faixa_alcancada)}, ${hd(maior.quando)})${maior.registro_em_enchentes ? ' ✓ registrado' : ''}${lista.length > 1 && cid === 'itajai' ? ` e mais ${lista.length - 1} régua(s)` : ''}`
      })
    linhas.push(`• ${dia(de) === dia(fim) ? dia(de) : `${dia(de)} a ${dia(fim)}`}: ${partes.join('; ')}.`)
  }
  linhas.push('"✓ registrado" é o episódio já conferido e gravado no histórico do site; os outros são captura. Peça "qual foi a última cheia em Blumenau?" ou "como foi a cheia de setembro?".')
  linhas.push(AVISO_CAPTADOS)
  return linhas.join('\n')
}

/** "Qual foi a última cheia em Blumenau?", "quando foi a última vez que Blumenau passou da cota de alerta?" */
export function textoUltimaCaptada(c: ContextoCaptados, cidadeId: string, cota?: string): string {
  const cs = cobertura(c, cidadeId)
  if (!cs.length) return semCobertura(c, cidadeId)
  const de = desde(c, cidadeId)!
  const minima = cota ? posicao(cota as FaixaCaptada) : -1
  const eps = episodiosDa(c, cidadeId).filter((e) => posicao(e.faixa_alcancada) >= minima)
  const ultima = eps[eps.length - 1]
  const nomeCota = cota ? nomeFaixa(c, cidadeId, cota as FaixaCaptada) : null
  if (!ultima) {
    const maior = cs.reduce((a, b) => (b.maior_leitura.nivel_m > a.maior_leitura.nivel_m ? b : a)).maior_leitura
    return [
      `Desde ${dia(de)}, quando o site passou a acompanhar ${c.nome(cidadeId)}, a régua não passou da cota${nomeCota ? ` de ${nomeCota}` : ' de referência'} em nenhuma medição captada.`,
      `A maior leitura captada foi ${metros(maior.nivel_m)} às ${hd(maior.quando)}${maior.faixa ? ` (${nomeFaixa(c, cidadeId, maior.faixa)})` : ''}.`,
      AVISO_CAPTADOS,
    ].join('\n')
  }
  const fimDaSerie = ate(c, cidadeId)!
  const emCurso = fimDaSerie.getTime() - ultima.fim.getTime() < 2 * 3_600_000
  return [
    `A última vez que ${c.nome(cidadeId)}${regua(ultima)} passou da cota${nomeCota ? ` de ${nomeCota}` : ''}, na série captada pelo site (desde ${dia(de)}):`,
    linhaEpisodio(c, ultima, false),
    emCurso ? `A série captada termina às ${hd(fimDaSerie)} ainda dentro desse episódio: ele pode não ter acabado. Para o nível de agora, peça "como está ${c.nome(cidadeId)}?".` : '',
    AVISO_CAPTADOS,
  ].filter(Boolean).join('\n')
}

/** "Qual foi o maior nível que o site já captou em Blumenau?" */
export function textoMaiorCaptada(c: ContextoCaptados, cidadeId: string): string {
  const cs = cobertura(c, cidadeId)
  if (!cs.length) return semCobertura(c, cidadeId)
  const de = desde(c, cidadeId)!
  const linhas = [`A maior leitura que o site captou em ${c.nome(cidadeId)} desde ${dia(de)}${cs.length > 1 ? ', por publicação (cada uma com o seu zero; não compare)' : ''}:`]
  for (const x of cs.slice().sort((a, b) => b.maior_leitura.nivel_m - a.maior_leitura.nivel_m)) {
    const m = x.maior_leitura
    const ep = c.dados.episodios.find((e) => e.regua === x.regua && e.cidade === cidadeId && Math.abs(e.quando.getTime() - m.quando.getTime()) < 60_000)
    const reg = ep?.registro_em_enchentes
    linhas.push(
      `• ${cidadeId === 'itajai' || cs.length > 1 ? `${x.regua}: ` : ''}${metros(m.nivel_m)} às ${hd(m.quando)}${m.relogio_defasado ? ' (hora do repasse, ~3 h atrasado)' : ''}${m.faixa ? ` (${nomeFaixa(c, cidadeId, m.faixa)})` : x.sem_faixa ? ` (sem faixa: ${x.sem_faixa})` : ''}${antiga(x)}.${reg ? ` Conferido e registrado no histórico: ${reg.pico_m != null ? metros(reg.pico_m) : ''}${reg.hora ? ` às ${reg.hora}` : ''}.` : ''}`,
    )
  }
  linhas.push(`A série captada vai de ${dia(de)} a ${dia(ate(c, cidadeId)!)}: antes disso o site não mede, e o histórico de cheias antigas está na aba Histórico. Peça "maior cheia de ${c.nome(cidadeId)}" para o registro histórico.`)
  linhas.push(AVISO_CAPTADOS)
  return linhas.join('\n')
}

/** "Quantas vezes Blumenau passou da cota de alerta desde que o site acompanha?" */
export function textoQuantasCaptadas(c: ContextoCaptados, cidadeId: string, cota?: string): string {
  const cs = cobertura(c, cidadeId)
  if (!cs.length) return semCobertura(c, cidadeId)
  const de = desde(c, cidadeId)!
  const minima = cota ? posicao(cota as FaixaCaptada) : -1
  const eps = episodiosDa(c, cidadeId).filter((e) => posicao(e.faixa_alcancada) >= minima)
  const nomeCota = cota ? nomeFaixa(c, cidadeId, cota as FaixaCaptada) : null
  const ref = cs[0]!.cota_referencia
  const doQue = nomeCota ? `da cota de ${nomeCota}` : ref ? `da cota de referência (${nomeFaixa(c, cidadeId, ref.chave as FaixaCaptada)}, ${metros(ref.valor_m)})` : 'da cota de referência'
  if (!eps.length) return `Desde ${dia(de)}, quando o site passou a acompanhar ${c.nome(cidadeId)}, a régua não passou ${doQue} em nenhuma medição captada.\n${AVISO_CAPTADOS}`
  const vezes = eps.length === 1 ? 'uma vez' : `${eps.length} vezes`
  return [
    `Desde ${dia(de)}, ${c.nome(cidadeId)} passou ${doQue} ${vezes} na série captada pelo site${cidadeId === 'itajai' ? ' (contando cada régua à parte)' : ''}:`,
    ...eps.map((e) => `• ${dia(e.inicio)}${dia(e.fim) !== dia(e.inicio) ? ` a ${dia(e.fim)}` : ''}: ${metros(e.maior_leitura_m)} (${nomeFaixa(c, e.cidade, e.faixa_alcancada)})${regua(e)}${e.registro_em_enchentes ? ' ✓ registrado' : ''}`),
    'Episódios separados por mais de 18 h abaixo da cota contam como dois; a série tem lacunas e pode ter perdido subidas curtas.',
    AVISO_CAPTADOS,
  ].join('\n')
}

/** "Como foi a cheia de setembro em Blumenau?", "o que aconteceu em 12 de setembro?" */
export function textoPeriodoCaptado(c: ContextoCaptados, p: { mes?: number; ano?: number; dia?: string }, cidadeId: string | null, agora: Date): string {
  const anoPadrao = agora.getFullYear()
  let de: Date
  let fim: Date
  let rotulo: string
  if (p.dia) {
    de = new Date(`${p.dia}T00:00:00-03:00`)
    fim = new Date(de.getTime() + 24 * 3_600_000)
    rotulo = `${p.dia.slice(8, 10)}/${p.dia.slice(5, 7)}`
  } else {
    const mes = p.mes ?? agora.getMonth() + 1
    const ano = p.ano ?? (mes > agora.getMonth() + 1 ? anoPadrao - 1 : anoPadrao)
    de = new Date(`${ano}-${String(mes).padStart(2, '0')}-01T00:00:00-03:00`)
    fim = new Date(`${mes === 12 ? ano + 1 : ano}-${String(mes === 12 ? 1 : mes + 1).padStart(2, '0')}-01T00:00:00-03:00`)
    rotulo = `${MESES[mes - 1]} de ${ano}`
  }
  const todos = c.dados.cobertura
  if (!todos.length) return `A coleta do site ainda não tem série captada. ${AVISO_CAPTADOS}`
  const inicioGeral = new Date(Math.min(...todos.map((x) => x.de.getTime())))
  const fimGeral = new Date(Math.max(...todos.map((x) => x.ate.getTime())))
  if (fim.getTime() <= inicioGeral.getTime()) {
    return `O site só acompanha as réguas desde ${dia(inicioGeral)}: ${rotulo} é anterior à série captada. Para cheias antigas, peça "cheias de ${p.ano ?? anoPadrao} em Blumenau" (histórico registrado).`
  }
  if (de.getTime() > fimGeral.getTime()) {
    return `A série captada vai até ${hd(fimGeral)}: ${rotulo} ainda não está nela.`
  }
  const eps = c.dados.episodios.filter((e) => (!cidadeId || e.cidade === cidadeId) && e.inicio.getTime() < fim.getTime() && e.fim.getTime() >= de.getTime())
  const onde = cidadeId ? ` em ${c.nome(cidadeId)}` : ''
  if (!eps.length) {
    if (cidadeId && !cobertura(c, cidadeId).length) return semCobertura(c, cidadeId)
    return `Em ${rotulo}${onde}, a série captada pelo site não tem cheia acima da cota de referência${cidadeId ? '' : ' em nenhuma cidade acompanhada'}. ${AVISO_CAPTADOS}`
  }
  const ordenados = eps.slice().sort((a, b) => a.inicio.getTime() - b.inicio.getTime() || a.cidade.localeCompare(b.cidade))
  return [
    `Cheias captadas pelo site em ${rotulo}${onde} (${ordenados.length} episódio${ordenados.length === 1 ? '' : 's'}):`,
    ...ordenados.map((e) => linhaEpisodio(c, e, !cidadeId)),
    AVISO_CAPTADOS,
  ].join('\n')
}
