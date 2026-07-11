"""
aplicar_vinculos.py

Aplica os vinculos manuais (vinculos_manuais.py) no data/internacionais.json
ATUAL, sem precisar rerodar o BERT. Rode sempre que editar VINCULOS.

Uso:
    cd scripts/
    python aplicar_vinculos.py
"""

import json
import os
import sys

import vinculos_manuais as vm

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_INT = os.path.join(RAIZ, "data", "internacionais.json")
PATH_NAC = os.path.join(RAIZ, "data", "filmes.json")


def main():
    with open(PATH_INT, encoding="utf-8") as f:
        internacionais = json.load(f)
    with open(PATH_NAC, encoding="utf-8") as f:
        nacionais = json.load(f)
    nac_por_tmdb = {x["tmdb_id"]: x for x in nacionais}

    aplicados = vm.aplicar(internacionais, nac_por_tmdb)

    with open(PATH_INT, "w", encoding="utf-8") as f:
        json.dump(internacionais, f, ensure_ascii=False, indent=2)

    print(f"Vinculos manuais aplicados: {aplicados}")
    # resumo
    for tid, links in vm.VINCULOS.items():
        fi = next((x for x in internacionais if x["tmdb_id"] == tid), None)
        if not fi:
            print(f"  {tid}: (internacional nao esta no pool)")
            continue
        topo = fi["similares_nacionais"][0] if fi["similares_nacionais"] else {}
        alvo = nac_por_tmdb.get(links[0], {}).get("titulo", "?")
        marca = "OK" if topo.get("manual") else "FALHOU"
        print(f"  [{marca}] {fi['titulo']}  ->  {alvo}  (topo manual={topo.get('manual')})")


if __name__ == "__main__":
    main()
