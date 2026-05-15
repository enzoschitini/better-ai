import json
import shlex
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class CurlCompiler:
    """
    Classe responsável por:
    - Compilar uma string CURL
    - Extrair método, headers, body e URL
    - Executar a requisição HTTP
    """

    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    # =========================================================
    # PUBLIC API
    # =========================================================

    def compile(self, curl_command: str) -> Dict[str, Any]:
        """
        Compila uma string CURL em um dicionário estruturado.
        """

        tokens = shlex.split(curl_command)

        if not tokens or tokens[0] != "curl":
            raise ValueError("Comando inválido. Deve iniciar com 'curl'.")

        result = {
            "method": "GET",
            "url": None,
            "headers": {},
            "params": {},
            "data": None,
            "json": None,
            "auth": None,
        }

        i = 1

        while i < len(tokens):
            token = tokens[i]

            # ==============================
            # METHOD
            # ==============================
            if token in ["-X", "--request"]:
                i += 1
                result["method"] = tokens[i].upper()

            # ==============================
            # HEADERS
            # ==============================
            elif token in ["-H", "--header"]:
                i += 1
                header = tokens[i]

                if ":" in header:
                    key, value = header.split(":", 1)
                    result["headers"][key.strip()] = value.strip()

            # ==============================
            # BODY
            # ==============================
            elif token in [
                "-d",
                "--data",
                "--data-raw",
                "--data-binary",
                "--data-urlencode",
            ]:
                i += 1
                raw_data = tokens[i]

                try:
                    parsed_json = json.loads(raw_data)
                    result["json"] = parsed_json
                except Exception:
                    result["data"] = raw_data

                # Define POST automaticamente
                if result["method"] == "GET":
                    result["method"] = "POST"

            # ==============================
            # BASIC AUTH
            # ==============================
            elif token in ["-u", "--user"]:
                i += 1
                auth = tokens[i]

                if ":" in auth:
                    username, password = auth.split(":", 1)
                    result["auth"] = (username, password)

            # ==============================
            # URL
            # ==============================
            elif token.startswith("http://") or token.startswith("https://"):
                result["url"] = token

            i += 1

        self._validate(result)

        return result

    def execute(self, curl_command: str) -> requests.Response:
        """
        Compila e executa um CURL.
        """

        request_data = self.compile(curl_command)

        return self.call_endpoint(
            method=request_data["method"],
            url=request_data["url"],
            headers=request_data["headers"],
            data=request_data["data"],
            json_data=request_data["json"],
            auth=request_data["auth"],
        )

    def call_endpoint(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        auth: Optional[tuple] = None,
    ) -> requests.Response:
        """
        Executa uma chamada HTTP.
        """

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            json=json_data,
            auth=auth,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )

        return response

    # =========================================================
    # HELPERS
    # =========================================================

    def response_to_dict(self, response: requests.Response) -> Dict[str, Any]:
        """
        Converte a resposta para dict estruturado.
        """

        try:
            body = response.json()
        except Exception:
            body = response.text

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
            "success": response.ok,
        }

    def pretty_print_response(self, response: requests.Response):
        """
        Exibe resposta formatada.
        """

        parsed = self.response_to_dict(response)

        print("=" * 60)
        print(f"STATUS: {parsed['status_code']}")
        print("=" * 60)

        print("\nHEADERS:")
        print(json.dumps(parsed["headers"], indent=4, ensure_ascii=False))

        print("\nBODY:")
        print(json.dumps(parsed["body"], indent=4, ensure_ascii=False)
              if isinstance(parsed["body"], dict)
              else parsed["body"])

        print("=" * 60)

    def get_domain(self, url: str) -> str:
        """
        Extrai domínio da URL.
        """

        return urlparse(url).netloc

    def _validate(self, data: Dict[str, Any]):
        """
        Valida dados compilados.
        """

        if not data["url"]:
            raise ValueError("URL não encontrada no CURL.")

        if not data["method"]:
            raise ValueError("Método HTTP inválido.")

    # =========================================================
    # EXTRA FEATURES
    # =========================================================

    def generate_python_code(self, curl_command: str) -> str:
        """
        Gera código Python equivalente ao CURL.
        """

        compiled = self.compile(curl_command)

        code = f"""
import requests

response = requests.request(
    method="{compiled['method']}",
    url="{compiled['url']}",
    headers={json.dumps(compiled['headers'], indent=4)},
    json={json.dumps(compiled['json'], indent=4)},
    data={repr(compiled['data'])}
)

print(response.status_code)
print(response.text)
"""

        return code.strip()


# =========================================================
# EXEMPLO DE USO
# =========================================================

if __name__ == "__main__":

    curl = '''
    curl -X POST "https://httpbin.org/post" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TOKEN_123" \
    -d '{"message":"hello world","value":123}'
    '''

    curl = '''
    curl --location --request POST 'http://localhost:8000/embedding'
    '''

    client = CurlCompiler(timeout=15)

    # Compilar CURL
    compiled = client.compile(curl)

    print("\nCURL COMPILADO:")
    print(json.dumps(compiled, indent=4, ensure_ascii=False))

    # Executar
    response = client.execute(curl)

    # Mostrar resposta
    client.pretty_print_response(response)

    # Gerar código equivalente
    print("\nCÓDIGO PYTHON GERADO:\n")
    print(client.generate_python_code(curl))