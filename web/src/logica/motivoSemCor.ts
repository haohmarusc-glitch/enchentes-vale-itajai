import { cotasOperacionais } from './cotasOperacionais'
import { idadeMin, MIN_VELHA } from './tempoReal'

/** O bruto estadual não deve esconder o motivo de recusa da leitura municipal. */
export function motivoSemCorNoMonitor(cotas: Record<string, number>, medidoEm: Date | null, agora: Date, temLeituraMunicipal: boolean, temBrutoEstadual: boolean, cidade: string): string {
  if (temLeituraMunicipal) {
    if (cidade === 'blumenau' && medidoEm && idadeMin(medidoEm, agora) > 120) {
      return 'A última medição tem mais de duas horas; Blumenau fica sem cor até receber leitura recente.'
    }
    return motivoSemCor(cotas, medidoEm, agora)
  }
  return temBrutoEstadual
    ? 'Há medição estadual abaixo, mas não há vínculo confirmado entre essa régua e as cotas municipais para calcular a cor.'
    : motivoSemCor(cotas, medidoEm, agora)
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
