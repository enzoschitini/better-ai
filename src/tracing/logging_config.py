import logging
import os
import sys
from typing import ClassVar, Iterable, Mapping, Optional, Union


class ColoredFormatter(logging.Formatter):
    """
    Formats log records with ANSI colors applied to the level name for terminal output.
    This formatter keeps the original level name intact after formatting so other
    handlers are not affected by the temporary colorized representation.

    Args:
    :param fmt (str): Log format string used to render each record.
    :param datefmt (str): Optional date format string used for timestamp rendering. Default is "None".
    :param use_colors (bool): Enables or disables ANSI color formatting for level names. Default is "True".

    Methods:
            format(): Formats a log record and colorizes the level name when enabled.
    """

    COLORS: ClassVar[Mapping[str, str]] = {
        "DEBUG":    "\033[36m",
        "INFO":     "\033[32m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[1;35m",
    }
    RESET: ClassVar[str] = "\033[0m"

    def __init__(self, fmt: str, datefmt: Optional[str] = None, use_colors: bool = True):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a single logging record and injects ANSI color codes into its level name.
        The method temporarily mutates the level name only during rendering and restores
        the original value immediately after formatting.

        Args:
        record (logging.LogRecord): The logging record instance that will be formatted.

        Returns:
                str: The formatted log message string.
        """
        if not self.use_colors:
            return super().format(record)

        color = self.COLORS.get(record.levelname, "")
        original = record.levelname
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original


def _supports_color() -> bool:
    """Detects TTY and respects https://no-color.org/."""
    if os.getenv("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class LogManager:
    """
    Centralizes logging bootstrap and logger retrieval for the application.
    This class configures the root logger only once, applies formatting and optional
    color support, and can silence noisy third-party libraries at custom levels.

    Args:
    :param level (str): Global root logging level used during setup. Default is "None".
    :param fmt (str): Log output format string used by the stream handler. Default is "None".
    :param silence (Iterable[str] | Mapping[str, str]): Logger names or explicit logger-level mapping to silence. Default is "None".
    :param silence_level (str): Level applied when silence is provided as an iterable of logger names. Default is "WARNING".
    :param use_colors (bool): Enables or disables color formatting when not explicitly inferred from terminal support. Default is "None".

    Methods:
            setup(): Configures root logging, formatter, and optional per-logger silence levels.
            get_logger(): Returns a named logger and auto-configures logging if needed.
    """

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
        Configures the root logging system once with formatter, level, and silencing rules.
        This method resolves defaults from environment variables and class constants,
        then replaces existing root handlers to prevent duplicated log output.

        Args:
        level (str): Optional root logging level; when omitted it falls back to LOG_LEVEL or INFO. Default is "None".
        fmt (str): Optional log message format; when omitted DEFAULT_FORMAT is used. Default is "None".
        silence (Iterable[str] | Mapping[str, str]): Logger names or logger-to-level mapping to reduce noise. Default is "None".
        silence_level (str): Level assigned to each name when silence is an iterable. Default is "WARNING".
        use_colors (bool): Forces color on or off; when omitted terminal capability is auto-detected. Default is "None".

        Returns:
                None: This method configures logging side effects and does not return data.
        """

        if cls._configured:
            return

        resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
        resolved_fmt = fmt or cls.DEFAULT_FORMAT
        resolved_colors = use_colors if use_colors is not None else _supports_color()

        if silence is None:
            resolved_silence: Mapping[str, str] = cls.DEFAULT_SILENCE
        elif isinstance(silence, Mapping):
            resolved_silence = silence
        else:
            resolved_silence = {name: silence_level for name in silence}

        root = logging.getLogger()
        root.setLevel(resolved_level)
        for h in list(root.handlers):
            root.removeHandler(h)

        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(fmt=resolved_fmt, use_colors=resolved_colors))
        root.addHandler(handler)

        for name, lvl in resolved_silence.items():
            logging.getLogger(name).setLevel(lvl.upper())

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Returns a logger instance by name and guarantees logging is initialized beforehand.
        This method ensures setup is executed lazily so consumers can request loggers
        without manual bootstrap calls.

        Args:
        name (str): Fully qualified logger name used by the logging module registry.

        Returns:
                logging.Logger: The configured logger instance associated with the given name.
        """
        if not cls._configured:
            cls.setup()
        return logging.getLogger(name)


class LoggingMixin:
    """
    Provides a reusable logger property and convenience methods for logging calls.
    This mixin routes all log operations through LogManager and sets stacklevel so
    log origin points to the actual caller instead of the mixin wrapper.

    Methods:
        logger(): Returns a class-scoped logger for the current instance.
        debug(): Logs a message with DEBUG severity preserving caller location.
        info(): Logs a message with INFO severity preserving caller location.
        warning(): Logs a message with WARNING severity preserving caller location.
        error(): Logs a message with ERROR severity preserving caller location.
        critical(): Logs a message with CRITICAL severity preserving caller location.
        exception(): Logs an exception message with traceback preserving caller location.
    """

    @property
    def logger(self) -> logging.Logger:
        """
        Builds and returns a logger name based on module and class of the current instance.
        This property provides consistent namespacing so logs can be filtered and traced
        at the class level across the codebase.

        Returns:
            logging.Logger: The class-scoped logger resolved by LogManager.
        """
        cls = type(self)
        return LogManager.get_logger(f"{cls.__module__}.{cls.__name__}")

    def debug(self, msg, *args, **kwargs):
        """
        Logs a message at DEBUG level while preserving the original caller location.
        The method injects stacklevel to keep filename and line number pointing to
        the calling site instead of this wrapper method.

        Args:
        msg: Message template or object to log.
        *args: Positional arguments used by the logging formatter.
        **kwargs: Additional keyword arguments accepted by logging, including stacklevel.

        Returns:
            None: This method forwards the log call and does not return data.
        """
        kwargs.setdefault("stacklevel", 2)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Logs a message at INFO level while preserving the original caller location.
        The method sets a default stacklevel value to ensure source metadata points
        to the caller context instead of the mixin.

        Args:
        msg: Message template or object to log.
        *args: Positional arguments used by the logging formatter.
        **kwargs: Additional keyword arguments accepted by logging, including stacklevel.

        Returns:
            None: This method forwards the log call and does not return data.
        """
        kwargs.setdefault("stacklevel", 2)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Logs a message at WARNING level while preserving the original caller location.
        A default stacklevel is injected to maintain accurate file and line metadata
        in the resulting log record.

        Args:
        msg: Message template or object to log.
        *args: Positional arguments used by the logging formatter.
        **kwargs: Additional keyword arguments accepted by logging, including stacklevel.

        Returns:
            None: This method forwards the log call and does not return data.
        """
        kwargs.setdefault("stacklevel", 2)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Logs a message at ERROR level while preserving the original caller location.
        The wrapper applies a default stacklevel so diagnostics reference the true
        source of the error log invocation.

        Args:
        msg: Message template or object to log.
        *args: Positional arguments used by the logging formatter.
        **kwargs: Additional keyword arguments accepted by logging, including stacklevel.

        Returns:
            None: This method forwards the log call and does not return data.
        """
        kwargs.setdefault("stacklevel", 2)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Logs a message at CRITICAL level while preserving the original caller location.
        This method ensures call-site attribution remains correct by setting a default
        stacklevel value before delegating to the logger.

        Args:
        msg: Message template or object to log.
        *args: Positional arguments used by the logging formatter.
        **kwargs: Additional keyword arguments accepted by logging, including stacklevel.

        Returns:
            None: This method forwards the log call and does not return data.
        """
        kwargs.setdefault("stacklevel", 2)
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """
        Logs an exception message with traceback at ERROR level and caller attribution.
        The method defaults stacklevel for accurate source mapping and delegates to
        logger.exception to include exception context in output.

        Args:
        msg: Message template or object to log.
        *args: Positional arguments used by the logging formatter.
        **kwargs: Additional keyword arguments accepted by logging, including stacklevel.

        Returns:
            None: This method forwards the log call and does not return data.
        """
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

