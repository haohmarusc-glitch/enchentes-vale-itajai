/**
 * 2ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026): o que o texto vira, o que cada
 * resposta diz e o que ela nunca diz (número velho como atual, subtração entre réguas, ponto inventado).
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro, pontoDoTexto } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import {
  linkDoMonitor, serieDeUmaRegua, textoAtrasadas, textoComparar, textoMontante, textoOrigemTracado, textoUltimaHora,
} from './respostas'
import { arquivoDoRioDaCidade, arquivoPeloNome } from './rios'
import { pinoSemLeituraDeAgora, reguaSemLeituraDeAgora } from '../logica/filtroSemLeitura'
import type { AoVivo } from '../dados/usarAoVivo'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { NivelSc } from '../dados/nivelSc'
import type { PontoSerie } from '../dados/serie'
import type { ReguaNoMapa } from '../logica/reguasNoMapa'
import type { Cidade } from '../dados/tipos'
import type { ControleMonitor, FiltroMonitor, MarcaNoMapa, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const estacoes = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const minAtras = (m: number) => new Date(AGORA.getTime() - m * 60_000)

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

function leitura(estacao: string, cidade: string, min: number | null, nivel = 2, extra: Partial<LeituraAoVivo> = {}): LeituraAoVivo {
  return { estacao, rio: 'itajai-acu', cidade, nivel_m: nivel, medidoEm: min == null ? null : minAtras(min), resgateDe: null, ...extra }
}

function aoVivo(leituras: LeituraAoVivo[], ops: { nivelSc?: NivelSc; series?: AoVivo['serie']['series']; resgates?: Record<string, string> } = {}): AoVivo {
  return {
    tempoReal: { situacao: 'ok', leituras, chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
    nivelSc: ops.nivelSc ?? (new Map() as NivelSc),
    serie: { situacao: 'ok', series: ops.series ?? {}, resgates: ops.resgates ?? {}, janelaHoras: 48, geradoEm: AGORA },
    agora: AGORA,
  }
}

// ---------------------------------------------------------------- cadastro

test('confluências: só as que o cadastro grava, com a coordenada dele; as outras dizem que não há ponto', () => {
  const benedito = cat.confluencias?.find((c) => c.id === 'benedito')
  assert.deepEqual([benedito?.lat, benedito?.lon], [-26.89134, -49.23557])
  const trombudo = cat.confluencias?.find((c) => c.id === 'trombudo-central')
  assert.deepEqual([trombudo?.lat, trombudo?.lon], [-27.2451031, -49.6906952])
  assert.ok(cat.confluencias?.some((c) => c.id === 'itajai-acu-nasce'))
  // 08/10/2026: o Luís Alves foi medido no OSM (achar_confluencias.py --gravar), como o Benedito.
  const luis = cat.confluencias?.find((c) => c.id === 'luis-alves')
  assert.deepEqual([luis?.lat, luis?.lon], [-26.87302, -48.78871])
  assert.equal(cat.confluencias?.length, 4)
  for (const id of ['ibirama', 'rio-dos-cedros', 'guabiruba']) assert.ok(cat.semPonto?.some((s) => s.id === id), id)
  assert.ok(!cat.semPonto?.some((s) => s.id === 'luis-alves'))
  assert.equal(pontoDoTexto('a confirmar por coordenada — antes ou depois da régua de Ilhota'), null)
  assert.deepEqual(pontoDoTexto('em −26,89134, −49,23557 (lat, lon), a 90 km'), { lat: -26.89134, lon: -49.23557 })
})

test('rio de cada cidade e rio pelo nome: só arquivos que existem em data/rios/', () => {
  const existe = (a: string) => readFileSync(new URL(`../../../data/rios/${a}.geojson`, import.meta.url), 'utf8').length > 0
  for (const c of cat.cidades) assert.ok(existe(arquivoDoRioDaCidade(c.id, c.rio)), c.id)
  for (const n of ['benedito', 'rio benedito', 'itajai mirim', 'itajai do sul', 'hercilio', 'trombudo', 'rio dos cedros', 'guabiruba']) {
    const a = arquivoPeloNome(n)
    assert.ok(a && existe(a), n)
  }
  assert.equal(arquivoPeloNome('tiete'), null)
})

// ---------------------------------------------------------------- interpretar

test('os pedidos novos viram os passos certos', () => {
  assert.deepEqual(passos('quais leituras estão atrasadas?'), [{ tipo: 'atrasadas' }])
  assert.deepEqual(passos('tem alguma régua atrasada?'), [{ tipo: 'atrasadas' }])
  assert.deepEqual(passos('mostrar só as réguas sem leitura'), [{ tipo: 'filtro', filtro: 'sem_leitura' }])
  assert.deepEqual(passos('limpar filtros'), [{ tipo: 'filtro', filtro: null }])
  assert.deepEqual(passos('abrir o gráfico desta régua'), [{ tipo: 'abrir_grafico' }])
  assert.deepEqual(passos('gráfico de Blumenau'), [{ tipo: 'abrir_grafico', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('o que mudou na última hora?'), [{ tipo: 'ultima_hora' }])
  assert.deepEqual(passos('o que mudou na última hora em Rio do Sul?'), [{ tipo: 'ultima_hora', cidadeId: 'rio-do-sul' }])
  assert.deepEqual(passos('de onde vem esse traçado?'), [{ tipo: 'origem_tracado' }])
  assert.deepEqual(passos('de onde vem o traçado do Benedito?'), [{ tipo: 'origem_tracado', rio: 'benedito' }])
  assert.deepEqual(passos('fonte do traçado de Timbó'), [{ tipo: 'origem_tracado', cidadeId: 'timbo' }])
  assert.deepEqual(passos('o que fica a montante daqui?'), [{ tipo: 'montante', foco: 'montante' }])
  assert.deepEqual(passos('o que fica a montante de Blumenau?'), [{ tipo: 'montante', foco: 'montante', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('afluentes deste trecho'), [{ tipo: 'montante', foco: 'afluentes' }])
  assert.deepEqual(passos('ver a confluência do Benedito'), [{ tipo: 'confluencia', id: 'benedito' }])
  assert.deepEqual(passos('onde o Benedito entra no Açu?'), [{ tipo: 'confluencia', id: 'benedito' }])
  assert.deepEqual(passos('onde nasce o Itajaí-Açu?'), [{ tipo: 'confluencia', id: 'itajai-acu-nasce' }])
  assert.deepEqual(passos('confluência do Luiz Alves'), [{ tipo: 'confluencia', id: 'luis-alves' }])
  assert.deepEqual(passos('comparar as réguas de Itajaí'), [{ tipo: 'comparar_reguas', cidadeId: 'itajai' }])
  assert.deepEqual(passos('copiar resumo desta cidade'), [{ tipo: 'copiar_resumo' }])
  assert.deepEqual(passos('copiar resumo de Gaspar para o WhatsApp'), [{ tipo: 'copiar_resumo', cidadeId: 'gaspar' }])
  assert.deepEqual(passos('copiar link desta visualização'), [{ tipo: 'copiar_link' }])
  assert.deepEqual(passos('mostre Itajaí e mostrar só as réguas sem leitura'), [
    { tipo: 'ir_cidade', cidadeId: 'itajai' },
    { tipo: 'filtro', filtro: 'sem_leitura' },
  ])
})

test('perguntas continuam perguntas; rio desconhecido pergunta, nunca inventa ponto', () => {
  for (const q of ['onde a água chega em Blumenau?', 'qual a maior cheia de Blumenau?', 'a cheia de 2008 em Gaspar', 'o que mudou na última hora em Pomerode?']) {
    assert.equal(interpretar(q, cat, fora), null, q)
  }
  const tiete = interpretar('ver a confluência do Tietê', cat, fora)
  assert.equal(tiete?.tipo, 'esclarecer')
})

// ---------------------------------------------------------------- respostas

test('atrasadas: a regra de idade do site, sem o número da leitura atrasada', () => {
  const v = aoVivo([
    leitura('Rio do Sul', 'rio-do-sul', 30, 4.21),
    leitura('Gaspar', 'gaspar', 100, 5.55),
    leitura('Blumenau', 'blumenau', 150, 6.66), // Blumenau: série horária, velha depois de 2 h
    leitura('Ilhota', 'ilhota', 200, 3.33),
    leitura('Brusque', 'brusque', null, 1.11),
  ])
  const t = textoAtrasadas(v, cat)
  assert.match(t, /Réguas municipais: 1 de 5 com leitura de agora/)
  assert.match(t, /Atrasadas[^\n]*\n• Gaspar: medida às 13:20 de 06\/10 \(há 1 h 40\)/)
  assert.match(t, /Velhas[^]*Blumenau: medida às 12:30[^]*Ilhota/)
  assert.match(t, /Sem horário publicado[^]*Brusque/)
  for (const n of ['5,55', '6,66', '3,33', '1,11']) assert.ok(!t.includes(n), `não mostra o número ${n}`)
})

test('atrasadas: estação estadual sem cidade no cadastro sai pelo nome da estação', () => {
  const nivelSc = new Map() as NivelSc
  nivelSc.situacoes = new Map([['botuvera-2', { codigo: null, estacao: 'SDC-SC Botuverá 2', tipo: 'sem_leitura', valorPublicadoM: null, medidoEm: null }]])
  const t = textoAtrasadas(aoVivo([leitura('Rio do Sul', 'rio-do-sul', 30)], { nivelSc }), cat)
  assert.match(t, /• SDC-SC Botuverá 2: a estação não publicou nível/)
  assert.ok(!t.includes('botuvera-2'))
})

test('atrasadas: primária e resgate da mesma régua contam como uma, e vale a mais fresca', () => {
  const v = aoVivo([
    leitura('Blumenau', 'blumenau', 300),
    leitura('Blumenau (AlertaBlu)', 'blumenau', 20, 2, { resgateDe: 'Blumenau' }),
  ])
  assert.match(textoAtrasadas(v, cat), /1 de 1 com leitura de agora[^]*Nenhuma régua municipal está atrasada/)
})

test('última hora: variação de UMA régua, com o passo, a lacuna e sem previsão', () => {
  const pts: PontoSerie[] = [70, 50, 40, 10, 0].map((m, i) => ({ medidoEm: minAtras(m), nivel_m: 5 + i * 0.05, regua: 'Rio do Sul' }))
  const t = textoUltimaHora({ nome: 'Rio do Sul', cidadeId: 'rio-do-sul', pontos: pts, publicacao: null, agora: AGORA })
  assert.match(t, /de 14:10 a 15:00: de 5,05 m para 5,20 m — subiu 15 cm/)
  assert.match(t, /4 medições, uma a cada ~10 min\. Lacuna: 30 min sem medição entre 14:20 e 14:50/)
  assert.match(t, /não previsão/)
  const velha = textoUltimaHora({ nome: 'Rio do Sul', cidadeId: 'rio-do-sul', pontos: pts.map((p) => ({ ...p, medidoEm: new Date(p.medidoEm.getTime() - 5 * 3_600_000) })), publicacao: null, agora: AGORA })
  assert.match(velha, /^Não há medição da régua de Rio do Sul na última hora/)
  assert.ok(!velha.includes('5,20'))
})

test('última hora: série horária compara com a medição anterior, se ela tem até 90 min', () => {
  const p = (m: number, n: number): PontoSerie => ({ medidoEm: minAtras(m), nivel_m: n, regua: 'Blumenau (AlertaBlu)' })
  const t = textoUltimaHora({ nome: 'Blumenau', cidadeId: 'blumenau', pontos: [p(84, 3.2), p(24, 3.29)], publicacao: 'Blumenau (AlertaBlu)', agora: AGORA })
  assert.match(t, /de 13:36 a 14:36: de 3,20 m para 3,29 m — subiu 9 cm/)
  const longe = textoUltimaHora({ nome: 'Blumenau', cidadeId: 'blumenau', pontos: [p(200, 3.2), p(24, 3.29)], publicacao: null, agora: AGORA })
  assert.match(longe, /^Só uma medição/)
})

test('última hora: Blumenau usa a publicação mais fresca sem fundir; Itajaí pergunta qual régua', () => {
  const p = (m: number, n: number, regua: string): PontoSerie => ({ medidoEm: minAtras(m), nivel_m: n, regua })
  const blu = serieDeUmaRegua([p(200, 5, 'Blumenau'), p(30, 5.1, 'Blumenau (AlertaBlu)'), p(5, 5.2, 'Blumenau (AlertaBlu)')], { 'Blumenau (AlertaBlu)': 'Blumenau' }, null)
  assert.ok(!('escolher' in blu))
  assert.equal(blu.pontos.length, 2)
  assert.equal(blu.publicacao, 'Blumenau (AlertaBlu)')
  const ita = serieDeUmaRegua([p(10, 1, 'DC-01 x'), p(10, 8, 'DC-10 y')], {}, null)
  assert.deepEqual(ita, { escolher: ['DC-01 x', 'DC-10 y'] })
})

test('comparar réguas: lado a lado, cada uma no zero dela; leitura velha marcada, sem faixa', () => {
  const r = (codigo: string, nivel: number | null, min: number | null, faixa: ReguaNoMapa['faixa']): ReguaNoMapa => ({
    codigo, titulo: codigo, cidade: 'itajai', nome: `Lugar ${codigo}`, lon: 0, lat: 0, nivel, medidoEm: min == null ? null : minAtras(min), faixa, motivoSemCor: null, cotas: {},
  })
  const t = textoComparar('Itajaí', [r('DC-10', 8.2, 10, 'atencao'), r('DC-01', 0.9, 400, 'normal'), r('DC-02', null, null, null), r('DC-03', 0.5, 10, 'normal')], AGORA)
  assert.match(t, /cada uma no zero dela: os números não se comparam entre si nem se subtraem/)
  const linhas = t.split('\n')
  assert.ok(linhas.findIndex((l) => l.includes('DC-01')) < linhas.findIndex((l) => l.includes('DC-10')), 'ordem por código, não por metro')
  assert.match(t, /DC-01 · Lugar DC-01: 0,90 m às [^\n]*leitura velha, não é o nível de agora/)
  assert.ok(!/DC-01[^\n]*Abaixo da atenção/.test(t), 'leitura velha não leva faixa')
  assert.match(t, /DC-10 · Lugar DC-10: 8,20 m às [^\n]*· Atenção/)
  assert.match(t, /DC-02 · Lugar DC-02: sem leitura nesta coleta/)
  assert.match(t, /DC-03 · Lugar DC-03: 0,50 m [^\n]*· Abaixo da atenção/, 'faixa com o nome do site, nunca "Normal"')
  assert.ok(!/diferen[cç]a|acima d[ae] DC|abaixo d[ae] DC/i.test(t))
})

test('montante e afluentes: pela árvore do cadastro, com o aviso de que ligação não é previsão', () => {
  const blu = textoMontante(cat, 'blumenau', 'montante')
  assert.match(blu, /Rio do Sul → Lontras → Apiúna → Ascurra → Indaial → Blumenau/)
  assert.match(blu, /Rio Benedito, de Timbó: Entra depois de Indaial/)
  assert.match(blu, /Rio dos Cedros, de Rio dos Cedros: chega ao rio de Timbó/)
  assert.match(blu, /Ligação pelo rio não é previsão/)
  const ind = textoMontante(cat, 'indaial', 'montante')
  assert.ok(!/Afluentes[^\n]*\n(?:•[^\n]*\n)*•[^\n]*Benedito/.test(ind), 'o Benedito não está acima de Indaial')
  assert.match(ind, /Entram logo DEPOIS da régua de Indaial, não acima: Rio Benedito, Rio dos Cedros/)
  assert.match(textoMontante(cat, 'taio', 'montante'), /Taió é cabeceira/)
  assert.match(textoMontante(cat, 'trombudo-central', 'montante'), /chega ao Rio Itajaí do Oeste em −27,24510, −49,69070[^]*sem posição confirmada|não tem posição confirmada/)
  const ita = textoMontante(cat, 'itajai', 'afluentes')
  assert.match(ita, /trecho do Itajaí-Açu que chega a Itajaí:\n• Rio Luís Alves/)
  assert.match(ita, /trecho do Itajaí-Mirim que chega a Itajaí:\n• Ribeirão Guabiruba/)
  assert.match(textoMontante(cat, 'brusque', 'afluentes'), /o cadastro não diz se antes ou depois da régua de Brusque/)
})

test('origem do traçado: a base do OSM gravada no arquivo, em horário de Brasília', () => {
  const props = JSON.parse(readFileSync(new URL('../../../data/rios/benedito.geojson', import.meta.url), 'utf8')).properties
  const t = textoOrigemTracado('Rio Benedito', props)
  assert.match(t, /Base do OpenStreetMap: 06\/10\/2026, 09:21 de Brasília \(arquivo bruto tracado-benedito-osm\.json\)/)
  assert.match(t, /não é mancha de inundação/)
  assert.match(textoOrigemTracado('X', { fonte: 'f', origem: [{ bruto: 'b.json', base_osm: null }] }), /não ficou registrada/)
})

test('link do Monitor: os parâmetros que ele lê ao abrir', () => {
  assert.equal(linkDoMonitor('https://x.dev/', { cidade: 'itajai', regua: { codigo: 'DC-05' }, fundo: 'satelite' }), 'https://x.dev/#/monitor/itajai?regua=DC-05&fundo=satelite')
  assert.equal(linkDoMonitor('https://x.dev/', { cidade: null, regua: null, fundo: 'escuro' }), 'https://x.dev/#/monitor?fundo=escuro')
})

test('filtro sem leitura: sem medição, sem horário ou velha; qualquer fonte fresca tira a cidade do filtro', () => {
  assert.equal(reguaSemLeituraDeAgora({ nivel: 1, medidoEm: minAtras(30), cidade: 'itajai' }, AGORA), false)
  assert.equal(reguaSemLeituraDeAgora({ nivel: 1, medidoEm: minAtras(200), cidade: 'itajai' }, AGORA), true)
  assert.equal(reguaSemLeituraDeAgora({ nivel: null, medidoEm: null, cidade: 'itajai' }, AGORA), true)
  const pino = (nivel: number | null, min: number | null, bruto: number | null) => ({
    cidade: { id: 'lontras' }, nivel, medidoEm: min == null ? null : minAtras(min), nivelBruto: bruto == null ? null : { medidoEm: minAtras(bruto) },
  })
  assert.equal(pinoSemLeituraDeAgora(pino(2, 20, null), AGORA), false)
  assert.equal(pinoSemLeituraDeAgora(pino(null, null, 20), AGORA), false) // estadual fresca
  assert.equal(pinoSemLeituraDeAgora(pino(2, 400, 400), AGORA), true)
  assert.equal(pinoSemLeituraDeAgora(pino(null, null, null), AGORA, true), false) // Itajaí: uma régua dela fresca
})

// ---------------------------------------------------------------- executar

function monitorFalso(cidade: string | null) {
  const chamadas: string[] = []
  let filtro: FiltroMonitor = null
  let marca: MarcaNoMapa | null = null
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({ cidade, cidadeNome: cidade === 'itajai' ? 'Itajaí' : cidade, regua: cidade === 'itajai' ? { codigo: 'DC-05', rotulo: 'DC-05 · Sítio Sr. Hilário' } : null, reguas: [], fundo: 'satelite' as Fundo, camada: null, camadasDisponiveis: [], reproducao: null, filtro, marca: marca?.rotulo ?? null }),
    escolherRegua: () => ({ ok: true, texto: '' }),
    enquadrarCidade: () => ({ ok: true, texto: '' }),
    zoom: () => ({ ok: true, texto: '' }),
    verBacia: () => ({ ok: true, texto: '' }),
    fundo: () => ({ ok: true, texto: '' }),
    camada: () => ({ ok: true, texto: '' }),
    aoVivo: () => ({ ok: true, texto: '' }),
    filtrar: (f) => { chamadas.push(`filtro:${f}`); filtro = f; return { ok: true, texto: f ? 'Filtro ligado.' : 'Filtro limpo.' } },
    marcarPonto: (p) => { chamadas.push(`marca:${p?.lat},${p?.lon}`); marca = p; return { ok: true, texto: 'Mapa centrado e marcado.' } },
    explicar: () => null,
    retrato: (): Retrato => ({ rota: cidade ? `/monitor/${cidade}` : '/monitor', cidade, filtro, marca }),
    restaurar: (r) => { chamadas.push(`restaurar:${r.filtro ?? '-'}`); filtro = r.filtro ?? null; marca = r.marca ?? null; return { ok: true, texto: 'ok' } },
  }
  return { c, chamadas }
}

function ambiente(inicial: ReturnType<typeof monitorFalso> | null, rota = '/acu', dados?: DadosDoChat) {
  const montados = new Map<string | null, ReturnType<typeof monitorFalso>>()
  let atual = inicial
  if (inicial) montados.set(inicial.c.cidade, inicial)
  let r = rota
  const navegacoes: string[] = []
  const amb: Ambiente = {
    navegar: (para) => {
      navegacoes.push(para)
      r = para
      const m = para.match(/^\/monitor(?:\/([a-z-]+))?/)
      if (m) {
        const cid = m[1] ?? null
        if (!montados.has(cid)) montados.set(cid, monitorFalso(cid))
        atual = montados.get(cid)!
      } else atual = null
    },
    rotaAtual: () => r,
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
    ...(dados ? { dados } : {}),
  }
  return { amb, navegacoes, montados }
}

const cidadeDe = (id: string) => {
  for (const [rioId, r] of Object.entries(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}
const dadosFalsos = (v: AoVivo | null): DadosDoChat => ({
  aoVivo: async () => v,
  cidade: cidadeDe,
  reguasNoMapa: () => [],
  tracado: async () => null,
  base: () => 'https://site.example/',
})
const ajuda = () => textoDeAjuda(fora, null)

beforeEach(() => limparRetratos())

test('filtro: abre o Monitor se preciso e liga; no Monitor, "voltar" restaura sem filtro', async () => {
  const pagina = ambiente(null, '/acu/gaspar')
  const s = await executar([{ tipo: 'filtro', filtro: 'sem_leitura' }], pagina.amb, cat, { cidadeAtual: 'gaspar', naMonitor: false, reguaAtual: null }, ajuda)
  assert.equal(s.texto, 'Filtro ligado.')
  assert.deepEqual(pagina.navegacoes, ['/monitor/gaspar'])
  assert.deepEqual(pagina.montados.get('gaspar')!.chamadas, ['filtro:sem_leitura'])
  limparRetratos()
  const m = monitorFalso('gaspar')
  const { amb } = ambiente(m, '/monitor/gaspar')
  const ctx = { cidadeAtual: 'gaspar', naMonitor: true, reguaAtual: null }
  await executar([{ tipo: 'filtro', filtro: 'sem_leitura' }], amb, cat, ctx, ajuda)
  await executar([{ tipo: 'voltar' }], amb, cat, ctx, ajuda)
  assert.equal(m.chamadas.at(-1), 'restaurar:-')
})

test('confluência com ponto: marca no Monitor e diz a coordenada e a fonte; sem ponto: só texto, a tela não muda', async () => {
  const { amb, navegacoes, montados } = ambiente(null)
  const s = await executar([{ tipo: 'confluencia', id: 'benedito' }], amb, cat, fora, ajuda)
  assert.deepEqual(navegacoes, ['/monitor'])
  assert.deepEqual(montados.get(null)!.chamadas, ['marca:-26.89134,-49.23557'])
  assert.match(s.texto, /Confluência do Rio Benedito[^:]*: −26,89134, −49,23557\. Fonte: Confluência medida no traçado do OpenStreetMap[^]*docs\/TRACADOS-AFLUENTES-2026-10-06\.md\.$/)
  const sem = ambiente(null)
  const semPonto = cat.semPonto!.find((x) => x.id === 'rio-dos-cedros')!
  const t = await executar([{ tipo: 'confluencia', id: 'rio-dos-cedros' }], sem.amb, cat, fora, ajuda)
  assert.deepEqual(sem.navegacoes, [])
  assert.match(t.texto, new RegExp(`^${semPonto.nome} não tem ponto de confluência gravado[^]*O mapa não marca um ponto estimado`))
})

test('copiar resumo: só com leitura de agora, e o texto vai para copiar, nunca é enviado', async () => {
  const fresca = aoVivo([leitura('Rio do Sul', 'rio-do-sul', 20, 4.5)])
  const { amb } = ambiente(null, '/acu/rio-do-sul', dadosFalsos(fresca))
  const s = await executar([{ tipo: 'copiar_resumo', cidadeId: 'rio-do-sul' }], amb, cat, fora, ajuda)
  assert.ok(s.copiar && /Rio do Sul — 4,50 m/.test(s.copiar))
  assert.match(s.copiar!, /Medido às 14:40 de 06\/10/)
  assert.ok(!/https?:|pages\.dev|github/.test(s.copiar!), 'sem endereço do site (D4)')
  assert.match(s.texto, /Quem envia é você/)
  const velha = await executar([{ tipo: 'copiar_resumo', cidadeId: 'rio-do-sul' }], ambiente(null, '/', dadosFalsos(aoVivo([leitura('Rio do Sul', 'rio-do-sul', 400, 4.5)]))).amb, cat, fora, ajuda)
  assert.equal(velha.copiar, undefined)
  assert.match(velha.texto, /Não há leitura de agora/)
  const itajai = await executar([{ tipo: 'copiar_resumo', cidadeId: 'itajai' }], ambiente(null, '/', dadosFalsos(fresca)).amb, cat, fora, ajuda)
  assert.match(itajai.texto, /várias réguas/)
})

test('copiar link: do Monitor, com régua e fundo, e o aviso do acesso restrito', async () => {
  const m = monitorFalso('itajai')
  const { amb } = ambiente(m, '/monitor/itajai', dadosFalsos(null))
  const s = await executar([{ tipo: 'copiar_link' }], amb, cat, { cidadeAtual: 'itajai', naMonitor: true, reguaAtual: 'DC-05' }, ajuda)
  assert.equal(s.copiar, 'https://site.example/#/monitor/itajai?regua=DC-05&fundo=satelite')
  assert.match(s.texto, /só abre para e-mail cadastrado/)
})

test('sem leituras carregadas: diz que não conseguiu, não inventa', async () => {
  const s = await executar([{ tipo: 'atrasadas' }], ambiente(null, '/', dadosFalsos(null)).amb, cat, fora, ajuda)
  assert.match(s.texto, /Não consegui carregar as leituras agora/)
  const semDados = await executar([{ tipo: 'atrasadas' }], ambiente(null).amb, cat, fora, ajuda)
  assert.match(semDados.texto, /Não consegui carregar/)
})

test('gráfico: abre a página da cidade no cartão "Últimas horas"; Itajaí não tem gráfico só', async () => {
  const { amb, navegacoes } = ambiente(null)
  await executar([{ tipo: 'abrir_grafico', cidadeId: 'blumenau' }], amb, cat, fora, ajuda)
  await executar([{ tipo: 'abrir_grafico', cidadeId: 'brusque' }], amb, cat, fora, ajuda)
  const ita = await executar([{ tipo: 'abrir_grafico', cidadeId: 'itajai' }], amb, cat, fora, ajuda)
  assert.deepEqual(navegacoes, ['/acu/blumenau?secao=grafico', '/mirim/brusque?secao=grafico', '/itajai'])
  assert.match(ita.texto, /onze réguas/)
})

test('última hora em Itajaí sem régua escolhida: pergunta, com as réguas da cidade', async () => {
  const p = (m: number, n: number, regua: string): PontoSerie => ({ medidoEm: minAtras(m), nivel_m: n, regua })
  const v = aoVivo([], { series: { 'itajai-acu': { itajai: [p(10, 1, 'DC-01 x'), p(5, 8, 'DC-10 y')] } } })
  const s = await executar([{ tipo: 'ultima_hora', cidadeId: 'itajai' }], ambiente(null, '/', dadosFalsos(v)).amb, cat, fora, ajuda)
  assert.match(s.texto, /Itajaí tem 2 réguas, cada uma com o seu zero/)
  assert.ok(s.sugestoes?.includes('comparar as réguas de Itajaí'))
})

test('a ajuda lista os pedidos novos', () => {
  const t = textoDeAjuda({ cidadeAtual: 'itajai', naMonitor: true, reguaAtual: null }, 'Itajaí').texto
  for (const f of ['só as réguas sem leitura', 'confluência do Benedito', 'leituras estão atrasadas', 'última hora', 'montante', 'copiar link']) {
    assert.ok(t.includes(f), f)
  }
})
