"""
gerar_internacionais.py
(c) Monta uma base APARTADA de filmes internacionais famosos (data/internacionais.json),
    usada apenas como ancoras de preferencia na pagina de Indicacoes.
    NAO entra no catalogo (que le somente filmes.json).

Para cada (titulo, ano) curado: busca no TMDB, pega o melhor match e extrai os
mesmos campos dos filmes brasileiros, marcando "origem": "internacional".

Uso:
    cd scripts/
    python gerar_internacionais.py
"""

import sys
import os
import json
import time

import gerar_filmes as g

sys.stdout.reconfigure(encoding="utf-8")

SAIDA = os.path.join(g.PROJECT_ROOT, "data", "internacionais.json")

# Lista curada: famosos, generos diversos. (titulo em ingles, ano)
CURADOS = [
    ("The Godfather", 1972), ("The Shawshank Redemption", 1994), ("Forrest Gump", 1994),
    ("Schindler's List", 1993), ("Fight Club", 1999), ("Moonlight", 2016),
    ("The Pursuit of Happyness", 2006), ("A Beautiful Mind", 2001), ("The Green Mile", 1999),
    ("Good Will Hunting", 1997), ("Dead Poets Society", 1989), ("Whiplash", 2014),
    ("12 Years a Slave", 2013), ("The Social Network", 2010), ("Marriage Story", 2019),
    ("Manchester by the Sea", 2016),
    ("Pulp Fiction", 1994), ("Goodfellas", 1990), ("Se7en", 1995),
    ("The Silence of the Lambs", 1991), ("No Country for Old Men", 2007), ("Parasite", 2019),
    ("Oldboy", 2003), ("Scarface", 1983), ("The Departed", 2006), ("Gone Girl", 2014),
    ("Prisoners", 2013), ("Heat", 1995), ("Joker", 2019),
    ("Die Hard", 1988), ("Mad Max: Fury Road", 2015), ("Gladiator", 2000),
    ("John Wick", 2014), ("The Dark Knight", 2008), ("Mission: Impossible", 1996),
    ("Terminator 2: Judgment Day", 1991), ("Top Gun: Maverick", 2022),
    ("Casino Royale", 2006), ("Kill Bill: Vol. 1", 2003),
    ("Inception", 2010), ("The Matrix", 1999), ("Interstellar", 2014),
    ("Blade Runner", 1982), ("Star Wars", 1977), ("Arrival", 2016),
    ("E.T. the Extra-Terrestrial", 1982), ("Back to the Future", 1985), ("Avatar", 2009),
    ("Dune", 2021), ("Alien", 1979), ("2001: A Space Odyssey", 1968),
    ("The Terminator", 1984), ("Ex Machina", 2014),
    ("Iron Man", 2008), ("The Avengers", 2012), ("Spider-Man", 2002),
    ("Black Panther", 2018), ("Logan", 2017), ("Guardians of the Galaxy", 2014),
    ("Avengers: Endgame", 2019), ("Spider-Man: Into the Spider-Verse", 2018),
    ("Bridget Jones's Diary", 2001), ("Titanic", 1997), ("La La Land", 2016),
    ("The Notebook", 2004), ("Pride & Prejudice", 2005), ("Notting Hill", 1999),
    ("Eternal Sunshine of the Spotless Mind", 2004), ("Before Sunrise", 1995),
    ("Call Me by Your Name", 2017), ("The Fault in Our Stars", 2014),
    ("The Grand Budapest Hotel", 2014), ("Superbad", 2007), ("The Hangover", 2009),
    ("Groundhog Day", 1993), ("The Secret Life of Walter Mitty", 2013),
    ("Little Miss Sunshine", 2006), ("Jojo Rabbit", 2019), ("The Truman Show", 1998),
    ("Mrs. Doubtfire", 1993),
    ("The Shining", 1980), ("Get Out", 2017), ("Hereditary", 2018),
    ("The Exorcist", 1973), ("A Quiet Place", 2018), ("It", 2017), ("Psycho", 1960),
    ("Spirited Away", 2001), ("Toy Story", 1995), ("The Lion King", 1994),
    ("Up", 2009), ("Coco", 2017), ("Your Name.", 2016), ("WALL·E", 2008),
    ("Shrek", 2001), ("Finding Nemo", 2003), ("How to Train Your Dragon", 2010),
    ("Inside Out", 2015), ("Ratatouille", 2007),
    ("The Lord of the Rings: The Fellowship of the Ring", 2001),
    ("Harry Potter and the Philosopher's Stone", 2001),
    ("Pirates of the Caribbean: The Curse of the Black Pearl", 2003),
    ("Jurassic Park", 1993), ("Raiders of the Lost Ark", 1981),
    ("The Hobbit: An Unexpected Journey", 2012), ("Life of Pi", 2012),
    ("The Lord of the Rings: The Return of the King", 2003),
    ("Saving Private Ryan", 1998), ("1917", 2019), ("Apocalypse Now", 1979),
    ("Full Metal Jacket", 1987), ("Dunkirk", 2017),
    ("The Greatest Showman", 2017), ("Bohemian Rhapsody", 2018), ("Rocketman", 2019),
    ("Django Unchained", 2012), ("The Good, the Bad and the Ugly", 1966),
    ("Once Upon a Time in the West", 1968),
    ("Casablanca", 1942), ("The Wizard of Oz", 1939),
]


def buscar_id(titulo, ano):
    params = {"query": titulo, "primary_release_year": ano, "language": "pt-BR"}
    dados = g.requisicao(f"{g.BASE_URL}/search/movie", params=params)
    if dados and dados.get("results"):
        return dados["results"][0]["id"]
    # tenta sem o ano
    params.pop("primary_release_year")
    dados = g.requisicao(f"{g.BASE_URL}/search/movie", params=params)
    if dados and dados.get("results"):
        return dados["results"][0]["id"]
    return None


def main():
    internacionais = []
    vistos = set()
    falhas = []

    print(f"Buscando {len(CURADOS)} filmes internacionais...\n")
    for i, (titulo, ano) in enumerate(CURADOS, 1):
        tmdb_id = buscar_id(titulo, ano)
        time.sleep(g.RATE_DELAY)
        if not tmdb_id or tmdb_id in vistos:
            falhas.append((titulo, ano))
            print(f"  [{i}/{len(CURADOS)}] X {titulo} ({ano}) - nao encontrado")
            continue

        dados = g.buscar_detalhes(tmdb_id)
        time.sleep(g.RATE_DELAY)
        if not dados:
            falhas.append((titulo, ano))
            continue

        filme = g.montar_entrada(dados)
        filme["origem"] = "internacional"
        # campos regionais nao se aplicam
        filme.pop("regiao", None)
        filme.pop("estado", None)
        internacionais.append(filme)
        vistos.add(tmdb_id)
        print(f"  [{i}/{len(CURADOS)}] ok {filme['titulo']} ({filme['ano']})")

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(internacionais, f, ensure_ascii=False, indent=2)

    print(f"\nSalvos: {len(internacionais)} filmes internacionais")
    print(f"Falhas: {len(falhas)}")
    for t, a in falhas:
        print(f"   - {t} ({a})")
    print(f"\nArquivo: {SAIDA}")


if __name__ == "__main__":
    main()
