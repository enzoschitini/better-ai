import uuid
import time
import secrets
import string

class IDGenerator:
    """
    Classe utilitária para geração de IDs únicos e versáteis.
    Engloba UUIDs, Timestamps, Tokens e IDs Customizados.
    """

    @classmethod
    def uuid(cls, version: int = 4) -> str:
        """Gera um UUID (v4 aleatório ou v1 baseado em tempo/MAC)."""
        if version == 1:
            return str(uuid.uuid1())
        return str(uuid.uuid4())

    @classmethod
    def timestamp(
        cls, 
        prefix: str = "", 
        separator: str = "", 
        as_hex: bool = False, 
        suffix_len: int = 4
    ) -> str:
        """
        Gera um ID baseado no tempo atual (nanosegundos).
        
        :param prefix: Texto no início do ID.
        :param separator: Caractere entre o prefixo e o ID.
        :param as_hex: Se True, encurta o ID usando base hexadecimal.
        :param suffix_len: Quantidade de caracteres aleatórios no final (evita colisão).
        """
        now_ns = time.time_ns()
        
        # Converte a base do tempo
        time_part = hex(now_ns)[2:] if as_hex else str(now_ns)
        
        # Gera sufixo aleatório seguro
        alphabet = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(suffix_len))
        
        # Montagem com tratamento de prefixo
        full_prefix = f"{prefix}{separator}" if prefix else ""
        return f"{full_prefix}{time_part}{random_part}"

    @classmethod
    def token(cls, length: int = 16, url_safe: bool = True) -> str:
        """Gera tokens aleatórios para sessões, cupons ou senhas."""
        if url_safe:
            return secrets.token_urlsafe(length)[:length]
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def custom(cls, pattern: str) -> str:
        """
        Gera ID baseado em uma máscara.
        # = Número, ? = Letra, * = Alfanumérico.
        Ex: custom("ID-####-??") -> 'ID-8291-XJ'
        """
        res = []
        for char in pattern:
            if char == '#':
                res.append(secrets.choice(string.digits))
            elif char == '?':
                res.append(secrets.choice(string.ascii_uppercase))
            elif char == '*':
                res.append(secrets.choice(string.ascii_letters + string.digits))
            else:
                res.append(char)
        return "".join(res)

if __name__ == "__main__":
    # --- 1. MODO TIMESTAMP (A estrela da flexibilidade) ---
    # Numérico simples (Nanosegundos + 4 dígitos aleatórios)
    print(f"Timestamp Puro:     {IDGenerator.timestamp()}")

    # Com prefixo e separador (Ideal para Bancos de Dados)
    print(f"Com Prefixo:       {IDGenerator.timestamp(prefix='USR', separator='_')}")

    # Versão Hexadecimal (Elegante e mais curta para URLs)
    print(f"Timestamp Hex:      {IDGenerator.timestamp(as_hex=True)}")

    # --- 2. MODO UUID ---
    # O padrão ouro para sistemas distribuídos
    print(f"UUID v4:            {IDGenerator.uuid()}")

    # --- 3. MODO TOKEN ---
    # Perfeito para códigos de recuperação de senha ou convites
    print(f"Token Curto:        {IDGenerator.token(length=8)}")

    # --- 4. MODO CUSTOMIZADO ---
    # Ideal para números de série ou protocolos de atendimento
    print(f"Protocolo:          {IDGenerator.custom('PROTO-####-????-**')}")