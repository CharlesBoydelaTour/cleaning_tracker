from enum import Enum
from typing import Any, Dict, Optional
from http import HTTPStatus


class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BaseApplicationException(Exception):
    """Exception de base pour l'application"""

    def __init__(
        self,
        error_code: str,
        user_message: str,
        technical_message: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
    ):
        self.error_code = error_code
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        self.severity = severity
        self.metadata = metadata or {}
        self.http_status = http_status

        super().__init__(self.technical_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'exception en dictionnaire pour la sérialisation"""
        return {
            "error_code": self.error_code,
            "user_message": self.user_message,
            "technical_message": self.technical_message,
            "severity": self.severity.value,
            "metadata": self.metadata,
            "http_status": self.http_status.value,
        }


# =============================================================================
# EXCEPTIONS MÉTIER
# =============================================================================


class BusinessException(BaseApplicationException):
    """Exception de base pour les erreurs métier"""

    def __init__(self, error_code: str, user_message: str, **kwargs):
        kwargs.setdefault("severity", ErrorSeverity.MEDIUM)
        super().__init__(error_code, user_message, **kwargs)


class HouseholdNotFound(BusinessException):
    """Exception levée quand un ménage n'est pas trouvé"""

    def __init__(self, household_id: str, **kwargs):
        super().__init__(
            error_code="HOUSEHOLD_NOT_FOUND",
            user_message=f"Le ménage avec l'ID {household_id} n'existe pas",
            technical_message=f"Household not found: {household_id}",
            http_status=HTTPStatus.NOT_FOUND,
            metadata={"household_id": household_id},
            **kwargs,
        )


class UserNotFound(BusinessException):
    """Exception levée quand un utilisateur n'est pas trouvé"""

    def __init__(self, user_id: str, **kwargs):
        super().__init__(
            error_code="USER_NOT_FOUND",
            user_message=f"L'utilisateur avec l'ID {user_id} n'existe pas",
            technical_message=f"User not found: {user_id}",
            http_status=HTTPStatus.NOT_FOUND,
            metadata={"user_id": user_id},
            **kwargs,
        )


class TaskNotFound(BusinessException):
    """Exception levée quand une tâche n'est pas trouvée"""

    def __init__(self, task_id: str, **kwargs):
        super().__init__(
            error_code="TASK_NOT_FOUND",
            user_message=f"La tâche avec l'ID {task_id} n'existe pas",
            technical_message=f"Task not found: {task_id}",
            http_status=HTTPStatus.NOT_FOUND,
            metadata={"task_id": task_id},
            **kwargs,
        )


class OccurrenceNotFound(BusinessException):
    """Exception levée quand une occurrence n'est pas trouvée"""

    def __init__(self, occurrence_id: str, **kwargs):
        super().__init__(
            error_code="OCCURRENCE_NOT_FOUND",
            user_message=f"L'occurrence avec l'ID {occurrence_id} n'existe pas",
            technical_message=f"Occurrence not found: {occurrence_id}",
            http_status=HTTPStatus.NOT_FOUND,
            metadata={"occurrence_id": occurrence_id},
            **kwargs,
        )


class TaskNotInHousehold(BusinessException):
    """Exception levée quand une tâche n'appartient pas au ménage spécifié"""

    def __init__(self, task_id: str, household_id: str, **kwargs):
        super().__init__(
            error_code="TASK_NOT_IN_HOUSEHOLD",
            user_message="La tâche demandée n'existe pas dans ce ménage",
            technical_message=f"Task {task_id} does not belong to household {household_id}",
            http_status=HTTPStatus.NOT_FOUND,
            metadata={"task_id": task_id, "household_id": household_id},
            **kwargs,
        )


class RoomNotFound(BusinessException):
    """Exception levée quand une pièce n'est pas trouvée"""

    def __init__(self, room_id: str, **kwargs):
        super().__init__(
            error_code="ROOM_NOT_FOUND",
            user_message=f"La pièce avec l'ID {room_id} n'existe pas",
            technical_message=f"Room not found: {room_id}",
            http_status=HTTPStatus.NOT_FOUND,
            metadata={"room_id": room_id},
            **kwargs,
        )

class UnauthorizedAccess(BusinessException):
    """Exception levée pour les accès non autorisés"""

    def __init__(self, resource: str, action: str, **kwargs):
        super().__init__(
            error_code="UNAUTHORIZED_ACCESS",
            user_message="Vous n'êtes pas autorisé à effectuer cette action",
            technical_message=f"Unauthorized access to {resource} for action {action}",
            http_status=HTTPStatus.FORBIDDEN,
            severity=ErrorSeverity.HIGH,
            metadata={"resource": resource, "action": action},
            **kwargs,
        )


class InsufficientPermissions(BusinessException):
    """Exception levée quand l'utilisateur n'a pas les permissions suffisantes"""

    def __init__(self, required_role: str, current_role: str, **kwargs):
        super().__init__(
            error_code="INSUFFICIENT_PERMISSIONS",
            user_message=f"Cette action nécessite le rôle '{required_role}' mais vous avez le rôle '{current_role}'",
            technical_message=f"Insufficient permissions: required {required_role}, has {current_role}",
            http_status=HTTPStatus.FORBIDDEN,
            severity=ErrorSeverity.HIGH,
            metadata={"required_role": required_role, "current_role": current_role},
            **kwargs,
        )


class BusinessRuleViolation(BusinessException):
    """Exception levée quand une règle métier est violée"""

    def __init__(self, rule: str, details: str, **kwargs):
        super().__init__(
            error_code="BUSINESS_RULE_VIOLATION",
            user_message=f"Règle métier violée: {details}",
            technical_message=f"Business rule violation: {rule} - {details}",
            http_status=HTTPStatus.CONFLICT,
            metadata={"rule": rule, "details": details},
            **kwargs,
        )


class DuplicateResource(BusinessException):
    """Exception levée lors de création de ressources dupliquées"""

    def __init__(self, resource_type: str, identifier: str, **kwargs):
        super().__init__(
            error_code="DUPLICATE_RESOURCE",
            user_message=f"Une ressource {resource_type} avec l'identifiant {identifier} existe déjà",
            technical_message=f"Duplicate {resource_type}: {identifier}",
            http_status=HTTPStatus.CONFLICT,
            metadata={"resource_type": resource_type, "identifier": identifier},
            **kwargs,
        )


# =============================================================================
# EXCEPTIONS TECHNIQUES
# =============================================================================


class TechnicalException(BaseApplicationException):
    """Exception de base pour les erreurs techniques"""

    def __init__(self, error_code: str, user_message: str, **kwargs):
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        kwargs.setdefault("http_status", HTTPStatus.INTERNAL_SERVER_ERROR)
        super().__init__(error_code, user_message, **kwargs)


class DatabaseError(TechnicalException):
    """Exception levée pour les erreurs de base de données"""

    def __init__(self, operation: str, details: str, **kwargs):
        super().__init__(
            error_code="DATABASE_ERROR",
            user_message="Une erreur technique est survenue. Veuillez réessayer plus tard",
            technical_message=f"Database error during {operation}: {details}",
            severity=ErrorSeverity.CRITICAL,
            metadata={"operation": operation, "details": details},
            **kwargs,
        )


class ExternalServiceError(TechnicalException):
    """Exception levée pour les erreurs de services externes"""

    def __init__(self, service_name: str, details: str, **kwargs):
        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            user_message="Un service externe est temporairement indisponible",
            technical_message=f"External service error from {service_name}: {details}",
            metadata={"service_name": service_name, "details": details},
            **kwargs,
        )


class ConfigurationError(TechnicalException):
    """Exception levée pour les erreurs de configuration"""

    def __init__(self, parameter: str, details: str, **kwargs):
        super().__init__(
            error_code="CONFIGURATION_ERROR",
            user_message="Erreur de configuration du système",
            technical_message=f"Configuration error for {parameter}: {details}",
            severity=ErrorSeverity.CRITICAL,
            metadata={"parameter": parameter, "details": details},
            **kwargs,
        )


# =============================================================================
# EXCEPTIONS DE VALIDATION
# =============================================================================


class ValidationException(BaseApplicationException):
    """Exception de base pour les erreurs de validation"""

    def __init__(self, error_code: str, user_message: str, **kwargs):
        kwargs.setdefault("severity", ErrorSeverity.LOW)
        kwargs.setdefault("http_status", HTTPStatus.BAD_REQUEST)
        super().__init__(error_code, user_message, **kwargs)


class InvalidInput(ValidationException):
    """Exception levée pour les entrées invalides"""

    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        super().__init__(
            error_code="INVALID_INPUT",
            user_message=f"Valeur invalide pour le champ '{field}': {reason}",
            technical_message=f"Invalid input for field {field} with value {value}: {reason}",
            metadata={"field": field, "value": str(value), "reason": reason},
            **kwargs,
        )


class MissingRequiredField(ValidationException):
    """Exception levée pour les champs requis manquants"""

    def __init__(self, field: str, **kwargs):
        super().__init__(
            error_code="MISSING_REQUIRED_FIELD",
            user_message=f"Le champ '{field}' est requis",
            technical_message=f"Missing required field: {field}",
            metadata={"field": field},
            **kwargs,
        )


class InvalidCredentials(ValidationException):
    """Exception levée pour les identifiants invalides"""

    def __init__(self, technical_message: str = None, **kwargs):
        final_technical_message = (
            technical_message or "Invalid authentication credentials"
        )
        super().__init__(
            error_code="INVALID_CREDENTIALS",
            user_message="Identifiants invalides",
            technical_message=final_technical_message,
            http_status=HTTPStatus.UNAUTHORIZED,
            severity=ErrorSeverity.MEDIUM,
            **kwargs,
        )


class TokenExpired(ValidationException):
    """Exception levée pour les tokens expirés"""

    def __init__(self, token_type: str = "access", **kwargs):
        super().__init__(
            error_code="TOKEN_EXPIRED",
            user_message="Votre session a expiré. Veuillez vous reconnecter",
            technical_message=f"Expired {token_type} token",
            http_status=HTTPStatus.UNAUTHORIZED,
            metadata={"token_type": token_type},
            **kwargs,
        )


class ValidationError(ValidationException):
    """Exception levée pour les erreurs de validation de schéma"""

    def __init__(self, errors: Dict[str, str], **kwargs):
        error_messages = [f"{field}: {message}" for field, message in errors.items()]
        super().__init__(
            error_code="VALIDATION_ERROR",
            user_message=f"Erreurs de validation: {'; '.join(error_messages)}",
            technical_message=f"Schema validation failed: {errors}",
            metadata={"validation_errors": errors},
            **kwargs,
        )


# =============================================================================
# UTILITAIRES
# =============================================================================


def get_http_status_from_exception(exception: Exception) -> HTTPStatus:
    """Retourne le code HTTP approprié pour une exception"""
    if isinstance(exception, BaseApplicationException):
        return exception.http_status

    # Mapping par défaut pour les exceptions Python standard
    exception_mapping = {
        ValueError: HTTPStatus.BAD_REQUEST,
        KeyError: HTTPStatus.NOT_FOUND,
        PermissionError: HTTPStatus.FORBIDDEN,
        FileNotFoundError: HTTPStatus.NOT_FOUND,
        ConnectionError: HTTPStatus.SERVICE_UNAVAILABLE,
        TimeoutError: HTTPStatus.REQUEST_TIMEOUT,
    }

    for exc_type, status in exception_mapping.items():
        if isinstance(exception, exc_type):
            return status

    return HTTPStatus.INTERNAL_SERVER_ERROR
