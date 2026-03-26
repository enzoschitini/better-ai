
documents = [
    {
        "id": "79258322-c06b-4e50-9a69-c8caa1136b3f",
        "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "metadata": {
            "Client": "1234",
            "client_id": "0011",
            "collection_id": "collection_01",
            "collection_name": "BetterAI",
            "created_at": "2026-03-25 18:58:43",
            "file_extension": "pdf",
            "file_id": "cucinare",
            "file_name": "LESSICO per CUCINARE.pdf",
            "user_id": "11"
        },
        "score": 0.382682741
    },

    {
        "id": "f75b0f7c-36ab-48d4-8da0-ec21b9ce688a",
        "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "metadata": {
            "Client": "1234",
            "client_id": "0011",
            "collection_id": "collection_01",
            "collection_name": "BetterAI",
            "created_at": "2026-03-25 18:58:43",
            "file_extension": "pdf",
            "file_id": "cucinare",
            "file_name": "LESSICO per CUCINARE.pdf",
            "user_id": "11"
        },
        "score": 0.359430343
    }
]

meneger = RetrievalManager(
    docs=documents,
    score_min=0.36,
    filter_by_score=True
)

print(meneger.get_files())