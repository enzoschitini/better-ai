import os
from fastapi import Header, HTTPException, Depends

class AuthService:
    @staticmethod
    def validate_betterai_key(authorization: str):
        back_end_api_key = os.getenv("BACK_END_API_KEY")

        if authorization != f"Bearer {back_end_api_key}":
            raise HTTPException(status_code=401, detail="Invalid Authorization Key")

    @staticmethod
    def validate_company_secret(client: str, secret_key: str):
        env_key_name = f"{client.upper()}_SECRET_KEY"
        secret_key_env = os.getenv(env_key_name)

        if secret_key_env is None:
            raise HTTPException(
                status_code=401,
                detail=f"Secret Key not found for client: {client}"
            )

        if secret_key != f"Bearer {secret_key_env}":
            raise HTTPException(status_code=401, detail="Invalid Company Secret Key")

class Authorization:
    @staticmethod
    def back_end_api_key(
        authorization: str = Header(...)
    ):
        AuthService.validate_betterai_key(authorization)
        return True

    @staticmethod
    def multikey(
        authorization: str = Header(...),
        client: str = Header(..., alias="Client"),
        secret_key: str = Header(..., alias="SecretKey"),
    ):
        # Valida chave master (BETTERAI_API_KEY)
        AuthService.validate_betterai_key(authorization)

        # Valida chave de empresa
        AuthService.validate_company_secret(client, secret_key)

        return True
