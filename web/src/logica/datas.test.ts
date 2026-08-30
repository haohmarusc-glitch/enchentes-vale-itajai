import assert from 'node:assert/strict'
import { test } from 'node:test'
import { comparaData, dataCurta, dataLegivel, granularidade, mesmoEvento } from './datas'

test('granularidade reconhece ISO parcial', () => {
  assert.equal(granularidade('2011-09-09'), 'dia')
  assert.equal(granularidade('1983-07'), 'mes')
  assert.equal(granularidade('1855'), 'ano')
})

test('mesmoEvento casa datas próximas — o pico desce o rio ao longo de dias', () => {
  assert.ok(mesmoEvento('2011-09-09', '2011-09-09'))
  assert.ok(mesmoEvento('2011-09-09', '2011-09'))
  assert.ok(mesmoEvento('2011-09-10', '2011-09-09'))
  assert.ok(mesmoEvento('2008-11-23', '2008-11-25'))
  assert.ok(mesmoEvento('2023-10-31', '2023-11-02'), 'a virada do mês não separa um evento')
})

test('mesmoEvento separa eventos distantes', () => {
  assert.equal(mesmoEvento('2011-09-09', '2011-09-20'), false)
  assert.equal(mesmoEvento('1983-07', '1983-08'), false, 'meses vizinhos são eventos distintos')
  assert.equal(mesmoEvento('2023-10-13', '2023-11'), false)
  assert.ok(mesmoEvento('2023-11-17', '2023-11'))
})

test('mesmoEvento recusa pareamento por ano — 2023 teve duas enchentes', () => {
  assert.equal(mesmoEvento('2023-10-13', '2023-11-17'), false)
  assert.equal(mesmoEvento('2023-10-13', '2023'), false)
  assert.equal(mesmoEvento('1984', '1984'), false)
})

test('dataLegivel em português', () => {
  assert.equal(dataLegivel('2011-09-09'), '9 de setembro de 2011')
  assert.equal(dataLegivel('1983-07'), 'julho de 1983')
  assert.equal(dataLegivel('1855'), '1855')
  assert.equal(dataCurta('2011-09-09'), '09/09/2011')
})

test('comparaData ordena datas de granularidade mista', () => {
  const datas = ['2011-09-09', '1855', '1983-07', '2023-11-17']
  assert.deepEqual([...datas].sort(comparaData), ['1855', '1983-07', '2011-09-09', '2023-11-17'])
})
