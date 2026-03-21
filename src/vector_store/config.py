from dataclasses import dataclass, field

@dataclass
class PineconeVectorStoreConfig:
    # --- Embeddings ---
    embedding_model: str = "text-embedding-3-large" 
    # Modelo utilizado para gerar os embeddings dos textos

    dimensions: int = 3072  
    # Dimensionalidade do vetor gerado pelo modelo de embedding

    embedding_batch_size: int = 100  
    # Quantidade de textos processados por batch na geração de embeddings

    # --- Index / Namespacing ---
    index_name: str = "backai-vectorstore"
    # Nome do índice no vector store (onde os vetores são armazenados)

    namespace: str = "default"  
    # Namespace padrão para separar dados dentro do índice (ex: por cliente ou contexto)

    global_namespace: str = "global" 
    # Namespace global compartilhado entre múltiplos contextos ou aplicações

    # --- Chunking / Preprocessing ---
    chunk_size: int = 3000  
    # Tamanho máximo de cada chunk de texto (em caracteres ou tokens, dependendo da implementação)

    chunk_overlap: int = 300  
    # Sobreposição entre chunks consecutivos para preservar contexto semântico

    separators: list = field(default_factory=lambda: ["\n\n", "\n", ".", " "])
    # Separadores usados para dividir o texto em partes menores de forma inteligente

    # --- Query / Retrieval ---
    top_k: int = 10000
    # Número máximo de vetores retornados na busca inicial por similaridade

    k: int = 5
    # Número final de documentos mais relevantes retornados ao usuário após filtragem/ranking

    # --- Maintenance / Operations ---
    delete_batch_size: int = 1000
    # Quantidade de vetores removidos por batch em operações de deleção

    # Enum responsável por centralizar os valores padrão do vector store,
    # organizando configurações de embeddings, indexação, chunking, busca e operações auxiliares.

