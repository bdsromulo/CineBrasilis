"""
buscar_youtube_gratis.py
Procura versões completas e gratuitas dos filmes do acervo no YouTube via
yt-dlp (mesmo princípio do BaixaTrack: busca ytsearch, sem chave de API).

Critérios para aceitar um vídeo como "o filme completo":
  1. Duração conhecida do filme (campo duracao > 0) e metragem Longa ou Média;
  2. Duração do vídeo bate com a do filme (tolerância ±8% ou ±4 min,
     o que for maior);
  3. Título normalizado do filme aparece no título do vídeo.

Grava cache incremental em cache_youtube.jsonl (keyed por tmdb_id, inclusive
os "sem resultado", para não repetir buscas). Pode ser interrompido e
retomado. Para aplicar ao filmes.json, rode aplicar_enriquecimentos.py.

Uso:
    cd scripts/
    python buscar_youtube_gratis.py
"""

import os
import json
import re
import time
from unidecode import unidecode
from yt_dlp import YoutubeDL

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FILMES_JSON  = os.path.join(PROJECT_ROOT, "data", "filmes.json")
CACHE_FILE   = os.path.join(SCRIPT_DIR, "cache_youtube.jsonl")

N_RESULTADOS = 6
RATE_DELAY   = 0.4
TOL_PERCENT  = 0.08
TOL_MIN_SEG  = 240

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "noprogress": True,
    "socket_timeout": 20,
}


def normalizar(texto):
    texto = unidecode(str(texto)).lower()
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def duracao_bate(dur_filme_seg, dur_video):
    if not dur_video:
        return False
    tolerancia = max(TOL_MIN_SEG, dur_filme_seg * TOL_PERCENT)
    return abs(dur_video - dur_filme_seg) <= tolerancia


def escolher_video(filme, entradas):
    titulo_norm = normalizar(filme["titulo"])
    dur_filme   = filme["duracao"] * 60
    candidatos  = []
    for e in entradas or []:
        if not e:
            continue
        titulo_video = normalizar(e.get("title") or "")
        if titulo_norm not in titulo_video:
            continue
        if not duracao_bate(dur_filme, e.get("duration")):
            continue
        candidatos.append(e)
    if not candidatos:
        return None
    # menor desvio de duração ganha
    candidatos.sort(key=lambda e: abs((e.get("duration") or 0) - dur_filme))
    escolhido = candidatos[0]
    return {
        "url":     escolhido.get("url") or f"https://www.youtube.com/watch?v={escolhido.get('id')}",
        "titulo":  escolhido.get("title", ""),
        "duracao": escolhido.get("duration"),
        "canal":   escolhido.get("channel") or escolhido.get("uploader") or "",
    }


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


def main():
    with open(FILMES_JSON, "r", encoding="utf-8") as f:
        filmes = json.load(f)

    ja_no_cache = carregar_cache_ids()

    alvo = [f for f in filmes
            if f.get("metragem") in ("Longa", "Média")
            and (f.get("duracao") or 0) > 0
            and f.get("tmdb_id")
            and f["tmdb_id"] not in ja_no_cache]

    # Longas mais votados primeiro (os que o público mais vai procurar)
    alvo.sort(key=lambda f: (f["metragem"] != "Longa", -(f.get("vote_count") or 0)))

    print(f"{len(alvo)} filmes a buscar ({len(ja_no_cache)} em cache)")

    encontrados = erros_seguidos = 0
    with open(CACHE_FILE, "a", encoding="utf-8") as cache, YoutubeDL(YDL_OPTS) as ydl:
        for i, filme in enumerate(alvo, 1):
            busca = f'ytsearch{N_RESULTADOS}:"{filme["titulo"]}" {filme.get("ano") or ""} filme completo'
            try:
                r = ydl.extract_info(busca, download=False)
                video = escolher_video(filme, r.get("entries"))
                erros_seguidos = 0
            except KeyboardInterrupt:
                print("\nInterrompido. Cache preservado; rode de novo para retomar.")
                return
            except Exception as e:
                erros_seguidos += 1
                print(f"  [{i}] ERRO em '{filme['titulo']}': {str(e)[:80]}")
                if erros_seguidos >= 10:
                    print("10 erros seguidos - possivel bloqueio. Parando; rode mais tarde.")
                    return
                time.sleep(30)
                continue

            cache.write(json.dumps(
                {"tmdb_id": filme["tmdb_id"], "video": video}, ensure_ascii=False
            ) + "\n")
            cache.flush()

            if video:
                encontrados += 1
                print(f"  [{i}/{len(alvo)}] OK {filme['titulo']} ({filme['ano']}) "
                      f"-> {video['url']}")
            elif i % 50 == 0:
                print(f"  [{i}/{len(alvo)}] ... ({encontrados} encontrados)")

            time.sleep(RATE_DELAY)

    print(f"\nConcluído. {encontrados} filmes com versão completa no YouTube.")


if __name__ == "__main__":
    main()
