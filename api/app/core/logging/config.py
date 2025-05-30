import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pydantic_settings import BaseSettings

from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Formatter qui ajoute des couleurs pour la console"""

    grey = "\x1b[38;21m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    COLORS = {
        logging.DEBUG: grey,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.grey)
        record.levelname = f"{log_color}{record.levelname}{self.reset}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Formatter pour sortie JSON structurée"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Ajouter les attributs personnalisés (contexte)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "household_id"):
            log_data["household_id"] = record.household_id

        # Ajouter l'exception si présente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Ajouter des données supplémentaires si présentes
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class LogConfig:
    """Configuration centralisée pour le système de logging"""

    def __init__(self):
        self.log_level = getattr(settings, "log_level", "INFO").upper()
        self.log_format = getattr(settings, "log_format", "json")  # 'json' ou 'text'
        self.log_file_path = getattr(settings, "log_file_path", "logs/app.log")
        self.log_max_bytes = getattr(settings, "log_max_bytes", 10 * 1024 * 1024)
        self.log_backup_count = getattr(settings, "log_backup_count", 5)
        self.environment = getattr(settings, "environment", "development")

        # Créer le répertoire de logs s'il n'existe pas
        if self.log_file_path:
            Path(self.log_file_path).parent.mkdir(parents=True, exist_ok=True)

    def get_console_handler(self) -> logging.StreamHandler:
        """Configure le handler pour la console"""
        console_handler = logging.StreamHandler(sys.stdout)

        if self.log_format == "json" or self.environment == "production":
            formatter = JSONFormatter()
        else:
            # Format texte avec couleurs pour le développement
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            if self.environment == "development":
                formatter = ColoredFormatter(format_string)
            else:
                formatter = logging.Formatter(format_string)

        console_handler.setFormatter(formatter)
        return console_handler

    def get_file_handler(self) -> Optional[logging.handlers.RotatingFileHandler]:
        """Configure le handler pour fichier avec rotation"""
        if not self.log_file_path:
            return None

        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file_path,
            maxBytes=self.log_max_bytes,
            backupCount=self.log_backup_count,
            encoding="utf-8",
        )

        # Toujours utiliser JSON pour les fichiers (facilite le parsing)
        formatter = JSONFormatter()
        file_handler.setFormatter(formatter)

        return file_handler

    def setup_logger(
        self,
        name: str,
        level: Optional[str] = None,
        extra_handlers: Optional[list] = None,
    ) -> logging.Logger:
        """
        Configure et retourne un logger

        Args:
            name: Nom du logger (ex: 'app.auth', 'app.database')
            level: Niveau de log spécifique (override la config globale)
            extra_handlers: Handlers supplémentaires à ajouter
        """
        logger = logging.getLogger(name)

        # Éviter la duplication des handlers
        if logger.hasHandlers():
            return logger

        # Définir le niveau
        log_level = getattr(logging, level or self.log_level)
        logger.setLevel(log_level)

        # Ajouter les handlers
        console_handler = self.get_console_handler()
        if console_handler:
            logger.addHandler(console_handler)

        file_handler = self.get_file_handler()
        if file_handler:
            logger.addHandler(file_handler)

        # Ajouter les handlers supplémentaires
        if extra_handlers:
            for handler in extra_handlers:
                logger.addHandler(handler)

        # Empêcher la propagation vers le logger root
        logger.propagate = False

        return logger

    def setup_app_loggers(self) -> Dict[str, logging.Logger]:
        """Configure tous les loggers de l'application"""
        loggers = {}

        # Logger principal de l'application
        loggers["app"] = self.setup_logger("app")

        # Loggers spécialisés
        loggers["auth"] = self.setup_logger("app.auth")
        loggers["database"] = self.setup_logger("app.database")
        loggers["api"] = self.setup_logger("app.api")
        loggers["celery"] = self.setup_logger("app.celery")
        loggers["external"] = self.setup_logger("app.external")  # Pour Supabase, etc.

        # Logger pour les requêtes HTTP (peut être plus verbeux en dev)
        if self.environment == "development":
            loggers["http"] = self.setup_logger("app.http", level="DEBUG")
        else:
            loggers["http"] = self.setup_logger("app.http", level="INFO")

        # Configurer les loggers tiers
        self._configure_third_party_loggers()

        return loggers

    def _configure_third_party_loggers(self):
        """Configure les loggers des bibliothèques tierces"""
        # Réduire le bruit des bibliothèques tierces
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        # Uvicorn logs
        if self.environment == "production":
            logging.getLogger("uvicorn").setLevel(logging.WARNING)
            logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# Instance globale de configuration
log_config = LogConfig()


# Fonction helper pour obtenir un logger
def get_logger(name: str) -> logging.Logger:
    """
    Obtient ou crée un logger avec la configuration par défaut

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
    """
    return log_config.setup_logger(name)


# Configuration automatique au chargement du module
def init_logging():
    """Initialise le système de logging de l'application"""
    loggers = log_config.setup_app_loggers()

    # Log de démarrage
    main_logger = loggers["app"]
    main_logger.info(
        "Logging system initialized",
        extra={
            "extra_data": {
                "environment": log_config.environment,
                "log_level": log_config.log_level,
                "log_format": log_config.log_format,
                "loggers_count": len(loggers),
            }
        },
    )

    return loggers
