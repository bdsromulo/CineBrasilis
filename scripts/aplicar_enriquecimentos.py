"""
aplicar_enriquecimentos.py
Aplica ao data/filmes.json os caches gerados por:
  - enriquecer_providers.py  (cache_providers.jsonl) -> campo onde_assistir
  - buscar_youtube_gratis.py (cache_youtube.jsonl)   -> campo youtube_gratis
  - enriquecer_premios.py    (cache_premios.json)    -> campo premios

Idempotente: pode rodar quantas vezes quiser, inclusive após o
gerar_filmes.py regenerar o filmes.json.

Uso:
    cd scripts/
    python aplicar_enriquecimentos.py
"""

import os
import json

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FILMES_JSON  = os.path.join(PROJECT_ROOT, "data", "filmes.json")

CACHE_PROVIDERS = os.path.join(SCRIPT_DIR, "cache_providers.jsonl")
CACHE_YOUTUBE   = os.path.join(SCRIPT_DIR, "cache_youtube.jsonl")
CACHE_PREMIOS   = os.path.join(SCRIPT_DIR, "cache_premios.json")


def ler_jsonl(caminho, campo):
    dados = {}
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        item = json.loads(linha)
                        dados[item["tmdb_id"]] = item.get(campo)
                    except (json.JSONDecodeError, KeyError):
                        pass
    return dados


def main():
    with open(FILMES_JSON, "r", encoding="utf-8") as f:
        filmes = json.load(f)

    providers = ler_jsonl(CACHE_PROVIDERS, "providers")
    youtube   = ler_jsonl(CACHE_YOUTUBE, "video")
    premios   = {}
    if os.path.exists(CACHE_PREMIOS):
        with open(CACHE_PREMIOS, "r", encoding="utf-8") as f:
            premios = json.load(f)

    n_prov = n_yt = n_prem = 0
    for filme in filmes:
        tid = filme.get("tmdb_id")
        if not tid:
            continue

        if tid in providers and providers[tid]:
            filme["onde_assistir"] = providers[tid]
            n_prov += 1

        video = youtube.get(tid)
        if video:
            filme["youtube_gratis"] = video["url"]
            n_yt += 1

        linhas = premios.get(str(tid))
        if linhas:
            filme["premios"] = linhas
            n_prem += 1

    with open(FILMES_JSON, "w", encoding="utf-8") as f:
        json.dump(filmes, f, ensure_ascii=False, indent=2)

    print(f"{len(filmes)} filmes | onde_assistir: {n_prov} | "
          f"youtube_gratis: {n_yt} | premios: {n_prem}")
    print(f"Gravado em {FILMES_JSON}")


if __name__ == "__main__":
    main()
