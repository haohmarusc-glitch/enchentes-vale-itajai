import { cotasOperacionais } from './cotasOperacionais'
import { idadeMin, MIN_VELHA } from './tempoReal'
import { dataHora, metros } from './formato'
import type { SituacaoEstadual } from '../dados/nivelSc'

/**
 * Por que a estação estadual da cidade não deu leitura — o motivo REAL, não "sem leitura"
 * (auditoria das cidades sem cor, 06/10/2026). Lontras publicava 21.474.836 m, Indaial está sem nível
 * desde 02/10 e Apiúna publica cota altimétrica: três situações diferentes, que a tela juntava numa só.
 */
export function motivoDaEstacaoEstadual(s: SituacaoEstadual, agora: Date): string {
  const cod = s.codigo ?? 'da rede estadual'
  const quando = s.medidoEm ? ` (${dataHora(s.medidoEm)})` : ''
  if (s.tipo === 'rejeitada') {
    const valor = s.valorPublicadoM != null ? `publicou ${metros(s.valorPublicadoM)}${quando}` : 'publicou um valor'
    const porque = s.valorPublicadoM != null && s.valorPublicadoM > 30
      ? 'valor impossível para nível de rio'
      : 'valor fora do plausível para esta estação'
    return `A estação estadual ${cod} ${valor} — ${porque}. A leitura foi rejeitada: não vira zero nem faixa.`
  }
  if (s.tipo === 'altimetrica') {
    const em = s.medidoEm ? ` em ${dataHora(s.medidoEm)}` : ''
    const valor = s.valorPublicadoM != null ? ` (${metros(s.valorPublicadoM)}${em})` : ''
    return `A estação estadual ${cod} publica cota altimétrica${valor}, não leitura de régua: a referência ` +
      'vertical não está validada, então o número não se compara com cota nenhuma.'
  }
  const velha = s.medidoEm && idadeMin(s.medidoEm, agora) > MIN_VELHA
  return velha
    ? `A estação estadual ${cod} não publica nível desde ${dataHora(s.medidoEm!)}.`
    : `A estação estadual ${cod} não publicou nível na última coleta.`
}

/**
 * O "Por que está cinza?" do Monitor. O bruto estadual não esconde o motivo de recusa da leitura
 * municipal, e os motivos se SOMAM: leitura recusada e falta de cota são coisas diferentes.
 */
export function motivoSemCorNoMonitor(
  cotas: Record<string, number>,
  medidoEm: Date | null,
  agora: Date,
  temLeituraMunicipal: boolean,
  temBrutoEstadual: boolean,
  cidade: string,
  situacaoEstadual?: SituacaoEstadual | null,
  /**
   * O último ponto da série da cidade, quando o arquivo de agora não traz leitura dela. Gaspar
   * (06/10/2026): a estação 21 parou às 16:50 e a série tinha esse ponto, mas a tela dizia "não há
   * leitura com horário válido" — que é outra coisa.
   */
  ultimaDaSerie?: { medidoEm: Date; nivel_m: number } | null,
): string {
  if (temLeituraMunicipal) {
    if (cidade === 'blumenau' && medidoEm && idadeMin(medidoEm, agora) > 120) {
      return 'A última medição tem mais de duas horas; Blumenau fica sem cor até receber leitura recente.'
    }
    return motivoSemCor(cotas, medidoEm, agora)
  }
  const semCotas = cotasOperacionais(cotas).length === 0
  if (temBrutoEstadual) {
    return semCotas
      ? 'Faltam faixas de acionamento para esta cidade. A medição estadual abaixo aparece só como número, sem classificação.'
      : 'Há medição estadual abaixo, mas não há vínculo confirmado entre essa estação e as cotas municipais para calcular a cor.'
  }
  const motivos: string[] = []
  if (situacaoEstadual) motivos.push(motivoDaEstacaoEstadual(situacaoEstadual, agora))
  if (semCotas) motivos.push('Faltam faixas de acionamento vinculadas à régua utilizada nesta cidade.')
  else if (situacaoEstadual) motivos.push('Não há leitura da régua das cotas desta cidade.')
  else if (ultimaDaSerie) {
    motivos.push(`A última leitura recebida é de ${dataHora(ultimaDaSerie.medidoEm)} (${metros(ultimaDaSerie.nivel_m)}): ` +
      'antiga demais para calcular a cor agora. Aguardando uma medição recente.')
  } else motivos.push(motivoSemCor(cotas, medidoEm, agora))
  return motivos.join(' ')
}

/** Explica a recusa da cor; usa as mesmas fases e limites do classificador. */
export function motivoSemCor(cotas: Record<string, number>, medidoEm: Date | null, agora: Date): string {
  if (cotasOperacionais(cotas).length === 0) {
    return 'Faltam faixas de acionamento vinculadas à régua utilizada nesta cidade.'
  }
  if (!medidoEm || !Number.isFinite(medidoEm.getTime())) {
    return 'Não há leitura com horário válido para comparar com as cotas.'
  }
  const idade = idadeMin(medidoEm, agora)
  if (idade < 0) return 'O horário da medição está no futuro e precisa ser conferido.'
  if (idade > MIN_VELHA) return 'A última leitura tem mais de 3 horas. Aguardando uma medição recente.'
  return 'Não há leitura utilizável da régua correspondente às cotas.'
}
