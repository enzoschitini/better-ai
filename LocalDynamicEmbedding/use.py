"""
Exemplo de uso da LocalDynamicEmbedding com o modelo local real
(sentence-transformers/all-MiniLM-L6-v2).

Requer: pip install -r requirements.txt
"""

from local_dynamic_embedding import LocalDynamicEmbedding

texto = """
A fotossíntese é o processo pelo qual plantas convertem luz solar em energia.
Esse processo ocorre principalmente nas folhas, dentro das células que contêm
cloroplastos.

O sistema solar é composto por oito planetas que orbitam o Sol. Mercúrio é o
planeta mais próximo do Sol, enquanto Netuno é o mais distante.

Machine learning é uma área da inteligência artificial focada em algoritmos
que aprendem padrões a partir de dados, sem serem explicitamente programados.
"""

# Ao não passar `embeddings`, a classe carrega automaticamente o modelo
# local "sentence-transformers/all-MiniLM-L6-v2".
pipeline = LocalDynamicEmbedding(chunk_size=200, chunk_overlap=30, top_k=2)

# Cenário 1: processa o texto (split + embeddings + storage local)
pipeline.process_text(texto, metadata={"fonte": "artigo_exemplo"})
print(f"Total de chunks armazenados: {pipeline.total_chunks}")

# Cenário 2: retriever consulta os chunks mais relevantes
resultados = pipeline.retrieve("O que é inteligência artificial?")
for i, r in enumerate(resultados, 1):
    print(f"\n{i}. score={r['score']:.4f}")
    print(f"   {r['content']}")

# Também é possível obter um Retriever nativo do LangChain, útil para
# plugar em chains como RetrievalQA:
retriever = pipeline.as_retriever()
docs = retriever.invoke("Fale sobre o sistema solar")
for doc in docs:
    print(doc.page_content)