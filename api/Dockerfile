# Multi-stage build pour optimiser l'image
FROM python:3.13-slim AS builder

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installer uv pour la gestion des dépendances
RUN pip install uv

# Copier les fichiers de dépendances
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Installer les dépendances dans un venv (inclure les dev dependencies car elles contiennent des outils nécessaires)
RUN uv sync --frozen

# Stage final
FROM python:3.13-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Créer un utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Copier le venv depuis le builder et ajuster les permissions
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Définir le répertoire de travail
WORKDIR /app

# Copier le code source
COPY --chown=appuser:appuser . .

# Changer vers l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Commande par défaut (sera surchargée dans docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]