{
  "job_id": "job_12345",
  "schema_version": "1.0",
  "created_at": "2026-04-22T10:15:30Z",
  "status": "pending",
  "priority": "normal",

  "metadata": {
    "identifiers": {
      "client_id": "client_abc",
      "workspace_id": "workspace_001",
      "user_id": "user_789",
      "file_id": "file_xyz"
    },

    "pipeline": {
        "generate_tags": True,
    },

    "embedding_metadata": {
      "source": "uploaded_file",
      "origin": "web_app",
      "language": "en",
      "tags": ["finance", "report", "2026"],
      "checksum_md5": "9e107d9d372bb6826bd81d3542a419d6"
    },

    "embedding_settings": {
      "model": "text-embedding-3-small",
      "dimensions": 1536,
      "chunk_size": 500,
      "chunk_overlap": 50,
      "normalize": True
    }
  },

  "file": {
    "name": "example.txt",
    "type": "text/plain",
    "size_bytes": 48213,
    "encoding": "utf-8",
    "path": "/uploads/client_abc/example.txt",
    "storage": {
      "provider": "s3",
      "bucket": "ai-processing-files",
      "region": "us-east-1",
      "key": "client_abc/2026/04/example.txt"
    }
  },

  "processing": {
    "pipeline": "embedding_pipeline_v2",
    "steps": [
      "load_file",
      "split_text",
      "generate_embeddings",
      "store_vectors"
    ],
    "retry_count": 0,
    "max_retries": 3
  },

  "output": {
    "vector_store": {
      "type": "opensearch",
      "index_name": "embeddings-index-v1",
      "namespace": "client_abc"
    },
    "destination": "vector_db"
  }
}






{
  "job_id": "job_12345",
  "schema_version": "1.0",
  "created_at": "2026-04-22T10:15:30Z",
  "status": "pending",
  "priority": "normal",

  "metadata": {
    "identifiers": {
      "client_id": "client_abc",
      "workspace_id": "workspace_001",
      "user_id": "user_789",
      "file_id": "file_xyz"
    },

    "pipeline": {
        "generate_tags": True,
    },

    "embedding_metadata": {
      "source": "uploaded_file",
      "origin": "web_app",
      "language": "en",
      "tags": ["finance", "report", "2026"],
      "checksum_md5": "9e107d9d372bb6826bd81d3542a419d6"
    },

    "embedding_settings": {
      "model": "text-embedding-3-small",
      "dimensions": 1536,
      "chunk_size": 500,
      "chunk_overlap": 50,
      "normalize": True
    }
  },

  "file_url": "https://s3.amazonaws.com/ai-processing-files/client_abc/2026/04/example.txt",
}