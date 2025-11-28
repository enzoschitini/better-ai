import requests
import base64

url = "https://better-ai-bucket-storage-production.up.railway.app/save-images"

payload = {
    "results": [
        {
            'status': 'success',
            'nm_image': 'xxxxx3.jpeg',
            'image_bytes': base64.b64encode(open("generated_images/2fbc4034-dd33-4324-947f-6fc278481ef7.jpg", "rb").read()).decode('utf-8')
        },
        {
            'status': 'success',
            'nm_image': 'xxxxx4.jpeg',
            'image_bytes': base64.b64encode(open("generated_images/f920a151-e613-4dbb-ba97-5a8abf3e1d1d.jpg", "rb").read()).decode('utf-8')
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)

    print("Status Code:", response.status_code)
    print("Response:", response.text)

    response.raise_for_status()  # lança erro se status != 2xx

except requests.exceptions.RequestException as e:
    print("Erro na requisição:", e)


# https://better-ai-bucket-storage-production.up.railway.app/images/image_name.jpeg

# Status Code: 200
# Response: {"status":"successo","message":"Imagens salvas com sucesso",
# "urls":["http://better-ai-bucket-storage-production.up.railway.app/images/xxxxx3.jpeg",
# "http://better-ai-bucket-storage-production.up.railway.app/images/xxxxx4.jpeg"]}