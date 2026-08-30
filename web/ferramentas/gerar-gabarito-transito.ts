/**
 * Gera `data/transito-esperado.json`: o encadeamento de trânsito para TODOS os
 * pares de cidades de cada rio.
 *
 * Por que existe: o `/previsao` do bot precisa do mesmo encadeamento que o
 * site faz, e o site é TypeScript enquanto o bot é Python. Duas implementações
 * de uma conta de vida podem divergir em silêncio — o site dizendo uma coisa e
 * o bot outra, sem ninguém perceber até a noite errada.
 *
 * O gabarito é o contrato entre as duas. Os dois lados têm um teste que o
 * reproduz; divergência de qualquer um fica vermelha na CI. E ele é gerado
 * importando o `transito.ts` do próprio site — gabarito feito a partir de uma
 * cópia da lógica não provaria nada sobre o original.
 *
 * Rodar depois de mexer em `transito.json` ou em `transito.ts`, e CONFERIR o
 * diff antes de commitar — o gabarito só vale se alguém olhou:
 *
 *     npm run gabarito
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { caminho } from '../src/logica/transito'
import type { Cidade, Trecho } from '../src/dados/tipos'

const RAIZ = new URL('../../', import.meta.url).pathname
const ler = (nome: string) => JSON.parse(readFileSync(RAIZ + nome, 'utf8'))

const estacoes = ler('data/estacoes.json') as {
  rios: Record<string, { cidades: Cidade[] }>
}
const transito = ler('data/transito.json') as { trechos: Trecho[] }

const caminhos: unknown[] = []
for (const [rioId, rio] of Object.entries(estacoes.rios)) {
  const cidades = [...rio.cidades].sort((a, b) => a.ordem - b.ordem).map((c) => c.id)
  for (const de of cidades) {
    for (const para of cidades) {
      if (de === para) continue
      const c = caminho(transito.trechos, rioId, de, para)
      caminhos.push({
        rio: rioId,
        de,
        para,
        resultado:
          c === null
            ? null
            : {
                horas_min: c.horasMin,
                horas_max: c.horasMax,
                direto: c.direto,
                confianca: c.confianca,
                // Os trechos pela identidade (de, para): é o que importa comparar.
                trechos: c.trechos.map((t) => [t.de, t.para]),
              },
      })
    }
  }
}

const gabarito = {
  _meta: {
    gerado_por: 'web/ferramentas/gerar-gabarito-transito.ts (npm run gabarito)',
    o_que_e:
      'Encadeamento de trânsito para todo par de cidades, de montante a jusante. ' +
      'Contrato entre o site (TypeScript) e o bot (Python): os dois têm teste que o reproduz.',
  },
  caminhos,
}

writeFileSync(RAIZ + 'data/transito-esperado.json', JSON.stringify(gabarito, null, 2) + '\n')
const achados = caminhos.filter((c) => (c as { resultado: unknown }).resultado !== null).length
console.log(`${caminhos.length} pares, ${achados} com caminho conhecido.`)
