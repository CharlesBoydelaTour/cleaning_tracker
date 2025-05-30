from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.routers import auth, households, tasks, occurrences, members, rooms
from app.core.database import init_db_pool  # Added import
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


app = FastAPI(title="Cleaning Tracker API", lifespan=lifespan)  # Added lifespan

# Ajout des gestionnaires d'exceptions
app.add_exception_handler(BaseApplicationException, application_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(households.router, prefix="/households", tags=["households"])
app.include_router(members.router, prefix="/households", tags=["members"])
app.include_router(rooms.router, prefix="/households", tags=["rooms"])
app.include_router(tasks.router, prefix="/households", tags=["tasks"])
app.include_router(occurrences.router, prefix="/occurrences", tags=["occurrences"])
