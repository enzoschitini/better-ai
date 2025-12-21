# Documentazione Tecnica: Definizione Payload

Questo documento specifica la struttura del payload per il processo di ingestione e embedding dei documenti.

---

## Esempio di Payload Ottimizzato

```json
{
  "company_id": "1",
  "file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
  "file_name": "name file.pdf",
  "file_url": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf",
  
  "metadata": {

    "filters": {
      "id_collection": "id_collection_01",
      "id_series": "id_series_01",
      "id_client": "id_client_01",
      "id_user": "id_user_01",
      "id_workspace": "id_workspace_01"
    },

    "additional_information": {
      "collection_name": "BetterAI Repo"
    }
  },
  
  "embedding_settings": {
    "llm_model": "text-embedding-3-large",
    "dimensions": 3072,
    "global_namespace": true,
    "batch_size": 200
  }
}

Se c'è, se ha il nome giusto, se ha un valore, se il valore è del tipo 

Metadata:

Può avre filters o additional_information, o tutti e due insieme ma non può venire senza uno dei due. Quel che hanno al loro interno non importa basta che non abbia valori nulli o json.




