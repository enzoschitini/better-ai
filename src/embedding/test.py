payload = {
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf",

    "embedding_settings": {
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
    },
    
    "metadata": {
        "id_collection": "id_collection_01",
        "id_series": "id_series_01",
        "id_client": "id_client_01",
        "id_user": "id_user_01",
        "id_workspace": "id_workspace_01"
    }
}

aggregate1 = {
    "test": "test",

    "test2": {
        "test3": "test"
    }
}

aggregate2 = {
    "test4": "test",

    "test5": {
        "test6": "test",

        "test7": {
            "test6": "test"
        }
    }
}

aggregates = [aggregate1, aggregate2]

for agg in aggregates:
    for key in agg.keys():
        payload[key] = agg[key]

import json

print(json.dumps(payload, indent=4))
