from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, tests
from app.database import engine, Base

# Import models so Base.metadata knows about them
import app.models.user  # noqa: F401
import app.models.test  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Create all tables on startup (dev only; use Alembic in production)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="FastAPI Student Performance Checker",
    description="Complete test management system with fullscreen violation detection"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(tests.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "message": "FastAPI Student Performance Checker is running"}
