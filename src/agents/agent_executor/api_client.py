import json
from typing import Any, Dict, Generator, Optional

import requests


class AgentApiClient:
    """Client for AgentOS runs endpoint with direct and stream modes."""

    def __init__(self, agent_id: str, host: str = "localhost", port: int = 7777):
        self.agent_id = agent_id
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.runs_url = f"{self.base_url}/agents/{self.agent_id}/runs"

    def run_direct(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "message": message,
            "stream": "false",
        }

        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        if extra_payload:
            payload.update(extra_payload)

        try:
            response = requests.post(self.runs_url, data=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to run direct API request: {str(e)}") from e

    def run_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
    ) -> Generator[Dict[str, Any], None, None]:
        payload: Dict[str, Any] = {
            "message": message,
            "stream": "true",
        }

        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        if extra_payload:
            payload.update(extra_payload)

        try:
            response = requests.post(self.runs_url, data=payload, stream=True, timeout=timeout)
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to start stream API request: {str(e)}") from e

        for line in response.iter_lines():
            if not line:
                continue

            decoded = line.decode("utf-8")
            if not decoded.startswith("data:"):
                continue

            json_str = decoded.replace("data:", "", 1).strip()
            if not json_str:
                continue

            try:
                yield json.loads(json_str)
            except Exception:
                continue
