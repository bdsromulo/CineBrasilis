"""
testar_indicacoes.py

Avalia a COERENCIA das recomendacoes (internacional -> brasileiro) apos o
gerar_similares_bert.py. Nao usa BERT aqui: apenas le os similares ja gravados
em internacionais.json e verifica se os filmes nacionais devolvidos batem com
o genero esperado de cada categoria.

Categorias testadas (pedido do usuario):
    - animacao  -> deve devolver animacao
    - infantil  -> deve devolver infantil (Familia) ou animacao
    - acao      -> acao
    - drama     -> drama
    - western   -> faroeste ou cangaco (western/cangaco brasileiro)

Uso:
    python testar_indicacoes.py
"""

import json
import os
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_INT = os.path.join(RAIZ, "data", "internacionais.json")
PATH_NAC = os.path.join(RAIZ, "data", "filmes.json")


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def tem_genero(filme, *nomes):
    gset = {norm(g) for g in (filme.get("genero") or [])}
    return any(norm(n) in gset for n in nomes)


def eh_cangaco_ou_western(filme):
    if tem_genero(filme, "Faroeste"):
        return True
    campos = " ".join([
        filme.get("titulo", ""),
        filme.get("sinopse", ""),
        " ".join(filme.get("tags", []) or []),
    ])
    campos = norm(campos)
    return any(k in campos for k in ["cangac", "cangaceir", "lampiao", "sertao", "faroeste", "western"])


# categoria -> (predicado para a ancora internacional, predicado de acerto no nacional, rotulo)
CATEGORIAS = {
    "animacao": (
        lambda f: tem_genero(f, "Animação"),
        lambda f: tem_genero(f, "Animação"),
        "animação",
    ),
    "infantil": (
        lambda f: tem_genero(f, "Família") and not tem_genero(f, "Animação"),
        lambda f: tem_genero(f, "Família", "Animação"),
        "infantil (Família) ou animação",
    ),
    "acao": (
        lambda f: tem_genero(f, "Ação") and not tem_genero(f, "Animação"),
        lambda f: tem_genero(f, "Ação"),
        "ação",
    ),
    "drama": (
        lambda f: tem_genero(f, "Drama") and not tem_genero(f, "Animação"),
        lambda f: tem_genero(f, "Drama"),
        "drama",
    ),
    "western": (
        lambda f: tem_genero(f, "Faroeste"),
        eh_cangaco_ou_western,
        "faroeste ou cangaço BR",
    ),
}

TOP_MOSTRAR = 8   # quantos similares exibir por ancora
N_ANCORAS = 3     # ancoras internacionais por categoria


def main():
    with open(PATH_INT, encoding="utf-8") as f:
        internacionais = json.load(f)
    with open(PATH_NAC, encoding="utf-8") as f:
        nacionais = json.load(f)
    br = {f.get("tmdb_id"): f for f in nacionais}

    print(f"Base: {len(internacionais)} internacionais | {len(nacionais)} nacionais\n")

    resumo = {}
    for chave, (pred_anchor, pred_hit, rotulo) in CATEGORIAS.items():
        # ancoras: as mais votadas da categoria que tenham similares
        candidatas = [f for f in internacionais
                      if pred_anchor(f) and f.get("similares_nacionais")]
        candidatas.sort(key=lambda f: f.get("vote_count", 0), reverse=True)
        ancoras = candidatas[:N_ANCORAS]

        print("=" * 78)
        print(f"CATEGORIA: {chave.upper()}  (esperado: {rotulo})")
        print("=" * 78)

        acertos_cat = 0
        total_cat = 0
        for anc in ancoras:
            gen = ", ".join(anc.get("genero") or [])
            print(f"\n▶ Âncora: {anc['titulo']} ({anc.get('ano')})  [{gen}]")
            sims = anc.get("similares_nacionais", [])[:TOP_MOSTRAR]
            for s in sims:
                fb = br.get(s.get("tmdb_id")) or br.get(s.get("id"))
                if not fb:
                    continue
                hit = pred_hit(fb)
                total_cat += 1
                acertos_cat += 1 if hit else 0
                marca = "✓" if hit else "·"
                gb = ", ".join(fb.get("genero") or [])
                extra = ""
                if "cos" in s:
                    extra = f"  (cos={s['cos']:.2f} gen={s['gen']:.2f})"
                print(f"    {marca} {fb.get('titulo','?')} ({fb.get('ano','?')}) "
                      f"[{gb}]{extra}")

        pct = (100 * acertos_cat / total_cat) if total_cat else 0
        resumo[chave] = pct
        print(f"\n  >> Coerência {chave}: {acertos_cat}/{total_cat} = {pct:.0f}%\n")

    print("#" * 78)
    print("RESUMO DE COERÊNCIA POR CATEGORIA")
    print("#" * 78)
    for chave, pct in resumo.items():
        print(f"  {chave:10s}: {pct:.0f}%")
    media = sum(resumo.values()) / len(resumo) if resumo else 0
    print(f"  {'MÉDIA':10s}: {media:.0f}%")


if __name__ == "__main__":
    main()
