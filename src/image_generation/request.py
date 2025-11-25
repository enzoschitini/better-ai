import requests
import base64

# URL do endpoint
url = "http://127.0.0.1:8000/save-images/"

# Exemplo de lista de imagens
results = [
    {
        'status': 'success',
        'nm_image': '2fbc4034.jpeg',
        'image_bytes': base64.b64encode(open("generated_images/2fbc4034-dd33-4324-947f-6fc278481ef7.jpg", "rb").read()).decode('utf-8')
    },

    {
        'status': 'success',
        'nm_image': 'f920a151.jpeg',
        'image_bytes': base64.b64encode(open("generated_images/f920a151-e613-4dbb-ba97-5a8abf3e1d1d.jpg", "rb").read()).decode('utf-8')
    }
]

# Montando o payload
payload = {"results": results}

# Fazendo a requisição POST
response = requests.post(url, json=payload)

# Mostrando a resposta
print(response.status_code)
print(response.json())
