```python
import json
import shlex
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class CurlCompiler:
    """
    Class to parse and execute curl commands programmatically using Python requests library.
    It supports extracting HTTP method, headers, authentication, payloads and URL from
    a curl command string, and provides functionality to execute the request and handle response data.

    Args: 
    :param timeout (int): Timeout for the HTTP requests in seconds. Default is 30.
    :param verify_ssl (bool): Whether to verify SSL certificates in HTTPS requests. Default is True.

    Methods:
            compile(): Parses the curl command and returns its components as a dictionary.
            execute(): Compiles the curl command and executes the HTTP request.
            call_endpoint(): Makes an HTTP request with given parameters.
            response_to_dict(): Converts a requests.Response to a dictionary format.
            pretty_print_response(): Prints a formatted HTTP response.
            get_domain(): Extracts the domain from a URL.
            generate_python_code(): Generates Python code representing the curl command.
    """
    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    # =========================================================
    # PUBLIC API
    # =========================================================

    def compile(self, curl_command: str) -> Dict[str, Any]:
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
        Parses the provided curl command string and executes the HTTP request accordingly.
        Returns the requests.Response object from the HTTP call.

        Args: 
        curl_command (str): The full curl command string to be parsed and executed.

        Returns:
                requests.Response: The response object received from executing the HTTP request.
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
        Executes an HTTP request with specified parameters using the requests library.

        Args: 
        method (str): HTTP method to use (e.g., 'GET', 'POST').
        url (str): Full URL to send the request to.
        headers (Optional[Dict[str, str]]): HTTP headers to include in the request.
        data (Optional[Any]): Raw data payload to send in the body of the request.
        json_data (Optional[Any]): JSON-serializable object to send as JSON payload.
        auth (Optional[tuple]): Tuple (username, password) for HTTP basic authentication.

        Returns:
                requests.Response: The response object resulting from the HTTP request.
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
        Converts a requests.Response object into a dictionary containing
        status code, headers, body, and success status.

        Args: 
        response (requests.Response): The HTTP response to convert.

        Returns:
                Dict[str, Any]: A dictionary representation of the response.
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
        Prints the HTTP response in a human-readable formatted style showing
        status, headers and body content with indents for clarity.

        Args: 
        response (requests.Response): The HTTP response to pretty print.

        Returns:
            None
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
        Extracts and returns the domain portion (netloc) from a given URL.

        Args: 
        url (str): The URL string to extract the domain from.

        Returns:
                str: The domain part of the URL.
        """
        return urlparse(url).netloc

    def _validate(self, data: Dict[str, Any]):
        if not data["url"]:
            raise ValueError("URL não encontrada no CURL.")

        if not data["method"]:
            raise ValueError("Método HTTP inválido.")

    # =========================================================
    # EXTRA FEATURES
    # =========================================================

    def generate_python_code(self, curl_command: str) -> str:
        """
        Generates Python code snippet using requests library that represents
        the equivalent HTTP request of the given curl command string.

        Args:
        curl_command (str): The curl command string to convert into Python code.

        Returns:
                str: Python code string ready to be executed or copied.
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
```