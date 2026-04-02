import tiktoken

class TokenCounter:
    def __init__(self, model: str):
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text)) if text else 0

if __name__ == "__main__":
    counter = TokenCounter("gpt-3.5-turbo")
    text = "Hello, how are you?"
    print(f"Token count for '{text}': {counter.count(text)}")
