import time
import json
import asyncio

from src.TextParses.highlights import HighlightsExtractor
from src.TextParses.parse_comments import CommentExtractor


def parte_1_sync():
    query = "Gere highlights com base na transcrição do vídeo"

    parser = HighlightsExtractor()
    resultado = parser.extract(query, "n8n.txt")

    return resultado


def parte_2_sync():
    with open("src/TextParses/text.txt", "r", encoding="utf-8") as file:
        scraper_comments = file.read().strip()

    parser = CommentExtractor()
    resultado = parser.extract(scraper_comments)

    return resultado


async def main():
    resultado_parte_1, resultado_parte_2 = await asyncio.gather(
        asyncio.to_thread(parte_1_sync),
        asyncio.to_thread(parte_2_sync),
    )

    return resultado_parte_1, resultado_parte_2


if __name__ == "__main__":
    # Início da metrificação
    start_time = time.perf_counter()

    resultado_parte_1, resultado_parte_2 = asyncio.run(main())

    print("Resultado Parte 1:")
    print(json.dumps(resultado_parte_1, indent=2, ensure_ascii=False))

    print("\nResultado Parte 2:")
    print(json.dumps(resultado_parte_2, indent=2, ensure_ascii=False))

    # Fim da metrificação
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    minutes = int(execution_time // 60)
    seconds = execution_time % 60

    print(f"\n⏱ Tempo total de execução: {minutes} min {seconds:.2f} s")


# python -m src.TextParses.parse