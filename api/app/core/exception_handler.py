"""
Gestionnaire global d'exceptions pour FastAPI
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Union
import logging

from app.core.exceptions import BaseApplicationException, get_http_status_from_exception
from app.core.logging import get_logger, with_context

logger = get_logger(__name__)


async def application_exception_handler(
    request: Request, exc: BaseApplicationException
) -> JSONResponse:
    """Gestionnaire pour les exceptions personnalisées de l'application"""

    # Log de l'exception avec le contexte approprié
    log_level = (
        logging.ERROR if exc.severity.value in ["high", "critical"] else logging.WARNING
    )

    logger.log(
        log_level,
        f"Exception métier: {exc.error_code}",
        extra=with_context(
            error_code=exc.error_code,
            severity=exc.severity.value,
            user_message=exc.user_message,
            technical_message=exc.technical_message,
            metadata=exc.metadata,
            http_status=exc.http_status.value,
            path=request.url.path,
            method=request.method,
        ),
        exc_info=exc.severity.value == "critical",
    )

    return JSONResponse(
        status_code=exc.http_status.value,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.user_message,
                "severity": exc.severity.value,
                "metadata": exc.metadata,
            }
        },
    )


async def http_exception_handler(
    request: Request, exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """Gestionnaire pour les HTTPException de FastAPI/Starlette"""

    logger.warning(
        f"HTTP Exception: {exc.status_code}",
        extra=with_context(
            status_code=exc.status_code,
            detail=str(exc.detail),
            path=request.url.path,
            method=request.method,
        ),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "severity": "medium",
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Gestionnaire pour les erreurs de validation Pydantic"""

    errors = {}
    for error in exc.errors():
        field_path = ".".join(str(x) for x in error["loc"])
        errors[field_path] = error["msg"]

    logger.warning(
        "Erreur de validation des données",
        extra=with_context(
            validation_errors=errors,
            path=request.url.path,
            method=request.method,
        ),
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Erreurs de validation des données",
                "severity": "low",
                "metadata": {"validation_errors": errors},
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Gestionnaire pour toutes les autres exceptions non gérées"""

    http_status = get_http_status_from_exception(exc)

    logger.error(
        "Exception non gérée",
        extra=with_context(
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            path=request.url.path,
            method=request.method,
            http_status=http_status.value,
        ),
        exc_info=True,
    )

    return JSONResponse(
        status_code=http_status.value,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Une erreur interne est survenue",
                "severity": "high",
            }
        },
    )
