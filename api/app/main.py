from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import auth, households, tasks, occurrences, members, rooms
from app.core.database import init_db_pool  # Added import


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

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(households.router, prefix="/households", tags=["households"])
app.include_router(members.router, prefix="/households", tags=["members"])
app.include_router(rooms.router, prefix="/households", tags=["rooms"])
app.include_router(tasks.router, prefix="/households", tags=["tasks"])
app.include_router(occurrences.router, prefix="/occurrences", tags=["occurrences"])
