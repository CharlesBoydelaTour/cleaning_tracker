# Environnement de développement full Docker

Ce document décrit comment lancer l'API FastAPI, le front React (Vite), Redis, Celery et une stack Supabase locale (simplifiée) entièrement dans Docker.

> Objectif: ne plus avoir besoin d'installer Python, Node ou Postgres localement. Seul Docker est requis.

## Services

- api: FastAPI + Uvicorn (hot reload)
- celery_worker: Worker Celery (debug, 1 worker)
- front: Vite React (hot reload)
- redis: Broker/Backend Celery
- supabase-db: Postgres (données)
- supabase-rest: PostgREST (API Supabase)
- supabase-auth: GoTrue (auth)
- supabase-storage: Storage API

## Lancement

```bash
docker compose -f docker-compose.dev.yml up --build
```

Ensuite:

- Front: <http://localhost:5173>
- API: <http://localhost:8000>
- Supabase REST (PostgREST): <http://localhost:3000> (interne, via service `supabase-rest`)
- Auth (GoTrue): <http://localhost:9999>
- Redis Commander (non inclus ici) : à ajouter si besoin

## Variables / overrides

Les clés Supabase (ANON/SERVICE) sont mock si non fournies. Pour personnaliser créez un fichier `.env` à la racine:

```bash
SUPABASE_ANON_KEY=... 
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
```

Puis relancez `docker compose up -d`.

## Notes

- Le volume `/app/.venv` est masqué par le bind mount. On le garde en volume anonyme grâce à la ligne `- /app/.venv` dans `docker-compose.dev.yml` pour réutiliser l'environnement créé dans l'image.
- Pour installer une nouvelle dépendance Python: modifiez `pyproject.toml` puis reconstruisez l'image API: `docker compose build api`.
- Pour une lib JS: `docker compose exec front bun add <lib>` (cela mettra à jour `package.json` local et le cache).

## Tests

API tests:

```bash
docker compose exec api pytest -q
```

## Migrations Supabase

Le flux automatisé complet Supabase CLI n'est pas entièrement encapsulé ici (stack minimaliste). Pour tirer parti des migrations vous pouvez continuer à utiliser `supabase migration up` localement OU intégrer les images officielles supplémentaires.

### Passer en mode Supabase Cloud

1. Créer un fichier `api/.env.remote` (exemple déjà fourni) avec:
	- `SUPABASE_URL` (URL du projet cloud)
	- `SUPABASE_ANON_KEY`
	- `SERVICE_ROLE_KEY` (ne jamais exposer côté front)
	- `DATABASE_URL` (string de connexion Postgres fournie par le dashboard)
2. Dans `docker-compose.dev.yml`, commenter la ligne `.env.dev` et décommenter `.env.remote`.
3. Redémarrer:

	```bash
	docker compose -f docker-compose.dev.yml up -d --build api celery_worker
	```

4. Appliquer les migrations sur la base distante:

	```bash
	supabase migration up --db-url "$DATABASE_URL"
	```

5. Vérifier:

	```bash
	docker compose exec api env | grep SUPABASE_URL
	```

Pour revenir au mode local, inverser simplement les fichiers d'env dans le compose.

## Prochaines améliorations potentielles

- Ajouter le studio (interface Supabase) via image `supabase/studio`.
- Ajouter Redis Commander pour inspecter Redis.
- Service Celery Beat séparé.
- Intégrer l'exécution des migrations au démarrage.
