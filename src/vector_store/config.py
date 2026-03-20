from enum import Enum

class PineconeVectorStoreConfig(str, Enum):
    # --- Embeddings ---
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"  
    # Modelo utilizado para gerar os embeddings dos textos

    DEFAULT_DIMENSIONS = 3072  
    # Dimensionalidade do vetor gerado pelo modelo de embedding

    DEFAULT_EMBEDDING_BATCH_SIZE = 100  
    # Quantidade de textos processados por batch na geração de embeddings

    # --- Index / Namespacing ---
    DEFAULT_INDEX_NAME = "backai-vectorstore"  
    # Nome do índice no vector store (onde os vetores são armazenados)

    DEFAULT_NAMESPACE = "default"  
    # Namespace padrão para separar dados dentro do índice (ex: por cliente ou contexto)

    DEFAULT_GLOBAL_NAMESPACE = "global"  
    # Namespace global compartilhado entre múltiplos contextos ou aplicações

    # --- Chunking / Preprocessing ---
    DEFAULT_CHUNK_SIZE = 3000  
    # Tamanho máximo de cada chunk de texto (em caracteres ou tokens, dependendo da implementação)

    DEFAULT_CHUNK_OVERLAP = 300  
    # Sobreposição entre chunks consecutivos para preservar contexto semântico

    DEFAULT_SEPARATORS = ["\n\n", "\n", ".", " "]  
    # Separadores usados para dividir o texto em partes menores de forma inteligente

    # --- Query / Retrieval ---
    DEFAULT_TOP_K = 10000  
    # Número máximo de vetores retornados na busca inicial por similaridade

    DEFAULT_K = 5  
    # Número final de documentos mais relevantes retornados ao usuário após filtragem/ranking

    # --- Maintenance / Operations ---
    DEFAULT_DELETE_BATCH_SIZE = 1000  
    # Quantidade de vetores removidos por batch em operações de deleção

    # --- Backend / Provider ---
    DEFAULT_BACKEND = "opensearch"  
    # Backend utilizado para armazenamento e busca vetorial

    # Enum responsável por centralizar os valores padrão do vector store,
    # organizando configurações de embeddings, indexação, chunking, busca e operações auxiliares.

