#!/usr/bin/env python3
"""
Segunda sonda: entrar nos JavaScripts onde os endereços de dados se escondem.

A primeira sonda respondeu o que era possível pela superfície. O que ela achou,
e que motiva esta:

* **CEMADEN** — o mapa responde, mas os endereços históricos que eu supunha
  (`sjc.salvar.cemaden.gov.br`, `dadosabertos.cemaden.gov.br`) **não resolvem
  mais**. A aplicação é OpenLayers antiga e busca os dados de algum lugar
  citado dentro de `js/script.js`. Mesmo padrão do `ajax/mares.php`, que
  também só apareceu quando lemos o JavaScript.
* **Defesa Civil de SC** — a página é uma aplicação de página única que lê a
  configuração de `mkssistemas.com.br/static-json/config.json`. A MKS é a mesma
  empresa da estação "Rio do Sul Estação MKS" que já coletamos. O config
  provavelmente aponta para a API de verdade.
* **Itajaí, Mapa.php** — 30 coordenadas na faixa de SC, com Leaflet. Falta
  parear cada uma com o nome da estação: por isso esta sonda imprime o trecho
  ao redor de cada coordenada, em vez de só contá-las.
* **AlertaBlu** — falha na verificação do certificado: "unable to get local
  issuer certificate". Quase sempre é o servidor não enviando a cadeia
  intermediária. A saída NÃO é desligar a verificação — isso abriria a coleta
  para qualquer um no caminho injetar número de nível de rio. Esta sonda
  diagnostica de que tipo é a falha, para escolher o conserto certo.

  E o AlertaBlu importa mais do que por chuva: ele publica **cotas de ruas** —
  em que nível do rio cada rua de Blumenau começa a alagar. É a informação mais
  útil que existe para quem mora lá, porque a pergunta real de quem está com
  medo não é "quantos metros" e sim "a MINHA rua". E é sugestão sem nenhuma
  previsão no meio: com o rio em 8,60 m, a tabela diz quais ruas já alagam
  nesse nível. Leitura de tabela, não modelo. Por isso a sonda também procura
  onde essa tabela mora.

Uso na VPS:
    python3 scripts/sonda_fontes2.py 2>&1 | tee /tmp/fontes2.txt
"""

import re
import ssl
import sys

UA = "enchentes-vale-itajai/0.1 (+https://github.com/haohmarusc-glitch/enchentes-vale-itajai)"

#: Endereços dentro de JavaScript: o que o mapa busca quando alguém abre.
RE_ENDPOINT = re.compile(
    r"""['"]([^'"\s]{4,120}?(?:\.json|\.php|/dados/|/api/|/rest/|/resources/dados)[^'"\s]{0,80})['"]""",
    re.I,
)
RE_AJAX = re.compile(
    r"""(?:\$\.(?:get|post|ajax|getJSON)|fetch|XMLHttpRequest|\.open)\s*\(\s*['"]?([^'")\s]{4,140})""",
    re.I,
)

JS = [
    ("CEMADEN — script principal", "https://mapainterativo.cemaden.gov.br/js/script.js"),
    ("CEMADEN — interface", "https://mapainterativo.cemaden.gov.br/template/js/interface.js"),
    ("CEMADEN — popups", "https://mapainterativo.cemaden.gov.br/js/FeaturePopups.min.js"),
    ("Defesa Civil SC — config", "https://mkssistemas.com.br/static-json/config.json"),
    ("Defesa Civil SC — aplicação", "https://monitoramento.defesacivil.sc.gov.br/assets/DjiAQoA-3o.js"),
    ("Itajaí — dashboard.js", "https://defesacivil.itajai.sc.gov.br/monitoramento/js/dashboard.js?v=1.8"),
]

MAPA_ITAJAI = "https://defesacivil.itajai.sc.gov.br/monitoramento/Mapa.php"
ALERTABLU = "https://alertablu.blumenau.sc.gov.br/"


def buscar(url: str, **extra):
    import requests

    return requests.get(url, headers={"User-Agent": UA}, timeout=30, **extra)


def endpoints(texto: str) -> list[str]:
    achados = set(RE_ENDPOINT.findall(texto)) | set(RE_AJAX.findall(texto))
    # Fora bibliotecas e folhas de estilo: procuramos dado, não recurso.
    return sorted(
        e for e in achados
        if not re.search(r"\.(css|png|jpg|gif|svg|woff2?|ttf)(\?|$)", e, re.I)
        and "jquery" not in e.lower()
    )


def sondar_js() -> None:
    for nome, url in JS:
        print(f"\n=== {nome}\n    {url}")
        try:
            r = buscar(url)
        except Exception as e:
            print(f"    FALHOU: {e}")
            continue
        print(f"    HTTP {r.status_code} · {len(r.content)} bytes")
        if r.status_code != 200:
            continue
        # Se for JSON pequeno, mostra inteiro: é configuração, e é curta.
        if r.text.lstrip()[:1] in "{[" and len(r.text) < 4000:
            print("    corpo inteiro (é configuração, e é curta):")
            for linha in r.text.splitlines():
                print(f"      {linha}")
            continue
        achados = endpoints(r.text)
        print(f"    endereços de dado citados: {len(achados)}")
        for e in achados[:40]:
            print(f"      {e}")
        if not achados:
            print("      (nenhum — pode estar montado por concatenação de variáveis)")
            # Última tentativa: qualquer literal com cara de caminho.
            crus = sorted(set(re.findall(r"""['"](/[a-z0-9_\-/]{6,60})['"]""", r.text, re.I)))
            for e in crus[:20]:
                print(f"      caminho solto: {e}")


def sondar_mapa_itajai() -> None:
    """
    Parear coordenada com nome de estação.

    Não basta contar coordenadas: uma coordenada sem nome não serve para dizer
    "a régua mais próxima de você é a DC-09". Por isso o trecho ao redor.
    """
    print(f"\n=== Itajaí — pares nome/coordenada\n    {MAPA_ITAJAI}")
    try:
        r = buscar(MAPA_ITAJAI)
    except Exception as e:
        print(f"    FALHOU: {e}")
        return
    print(f"    HTTP {r.status_code} · {len(r.content)} bytes")
    if r.status_code != 200:
        return

    texto = r.text
    vistos = 0
    for m in re.finditer(r"-2[0-9]\.\d{3,}", texto):
        vistos += 1
        if vistos > 18:
            print("    ... (mais coordenadas adiante)")
            break
        ini, fim = max(0, m.start() - 260), min(len(texto), m.end() + 200)
        trecho = " ".join(texto[ini:fim].split())
        print(f"\n    --- coordenada {m.group(0)}")
        print(f"        {trecho}")


def sondar_alertablu() -> None:
    """
    De que tipo é a falha de certificado do AlertaBlu.

    Três hipóteses, com consertos diferentes:
    1. servidor não manda a cadeia intermediária -> baixar o intermediário e
       apontar o `verify` para um pacote que o inclua;
    2. certificado expirado ou para outro domínio -> não há conserto do nosso
       lado, e a fonte não serve;
    3. a VPS está com o pacote de raízes desatualizado -> `update-ca-certificates`
       resolve para todo mundo, não só para nós.

    Desligar a verificação NÃO está na lista: abriria a coleta para qualquer um
    no caminho injetar nível de rio.
    """
    print(f"\n=== AlertaBlu — diagnóstico do certificado\n    {ALERTABLU}")
    try:
        import certifi
        print(f"    pacote de raízes em uso: {certifi.where()}")
    except ImportError:
        print("    certifi não instalado (o requests usa o do sistema)")

    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE
    try:
        import socket

        with socket.create_connection(("alertablu.blumenau.sc.gov.br", 443), timeout=20) as cru:
            with contexto.wrap_socket(cru, server_hostname="alertablu.blumenau.sc.gov.br") as tls:
                cert = tls.getpeercert()
                print(f"    TLS negociado: {tls.version()}")
                print(f"    validade: {cert.get('notBefore')} até {cert.get('notAfter')}")
                print(f"    emitido para: {cert.get('subject')}")
                print(f"    emissor: {cert.get('issuer')}")
                print(f"    outros nomes: {cert.get('subjectAltName')}")
    except Exception as e:
        print(f"    não deu para inspecionar: {e}")

    # E a pergunta prática: com verificação normal, funciona?
    corpo = None
    try:
        r = buscar(ALERTABLU)
        corpo = r.text
        print(f"    com verificação normal: HTTP {r.status_code} · {len(r.content)} bytes")
    except Exception as e:
        print(f"    com verificação normal: FALHA — {type(e).__name__}")
        print(f"      {str(e)[:300]}")

    if corpo is None:
        # Sem TLS não dá para ler o site, mas dá para perguntar ao HTTP simples
        # onde ficam as páginas — o redirecionamento costuma revelar os caminhos.
        try:
            r = buscar("http://alertablu.blumenau.sc.gov.br/", allow_redirects=False)
            print(f"    em http simples: HTTP {r.status_code} -> {r.headers.get('Location')}")
        except Exception as e:
            print(f"    em http simples: FALHA — {type(e).__name__}")
        return

    ligacoes = sorted(set(re.findall(r"""href=['"]([^'"#]{2,120})['"]""", corpo, re.I)))
    interessantes = [
        l for l in ligacoes
        if re.search(r"cota|rua|pluvi|nivel|n[ií]vel|mapa|hidro|alag", l, re.I)
    ]
    print(f"    páginas com cara de cota de rua / nível / chuva: {len(interessantes)}")
    for l in interessantes[:30]:
        print(f"      {l}")
    if not interessantes:
        print(f"      (nenhuma entre {len(ligacoes)} ligações; o site pode ser montado em JS)")


def main() -> int:
    # Sem isto, `python3 sonda.py | tee arquivo.txt` — que é como a sonda é
    # usada — guarda tudo em bloco e só descarrega no fim: quem roda fica
    # olhando um terminal parado por meio minuto, sem saber se travou.
    sys.stdout.reconfigure(line_buffering=True)
    try:
        import requests  # noqa: F401
    except ImportError:
        sys.exit("Instale a dependência: pip install requests")

    sondar_js()
    sondar_mapa_itajai()
    sondar_alertablu()
    print("\n\nCole a saída de volta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
