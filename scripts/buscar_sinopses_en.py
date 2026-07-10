"""
buscar_sinopses_en.py

Baixa a sinopse EM INGLES (overview en-US do TMDB) dos filmes nacionais e
salva num arquivo APARTADO: data/sinopses_en.json  ({ tmdb_id: overview_en }).

Fica separado do filmes.json (que ja tem 30MB) para nao pesar o carregamento
das outras paginas — o detalhe carrega este arquivo so quando o idioma e ingles.

Resumivel: salva a cada lote; rodar de novo continua de onde parou.

Uso:
    cd scripts/
    python buscar_sinopses_en.py
"""

import json
import os
import sys
import time

import gerar_filmes as g

sys.stdout.reconfigure(encoding="utf-8")

SRC = os.path.join(g.PROJECT_ROOT, "data", "filmes.json")
OUT = os.path.join(g.PROJECT_ROOT, "data", "sinopses_en.json")


def main():
    with open(SRC, encoding="utf-8") as f:
        filmes = json.load(f)

    feitos = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            feitos = json.load(f)

    # so filmes "visiveis" (com poster) e que tenham sinopse em PT
    alvo = [fm for fm in filmes
            if fm.get("poster_url") and (fm.get("sinopse") or "").strip()]
    pendentes = [fm for fm in alvo if str(fm["tmdb_id"]) not in feitos]

    print(f"Alvo: {len(alvo)} | ja feitos: {len(feitos)} | pendentes: {len(pendentes)}")

    for i, fm in enumerate(pendentes, 1):
        tid = fm["tmdb_id"]
        dados = g.requisicao(f"{g.BASE_URL}/movie/{tid}", params={"language": "en-US"})
        time.sleep(g.RATE_DELAY)
        ov = ((dados or {}).get("overview") or "").strip()
        if ov:
            feitos[str(tid)] = ov
        if i % 200 == 0:
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(feitos, f, ensure_ascii=False)
            print(f"  {i}/{len(pendentes)} (com EN: {len(feitos)})")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(feitos, f, ensure_ascii=False)
    print(f"Concluido. Sinopses EN salvas: {len(feitos)}")


if __name__ == "__main__":
    main()
