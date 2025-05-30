"""
Module de logging centralisé pour l'application Cleaning Tracker

Usage simple:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Message")

Usage avec contexte:
    from app.core.logging import get_logger, with_context
    logger = get_logger(__name__)
    logger.info("Action utilisateur", extra=with_context(user_id="123", household_id="456"))
"""

from app.core.logging.config import get_logger, init_logging, log_config
from typing import Dict, Any


def with_context(**kwargs) -> Dict[str, Any]:
    """
    Helper pour ajouter du contexte aux logs

    Usage:
        logger.info("Message", extra=with_context(user_id="123", request_id="abc"))
    """
    return {"extra_data": kwargs}


# Initialiser le logging au chargement du module
init_logging()

__all__ = ["get_logger", "init_logging", "log_config", "with_context"]
