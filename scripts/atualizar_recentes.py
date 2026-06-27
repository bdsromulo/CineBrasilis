"""
atualizar_recentes.py
(a) Busca filmes brasileiros lancados em maio e junho de 2026 e os adiciona
    ao filmes.json (sem duplicar os ja existentes).
(b) Classifica TODOS os filmes da base em Curta / Media / Longa pela duracao.

Reaproveita as funcoes de gerar_filmes.py.

Uso:
    cd scripts/
    python atualizar_recentes.py
"""

import sys
import json
import time

import gerar_filmes as g

sys.stdout.reconfigure(encoding="utf-8")

INTERVALOS = [
    ("2026-05-01", "2026-05-31"),
    ("2026-06-01", "2026-06-30"),
]


def coletar_ids_recentes():
    ids = set()
    for inicio, fim in INTERVALOS:
        encontrados = g.buscar_ids_por_intervalo(inicio, fim)
        ids.update(encontrados)
        print(f"  {inicio} a {fim}: {len(encontrados)} encontrados")
    return ids


def main():
    # Carrega base atual
    with open(g.JSON_OUT, encoding="utf-8") as f:
        filmes = json.load(f)
    por_tmdb = {f["tmdb_id"]: f for f in filmes}
    print(f"Base atual: {len(filmes)} filmes\n")

    # (a) Coleta e adiciona recentes
    print("[a] Coletando IDs de maio/junho 2026...")
    ids = coletar_ids_recentes()
    novos = [i for i in ids if i not in por_tmdb]
    print(f"\n{len(ids)} IDs no periodo, {len(novos)} novos a adicionar.\n")

    adicionados = 0
    for i, tmdb_id in enumerate(novos, 1):
        dados = g.buscar_detalhes(tmdb_id)
        time.sleep(g.RATE_DELAY)
        if not dados:
            continue
        filme = g.montar_entrada(dados)
        filmes.append(filme)
        adicionados += 1
        print(f"  [{i}/{len(novos)}] + {filme['titulo']} ({filme['ano']})")

    # (b) Classifica metragem em toda a base
    print("\n[b] Classificando metragem de toda a base...")
    contagem = {"Curta": 0, "Média": 0, "Longa": 0, "": 0}
    for filme in filmes:
        m = g.classificar_metragem(filme.get("duracao") or 0)
        filme["metragem"] = m
        contagem[m] += 1

    # Salva
    with open(g.JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(filmes, f, ensure_ascii=False, indent=2)

    print(f"\nAdicionados: {adicionados} filmes recentes")
    print(f"Base final:  {len(filmes)} filmes")
    print("Distribuicao por metragem:")
    print(f"  Curta:        {contagem['Curta']}")
    print(f"  Média:        {contagem['Média']}")
    print(f"  Longa:        {contagem['Longa']}")
    print(f"  Sem duracao:  {contagem['']}")
    print(f"\nJSON atualizado: {g.JSON_OUT}")


if __name__ == "__main__":
    main()
