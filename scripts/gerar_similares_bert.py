import json
import os
import sys

# Tentar importar as bibliotecas
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"Erro: Dependências não encontradas. Certifique-se de ter instalado sentence-transformers e scikit-learn. Erro original: {e}")
    sys.exit(1)

def gerar_similares():
    # Caminhos
    path_internacionais = os.path.join("data", "internacionais.json")
    path_nacionais = os.path.join("data", "filmes.json")

    # Carregar arquivos
    print("Carregando bases de dados...")
    with open(path_internacionais, "r", encoding="utf-8") as f:
        internacionais = json.load(f)
    
    with open(path_nacionais, "r", encoding="utf-8") as f:
        nacionais = json.load(f)
        
    print(f"Encontrados {len(internacionais)} filmes internacionais e {len(nacionais)} filmes nacionais.")

    # Inicializar modelo BERT
    print("Carregando o modelo de NLP (Isso pode demorar um pouco na primeira vez pois baixará os pesos)...")
    # Este modelo é leve, multilíngue e excelente para medir similaridade semântica
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # Preparar as sinopses
    print("Extraindo e processando sinopses...")
    
    # Textos dos nacionais
    textos_nacionais = []
    ids_nacionais = []
    
    for f in nacionais:
        sinopse = f.get("sinopse", "") or f.get("overview", "")
        titulo = f.get("titulo", "")
        # Adicionar titulo na string ajuda se a sinopse for muito curta
        texto = f"{titulo}. {sinopse}"
        textos_nacionais.append(texto)
        ids_nacionais.append(f.get("id"))
        
    # Textos dos internacionais
    textos_internacionais = []
    
    for f in internacionais:
        sinopse = f.get("sinopse", "") or f.get("overview", "")
        titulo = f.get("titulo", "")
        texto = f"{titulo}. {sinopse}"
        textos_internacionais.append(texto)
        
    print("Gerando embeddings para filmes internacionais...")
    emb_internacionais = model.encode(textos_internacionais, show_progress_bar=True)
    
    print("Gerando embeddings para filmes nacionais...")
    emb_nacionais = model.encode(textos_nacionais, show_progress_bar=True)
    
    print("Calculando similaridade de cossenos...")
    # shape: (n_internacionais, n_nacionais)
    matriz_similaridade = cosine_similarity(emb_internacionais, emb_nacionais)
    
    # Processar top 12 para cada filme internacional
    top_n = 12
    
    print(f"Atribuindo top {top_n} filmes nacionais para cada internacional...")
    for i, filme_int in enumerate(internacionais):
        scores_para_este_filme = matriz_similaridade[i]
        
        # Obter os índices dos n_top scores mais altos
        # argsort retorna ordem crescente, pegamos os últimos top_n e invertemos para decrescente
        indices_top = scores_para_este_filme.argsort()[-top_n:][::-1]
        
        similares = []
        for idx in indices_top:
            similares.append({
                "id": ids_nacionais[idx],
                "score": float(scores_para_este_filme[idx])
            })
            
        # Adicionar ou substituir no json original
        filme_int["similares_nacionais"] = similares

    # Salvar o arquivo
    print("Salvando arquivo internacionais.json...")
    with open(path_internacionais, "w", encoding="utf-8") as f:
        json.dump(internacionais, f, ensure_ascii=False, indent=2)
        
    print("Sucesso! O sistema de recomendações por NLP foi atualizado.")

if __name__ == "__main__":
    gerar_similares()
