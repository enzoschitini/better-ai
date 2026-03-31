## How to use LoadRequestFile

### Code

```python
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    loader = LoadRequestFile(
        file,
        #allowed_extensions=["txt", "pdf"],
        #allowed_mimetypes=["text/plain", "application/pdf"],
        max_size_mb=5,
    )
    result = await loader.load()
    return result.to_dict()
```

### CURL

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@caminho/do/seu/arquivo.txt"
```
