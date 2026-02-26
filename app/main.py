from fastapi import FastAPI
from app.routers import users
from app.database import engine, Base

# Create all tables (for development; use Alembic migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI CRUD App",
    description="Users CRUD API with PostgreSQL",
    version="1.0.0",
)

# Include routers
app.include_router(users.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "message": "FastAPI is running"}
