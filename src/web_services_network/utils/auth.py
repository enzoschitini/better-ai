import os
from dotenv import load_dotenv

from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

load_dotenv()

class Authorization:
    @staticmethod
    def _get_header_authorization(
        authorization: str = Header(...),
        user: str = Header(..., alias="user")
    ):
        # print("Authorization Header:", authorization)
        # print("User Header:", user)

        # validação besta
        if not authorization:
            return {"valid": False}

        return {
            "valid": True,
            "token": authorization
        }
    
    @staticmethod
    def validate_api_key(
        api_key: str = Security(APIKeyHeader(name="X-API-Key"))
    ):
        expected_api_key = os.getenv("BETTERAI_API_KEY")

        # print("API KEY RECEBIDA:", api_key)
        # print("API KEY ESPERADA:", expected_api_key)

        if api_key == expected_api_key:
            return True

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key"
        )
