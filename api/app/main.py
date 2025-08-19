from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.routers import auth, households, members, rooms, task_definitions, task_occurrences, notification_preferences

import os
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
    db_optional = os.getenv("DB_OPTIONAL", "0") == "1"
    try:
        timeout = float(os.getenv("DB_INIT_TIMEOUT", "10"))
    except ValueError:
        timeout = 10.0
    app.state.db_pool = await init_db_pool(optional=db_optional, timeout=timeout)
    if app.state.db_pool:
        print("Database connection pool initialized.")
    else:
        print("Database pool NOT initialized (DB_OPTIONAL=1).")
    yield
    if app.state.db_pool:
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
    allow_origins=settings.cors_origins,
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
    "redoc": "/redoc",
    "db_connected": bool(app.state.db_pool)
    }

@app.get("/healthz", tags=["health"]) 
async def healthz():
    return {"status": "ok", "db": bool(app.state.db_pool)}