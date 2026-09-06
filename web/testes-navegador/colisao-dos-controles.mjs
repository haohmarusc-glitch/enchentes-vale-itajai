/**
 * OS CONTROLES DO MONITOR NÃO PODEM SE COBRIR.
 *
 * O que esta sonda reprova, e que já aconteceu em produção:
 *  - a barra de reprodução por cima dos botões Escuro/Satélite/Mapa (o fundo
 *    do mapa aparecia e não trocava — `z-index` decide quem recebe o toque,
 *    não quem ocupa o espaço);
 *  - o rodapé subindo por cima do botão "−", que é como se volta para a bacia
 *    inteira depois de se perder no zoom;
 *  - a legenda e a barra desenhadas por cima do menu de cidades aberto.
 *
 * Mede duas coisas por caso: se as CAIXAS dos blocos se cruzam, e quem recebe
 * o toque no centro de cada botão (`elementFromPoint`).
 *
 * Botão fora da janela, ou rolado para fora do painel que o contém, NÃO conta
 * como coberto — foi o engano que fez esta sonda mentir três vezes antes de
 * ficar de pé.
 */
import { abrir } from './base.mjs'
const SAIDA = process.env.SAIDA || '.'
const casos = [[1280, 900], [1440, 700], [1920, 1080], [390, 844], [360, 640]]
let falhas = 0
for (const menuAberto of [false, true]) {
  console.log(`\n=== menu de cidades ${menuAberto ? 'ABERTO' : 'fechado'} ===`)
  for (const [w, h] of casos) {
    const { b, pg } = await abrir('#/monitor', { largura: w, altura: h })
    // O mapa precisa estar DENTRO da janela: elementFromPoint devolve null
    // fora dela, e "null" não é "coberto".
    await pg.evaluate(() => document.querySelector('canvas')?.scrollIntoView({ block: 'center' }))
    await pg.waitForTimeout(500)
    if (menuAberto) { await pg.getByRole('button', { name: /Cidades/ }).click(); await pg.waitForTimeout(800) }
    const r = await pg.evaluate(() => {
      const cruza = (a, c) => a.left < c.right && c.left < a.right && a.top < c.bottom && c.top < a.bottom
      const fundos = document.querySelector('[aria-label="Fundo do mapa"]')
      const legenda = fundos?.closest('[class*="_legenda_"]')
      const folhas = {
        zoom: document.querySelector('[aria-label="Zoom do mapa"]'),
        menu: document.querySelector('#menu-cidades'),
        topo: document.querySelector('[class*="_topo_"]'),
        legenda,
        controles: document.querySelector('[class*="_controles_"]'),
      }
      const nomes = Object.keys(folhas).filter(n => folhas[n])
      const colisoes = []
      for (let i = 0; i < nomes.length; i++) for (let j = i + 1; j < nomes.length; j++) {
        const a = folhas[nomes[i]], c = folhas[nomes[j]]
        if (a.contains(c) || c.contains(a)) continue
        if (cruza(a.getBoundingClientRect(), c.getBoundingClientRect())) colisoes.push(`${nomes[i]}×${nomes[j]}`)
      }
      const vh = innerHeight, vw = innerWidth
      const cobertos = [], foraDaJanela = []
      for (const btn of document.querySelectorAll(
        '[aria-label="Zoom do mapa"] button, [aria-label="Fundo do mapa"] button, #menu-cidades button')) {
        const k = btn.getBoundingClientRect()
        if (k.width === 0 || k.height === 0) continue
        const cx = k.left + k.width / 2, cy = k.top + k.height / 2
        const nome = (btn.getAttribute('aria-label') || btn.textContent.trim()).slice(0, 16)
        if (cx < 0 || cy < 0 || cx > vw || cy > vh) { foraDaJanela.push(nome); continue }
        // Rolado para fora DENTRO do próprio painel (o menu tem barra de
        // rolagem): não está coberto, está fora da parte visível dele.
        let recortado = false
        for (let p = btn.parentElement; p && p !== document.body; p = p.parentElement) {
          const s = getComputedStyle(p)
          if (s.overflowY === 'auto' || s.overflowY === 'scroll' || s.overflowY === 'hidden') {
            const pk = p.getBoundingClientRect()
            if (cy < pk.top || cy > pk.bottom || cx < pk.left || cx > pk.right) { recortado = true; break }
          }
        }
        if (recortado) { foraDaJanela.push(nome); continue }
        const el = document.elementFromPoint(cx, cy)
        if (!(el === btn || btn.contains(el))) cobertos.push(`${nome}←${(el?.className || el?.tagName || 'null').toString().slice(0, 18)}`)
      }
      return { colisoes, cobertos, foraDaJanela: foraDaJanela.length }
    })
    const ok = r.colisoes.length === 0 && r.cobertos.length === 0
    if (!ok) falhas++
    console.log(`  ${String(w).padStart(4)}x${h}: ${ok ? 'OK' : 'FALHA'}` +
      (r.colisoes.length ? ` colisões=[${r.colisoes}]` : '') +
      (r.cobertos.length ? ` cobertos=[${r.cobertos.slice(0, 4)}]` : '') +
      (r.foraDaJanela ? ` (${r.foraDaJanela} fora da janela, não contam)` : ''))
    if (!ok) await pg.screenshot({ path: `${SAIDA}/falha-${w}x${h}-menu${menuAberto}.png` })
    await b.close()
  }
}
console.log(`\n${falhas} caso(s) com falha.`)
process.exit(falhas === 0 ? 0 : 1)
