/**
 * 15ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): as cheias que a coleta do site já captou —
 * lista, última, maior, quantas e por período, a partir de `data/eventos-captados.json`.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { textoListaCaptados, textoMaiorCaptada, textoPeriodoCaptado, textoQuantasCaptadas, textoUltimaCaptada, type ContextoCaptados } from './captados'
import { lerEventosCaptados } from '../dados/eventosCaptados'
import type { Cidade } from '../dados/tipos'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const estacoes = ler('estacoes.json')
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const emBlumenau: Contexto = { cidadeAtual: 'blumenau', naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z')
const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}
const cidadeDoCadastro = (id: string): Cidade | null => {
  for (const r of Object.values(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return c
  }
  return null
}

test('frases: lista, última, maior, quantas e período; o histórico antigo continua no motor', () => {
  assert.deepEqual(passos('quais cheias o site captou?'), [{ tipo: 'captados', pergunta: 'lista' }])
  assert.deepEqual(passos('o que aconteceu nos últimos meses?'), [{ tipo: 'captados', pergunta: 'lista' }])
  assert.deepEqual(passos('cheias recentes em Blumenau'), [{ tipo: 'captados', pergunta: 'lista', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('qual foi a última cheia em Blumenau?'), [{ tipo: 'captados', pergunta: 'ultima', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quando foi a última vez que Blumenau passou da cota de alerta?'), [{ tipo: 'captados', pergunta: 'ultima', cota: 'alerta', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('última cheia', emBlumenau), [{ tipo: 'captados', pergunta: 'ultima' }])
  assert.deepEqual(passos('qual foi o maior nível que o site já captou em Blumenau?'), [{ tipo: 'captados', pergunta: 'maior', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('maior leitura captada em Rio do Sul'), [{ tipo: 'captados', pergunta: 'maior', cidadeId: 'rio-do-sul' }])
  assert.deepEqual(passos('quantas vezes Blumenau passou da cota de alerta desde que o site acompanha?'), [{ tipo: 'captados', pergunta: 'quantas', cota: 'alerta', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quantas vezes o rio passou da cota de atenção em Blumenau este ano?'), [{ tipo: 'captados', pergunta: 'quantas', cota: 'atencao', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quantas cheias o site captou em Blumenau?'), [{ tipo: 'captados', pergunta: 'quantas', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('como foi a cheia de setembro em Blumenau?'), [{ tipo: 'captados', pergunta: 'periodo', mes: 9, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('o que aconteceu em setembro?'), [{ tipo: 'captados', pergunta: 'periodo', mes: 9 }])
  assert.deepEqual(passos('cheias de setembro de 2026 em Blumenau'), [{ tipo: 'captados', pergunta: 'periodo', mes: 9, ano: 2026, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('o que aconteceu em 12 de setembro?'), [{ tipo: 'captados', pergunta: 'periodo', dia: '2026-09-12' }])
  assert.deepEqual(passos('qual foi o pico de 12 de setembro em Blumenau?'), [{ tipo: 'captados', pergunta: 'periodo', dia: '2026-09-12', cidadeId: 'blumenau' }])
  // O passado antigo é do motor (enchentes.json), e a 14ª entrega continua com a série de 48 h.
  assert.equal(interpretar('cheias de setembro de 2011 em Blumenau', cat, fora), null)
  assert.equal(interpretar('qual foi a maior cheia de Blumenau?', cat, fora), null)
  assert.equal(interpretar('quantas cheias passaram de 10 m em Rio do Sul?', cat, fora), null)
  assert.deepEqual(passos('quando Blumenau passou da cota de alerta?'), [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', cota: 'alerta', cidadeId: 'blumenau' }])
  assert.equal(interpretar('qual foi a última cheia em Pomerode?', cat, fora), null)
})

// Um arquivo pequeno, com as regras do script: Blumenau com dois episódios (um registrado), Itajaí por régua,
// Rio do Sul com a publicação antiga, Taió sem episódio.
const DADOS = lerEventosCaptados({
  gerado_em: '2026-10-05T18:00:00Z',
  cobertura: [
    { cidade: 'blumenau', rio: 'itajai-acu', regua: 'Blumenau', no_cadastro: true, varias_ao_mesmo_tempo: false, publicacoes: ['Blumenau', 'Blumenau (AlertaBlu)'], de: '2026-08-31T10:00:00', ate: '2026-10-05T15:00:00', leituras: 2371, cota_referencia: { chave: 'atencao', valor_m: 4 }, sem_faixa: null, maior_leitura: { nivel_m: 7.87, quando: '2026-09-12T05:00:00', horario_de: 'Blumenau (AlertaBlu)', relogio_defasado: false, faixa: 'alerta' } },
    { cidade: 'rio-do-sul', rio: 'itajai-acu', regua: 'Rio do Sul Estação MKS', no_cadastro: false, varias_ao_mesmo_tempo: false, publicacoes: ['Rio do Sul Estação MKS'], de: '2026-08-30T16:00:00', ate: '2026-09-09T02:00:00', leituras: 769, cota_referencia: { chave: 'atencao', valor_m: 4.5 }, sem_faixa: null, maior_leitura: { nivel_m: 7.06, quando: '2026-09-01T05:35:00', horario_de: 'Rio do Sul Estação MKS', relogio_defasado: false, faixa: 'inundacao' } },
    { cidade: 'rio-do-sul', rio: 'itajai-acu', regua: 'Rio do Sul, Ponte Dom Tito Buss (Asthon)', no_cadastro: true, varias_ao_mesmo_tempo: false, publicacoes: ['Rio do Sul, Ponte Dom Tito Buss (Asthon)'], de: '2026-09-09T02:00:00', ate: '2026-10-05T15:00:00', leituras: 2478, cota_referencia: { chave: 'atencao', valor_m: 4.5 }, sem_faixa: null, maior_leitura: { nivel_m: 6.35, quando: '2026-10-01T08:13:00', horario_de: 'Rio do Sul, Ponte Dom Tito Buss (Asthon)', relogio_defasado: false, faixa: 'alerta' } },
    { cidade: 'taio', rio: 'itajai-acu', regua: 'Taió — Rio Itajaí do Oeste, Centro', no_cadastro: false, varias_ao_mesmo_tempo: false, publicacoes: ['Taió — Rio Itajaí do Oeste, Centro'], de: '2026-09-04T00:00:00', ate: '2026-10-05T15:00:00', leituras: 3023, cota_referencia: { chave: 'atencao', valor_m: 7 }, sem_faixa: null, maior_leitura: { nivel_m: 6.95, quando: '2026-09-12T03:43:00', horario_de: 'Taió — Rio Itajaí do Oeste, Centro', relogio_defasado: false, faixa: 'monitoramento' } },
    { cidade: 'itajai', rio: 'itajai-acu', regua: 'DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)', no_cadastro: true, varias_ao_mesmo_tempo: true, publicacoes: ['DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)'], de: '2026-08-30T16:00:00', ate: '2026-10-05T15:00:00', leituras: 3268, cota_referencia: { chave: 'atencao da própria estação', valor_m: 3 }, sem_faixa: null, maior_leitura: { nivel_m: 4.37, quando: '2026-09-12T04:00:00', horario_de: 'DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)', relogio_defasado: false, faixa: 'alerta' } },
    { cidade: 'itajai', rio: 'itajai-acu', regua: 'DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL', no_cadastro: true, varias_ao_mesmo_tempo: true, publicacoes: ['DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL'], de: '2026-08-30T16:00:00', ate: '2026-10-05T15:00:00', leituras: 3278, cota_referencia: { chave: 'atencao da própria estação', valor_m: 1.16 }, sem_faixa: 'régua de estuário: a maré cruza a cota sem enchente', maior_leitura: { nivel_m: 2, quando: '2026-09-12T03:01:00', horario_de: 'DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL', relogio_defasado: false, faixa: null } },
  ],
  episodios: [
    { id: '2026-09-01-blumenau', rio: 'itajai-acu', cidade: 'blumenau', regua: 'Blumenau', no_cadastro: true, inicio: '2026-08-31T10:05:00', fim: '2026-09-03T01:00:00', maior_leitura_m: 7.58, quando: '2026-09-01T09:00:00', horario_de: 'Blumenau (AlertaBlu)', relogio_defasado: false, cota_referencia: { chave: 'atencao', valor_m: 4 }, faixa_alcancada: 'alerta', leituras: 273, maior_lacuna_min: 80, leituras_suspeitas: 0, registro_em_enchentes: { data: '2026-09-01', hora: '09:00', pico_m: 7.58, referencia: 'régua', confianca: 'alta' } },
    { id: '2026-09-01-rio-do-sul-rio', rio: 'itajai-acu', cidade: 'rio-do-sul', regua: 'Rio do Sul Estação MKS', no_cadastro: false, inicio: '2026-08-31T12:45:00', fim: '2026-09-09T02:05:00', maior_leitura_m: 7.06, quando: '2026-09-01T05:35:00', horario_de: 'Rio do Sul Estação MKS', relogio_defasado: false, cota_referencia: { chave: 'atencao', valor_m: 4.5 }, faixa_alcancada: 'inundacao', leituras: 596, maior_lacuna_min: 980, leituras_suspeitas: 0, registro_em_enchentes: null },
    { id: '2026-09-12-blumenau', rio: 'itajai-acu', cidade: 'blumenau', regua: 'Blumenau', no_cadastro: true, inicio: '2026-09-10T11:35:00', fim: '2026-09-14T08:00:00', maior_leitura_m: 7.87, quando: '2026-09-12T05:00:00', horario_de: 'Blumenau (AlertaBlu)', relogio_defasado: false, cota_referencia: { chave: 'atencao', valor_m: 4 }, faixa_alcancada: 'alerta', leituras: 310, maior_lacuna_min: 975, leituras_suspeitas: 0, registro_em_enchentes: { data: '2026-09-12', hora: '05:15', pico_m: 7.87, referencia: 'régua', confianca: 'alta' } },
    { id: '2026-09-12-itajai-dc-11', rio: 'itajai-acu', cidade: 'itajai', regua: 'DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)', no_cadastro: true, inicio: '2026-09-10T02:00:00', fim: '2026-09-15T05:30:00', maior_leitura_m: 4.37, quando: '2026-09-12T04:00:00', horario_de: 'DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)', relogio_defasado: false, cota_referencia: { chave: 'atencao da própria estação', valor_m: 3 }, faixa_alcancada: 'alerta', leituras: 214, maior_lacuna_min: 690, leituras_suspeitas: 0, registro_em_enchentes: null },
    { id: '2026-09-22-blumenau', rio: 'itajai-acu', cidade: 'blumenau', regua: 'Blumenau', no_cadastro: true, inicio: '2026-09-21T23:00:00', fim: '2026-09-24T09:00:00', maior_leitura_m: 6.62, quando: '2026-09-22T12:00:00', horario_de: 'Blumenau (AlertaBlu)', relogio_defasado: false, cota_referencia: { chave: 'atencao', valor_m: 4 }, faixa_alcancada: 'alerta', leituras: 59, maior_lacuna_min: 60, leituras_suspeitas: 0, registro_em_enchentes: null },
    { id: '2026-10-01-blumenau', rio: 'itajai-acu', cidade: 'blumenau', regua: 'Blumenau', no_cadastro: true, inicio: '2026-10-01T10:00:00', fim: '2026-10-02T09:00:00', maior_leitura_m: 4.53, quando: '2026-10-01T20:00:00', horario_de: 'Blumenau', relogio_defasado: true, cota_referencia: { chave: 'atencao', valor_m: 4 }, faixa_alcancada: 'atencao', leituras: 24, maior_lacuna_min: 60, leituras_suspeitas: 0, registro_em_enchentes: null },
  ],
})
const ctx: ContextoCaptados = { dados: DADOS, cidade: cidadeDoCadastro, nome: (id) => cidadeDoCadastro(id)?.nome ?? id }

test('textos: captura e não registro, hora da medição, lacuna, publicação antiga, régua de Itajaí, o 199', () => {
  const lista = textoListaCaptados(ctx, null)
  assert.match(lista, /^Cheias que a coleta do site captou desde 30\/08/)
  assert.match(lista, /• 12\/09: Itajaí \(DC-11\) 4,37 m \(Alerta, 04:00 de 12\/09\); Blumenau 7,87 m \(Alerta, 05:00 de 12\/09\) ✓ registrado\./, 'mesma faixa: a crista que veio antes primeiro')
  assert.match(lista, /• 01\/09: Rio do Sul 7,06 m \(Inundação, 05:35 de 01\/09\); Blumenau 7,58 m \(Alerta, 09:00 de 01\/09\) ✓ registrado\./, 'a faixa mais grave primeiro')
  assert.ok(lista.indexOf('• 01/10:') < lista.indexOf('• 22/09:') && lista.indexOf('• 22/09:') < lista.indexOf('• 12/09:'), 'da mais recente para a mais antiga')
  assert.match(lista, /não é registro oficial nem pico conferido[^]*199/)
  const blu = textoListaCaptados(ctx, 'blumenau')
  assert.match(blu, /^Cheias que o site captou em Blumenau desde 31\/08 \(4\)/)
  assert.match(blu, /• 4,53 m \(Atenção\) às 20:00 de 01\/10 \(hora do repasse, que anda ~3 h atrasado\)/)
  assert.match(blu, /• 7,87 m \(Alerta\) às 05:00 de 12\/09; acima da cota de 4,00 m de 11:35 de 10\/09 a 08:00 de 14\/09 \(92 h\); houve 16 h sem medição no meio\. Conferido e registrado no histórico: 7,87 m às 05:15, régua\./)
  const ultima = textoUltimaCaptada(ctx, 'blumenau')
  assert.match(ultima, /^A última vez que Blumenau passou da cota, na série captada pelo site \(desde 31\/08\):\n• 4,53 m \(Atenção\) às 20:00 de 01\/10/)
  assert.match(textoUltimaCaptada(ctx, 'blumenau', 'alerta'), /passou da cota de Alerta[^]*• 6,62 m \(Alerta\) às 12:00 de 22\/09/)
  assert.match(textoUltimaCaptada(ctx, 'blumenau', 'emergencia'), /não passou da cota de Alerta Máximo em nenhuma medição captada\.\nA maior leitura captada foi 7,87 m às 05:00 de 12\/09 \(Alerta\)/)
  assert.match(textoUltimaCaptada(ctx, 'taio'), /Desde 04\/09, quando o site passou a acompanhar Taió, a régua não passou da cota de referência[^]*6,95 m às 03:43 de 12\/09 \(Monitoramento\)/)
  assert.match(textoUltimaCaptada(ctx, 'gaspar'), /ainda não tem série captada de Gaspar/)
  const maior = textoMaiorCaptada(ctx, 'rio-do-sul')
  assert.match(maior, /por publicação \(cada uma com o seu zero; não compare\)/)
  assert.match(maior, /• Rio do Sul Estação MKS: 7,06 m às 05:35 de 01\/09 \(Inundação\) — publicação antiga, "Rio do Sul Estação MKS", fora do cadastro atual\./)
  assert.match(maior, /• Rio do Sul, Ponte Dom Tito Buss \(Asthon\): 6,35 m às 08:13 de 01\/10 \(Alerta\)\./)
  assert.match(textoMaiorCaptada(ctx, 'blumenau'), /^A maior leitura que o site captou em Blumenau desde 31\/08:\n• 7,87 m às 05:00 de 12\/09 \(Alerta\)\. Conferido e registrado no histórico: 7,87 m às 05:15\./)
  const quantas = textoQuantasCaptadas(ctx, 'blumenau', 'alerta')
  assert.match(quantas, /^Desde 31\/08, Blumenau passou da cota de Alerta 3 vezes na série captada pelo site:/)
  assert.match(quantas, /• 31\/08 a 03\/09: 7,58 m \(Alerta\) ✓ registrado/)
  assert.match(textoQuantasCaptadas(ctx, 'blumenau'), /passou da cota de referência \(Atenção, 4,00 m\) 4 vezes/)
  assert.match(textoQuantasCaptadas(ctx, 'taio'), /não passou da cota de referência \(Atenção, 7,00 m\) em nenhuma medição captada/)
  const setembro = textoPeriodoCaptado(ctx, { mes: 9 }, 'blumenau', AGORA)
  assert.match(setembro, /^Cheias captadas pelo site em setembro de 2026 em Blumenau \(3 episódios\):/)
  const dia12 = textoPeriodoCaptado(ctx, { dia: '2026-09-12' }, null, AGORA)
  assert.match(dia12, /em 12\/09 \(2 episódios\):\n• Itajaí \(DC-11\): 4,37 m[^]*\n• Blumenau: 7,87 m/, 'na ordem em que cada régua passou da cota')
  assert.match(textoPeriodoCaptado(ctx, { mes: 7 }, null, AGORA), /só acompanha as réguas desde 30\/08: julho de 2026 é anterior à série captada/)
  assert.match(textoPeriodoCaptado(ctx, { mes: 10 }, 'taio', AGORA), /Em outubro de 2026 em Taió, a série captada pelo site não tem cheia acima da cota de referência/)
  assert.match(textoPeriodoCaptado(ctx, { mes: 9 }, 'itajai', AGORA), /• DC-11: 4,37 m \(Alerta\)/)
  for (const t of [lista, blu, ultima, maior, quantas, setembro, dia12]) {
    assert.doesNotMatch(t, /\bpico\b(?! conferido)/i, 'nunca chama a maior leitura de pico')
    assert.match(t, /199/)
  }
})

function ambiente() {
  const dados: DadosDoChat = {
    aoVivo: async () => null,
    cidade: (id) => {
      const c = cidadeDoCadastro(id)
      return c ? { cidade: c, rioId: 'itajai-acu' } : null
    },
    reguasNoMapa: () => [],
    tracado: async () => null,
    base: () => '',
    captados: () => DADOS,
  }
  const navegacoes: string[] = []
  const amb: Ambiente = { navegar: (p) => navegacoes.push(p), rotaAtual: () => '/', monitor: () => null, esperarMonitor: async () => null, dados }
  return { amb, navegacoes }
}
const rodar = (texto: string, amb: Ambiente, c: Contexto = fora) => {
  const r = interpretar(texto, cat, c)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, c, () => textoDeAjuda(fora, null))
}

beforeEach(() => limparRetratos())

test('executor: o link para a aba Histórico, as sugestões, a cidade da página; nada navega', async () => {
  const { amb, navegacoes } = ambiente()
  const r = await rodar('qual foi a última cheia em Blumenau?', amb)
  assert.match(r.texto, /^A última vez que Blumenau passou da cota/)
  assert.deepEqual(r.link, { texto: 'Histórico de Blumenau →', para: '/acu/blumenau?aba=historico' })
  assert.ok(r.sugestoes?.includes('maior cheia de Blumenau'), 'aponta o histórico registrado, que é do motor')
  const semCidade = await rodar('qual foi a última cheia?', amb)
  assert.match(semCidade.texto, /Em qual cidade\?/)
  const daPagina = await rodar('última cheia', amb, emBlumenau)
  assert.match(daPagina.texto, /Blumenau/)
  const lista = await rodar('quais cheias o site captou?', amb)
  assert.match(lista.texto, /^Cheias que a coleta do site captou/)
  assert.equal(lista.link, undefined)
  assert.deepEqual(navegacoes, [])
})

test('a ajuda lista os pedidos da 15ª entrega', () => {
  for (const c of [fora, { cidadeAtual: null, naMonitor: true, reguaAtual: null } as Contexto]) {
    const t = textoDeAjuda(c, null).texto
    for (const f of ['quais cheias o site captou?', 'última cheia em', 'como foi a cheia de setembro', 'desde que o site acompanha?']) assert.ok(t.includes(f), f)
  }
})
