"""
enriquecer_providers.py
Busca "onde assistir" (watch providers, região BR) no TMDB para todos os
filmes do acervo e grava um cache incremental em cache_providers.jsonl.

Os dados vêm da JustWatch via TMDB — a atribuição "Fonte: JustWatch" é
obrigatória na exibição.

O cache é keyed por tmdb_id, então o script pode ser reexecutado a qualquer
momento (ex.: após nova extração do gerar_filmes.py) e só busca o que falta.
Para aplicar o cache ao filmes.json, rode aplicar_enriquecimentos.py.

Uso:
    cd scripts/
    python enriquecer_providers.py
"""

import os
import json
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TMDB_TOKEN")
if not TOKEN:
    print("Erro: defina TMDB_TOKEN no arquivo .env")
    sys.exit(1)

BASE_URL = "https://api.themoviedb.org/3"
HEADERS  = {"accept": "application/json", "Authorization": f"Bearer {TOKEN}"}

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FILMES_JSON  = os.path.join(PROJECT_ROOT, "data", "filmes.json")
CACHE_FILE   = os.path.join(SCRIPT_DIR, "cache_providers.jsonl")

WORKERS    = 8
RATE_DELAY = 0.05   # por worker; efetivo ~ WORKERS/RATE_DELAY req/s no teto

_lock = threading.Lock()


def carregar_cache_ids():
    ids = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        ids.add(json.loads(linha)["tmdb_id"])
                    except (json.JSONDecodeError, KeyError):
                        pass
    return ids


def extrair_br(dados):
    """Reduz a resposta do TMDB ao bloco BR com nome+logo por categoria."""
    br = (dados or {}).get("results", {}).get("BR")
    if not br:
        return None

    def simplificar(lista):
        return [
            {"nome": p.get("provider_name", ""), "logo": p.get("logo_path", "")}
            for p in lista
        ]

    saida = {"link": br.get("link", "")}
    for categoria in ("flatrate", "free", "ads", "rent", "buy"):
        if br.get(categoria):
            saida[categoria] = simplificar(br[categoria])
    return saida


def buscar(tmdb_id):
    url = f"{BASE_URL}/movie/{tmdb_id}/watch/providers"
    for tentativa in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 5)))
                continue
            if r.status_code == 200:
                return extrair_br(r.json())
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 ** tentativa)
    return "ERRO"


def processar(tmdb_id, arquivo):
    resultado = buscar(tmdb_id)
    time.sleep(RATE_DELAY)
    if resultado == "ERRO":
        return None  # não grava; tenta de novo na próxima execução
    with _lock:
        arquivo.write(json.dumps(
            {"tmdb_id": tmdb_id, "providers": resultado}, ensure_ascii=False
        ) + "\n")
        arquivo.flush()
    return resultado


def main():
    with open(FILMES_JSON, "r", encoding="utf-8") as f:
        filmes = json.load(f)

    ja_no_cache = carregar_cache_ids()
    pendentes = [f["tmdb_id"] for f in filmes
                 if f.get("tmdb_id") and f["tmdb_id"] not in ja_no_cache]

    print(f"{len(filmes)} filmes | {len(ja_no_cache)} em cache | {len(pendentes)} pendentes")

    feitos = com_dados = 0
    with open(CACHE_FILE, "a", encoding="utf-8") as arquivo:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futuros = {pool.submit(processar, tid, arquivo): tid for tid in pendentes}
            for fut in as_completed(futuros):
                feitos += 1
                if fut.result():
                    com_dados += 1
                if feitos % 500 == 0:
                    print(f"  {feitos}/{len(pendentes)} ({com_dados} com providers BR)")

    print(f"\nConcluído: {feitos} processados, {com_dados} com providers BR.")
    print(f"Cache: {CACHE_FILE}")


if __name__ == "__main__":
    main()
