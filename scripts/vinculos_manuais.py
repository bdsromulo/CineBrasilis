"""
vinculos_manuais.py

Vinculos curados (subjetivos) entre um filme internacional e producoes
brasileiras diretamente associadas. Esses vinculos assumem SCORE MAXIMO e
PRIMEIRO LUGAR nas indicacoes daquele internacional.

Chave = tmdb_id do internacional; valor = lista de tmdb_id de nacionais.

A funcao aplicar() e chamada:
  - agora, por aplicar_vinculos.py (injeta direto no internacionais.json), e
  - no futuro, pelo gerar_similares_bert.py (se o BERT for rerodado),
para que os vinculos sejam sempre absorvidos.
"""

# tmdb_id internacional -> [tmdb_id nacional, ...]   (# comentario = titulos)
VINCULOS = {
    2062:   [199739],   # Ratatouille           -> Ratatoing
    14160:  [199700],   # Up: Altas Aventuras   -> Voando Em Busca de Aventuras!
    920:    [217194],   # Carros                -> Os Carrinhos
    49013:  [217194],   # Carros 2              -> Os Carrinhos
    260514: [217194],   # Carros 3              -> Os Carrinhos
    105:    [51137],    # De Volta para o Futuro-> Turma da Monica em Uma Aventura no Tempo
}


def aplicar(internacionais, nac_por_tmdb):
    """
    Coloca os vinculos manuais no TOPO de similares_nacionais de cada
    internacional, com score acima de qualquer match real (=> normalizado 1.0
    e primeiro lugar). Idempotente: pode rodar quantas vezes quiser.

    internacionais: lista de dicts (data/internacionais.json)
    nac_por_tmdb:   dict tmdb_id -> filme nacional (para pegar o slug 'id')
    """
    aplicados = 0
    for f in internacionais:
        links = VINCULOS.get(f.get("tmdb_id"))
        if not links:
            continue
        sims = f.get("similares_nacionais") or []
        max_score = max((s.get("score", 0) for s in sims), default=1.0) or 1.0
        boost = max_score * 1.5 + 1.0
        vinculados = set(links)
        # remove entradas antigas dos vinculados (evita duplicar / re-rodar)
        sims = [s for s in sims if s.get("tmdb_id") not in vinculados]
        manuais = []
        for nid in links:
            nac = nac_por_tmdb.get(nid)
            if not nac:
                continue
            manuais.append({
                "tmdb_id": nid,
                "id": nac.get("id"),
                "score": boost,
                "cos": 1.0,
                "gen": 1.0,
                "manual": True,
            })
            aplicados += 1
        f["similares_nacionais"] = manuais + sims
    return aplicados
