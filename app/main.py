from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import users, tests
from app.database import engine, Base
import os

# Import models so Base.metadata knows about them
import app.models.user  # noqa: F401
import app.models.test  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="Student Performance Checker",
    description="Complete test management system with fullscreen monitoring and violation detection",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(users.router)
app.include_router(tests.router)


@app.get("/", tags=["pages"])
def serve_home():
    """Serve the main page."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "Student Performance Checker API is running"}


@app.get("/teacher", tags=["pages"])
def serve_teacher_dashboard():
    """Serve teacher dashboard."""
    path = os.path.join(static_dir, "teacher.html")
    return FileResponse(path)


@app.get("/student/test/{token}", tags=["pages"])
def serve_student_test(token: str):
    """Serve student test page."""
    path = os.path.join(static_dir, "exam.html")
    return FileResponse(path)


@app.get("/results/{result_id}", tags=["pages"])
def serve_results_page(result_id: int):
    """Serve results page."""
    path = os.path.join(static_dir, "results.html")
    return FileResponse(path)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "message": "Student Performance Checker is running"}
