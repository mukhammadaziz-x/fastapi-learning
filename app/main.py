"""Educational Startup Platform — Main FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import engine, Base

# Import ALL models so Base.metadata knows about them
import app.models  # noqa: F401

# Import routers
from app.routers import (
    auth,
    users,
    subjects,
    groups,
    enrollments,
    assignments,
    submissions,
    leaderboard,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create tables on startup, dispose engine on shutdown."""
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="EduPlatform — Educational Startup API",
    description=(
        "Comprehensive educational platform with role-based access (Admin, Teacher, Student), "
        "subject-specific exam types (code editor, kahoot, essay, multiple choice), "
        "leaderboard, ranking algorithm, violation monitoring, and analytics dashboards."
    ),
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── Register all routers ──────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subjects.router)
app.include_router(groups.router)
app.include_router(enrollments.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
app.include_router(leaderboard.router)


# ── Pages ─────────────────────────────────────────────────────────
@app.get("/", tags=["Pages"])
def serve_home():
    """Login sahifasi."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "EduPlatform API — /docs"}


@app.get("/dashboard/admin", tags=["Pages"])
def serve_admin_dashboard():
    return FileResponse(os.path.join(static_dir, "admin.html"))


@app.get("/dashboard/teacher", tags=["Pages"])
def serve_teacher_dashboard():
    return FileResponse(os.path.join(static_dir, "teacher.html"))


@app.get("/dashboard/student", tags=["Pages"])
def serve_student_dashboard():
    return FileResponse(os.path.join(static_dir, "student.html"))


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "3.0.0", "platform": "EduPlatform"}
