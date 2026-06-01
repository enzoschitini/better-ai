# app/logging_config.py
import logging
import os
import sys
from typing import ClassVar, Iterable, Mapping, Optional, Union


class ColoredFormatter(logging.Formatter):
    """Formatter que aplica cores ANSI ao nível do log."""

    COLORS: ClassVar[Mapping[str, str]] = {
        "DEBUG":    "\033[36m",    # ciano
        "INFO":     "\033[32m",    # verde
        "WARNING":  "\033[33m",    # amarelo
        "ERROR":    "\033[31m",    # vermelho
        "CRITICAL": "\033[1;35m",  # magenta negrito
    }
    RESET: ClassVar[str] = "\033[0m"

    def __init__(self, fmt: str, datefmt: Optional[str] = None, use_colors: bool = True):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        if not self.use_colors:
            return super().format(record)

        color = self.COLORS.get(record.levelname, "")
        original = record.levelname
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original  # restaura para não afetar outros handlers


def _supports_color() -> bool:
    """Detecta TTY e respeita https://no-color.org/."""
    if os.getenv("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class LogManager:
    """Configuração global de logging."""

    DEFAULT_FORMAT: ClassVar[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DEFAULT_SILENCE: ClassVar[Mapping[str, str]] = {
        "httpx": "WARNING",
        "httpcore": "WARNING",
        "openai": "WARNING",
        "agno": "WARNING",
    }

    _configured: ClassVar[bool] = False

    @classmethod
    def setup(
        cls,
        level: Optional[str] = None,
        fmt: Optional[str] = None,
        silence: Optional[Union[Iterable[str], Mapping[str, str]]] = None,
        silence_level: str = "WARNING",
        use_colors: Optional[bool] = None,
    ) -> None:
        """
        Configura logging da aplicação. Chame UMA vez no entry point.

        Args:
            level: DEBUG/INFO/WARNING/ERROR/CRITICAL. Default: env LOG_LEVEL ou INFO.
            fmt: formato das mensagens. Default: DEFAULT_FORMAT.
            silence: libs a silenciar. Lista (["httpx", "openai"]) ou mapping
                     ({"httpx": "ERROR"}). None usa DEFAULT_SILENCE.
            silence_level: nível usado quando `silence` é uma lista.
            use_colors: força cores on/off. Default: detecta TTY.
        """
        if cls._configured:
            return

        resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
        resolved_fmt = fmt or cls.DEFAULT_FORMAT
        resolved_colors = use_colors if use_colors is not None else _supports_color()

        # Normaliza `silence` para Mapping[str, str]
        if silence is None:
            resolved_silence: Mapping[str, str] = cls.DEFAULT_SILENCE
        elif isinstance(silence, Mapping):
            resolved_silence = silence
        else:
            resolved_silence = {name: silence_level for name in silence}

        root = logging.getLogger()
        root.setLevel(resolved_level)
        for h in list(root.handlers):  # evita handlers duplicados em reloads
            root.removeHandler(h)

        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(fmt=resolved_fmt, use_colors=resolved_colors))
        root.addHandler(handler)

        for name, lvl in resolved_silence.items():
            logging.getLogger(name).setLevel(lvl.upper())

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if not cls._configured:
            cls.setup()
        return logging.getLogger(name)


class LoggingMixin:
    """
    Dá a qualquer classe um logger nomeado + atalhos para os níveis.

    Uso:
        class ContentGenerator(LoggingMixin):
            def run(self):
                self.info("começando")
                self.debug("payload=%s", payload)
                try:
                    ...
                except Exception:
                    self.exception("falhou")
    """

    @property
    def logger(self) -> logging.Logger:
        cls = type(self)
        return LogManager.get_logger(f"{cls.__module__}.{cls.__name__}")

    # stacklevel=2 garante que filename/lineno apontem para quem chamou,
    # não para esta classe.
    def debug(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 2)
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Use dentro de `except`: loga em ERROR com traceback."""
        kwargs.setdefault("stacklevel", 2)
        self.logger.exception(msg, *args, **kwargs)

if __name__ == "__main__":
    # Setup com controle fino por lib (mapping):
    LogManager.setup(
        level="INFO",
        silence={
            "httpx": "ERROR",
            "openai": "WARNING",
            "sqlalchemy.engine": "WARNING",
        },
    )

    # Formato customizado, sem cores (para arquivo, CI etc.):
    LogManager.setup(
        fmt="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d — %(message)s",
        use_colors=False,
    )

    # Em uma classe:
    #from src.tracing.logging_config import LoggingMixin

    class ContentGenerator(LoggingMixin):
        def run(self, prompt: str):
            self.info("gerando conteúdo")
            self.debug("prompt=%r", prompt)
            try:
                result = "Simulated generated content based on prompt: " + prompt
                self.debug("resultado simulado: %r", result)
            except Exception:
                self.exception("falha ao chamar modelo")
                raise
            self.info("conteúdo gerado em %d chars", len(result))
            return result
        
        def simulate_error(self):
            self.error("simulando erro")
            #raise ValueError("Erro simulado para teste de logging")
    
    generator = ContentGenerator()
    generator.run("Escreva um post sobre IA e sustentabilidade.")
    generator.simulate_error()
    
    # python -m src.tracing.logging_config
