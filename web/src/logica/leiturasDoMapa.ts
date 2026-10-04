import type { EstadoTempoReal } from '../dados/tempoReal'
import { frescorDaCidade, idadeMin } from './tempoReal'

/**
 * O tempo real que o MAPA DO RIO (`MapaRios`) pode desenhar: só leituras que
 * não estão velhas pela regra da cidade (`frescorDaCidade`).
 *
 * Auditoria de 03/10/2026, item 1: em `/acu` o pino de Indaial mostrava
 * "4,10 m" de uma leitura de 12/09, vinte dias antes, enquanto a lista ao lado
 * dizia "sem leitura recente" e a página da cidade, "Leitura antiga". O motor
 * do mapa (`mapaMotor.ts`, arquivo do Monitor) põe o número no pino sem olhar a
 * idade e só escreve a idade quando `mostrarIdade` está ligado, o que acontece
 * no Monitor e não aqui. A saída escolhida é a da lista e da cor: leitura velha
 * é "sem leitura". O motor fica intacto, e o Monitor, que mostra a idade, não muda.
 *
 * Sem carimbo de hora também não entra: não dá para saber se é de agora.
 */
export function semLeiturasVelhas(t: EstadoTempoReal, agora: Date): EstadoTempoReal {
  const leituras = t.leituras.filter(
    (l) => l.medidoEm !== null && frescorDaCidade(idadeMin(l.medidoEm, agora), l.cidade) !== 'velha',
  )
  return leituras.length === t.leituras.length ? t : { ...t, leituras }
}
