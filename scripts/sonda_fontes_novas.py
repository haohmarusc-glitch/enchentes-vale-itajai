#!/usr/bin/env python3
"""
Sonda das duas fontes de tempo real mapeadas em `docs/fontes-tempo-real.md`.

Elas resolveriam o maior buraco do projeto — dez das quinze cidades não têm
nível ao vivo, e Blumenau, que tem a série histórica mais longa, é uma delas:

* **Defesa Civil de SC**, GraphQL: 174 estações no estado, 61 na bacia do
  Itajaí, incluindo Timbó, Ibirama, Apiúna, Guabiruba, Botuverá e as barragens.
* **AlertaBlu / Defesa Civil de Blumenau**: `nivel_oficial.json`, com série
  horária do Itajaí-Açu em Blumenau.

Esta sonda NÃO coleta e NÃO escreve em `data/`. Ela responde três perguntas
que precisam de resposta antes de qualquer coletor entrar em produção:

1. **O robots.txt de Blumenau permite?** O AlertaBlu foi recusado antes por
   isso (`docs/cotas-de-ruas.md`), e a mesma régua vale agora que a fonte
   interessa mais. A sonda lê o robots — que é feito para robô ler — e mostra
   a regra para cada caminho que se pretende usar.
2. **A cadeia de certificado de Blumenau fecha?** A sondagem de 30/08 falhou
   com "unable to get local issuer certificate". Desligar a verificação não é
   opção: abriria a coleta para qualquer um no caminho injetar nível de rio.
3. **Quais estações a Defesa Civil de SC publica na bacia, com que código e
   que nível agora?** Sem isso não dá para mapear estação → cidade, e sem esse
   mapa nenhuma leitura pode virar aviso: ela seria comparada com a cota de
   outra régua.

Uso na VPS (daqui do sandbox nenhum destes domínios responde):
    python3 scripts/sonda_fontes_novas.py 2>&1 | tee /tmp/fontes_novas.txt
"""

import json
import re
import sys
import time

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"
PAUSA_S = 1.0

BLUMENAU = "https://defesacivil.blumenau.sc.gov.br"
CAMINHOS_BLUMENAU = ["/static/data/nivel_oficial.json", "/static/data/situacao_atual.json",
                     "/p/enchentes", "/p/cotas"]
GRAPHQL = "https://monitoramento.defesacivil.sc.gov.br/graphql"
CLIENTE = "secretaria-de-defesa-civil"

Q_TAGS = """query Tags_data { tags_data(clients: ["%s"]) { qualle_meteorologia {
  codigo name { prefix general local } timestamp
  position { bacia latitude longitude regiao altitude }
  data { rio { rio_nome { value } rio_nivel { value unit { value } }
               rio_nivel_tendencia { value } }
         chuva { acumulado { h001 { value } h024 { value } } } } } } }""" % CLIENTE


def buscar(url, **extra):
    import requests

    time.sleep(PAUSA_S)
    return requests.get(url, headers={"User-Agent": UA}, timeout=30, **extra)


def cabecalho(titulo, url=""):
    print(f"\n{'=' * 70}\n=== {titulo}" + (f"\n    {url}" if url else ""))


def robots_permite(texto: str, caminho: str) -> bool:
    """Só as regras do agente `*`. `Disallow:` vazio é permissão explícita."""
    atual, proibidos = None, []
    for linha in texto.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if not linha or ":" not in linha:
            continue
        chave, valor = (p.strip() for p in linha.split(":", 1))
        if chave.lower() == "user-agent":
            atual = valor
        elif chave.lower() == "disallow" and atual == "*" and valor:
            proibidos.append(valor)
    return not any(caminho.startswith(p) for p in proibidos)


def sondar_blumenau():
    cabecalho("Blumenau — o robots.txt permite?", BLUMENAU + "/robots.txt")
    try:
        r = buscar(BLUMENAU + "/robots.txt")
    except Exception as e:
        print(f"    FALHOU: {e}")
        print("    Se for erro de certificado, é o mesmo de 30/08. NÃO desligar a verificação:")
        print("    isso abriria a coleta para qualquer um no caminho injetar nível de rio.")
        print("    O conserto é instalar a cadeia intermediária no servidor — ou pedir o dado")
        print("    à Defesa Civil por outro caminho.")
        return
    print(f"    HTTP {r.status_code} · {len(r.content)} bytes")
    if r.status_code == 200:
        for linha in r.text.splitlines()[:25]:
            print(f"      {linha}")
        print()
        for c in CAMINHOS_BLUMENAU:
            print(f"    {'PODE   ' if robots_permite(r.text, c) else 'PROIBE '} {c}")
    else:
        print("    sem robots.txt publicado — a norma trata isso como permissão")

    print("\n    --- o que cada caminho responde (só cabeçalho, sem guardar nada):")
    for c in CAMINHOS_BLUMENAU:
        try:
            p = buscar(BLUMENAU + c)
            tipo = p.headers.get("Content-Type", "?")[:40]
            print(f"      {p.status_code} {len(p.content):>8} bytes  {tipo}  {c}")
            if c.endswith("nivel_oficial.json") and p.status_code == 200:
                try:
                    d = p.json()
                    print(f"         chaves: {list(d)[:8]}")
                    niveis = d.get("niveis") or []
                    print(f"         pontos na série: {len(niveis)}")
                    if niveis:
                        print(f"         último: {json.dumps(niveis[-1], ensure_ascii=False)[:200]}")
                    cond = d.get("condicoes") or d.get("condicao")
                    if cond:
                        print(f"         faixas: {json.dumps(cond, ensure_ascii=False)[:300]}")
                except ValueError:
                    print("         (não é JSON)")
        except Exception as e:
            print(f"      FALHOU {c}: {e}")


def sondar_defesacivil_sc():
    cabecalho("Defesa Civil de SC — GraphQL", GRAPHQL)
    import requests

    try:
        time.sleep(PAUSA_S)
        r = requests.post(GRAPHQL, json={"query": Q_TAGS, "operationName": "Tags_data"},
                          headers={"User-Agent": UA}, timeout=60)
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    print(f"    HTTP {r.status_code} · {len(r.content)} bytes")
    if r.status_code != 200:
        print(f"    corpo: {r.text[:300]}")
        return
    try:
        corpo = r.json()
    except ValueError:
        print(f"    resposta não é JSON: {r.text[:200]}")
        return
    if corpo.get("errors"):
        print(f"    a consulta foi recusada: {json.dumps(corpo['errors'], ensure_ascii=False)[:400]}")
        return

    estacoes = (((corpo.get("data") or {}).get("tags_data") or {})
                .get("qualle_meteorologia") or [])
    print(f"    estações no estado: {len(estacoes)}")

    def bacia(s):
        return ((s.get("position") or {}).get("bacia") or "")

    do_itajai = [s for s in estacoes if "itaja" in bacia(s).lower()]
    print(f"    na bacia do Itajaí: {len(do_itajai)}")
    print()
    print(f"    {'código':14} {'nível':>8} {'chuva 24h':>10} {'rio':22} estação")
    for s in sorted(do_itajai, key=lambda x: x.get("codigo") or ""):
        d = (s.get("data") or {})
        rio = (d.get("rio") or {})
        nivel = ((rio.get("rio_nivel") or {}).get("value"))
        rio_nome = ((rio.get("rio_nome") or {}).get("value") or "")
        chuva = (((d.get("chuva") or {}).get("acumulado") or {}).get("h024") or {}).get("value")
        nome = " ".join(x for x in [(s.get("name") or {}).get("general"),
                                    (s.get("name") or {}).get("local")] if x)
        print(f"    {str(s.get('codigo')):14} {str(nivel):>8} {str(chuva):>10} "
              f"{str(rio_nome)[:22]:22} {nome[:40]}")

    # O que decide se dá para usar: existe cota por estação nesta resposta?
    print()
    print("    campos disponíveis numa estação (para saber se vem cota de referência):")
    if do_itajai:
        print("      " + json.dumps(do_itajai[0], ensure_ascii=False)[:900])


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    print(__doc__)
    sondar_blumenau()
    sondar_defesacivil_sc()
    print("\n" + "=" * 70)
    print("O que decide: (1) se o robots de Blumenau permite os /static/data/;")
    print("(2) se a cadeia de certificado fecha; (3) quantas estações da bacia a")
    print("Defesa Civil de SC publica e se a resposta traz COTA por estação.")
    print("Sem cota por estação, nenhuma leitura nova pode virar aviso — ela seria")
    print("comparada com a cota de outra régua, que é o erro que o projeto recusa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
