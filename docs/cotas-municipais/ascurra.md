# Ascurra — Ponte do Beber e cotas

**Site da Prefeitura:** https://ascurra.sc.gov.br/  
**COMPDEC:** (47) 98410-0763 · sem portal próprio de monitoramento  
**Estação no monitor:** DCSC-00003 · tronco do Itajaí-Açu  
**Consulta:** 3 de setembro de 2026  
**Emergência:** 199. Este arquivo não substitui aviso oficial.

Não há API municipal. Nível ao vivo: mapa DC-SC. A Prefeitura publica prevenção (plano familiar, cores de alerta estaduais), não régua ao vivo.

---

## Faixas oficiais (Ponte do Beber)

Fonte: Prefeitura / Defesa Civil Municipal, 22 de maio de 2026 ([Instagram @prefeituraascurra](https://www.instagram.com/p/DYpKHbxgGsq/)).

| Fase | Faixa |
|---|---|
| Monitoramento | até **8,50 m** |
| Atenção | 8,50 a **9,76 m** |
| Alerta | 9,76 a **10,76 m** |
| Emergência | acima de **10,76 m** |

A **9,76 m** o primeiro ponto de interdição é a **Travessa Zonta** (acesso ao rio; há pedido de dique nesse ponto).

```json
"cotas_m": {
  "monitoramento_ate": 8.5,
  "atencao": 8.5,
  "alerta": 9.76,
  "emergencia": 10.76
}
```

**Conferir régua:** o monitor mostra ~7,95 m bruto na DCSC-00003. A escala 8,5–10,8 m é alta frente a Indaial (6 m) e Rio do Sul (4,5–6,5). Só pintar se a Ponte do Beber for a mesma estação. Se não for, cadastrar cotas só na régua municipal.

---

## O que o site tem (e não tem)

Tem: cores de alerta da DC-SC, kit de emergência, telefone da COMPDEC.  
Não tem: página “nível do rio”, JSON, mancha por cota, tabela de rua.

Demanda ao Estado (2026): equipamentos, drenagem no bairro Estação, dique na Travessa Zonta, macrodrenagem Centro/Vila Nova.
