"""
Lote p/ buscar_sinopses_en.py: processa um trecho e sai (evita rodadas
lendarias som quieto). Retomavel sincronizada com o script original.
Use: py lote_sinopses.py [TAMANHO]
"""
import json
import sys
import time

import gerar_filmes as g

sys.stdout.reconfigure(encoding="utf-8")

LIMITE = int(sys.argv[1]) if len(sys.argv) > 1 else 500

SRC = g.PROJECT_ROOT + "/data/filmes.json"
OUT = g.PROJECT_ROOT + "/data/sinopses_en.json"

with open(SRC, encoding="utf-8") as f:
    filmes = json.load(f)
with open(OUT, encoding="utf-8") as f:
    feitos = json.load(f)

alvo = [x for x in filmes
        if x.get("poster_url") and (x.get("sinopse") or "").strip()]
pend = [x for x in alvo if str(x["tmdb_id"]) not in feitos]
# "ult" = processa os ultimos da base primeiro (filmes novos, que importam
# para o modo EN do site agora); default = backlog antigo em ordem.
if len(sys.argv) > 2 and sys.argv[2] == "ult":
    pend = pend[::-1]
print(f"pendentes: {len(pend)} | processando: {min(len(pend), LIMITE)}")

for i, fm in enumerate(pend[:LIMITE], 1):
    tid = fm["tmdb_id"]
    dados = g.requisicao(f"{g.BASE_URL}/movie/{tid}", params={"language": "en-US"})
    time.sleep(g.RATE_DELAY)
    ov = ((dados or {}).get("overview") or "").strip()
    if ov:
        feitos[str(tid)] = ov
    if i % 100 == 0:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(feitos, f, ensure_ascii=False)
        print(f"  {i}/{LIMITE} (total EN: {len(feitos)})", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(feitos, f, ensure_ascii=False)
print(f"Lote concluido. Total EN: {len(feitos)} | restantes: {len(pend) - LIMITE}")
