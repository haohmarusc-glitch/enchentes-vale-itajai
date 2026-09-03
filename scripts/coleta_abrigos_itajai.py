#!/usr/bin/env python3
"""
Baixa os abrigos oficiais da Defesa Civil de Itajaí do ArcGIS da Prefeitura.

Serviço PÚBLICO, sem token (descoberto em 02/09/2026):
  https://arcgis.itajai.sc.gov.br/server/rest/services/Hosted/Abrigos_Defesa_Civil_view_completo/FeatureServer/0/query

Armadilhas já tratadas: usar `f=json` (com `f=geojson` este serviço dá HTTP 500);
é o `_view_completo` em `Hosted/` (aberto), não o de `defesacivil/` (exige token);
os campos vêm truncados pelo ArcGIS (`nome_do_ab`, `sigla_do_a`, `capacida_2`).

REGRA DE EXIBIÇÃO (por que este coletor NÃO grava situacao/lotacao): a fonte tem
`situacao` e `lotacao`, mas eles são CADASTRO, não estado atual. Se entrassem no
arquivo, mais cedo ou mais tarde alguém os renderizaria como "aberto agora" numa
tela de enchente. Preferimos que o dado não exista a que exista com risco de ser
mal lido — quem ativa abrigo e manda evacuar é a Defesa Civil (199). O
`data/abrigos-itajai.json` é gerado SEM esses campos, e o site mostra a ressalva.

Rodar na VPS: o container do assistente tem proxy que bloqueia este host.

Uso: python3 scripts/coleta_abrigos_itajai.py   → data/abrigos-itajai.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = ("https://arcgis.itajai.sc.gov.br/server/rest/services/Hosted/"
        "Abrigos_Defesa_Civil_view_completo/FeatureServer/0/query")
UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
SAIDA = Path(__file__).resolve().parent.parent / "data" / "abrigos-itajai.json"

AVISO = ("Esta lista é CADASTRO de abrigos, NÃO estado atual. NUNCA exibir como 'aberto agora' "
         "nem sugerir que o morador se dirija a um deles por conta própria. Quem ATIVA abrigo e "
         "manda evacuar é a Defesa Civil (199). O site pode mostrar 'abrigo cadastrado mais próximo' "
         "como INFORMAÇÃO, com essa ressalva.")


def baixar() -> dict:
    r = requests.get(BASE, params={"where": "1=1", "outFields": "*", "outSR": 4326, "f": "json"},
                     headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("error"):
        raise RuntimeError(f"ArcGIS: {j['error']}")
    return j


def converter(j: dict) -> list[dict]:
    """Só os campos que servem para INFORMAR — situacao/lotacao ficam de fora de propósito."""
    out = []
    for f in j.get("features", []):
        a = f.get("attributes", {})
        g = f.get("geometry") or {}
        nome = (a.get("nome_do_ab") or "").replace("_", " ").strip() or None
        out.append({
            "nome": nome,
            "endereco": a.get("endereco"),
            "zona_defesa_civil": a.get("sigla_do_a"),   # ex.: Z2-2, Z10-6
            "capacidade": a.get("capacida_2"),
            "lat": g.get("y"),
            "lon": g.get("x"),
        })
    return out


def main() -> int:
    try:
        j = baixar()
    except Exception as e:  # noqa: BLE001 — a rede é o ponto frágil; reporta e sai
        print(f"ERRO ao baixar abrigos: {e}", file=sys.stderr)
        return 1
    abrigos = converter(j)
    com_coord = [a for a in abrigos if a["lat"] is not None and a["lon"] is not None]
    sem_nome = sum(1 for a in abrigos if not a["nome"])
    sem_zona = sum(1 for a in abrigos if not a["zona_defesa_civil"])
    caps = [a["capacidade"] for a in abrigos if isinstance(a["capacidade"], (int, float))]
    saida = {
        "_meta": {
            "origem": "ArcGIS da Prefeitura de Itajaí — Hosted/Abrigos_Defesa_Civil_view_completo (FeatureServer, público sem token)",
            "url": BASE,
            "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total": len(abrigos),
            "com_coordenada": len(com_coord),
            "AVISO_EXIBICAO": AVISO,
            "campos_descartados": "situacao e lotacao existem na fonte mas NÃO foram importados — seriam lidos como estado atual.",
            "qualidade": (f"{sem_nome} registro(s) sem nome/endereço na fonte (só coordenada). "
                          f"{sem_zona} sem zona de Defesa Civil. "
                          f"Capacidade de {min(caps)} a {max(caps)}." if caps else ""),
            "atualizar_com": "scripts/coleta_abrigos_itajai.py (usar f=json; f=geojson dá HTTP 500 neste serviço)",
        },
        "abrigos": abrigos,
    }
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(abrigos)} abrigos ({len(com_coord)} com coordenada) → {SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
