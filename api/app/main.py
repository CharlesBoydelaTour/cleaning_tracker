from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.routers import auth, households, members, rooms, task_definitions, task_occurrences, notification_preferences

from app.core.database import init_db_pool
from app.core.exceptions import BaseApplicationException
from app.core.exception_handler import (
    application_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database connection pool
    app.state.db_pool = await init_db_pool()
    print("Database connection pool initialized.")
    yield
    # Shutdown: Close the database connection pool
    await app.state.db_pool.close()
    print("Database connection pool closed.")


app = FastAPI(
    title="Cleaning Tracker API", 
    version="2.0.0",
    description="API pour gérer les tâches ménagères avec support des récurrences",
    lifespan=lifespan
)

# Configuration CORS pour permettre les requêtes depuis le front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.model_config.get("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000,http://127.0.0.1:3000"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajout des gestionnaires d'exceptions
app.add_exception_handler(BaseApplicationException, application_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(task_definitions.router, tags=["task-definitions"])  # Routes globales (comme /catalog)
app.include_router(task_occurrences.router, tags=["task-occurrences"])  # Routes globales (comme /occurrences/{id}/complete)
app.include_router(households.router, prefix="/households", tags=["households"])
app.include_router(members.router, prefix="/households", tags=["members"])
app.include_router(rooms.router, prefix="/households", tags=["rooms"])
app.include_router(task_definitions.household_router, prefix="/households", tags=["household-task-definitions"])  # Routes de ménage
app.include_router(task_occurrences.household_router, prefix="/households", tags=["household-task-occurrences"])  # Routes de ménage
app.include_router(notification_preferences.router, tags=["notification-preferences"])

# Root endpoint
@app.get("/", tags=["root"])
async def read_root():
    return {
        "message": "Cleaning Tracker API v2.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }