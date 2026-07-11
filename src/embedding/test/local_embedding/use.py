from langchain_community.embeddings import DeterministicFakeEmbedding
from src.embedding.modules.local_embedding import LocalDynamicEmbedding
import time

texto = """
A fotossíntese é o processo pelo qual plantas convertem luz solar em energia.
Esse processo ocorre principalmente nas folhas, dentro das células que contêm cloroplastos.

O sistema solar é composto por oito planetas que orbitam o Sol.
Mercúrio é o planeta mais próximo do Sol, enquanto Netuno é o mais distante.

Machine learning é uma área da inteligência artificial focada em algoritmos
que aprendem padrões a partir de dados, sem serem explicitamente programados.
"""

# Usamos um embedding determinístico e leve apenas para validar o
# fluxo (chunking -> embeddings -> storage -> retrieval) sem depender
# de baixar um modelo real de sentence-transformers neste teste.

start_time = time.time()

fake_embeddings = DeterministicFakeEmbedding(size=384)

pipeline = LocalDynamicEmbedding(
    embeddings=fake_embeddings,
    chunk_size=120,
    chunk_overlap=20,
    top_k=2,
)

n_chunks = pipeline.process_text(texto, metadata={"fonte": "teste"})
print(f"Chunks gerados: {n_chunks}")
print(f"Total de chunks armazenados: {pipeline.total_chunks}")

resultados = pipeline.retrieve("O que é machine learning?")
print("\nResultados do retriever:")
for i, r in enumerate(resultados, 1):
    print(f"{i}. score={r['score']:.4f} | metadata={r['metadata']}")
    print(f"   conteúdo: {r['content'][:80]}...")

retriever = pipeline.as_retriever()
print(f"\nObjeto Retriever nativo do LangChain: {type(retriever)}")

# Testa erro ao consultar sem processar nada
vazio = LocalDynamicEmbedding(embeddings=fake_embeddings)
try:
    vazio.retrieve("teste")
except RuntimeError as e:
    print(f"\nErro esperado ao consultar sem processar texto: {e}")

print("\nOK: fluxo completo executado com sucesso.")
end_time = time.time()
print(f"Tempo total de execução: {end_time - start_time:.2f} segundos")

# python -m src.embedding.test.local_embedding.use