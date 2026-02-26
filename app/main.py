from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import users
from app.database import engine, Base

# Import models so Base.metadata knows about them
import app.models.user  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Create all tables on startup (dev only; use Alembic in production)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="FastAPI CRUD App",
    description="Users CRUD API with PostgreSQL"
)

# Include routers
app.include_router(users.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "message": "FastAPI is running"}
