# Campos disponíveis na API TMDB

Levantamento feito com `GET /movie/598` (Cidade de Deus) + `append_to_response=credits,videos,keywords,watch/providers,release_dates`.

---

## Campos de topo (retornados diretamente)

| Campo | Tipo | O que é | Uso no projeto |
|---|---|---|---|
| `id` | int | ID interno do TMDB | ✅ já usado como `tmdb_id` |
| `title` | str | Título localizado (pt-BR) | ✅ já usado como `titulo` |
| `original_title` | str | Título no idioma original | — irrelevante pra BR |
| `overview` | str | Sinopse | ✅ já usado como `sinopse` |
| `release_date` | str | Data completa de lançamento (YYYY-MM-DD) | ✅ ano já extraído |
| `vote_average` | float | Nota média (0–10) | ✅ já usado como `avaliacao` |
| `vote_count` | int | Número de avaliações | ➕ útil para filtrar filmes com poucas notas |
| `popularity` | float | Score de popularidade do TMDB | — interno, pouco relevante |
| `poster_path` | str | Caminho do poster | ✅ já usado como `poster_url` |
| `backdrop_path` | str | Imagem de fundo panorâmica | ➕ pode servir de banner na página de detalhes |
| `runtime` | int | Duração em minutos | ➕ **adicionar como `duracao`** |
| `budget` | int | Orçamento em dólares | ➕ curiosidade/informação de apoio |
| `revenue` | int | Bilheteria em dólares | ➕ curiosidade/informação de apoio |
| `imdb_id` | str | ID no IMDB (ex: tt0317248) | ➕ útil para link externo `imdb.com/title/{id}` |
| `homepage` | str | Site oficial do filme | — geralmente vazio |
| `status` | str | Estado de lançamento (Released, etc.) | — pouco útil |
| `tagline` | str | Slogan do filme | — decidido não usar |
| `original_language` | str | Idioma original (ex: "pt") | — irrelevante pra BR |
| `origin_country` | list[str] | Países de origem (ex: ["BR"]) | — já filtramos por BR no discover |
| `adult` | bool | Flag de conteúdo adulto | — não relevante |
| `video` | bool | Flag interna do TMDB | — ignorar |
| `softcore` | bool | Flag interna do TMDB | — ignorar |
| `belongs_to_collection` | obj/null | Franquia ou coleção | — raramente preenchido para filmes BR |
| `genres` | list[{id, name}] | Gêneros | ✅ já usado como `genero` |
| `production_companies` | list[{id, name, logo_path, origin_country}] | Produtoras | ➕ **adicionar `[0].name` como `produtora`** |
| `production_countries` | list[{iso_3166_1, name}] | Países de produção | ➕ útil como complemento ao campo `estado` |
| `spoken_languages` | list[{iso_639_1, name}] | Idiomas falados no filme | — pouco útil para BR |

---

## Campos via `append_to_response`

### `credits`
| Subcampo | O que é | Uso |
|---|---|---|
| `cast[].name` | Nome do ator | ✅ já usado como `elenco` |
| `cast[].character` | Nome do personagem | ➕ poderia enriquecer a exibição do elenco |
| `cast[].profile_path` | Foto do ator | ➕ para exibir foto junto ao nome |
| `crew[].name` (job=Director) | Diretor | ✅ já usado como `diretor` |
| `crew[].name` (job=Writer/Screenplay) | Roteirista | ➕ campo novo possível |
| `crew[].name` (job=Original Music Composer) | Compositor | ➕ campo novo possível |

### `videos`
| Subcampo | O que é | Uso |
|---|---|---|
| `results[].key` (type=Trailer, site=YouTube) | Chave do trailer no YouTube | ✅ já usado como `trailer` |

### `keywords`
| Subcampo | O que é | Uso |
|---|---|---|
| `keywords[].name` | Palavras-chave temáticas (ex: "favela", "rio de janeiro", "gang war") | ➕ **pode popular o campo `tags` automaticamente** |

### `watch/providers` (filtrado por `results.BR`)
| Subcampo | O que é | Uso |
|---|---|---|
| `flatrate[].provider_name` | Serviços de streaming onde está disponível (Netflix, Globoplay, etc.) | ➕ **muito útil para a página de detalhes** |
| `rent[].provider_name` | Plataformas onde pode alugar | ➕ secundário |
| `buy[].provider_name` | Plataformas onde pode comprar | ➕ secundário |

### `release_dates` (filtrado por `results[iso_3166_1=BR]`)
| Subcampo | O que é | Uso |
|---|---|---|
| `release_dates[].certification` | Classificação indicativa no Brasil (ex: "16", "12") | ➕ útil para exibição nos detalhes |

---

## Resumo: o que vale adicionar ao script

| Campo novo no JSON | Origem na API | Observação |
|---|---|---|
| `duracao` | `runtime` | minutos, int |
| `produtora` | `production_companies[0].name` | primeira produtora listada |
| `produtoras` | `production_companies[].name` | lista completa se quiser |
| `tags` | `keywords.keywords[].name` | substitui preenchimento manual |
| `classificacao` | `release_dates` BR `.certification` | ex: "16", "12", "L" |
| `onde_assistir` | `watch/providers` BR `flatrate[].provider_name` | Netflix, Globoplay, etc. |
| `backdrop_url` | `backdrop_path` | `https://image.tmdb.org/t/p/w1280{backdrop_path}` |
| `imdb_id` | `imdb_id` | para link externo |
| `orcamento` | `budget` | 0 quando não informado |
| `bilheteria` | `revenue` | 0 quando não informado |

---

## O que NÃO vem da TMDB

- **Estado/região de produção brasileiro** (RJ, SP, etc.) → precisa da ANCINE
- **Prêmios** (Oscar, Grande Prêmio do Cinema Brasileiro, etc.) → preenchimento manual
- **`similares_internacionais`** → preenchimento manual/curadoria
