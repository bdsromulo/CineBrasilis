"""
enriquecer_premios.py
Busca prêmios (P166 - award received) e indicações (P1411 - nominated for)
de filmes brasileiros no Wikidata via SPARQL e grava cache_premios.json.

Match com o acervo: imdb_id (P345) -> tmdb_id (P4947) -> título+ano.
Para aplicar ao filmes.json, rode aplicar_enriquecimentos.py.

Uso:
    cd scripts/
    python enriquecer_premios.py
"""

import os
import json
import re
import sys
import time
import requests
from unidecode import unidecode

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FILMES_JSON  = os.path.join(PROJECT_ROOT, "data", "filmes.json")
CACHE_FILE   = os.path.join(SCRIPT_DIR, "cache_premios.json")

WDQS = "https://query.wikidata.org/sparql"
UA   = "CineBrasilis/1.0 (projeto academico UTFPR; contato via github.com/bdsromulo/CineBrasilis)"

# Uma query por propriedade: P166 = prêmio recebido, P1411 = indicado a
QUERY_TEMPLATE = """
SELECT ?film ?filmLabel ?imdb ?tmdb ?dataPub ?premioLabel ?quando WHERE {{
  ?film wdt:P495 wd:Q155 .
  ?film p:{prop} ?st .
  ?st ps:{prop} ?premio .
  OPTIONAL {{ ?st pq:P585 ?quando . }}
  OPTIONAL {{ ?film wdt:P345 ?imdb . }}
  OPTIONAL {{ ?film wdt:P4947 ?tmdb . }}
  OPTIONAL {{ ?film wdt:P577 ?dataPub . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "pt,pt-br,en". }}
}}
"""


def rodar_query(prop):
    query = QUERY_TEMPLATE.format(prop=prop)
    for tentativa in range(4):
        try:
            r = requests.get(
                WDQS,
                params={"query": query, "format": "json"},
                headers={"User-Agent": UA},
                timeout=120,
            )
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            print(f"  [HTTP {r.status_code}] tentativa {tentativa + 1}")
        except requests.RequestException as e:
            print(f"  [Erro] {e} (tentativa {tentativa + 1})")
        time.sleep(10 * (tentativa + 1))
    return []


def valor(binding, chave):
    return binding.get(chave, {}).get("value", "")


def normalizar(texto):
    texto = unidecode(str(texto)).lower()
    return re.sub(r"[^a-z0-9]+", "", texto)


def montar_linha(prefixo, binding):
    premio = valor(binding, "premioLabel")
    if not premio or premio.startswith("Q"):
        return None
    quando = valor(binding, "quando")[:4]
    return f"{prefixo}: {premio}" + (f" ({quando})" if quando else "")


def main():
    with open(FILMES_JSON, "r", encoding="utf-8") as f:
        filmes = json.load(f)

    por_imdb   = {f["imdb_id"]: f["tmdb_id"] for f in filmes if f.get("imdb_id")}
    por_tmdb   = {str(f["tmdb_id"]): f["tmdb_id"] for f in filmes if f.get("tmdb_id")}
    por_titulo = {}
    for f in filmes:
        if f.get("titulo") and f.get("ano"):
            por_titulo[(normalizar(f["titulo"]), f["ano"])] = f["tmdb_id"]

    resultado = {}          # tmdb_id -> lista ordenada de strings
    stats = {"imdb": 0, "tmdb": 0, "titulo": 0, "sem_match": 0}

    for prop, prefixo in (("P166", "Vencedor"), ("P1411", "Indicado")):
        print(f"Consultando Wikidata ({prop})...")
        bindings = rodar_query(prop)
        print(f"  {len(bindings)} statements retornados")

        for b in bindings:
            linha = montar_linha(prefixo, b)
            if not linha:
                continue

            tmdb_id = None
            if valor(b, "imdb") in por_imdb:
                tmdb_id = por_imdb[valor(b, "imdb")]
                stats["imdb"] += 1
            elif valor(b, "tmdb") in por_tmdb:
                tmdb_id = por_tmdb[valor(b, "tmdb")]
                stats["tmdb"] += 1
            else:
                titulo = normalizar(valor(b, "filmLabel"))
                data   = valor(b, "dataPub")[:4]
                if titulo and data.isdigit():
                    ano = int(data)
                    for a in (ano, ano - 1, ano + 1):
                        if (titulo, a) in por_titulo:
                            tmdb_id = por_titulo[(titulo, a)]
                            stats["titulo"] += 1
                            break
            if tmdb_id is None:
                stats["sem_match"] += 1
                continue

            resultado.setdefault(tmdb_id, set()).add(linha)

    # sets -> listas ordenadas (Vencedor antes de Indicado, depois alfabético)
    final = {
        str(tid): sorted(linhas, key=lambda x: (not x.startswith("Vencedor"), x))
        for tid, linhas in resultado.items()
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=1)

    print(f"\nMatch por imdb: {stats['imdb']} | tmdb: {stats['tmdb']} | "
          f"titulo+ano: {stats['titulo']} | sem match: {stats['sem_match']}")
    print(f"{len(final)} filmes do acervo com prêmios/indicações -> {CACHE_FILE}")


if __name__ == "__main__":
    main()
