/** Regressão da simulação, sem depender de fontes ao vivo. Rodar após o build. */
import assert from 'node:assert/strict'
import { mkdirSync } from 'node:fs'
import { chromium } from 'playwright'
import { preview } from 'vite'

const servidor = await preview({ preview: { port: 4327, strictPort: true } })
const navegador = await chromium.launch()
const base = servidor.resolvedUrls.local[0].replace(/\/$/, '')
mkdirSync('../tmp/pesquisa-chegada', { recursive: true })
try {
  for (const [largura, fuso] of [[390, 'Asia/Tokyo'], [1280, 'America/Sao_Paulo']]) {
    const pagina = await navegador.newPage({ viewport: { width: largura, height: 950 }, timezoneId: fuso })
    const erros = []
    pagina.on('pageerror', (e) => erros.push(e.message))
    await pagina.route('**/*', (rota) => new URL(rota.request().url()).origin === new URL(base).origin
      ? rota.continue() : rota.abort())
    await pagina.goto(`${base}/#/itajai`)
    const painel = pagina.locator('section[aria-labelledby="simulacao-chegada-titulo"]')
    await painel.waitFor()
    assert.match(await painel.innerText(), /Média histórica indisponível/)
    await pagina.getByLabel('Data e hora do pico em Blumenau — Brasília').fill('2026-09-11T10:00')
    await pagina.getByRole('button', { name: 'Simular coincidência com a maré' }).click()
    assert.match(await painel.innerText(), /12\/09\/2026, 00:00 até 12\/09\/2026, 03:00/)
    assert.match(await painel.innerText(), /Há preamar dentro da janela simulada/)
    assert.equal(await painel.locator('table tbody tr').count(), 3)
    assert.equal(await pagina.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
    await painel.screenshot({ path: `../tmp/pesquisa-chegada/simulacao-${largura}.png` })
    await pagina.getByLabel('Data e hora do pico em Blumenau — Brasília').fill('2027-02-01T10:00')
    assert.equal(await painel.getByRole('heading', { name: 'Janela de chegada neste cenário' }).count(), 0)
    await pagina.getByRole('button', { name: 'Simular coincidência com a maré' }).click()
    assert.match(await painel.innerText(), /Tábua insuficiente/)
    assert.equal(await painel.locator('table').count(), 0)
    await pagina.getByLabel('Tempo entre os picos').selectOption('manual')
    await pagina.getByLabel('Mínimo (horas)').fill('20')
    await pagina.getByLabel('Máximo (horas)').fill('18')
    await pagina.getByRole('button', { name: 'Simular coincidência com a maré' }).click()
    assert.match(await painel.getByRole('alert').innerText(), /mínimo menor que o máximo/)
    await pagina.getByLabel('Máximo (horas)').fill('23')
    await pagina.getByRole('button', { name: 'Simular coincidência com a maré' }).click()
    assert.match(await painel.innerText(), /Intervalo hipotético informado por você/)
    await painel.locator('summary').click()
    assert.match(await painel.innerText(), /Setembro de 2011: 19 h relatadas/)
    assert.deepEqual(erros, [])
    console.log(`OK: ${largura}px / ${fuso}, limites, falta de tábua, entrada inválida, troca de cenário e pesquisa.`)
    await pagina.close()
  }
} finally {
  await navegador.close()
  await servidor.httpServer.close()
}
