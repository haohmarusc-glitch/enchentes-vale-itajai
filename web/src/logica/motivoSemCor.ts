import { idadeMin, MIN_VELHA } from './tempoReal'

/** Explica a recusa da cor; usa as mesmas fases e limites do classificador. */
export function motivoSemCor(cotas: Record<string, number>, medidoEm: Date | null, agora: Date): string {
  const fases = ['monitoramento', 'atencao', 'alerta', 'inundacao', 'emergencia']
  if (!Object.keys(cotas).some((k) => fases.includes(k))) {
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
