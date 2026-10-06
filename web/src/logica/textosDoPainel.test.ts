import { test } from 'node:test'
import assert from 'node:assert/strict'
import { MOTIVO_VARIAS_REGUAS, ressalvaDoBruto, textoEquivalencia, textoSemCota } from './textosDoPainel'
import { motivoDaEstacaoEstadual, motivoSemCorNoMonitor } from './motivoSemCor'
import { montarNivelSc } from '../dados/nivelSc'

const agora = new Date('2026-10-06T03:00:00Z')

test('sem cota: o texto segue a origem da cor e nunca anuncia cinza sob uma cor estadual', () => {
  assert.match(textoSemCota('municipal'), /fica cinza/)
  assert.doesNotMatch(textoSemCota('estadual'), /cinza/)
  assert.match(textoSemCota('estadual'), /classificação que a Defesa Civil de SC publica/)
  assert.doesNotMatch(textoSemCota('varias'), /cinza|Sem cota/)
})

test('ressalva do bruto: não afirma "zero diferente" e não nega a origem estadual da cor', () => {
  for (const cotas of [true, false]) {
    for (const estadual of [true, false]) {
      const t = ressalvaDoBruto(cotas, estadual)
      assert.doesNotMatch(t, /zero diferente/)
      assert.match(t, /não está validada/)
      if (estadual) assert.match(t, /A cor do pino é a classificação/)
      else assert.match(t, /não define a cor/)
      if (!cotas) assert.doesNotMatch(t, /acima/)
    }
  }
})

test('várias réguas: o motivo não diz que falta cota', () => {
  assert.doesNotMatch(MOTIVO_VARIAS_REGUAS, /Faltam faixas|sem cota/i)
})

/** O `ultimo_nivel_sc.json` de 06/10/2026 00:31 (Brasília), só com as linhas das cidades auditadas. */
const publicado = {
  leituras: [
    { codigo: 'DCSC-00030', estacao: 'Ilhota', cidade: 'ilhota', nivel_bruto_m: 9.49, medido_em: '2026-10-06T00:31:27' },
    { codigo: 'DCSC-00029', estacao: 'Guabiruba', cidade: 'guabiruba', nivel_bruto_m: 0.63, medido_em: '2026-10-06T00:31:32' },
  ],
  suspeitas: [
    { codigo: 'DCSC-00032', estacao: 'Lontras', cidade: 'lontras', nivel_bruto_m: 21474836.0, medido_em: '2026-10-06T00:31:27', motivo: '> 30.0 m' },
  ],
  sem_leitura: [
    { codigo: 'DCSC-00006', estacao: 'SDC-SC Indaial', cidade: 'indaial', medido_em: '2026-10-02T17:22:50', motivo: 'value null' },
    { codigo: 'DCSC-00044', estacao: 'Fora da cadeia', cidade: null, medido_em: '2026-10-06T00:31:32' },
  ],
  altimetricas: [
    { codigo: 'DCSC-00178', estacao: 'Apiúna (H)', cidade: 'apiuna', valor_publicado_m: 81.17, medido_em: '2026-10-05T23:53:02' },
  ],
}

test('o carregador lê os três baldes; estação sem cidade fica de fora', () => {
  const m = montarNivelSc(publicado)
  assert.deepEqual([...m.keys()].sort(), ['guabiruba', 'ilhota'])
  const s = m.situacoes!
  assert.deepEqual([...s.keys()].sort(), ['apiuna', 'indaial', 'lontras'])
  assert.equal(s.get('lontras')!.tipo, 'rejeitada')
  assert.equal(s.get('lontras')!.valorPublicadoM, 21474836)
  assert.equal(s.get('indaial')!.tipo, 'sem_leitura')
  assert.equal(s.get('apiuna')!.tipo, 'altimetrica')
})

test('Lontras: valor impossível rejeitado, e a falta de cota dita à parte — nunca emergência nem zero', () => {
  const s = montarNivelSc(publicado).situacoes!.get('lontras')!
  const t = motivoSemCorNoMonitor({}, null, agora, false, false, 'lontras', s)
  assert.match(t, /DCSC-00032 publicou 21\.474\.836,00 m/)
  assert.match(t, /impossível para nível de rio/)
  assert.match(t, /não vira zero nem faixa/)
  assert.match(t, /Faltam faixas de acionamento/)
})

test('Indaial: a estação estadual está sem nível desde 02/10, e as cotas (Celesc) não têm leitura', () => {
  const s = montarNivelSc(publicado).situacoes!.get('indaial')!
  const t = motivoSemCorNoMonitor({ atencao: 3, alerta: 4, emergencia: 5.5 }, null, agora, false, false, 'indaial', s)
  assert.match(t, /DCSC-00006 não publica nível desde 02\/10/)
  assert.match(t, /Não há leitura da régua das cotas/)
})

test('Apiúna: cota altimétrica mostrada com a ressalva, sem faixa', () => {
  const s = montarNivelSc(publicado).situacoes!.get('apiuna')!
  const t = motivoDaEstacaoEstadual(s, agora)
  assert.match(t, /cota altimétrica \(81,17 m/)
  assert.match(t, /referência vertical não está validada/)
})

test('Ilhota e Guabiruba: há número; o motivo é vínculo (Ilhota) ou falta de faixa (Guabiruba), sem afirmar zero diferente', () => {
  const ilhota = motivoSemCorNoMonitor({ atencao: 9.2, alerta: 10, emergencia: 10.5 }, null, agora, false, true, 'ilhota')
  assert.match(ilhota, /não há vínculo confirmado/)
  const guabiruba = motivoSemCorNoMonitor({}, null, agora, false, true, 'guabiruba')
  assert.match(guabiruba, /Faltam faixas/)
  assert.match(guabiruba, /só como número, sem classificação/)
  for (const t of [ilhota, guabiruba]) assert.doesNotMatch(t, /zero diferente/)
})

test('Gaspar: sem leitura no arquivo de agora, mas com ponto na série — diz a hora e o valor, não "sem horário válido"', () => {
  const ultima = { medidoEm: new Date('2026-10-05T19:50:00Z'), nivel_m: 1.92 }
  const t = motivoSemCorNoMonitor({ atencao: 5, emergencia: 7 }, null, agora, false, false, 'gaspar', null, ultima)
  assert.match(t, /A última leitura recebida é de .* \(1,92 m\)/)
  assert.match(t, /antiga demais/)
  assert.doesNotMatch(t, /horário válido/)
})

test('equivalência estadual: as quatro cidades do cadastro dizem "não confirmada", com estação e distância', async () => {
  const { readFileSync } = await import('node:fs')
  const est = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8')) as {
    rios: Record<string, { cidades: { id: string; equivalencia_estadual?: Parameters<typeof textoEquivalencia>[0] }[] }>
  }
  const com = Object.values(est.rios).flatMap((r) => r.cidades).filter((c) => c.equivalencia_estadual)
  assert.deepEqual(com.map((c) => c.id).sort(), ['lontras', 'rio-dos-cedros', 'timbo', 'trombudo-central'])
  for (const c of com) {
    const t = textoEquivalencia(c.equivalencia_estadual!)
    assert.match(t, /não confirmada/)
    assert.match(t, new RegExp(c.equivalencia_estadual!.codigo))
    assert.match(t, /Proximidade não basta/)
  }
  assert.match(textoEquivalencia({ codigo: 'DCSC-00032', nome_na_dcsc: 'Lontras', distancia_km: 0.82, status: 'não confirmada' }), /DCSC-00032 \(Lontras\), a 0,82 km: não confirmada/)
})
