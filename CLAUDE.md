# CLAUDE.md — Guia do agente para o CineBrasilis

Site estático que cataloga o cinema brasileiro (TMDB + ANCINE). Publicado em
https://cinebrasilis.com.br via GitHub Pages: **push em `origin/main` = deploy**.

- Repositório de origem: `origin` → https://github.com/bdsromulo/CineBrasilis
- Dados: `data/filmes.json` (nacional), `data/internacionais.json` (âncoras de
  recomendação, NÃO entra no catálogo), `data/sinopses_en.json` (modo EN)
- Documentação do junto: `README.md`, `docs/tmdb_campos.md`, docstrings de `scripts/`

## Ambiente

- Python do sistema (`py`): deps leves `requirements.txt` + `yt_dlp` (não listada lá).
- `.venv-ml`: torch + sentence-transformers (só para `gerar_similares_bert.py`).
- Credenciais: `scripts/.env` (`TMDB_TOKEN`, `TMDB_API_KEY`).

## 🔄 Procedimento de atualização do acervo (rodada)

Executar dentro de `scripts/`, na ordem (todos com o Python do sistema, exceto BERT):

1. `atualizar_recentes.py` — editar `INTERVALOS` para o período faltante e rodar
   (adiciona lançamentos ao `data/filmes.json`, sem duplicar, e reclassifica metragem).
   Consulte a data do último commit de acervo para saber o período faltante.
2. `merge_ancine.py` — re-vínculo estado/região via CSVs da OCA/ANCINE em
   `data/obras-nao-pub-brasileiras-csv/` (idempotente).
3. `enriquecer_providers.py` — cache incremental de "Onde Assistir" (JustWatch via
   TMDB), só IDs novos.
4. `aplicar_enriquecimentos.py` — aplica os caches (`cache_providers.jsonl`,
   `cache_youtube.jsonl`, `cache_premios.json`) ao `filmes.json`.
5. `buscar_sinopses_en.py` — sinopses EN dos filmes novos (incremental, retomável).
6. Regenerar `scripts/filmes.xlsx` (paridade com rodadas anteriores): a partir da
   raiz de `scripts/`, `py -c "import json, gerar_filmes as g; g.salvar_excel(json.load(open(g.JSON_OUT, encoding='utf-8')))"`.
7. `..\ \ .venv-ml\Scripts\python.exe gerar_similares_bert.py` — recalcula
   recomendações (reaplica vínculos manuais ao final, via `vinculos_manuais.vm`).
   Rodar por ÚLTIMO, quando `filmes.json` e `internacionais.json` estiverem fechados.
8. Commit de `data/*.json` + `scripts/` e push → publica em cinebrasilis.com.br.

## ⚠️ PROTOCOLO: busca de filmes completos no YouTube (`buscar_youtube_gratis.py`)

**NUNCA rode este script por iniciativa própria** (nem para "completar o acervo"
durante uma rodada de atualização). Só execute quando:

1. O usuário instruir diretamente (ex.: "rode buscar_youtube_gratis.py"), OU
2. O usuário autorizar explicitamente uma rodada de busca em massa.

**Motivo:** o YouTube aplica *soft blocks* quando há um volume alto de buscas via
yt-dlp em pouco tempo, comprometendo o ambiente e rodadas futuras (entradas ficam
em cache como "sem resultado", dificultando reexecuções).

Os filmes novos **não ficam sem alternativa**: a página do detalhe tem o botão
"Procurar no YouTube" (`js/detalhes.js`), que funciona sempre — busca ao vivo no
navegador do usuário, sem API e sem risco de bloqueio. O campo `youtube_gratis`
(session via cache) é apenas um bônus para títulos já confirmados.
