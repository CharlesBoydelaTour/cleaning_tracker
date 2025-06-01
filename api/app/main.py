from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.routers import auth, households, members, rooms, task_definitions, task_occurrences
from app.core.database import init_db_pool
from app.core.exceptions import BaseApplicationException
from app.core.exception_handler import (
    application_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)


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

# Root endpoint
@app.get("/", tags=["root"])
async def read_root():
    return {
        "message": "Cleaning Tracker API v2.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }