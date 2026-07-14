
if __name__ == "__main__":
    from src.embedding.modules.local_embedding.module import LocalDynamicEmbedding, EmbeddingFactory
    # Rode com:  python -m src.embedding.modules.local_embedding
    # (precisa ser via -m por causa do import relativo da EmbeddingFactory)

    print("Provedores disponíveis:", EmbeddingFactory.available())
    print("-" * 60)

    texto = (
        "A energia solar é uma fonte renovável que converte a luz do sol "
        "em eletricidade por meio de painéis fotovoltaicos.\n\n"
        "A energia eólica aproveita a força dos ventos para girar turbinas "
        "e gerar eletricidade de forma limpa.\n\n"
        "Já os combustíveis fósseis, como petróleo e carvão, são fontes "
        "não renováveis e liberam muito CO2 na atmosfera.\n\n"
        "O uso de baterias é essencial para armazenar a energia gerada por "
        "fontes intermitentes como sol e vento."
    )

    # 1) Montando o fluxo passo a passo (API fluente).
    #    Sem passar embeddings -> a classe usa fake(size=...) sozinha.
    pipeline = (
        LocalDynamicEmbedding()
        .with_fake_embeddings(size=384)
        .with_splitter(chunk_size=120, chunk_overlap=20)
        .with_top_k(3)
    )

    qtd = pipeline.process_text(texto, metadata={"fonte": "apostila_energia"})
    print(f"Chunks gerados: {qtd} | total acumulado: {pipeline.total_chunks}")
    print("-" * 60)

    # 2) Acessando cada chunk: texto, metadados e embedding.
    for chunk in pipeline.chunks:
        preview = chunk.content[:60].replace("\n", " ")
        print(f"[{chunk.index}] len={chunk.length} dim={chunk.dim} "
              f"meta={chunk.metadata}")
        print(f"     texto: {preview}...")
        print(f"     embedding[:3]: {chunk.embedding[:3]}")
    print("-" * 60)

    # 3) Recuperação por similaridade (com o vetor no resultado).
    consulta = "como gerar eletricidade a partir do vento?"
    print(f"Consulta: {consulta!r}")
    for i, r in enumerate(pipeline.retrieve(consulta, include_embedding=True), 1):
        print(f"  #{i} score={r['score']:.4f} | dim={len(r['embedding'])}")
        print(f"      {r['content'][:70]}...")
    print("-" * 60)

    # 4) get_chunks() em forma de dict (pronto para JSON).
    import json
    exemplo = pipeline.get_chunks(include_embedding=False)[0]
    print("get_chunks()[0] (sem embedding):")
    print(json.dumps(exemplo, ensure_ascii=False, indent=2))
    print("-" * 60)

    # 5) Trocar para outro provedor é só uma linha (comentado pois exige deps):
    # pipeline_openai = LocalDynamicEmbedding.from_openai_embeddings(
    #     model="text-embedding-3-large", chunk_size=3000, chunk_overlap=300, top_k=5
    # )

    print("Demo concluída com sucesso.")

# python -m src.embedding.modules.local_embedding.test.use