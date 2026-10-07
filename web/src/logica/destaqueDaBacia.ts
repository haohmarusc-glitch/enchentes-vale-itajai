/**
 * O DESTAQUE da bacia: a cidade com a faixa mais grave no mapa, para a faixa de aviso sob a busca do
 * Monitor no celular (maquete de 07/10/2026, correção 1 do Jefferson: "só mostrar atenção se houver
 * faixa válida para essa leitura; caso contrário, mostrar apenas o nível").
 *
 * A faixa de um pino já nasce válida ou não: `faixaDaCidade` só pinta com cota do cadastro e leitura
 * fresca; sem isso o pino é `sem-dado`. Aqui a regra é mais estreita ainda:
 *  - só faixa MUNICIPAL (a cota do projeto na régua da cidade). A faixa estadual é classificação da
 *    Defesa Civil de SC e tem o próprio chip; não vira destaque nosso;
 *  - só acima de "Abaixo da atenção": `normal` e `monitoramento` não são aviso;
 *  - `varias` (Itajaí) e `sem-dado` nunca;
 *  - o número que acompanha é o NÍVEL do próprio pino, com a hora dele — nunca outra régua.
 *
 * Sem cidade nessas condições, devolve null e a faixa não aparece — não existe "tudo normal" aqui,
 * porque uma cidade sem leitura não é uma cidade normal.
 */
import type { Faixa } from './tempoReal'

export interface PinoParaDestaque {
  cidade: { id: string; nome: string }
  rioId: string
  faixa: Faixa
  origemFaixa?: 'municipal' | 'estadual'
  nivel: number | null
  medidoEm: Date | null
}

const GRAVIDADE: Record<Faixa, number> = {
  emergencia: 6,
  inundacao: 5,
  alerta: 4,
  atencao: 3,
  monitoramento: 0,
  normal: 0,
  varias: 0,
  'sem-dado': 0,
}

export function destaqueDaBacia<T extends PinoParaDestaque>(pinos: readonly T[]): T | null {
  let melhor: T | null = null
  for (const p of pinos) {
    if (p.origemFaixa === 'estadual') continue
    if (p.nivel == null || p.medidoEm == null) continue
    const g = GRAVIDADE[p.faixa]
    if (g === 0) continue
    if (!melhor || g > GRAVIDADE[melhor.faixa] || (g === GRAVIDADE[melhor.faixa] && p.cidade.nome.localeCompare(melhor.cidade.nome, 'pt-BR') < 0)) {
      melhor = p
    }
  }
  return melhor
}
