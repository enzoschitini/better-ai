import json
from io import BytesIO
import time
from src.knowledge_base.file_content_extractor import FileContentExtractor

# Início da metrificação
start_time = time.perf_counter()

# Caminho do arquivo MP4
file_path = 'src/TextParses/N8N.mp4'
#file_path = 'src/ParseComments/text.txt'

# Abrir o arquivo em modo binário e carregá-lo em uma variável BytesIO
with open(file_path, 'rb') as file:
    mp4_data = BytesIO(file.read())

extractor = FileContentExtractor(mp4_data, "mp4")
result = extractor.extract()

file_content = result["response"]["file_content"]

with open("transcricao.txt", "w", encoding="utf-8") as f:
    f.write(file_content)

print(json.dumps(result, indent=4))

# Fim da metrificação
end_time = time.perf_counter()
execution_time = end_time - start_time

minutes = int(execution_time // 60)
seconds = execution_time % 60

print(f"\n⏱ Tempo total de execução: {minutes} min {seconds:.2f} s")

# Agora a variável mp4_data contém o conteúdo do arquivo como BytesIO
# python -m src.TextParses.extract
