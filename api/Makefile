# =============================================================================
# CLEANING TRACKER API - Makefile
# =============================================================================

.PHONY: help install dev staging prod clean test lint format docker-build

# Variables
PYTHON := uv run python
PIP := uv
PYTEST := uv run pytest
DOCKER_COMPOSE := docker-compose

# Couleurs pour l'affichage
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
RESET := \033[0m

# Aide par défaut
help: ## Affiche cette aide
	@echo "$(BLUE)🧹 Cleaning Tracker API - Commandes disponibles$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# =============================================================================
# INSTALLATION ET DEPENDENCIES
# =============================================================================

install: ## Installe toutes les dépendances
	@echo "$(YELLOW)📦 Installation des dépendances...$(RESET)"
	$(PIP) sync

install-dev: ## Installe les dépendances de développement
	@echo "$(YELLOW)📦 Installation des dépendances de développement...$(RESET)"
	$(PIP) sync --dev

# =============================================================================
# DÉVELOPPEMENT
# =============================================================================

dev: ## Lance l'API en mode développement local
	@echo "$(GREEN)🚀 Démarrage en mode développement local...$(RESET)"
	@chmod +x scripts/start-dev.sh
	@./scripts/start-dev.sh
	
dev-worker: ## Lance le worker Celery en mode développement
	@echo "$(GREEN)👷 Démarrage du worker Celery...$(RESET)"
	@export ENVIRONMENT=development && $(PYTHON) -m celery -A app.core.celery_app worker --loglevel=debug

# =============================================================================
# STAGING (Docker local)
# =============================================================================

staging: ## Lance l'application en mode staging avec Docker
	@echo "$(GREEN)🐳 Démarrage en mode staging (Docker)...$(RESET)"
	@chmod +x scripts/start-staging.sh
	@./scripts/start-staging.sh

staging-logs: ## Affiche les logs en mode staging
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

staging-stop: ## Arrête les services staging
	@echo "$(RED)🛑 Arrêt des services staging...$(RESET)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

# =============================================================================
# PRODUCTION
# =============================================================================

prod: ## Lance l'application en mode production
	@echo "$(GREEN)🌍 Démarrage en mode production...$(RESET)"
	@chmod +x scripts/start-prod.sh
	@./scripts/start-prod.sh

prod-logs: ## Affiche les logs en mode production
	@$(DOCKER_COMPOSE) logs -f

prod-stop: ## Arrête les services production
	@echo "$(RED)🛑 Arrêt des services production...$(RESET)"
	@$(DOCKER_COMPOSE) down

# =============================================================================
# TESTS
# =============================================================================

test: ## Lance tous les tests
	@echo "$(YELLOW)🧪 Lancement des tests...$(RESET)"
	@export ENVIRONMENT=development && $(PYTEST) -v

test-fast: ## Lance les tests rapides uniquement
	@echo "$(YELLOW)⚡ Tests rapides...$(RESET)"
	@export ENVIRONMENT=development && $(PYTEST) -v -m "not slow"

test-coverage: ## Lance les tests avec coverage
	@echo "$(YELLOW)📊 Tests avec coverage...$(RESET)"
	@export ENVIRONMENT=development && $(PYTEST) --cov=app --cov-report=html --cov-report=term

# =============================================================================
# QUALITÉ DU CODE
# =============================================================================

lint: ## Vérifie le style du code avec ruff
	@echo "$(YELLOW)🔍 Vérification du style...$(RESET)"
	@$(PIP) run ruff check .

format: ## Formate le code avec ruff
	@echo "$(YELLOW)✨ Formatage du code...$(RESET)"
	@$(PIP) run ruff format .
	@$(PIP) run ruff check --fix .

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Construit l'image Docker
	@echo "$(YELLOW)🐳 Construction de l'image Docker...$(RESET)"
	@docker build -t cleaning-tracker-api .

docker-clean: ## Nettoie les images Docker inutilisées
	@echo "$(YELLOW)🧹 Nettoyage Docker...$(RESET)"
	@docker system prune -f

# =============================================================================
# UTILITAIRES
# =============================================================================

clean: ## Nettoie les fichiers temporaires
	@echo "$(YELLOW)🧹 Nettoyage...$(RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf htmlcov

env-check: ## Vérifie la configuration d'environnement
	@echo "$(BLUE)🔧 Vérification de l'environnement...$(RESET)"
	@echo "ENVIRONMENT: $${ENVIRONMENT:-development}"
	@echo "Fichiers .env disponibles:"
	@ls -la .env* 2>/dev/null || echo "Aucun fichier .env trouvé"

logs: ## Affiche les logs de l'application
	@echo "$(BLUE)📄 Logs de l'application...$(RESET)"
	@tail -f logs/app.log

# =============================================================================
# MIGRATION ET BASE DE DONNÉES
# =============================================================================

db-test: ## Test la connexion à la base de données
	@echo "$(YELLOW)🗄️  Test de connexion à la base...$(RESET)"
	@export ENVIRONMENT=development && $(PYTHON) scripts/test_db_connection.py

# Par défaut, affiche l'aide
.DEFAULT_GOAL := help
