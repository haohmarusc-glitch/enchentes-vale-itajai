/** Lê os JSONs do disco (Node) para os testes do motor — os mesmos arquivos que o site usa. */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { Dados } from '../motor'

const D = fileURLToPath(new URL('../../../../data/', import.meta.url)) // repo/data/
const j = (p: string) => JSON.parse(readFileSync(D + p, 'utf-8'))

export const dados: Dados = {
  enchentes: j('enchentes.json'),
  transito: j('transito.json'),
  estacoes: j('estacoes.json'),
  atlas: {
    'itajai-acu': j('brutos/atlas-desastres-recorte-itajai-acu-2026-09-21.json'),
    'itajai-mirim': j('brutos/atlas-desastres-recorte-itajai-mirim-2026-09-21.json'),
  },
  chuvaEventos: j('brutos/inmet-chuva-eventos-atlas-2026-09-22.json'),
  cotasAna: j('brutos/hidroweb-mirim-2026-09-22/cotas_itajai_mirim_diaria.json'),
  picosMirim: j('brutos/hidroweb-mirim-2026-09-22/picos_itajai_mirim_1997_2021.json'),
}
