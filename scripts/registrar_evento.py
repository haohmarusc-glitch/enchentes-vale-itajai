"""Arquiva os JSONs dos coletores sem alterar leituras ou publicar alertas."""
import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESPERADOS = ("ultimo.json", "ultimo_nivel_sc.json", "ultimo_barragens.json",
             "ultimo_taio.json", "ultimo_gaspar.json")


def registrar(entrada: Path, destino: Path, evento: str) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", evento):
        raise ValueError("Identificador de evento inválido")
    pasta = destino / evento
    objetos = pasta / "objetos"
    objetos.mkdir(parents=True, exist_ok=True)
    registro = {"registrado_em": datetime.now(timezone.utc).isoformat(),
                "evento": evento, "arquivos": {}, "problemas": {}}
    nomes = sorted(set(ESPERADOS) | {p.name for p in entrada.glob("ultimo*.json")})
    for nome in nomes:
        try:
            bruto = (entrada / nome).read_bytes()
            dados = json.loads(bruto)
            if not isinstance(dados, dict):
                raise ValueError("JSON não é objeto")
            sha = hashlib.sha256(bruto).hexdigest()
            arquivo = objetos / f"{sha}.json.gz"
            # Publicação atômica: um leitor nunca encontra gzip incompleto.
            if not arquivo.exists():
                temporario = objetos / f"{sha}.tmp"
                temporario.write_bytes(gzip.compress(bruto, mtime=0))
                temporario.replace(arquivo)
            registro["arquivos"][nome] = {"sha256": sha,
                "objeto": f"objetos/{sha}.json.gz",
                "coletado_em": dados.get("coletado_em")}
        except (OSError, ValueError) as erro:
            registro["problemas"][nome] = str(erro)
    with (pasta / "capturas.ndjson").open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=RAIZ / "data/tempo-real")
    parser.add_argument("--destino", type=Path, default=RAIZ / "data/eventos-registro")
    parser.add_argument("--evento")
    args = parser.parse_args()
    evento = args.evento
    if evento is None:
        config = json.loads((RAIZ / "data/evento-ativo.json").read_text(encoding="utf-8"))
        evento = config.get("evento")
    if not evento:
        return
    registro = registrar(args.entrada, args.destino, evento)
    print(f"Evento {evento}: {len(registro['arquivos'])} arquivos preservados; "
          f"{len(registro['problemas'])} ausentes ou inválidos.")


if __name__ == "__main__":
    main()
