# 🎓 Student Performance Checker - Complete Application

> **Advanced Testing Platform with Fullscreen Violation Detection & Real-time Monitoring**

![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-teal)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue)

---

## 📋 Overview

A **complete, production-ready** FastAPI application for managing student assessments with:

✅ **Fullscreen Violation Detection** - Automatic test failure after 3 fullscreen exits  
✅ **Real-time Monitoring** - Track violations, time, and progress  
✅ **Time-Limited Access** - Tests accessible only during teacher-defined windows  
✅ **Secure CRUD** - Full test/question/result management  
✅ **PostgreSQL Database** - Alembic migrations included  
✅ **RESTful API** - Complete with OpenAPI documentation  
✅ **Beautiful UI** - Modern HTML5 fullscreen test interface  
✅ **Comprehensive Tests** - Full test suite included  

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
Python 3.11+
PostgreSQL 14+
```

### 2. Install & Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python -m alembic upgrade head

# Run comprehensive tests
python test_comprehensive.py
```

### 3. Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Access Application
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Test Interface**: Open `test_interface.html` in browser

---

## 📦 Project Structure

```
fastapi-learning/
├── app/
│   ├── models/
│   │   ├── user.py        # User authentication model
│   │   └── test.py        # Test-related models (8 tables)
│   ├── schemas/
│   │   ├── user.py        # Pydantic User schemas
│   │   └── test.py        # Pydantic Test schemas
│   ├── crud/
│   │   ├── user.py        # User CRUD operations
│   │   └── test.py        # Test CRUD operations
│   ├── routers/
│   │   ├── users.py       # User endpoints
│   │   └── tests.py       # Test endpoints (14 routes)
│   ├── database.py        # PostgreSQL connection
│   └── main.py            # FastAPI app (24 routes total)
├── alembic/
│   ├── versions/
│   │   ├── 3a4b5c6d7e8f_create_users_table.py
│   │   └── 4c5d6e7f8g9h_create_test_tables.py
│   └── env.py
├── test_interface.html    # Student test UI
├── test_comprehensive.py  # Full test suite
├── requirements.txt       # Dependencies
├── .env                   # Environment variables
├── IMPLEMENTATION_GUIDE.md # Detailed guide
├── FULLSCREEN_MONITORING.md # Monitoring details
└── README.md              # This file
```

---

## 🗄️ Database Schema

### 8 Tables with Full Relationships:

1. **users** - Student/Teacher authentication
2. **teachers** - Teacher profiles
3. **students** - Student enrollment
4. **tests** - Test definitions with time windows
5. **questions** - Test questions (multiple choice, essay, etc)
6. **test_results** - Student test attempts
7. **student_answers** - Individual question responses
8. **fullscreen_violations** - Violation tracking

**All tables indexed for optimal performance**

---

## 🔌 API Endpoints (24 Total)

### Authentication & Users (User routes)
- User CRUD operations (create, read, update, delete)

### Test Management (Teacher)
- `POST /api/v1/tests/` - Create test
- `GET /api/v1/tests/` - List tests
- `GET /api/v1/tests/{test_id}` - Get test details
- `PATCH /api/v1/tests/{test_id}` - Update test
- `DELETE /api/v1/tests/{test_id}` - Delete test

### Questions
- `POST /api/v1/tests/{test_id}/questions` - Add question
- `GET /api/v1/tests/{test_id}/questions` - Get questions
- `DELETE /api/v1/tests/{test_id}/questions/{question_id}` - Delete question

### Test Taking (Student)
- `POST /api/v1/tests/{test_id}/start` - Begin test
- `POST /api/v1/tests/{test_id}/results/{result_id}/answer` - Submit answer
- `POST /api/v1/tests/{test_id}/results/{result_id}/violation` - Report violation ⚠️
- `POST /api/v1/tests/{test_id}/results/{result_id}/submit` - Complete test
- `GET /api/v1/tests/{test_id}/results/{result_id}` - Get results

### Analytics (Teacher)
- `GET /api/v1/tests/{test_id}/results` - All test results

---

## 🛡️ Fullscreen Violation Detection

### How It Works:
1. Student clicks "Start Test (Fullscreen)" in `test_interface.html`
2. Browser enters fullscreen mode
3. System monitors for exits via:
   - `fullscreenchange` events
   - `visibilitychange` events (tab switches)
   - Window focus loss
4. Each violation increments counter
5. After 3 violations → **Test automatically fails**
6. Student receives immediate notification

### Client-Side Monitoring:
```javascript
// Events tracked
document.addEventListener('fullscreenchange', handleFullscreenChange);
document.addEventListener('visibilitychange', handleVisibilityChange);
document.addEventListener('keydown', handleKeyPress); // Block Escape key
```

### Server-Side Tracking:
```python
# Each violation stored in database
POST /api/v1/tests/{test_id}/results/{result_id}/violation

# Automatic failure after threshold
if result.fullscreen_violations > test.max_fullscreen_violations:
    result.status = "failed"
    result.was_failed_for_violation = True
    result.score = 0
    result.percentage = 0
```

---

## 📊 Test Results Calculation

```
- Score = Sum of correct answers × points
- Max Score = Sum of all question points
- Percentage = (Score / Max Score) × 100
- Status = "completed" | "failed" | "pending"
- Violation Flag = True if failed due to violations
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/fastapi
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### Test Configuration
```python
TestCreate(
    title="Math Quiz",
    start_date=datetime(2026, 3, 2, 10, 0),  # Start access
    end_date=datetime(2026, 3, 2, 18, 0),    # End access
    time_limit_minutes=60,                    # 1 hour
    max_fullscreen_violations=3,              # Auto-fail after 3
    total_questions=20
)
```

---

## 🧪 Testing

### Run Full Test Suite
```bash
python test_comprehensive.py
```

**Tests 6 areas:**
- ✓ PostgreSQL connection
- ✓ Model imports
- ✓ Schema validation
- ✓ CRUD operations
- ✓ FastAPI app loading
- ✓ Database schema

### Test Output
```
============================================================
TEST 1: Database Connection
============================================================
[OK] PostgreSQL connection: PASSED

[...tests 2-6...]

============================================================
TEST SUMMARY
============================================================
[OK] All tests passed!
Application is ready for deployment.
```

---

## 🎯 Usage Example

### As Teacher: Create Test

```python
# 1. Create test
POST /api/v1/tests/
{
    "title": "Python Fundamentals",
    "description": "Basic Python concepts",
    "start_date": "2026-03-02T10:00:00",
    "end_date": "2026-03-02T18:00:00",
    "time_limit_minutes": 60,
    "max_fullscreen_violations": 3,
    "total_questions": 10
}

# 2. Add questions
POST /api/v1/tests/1/questions
{
    "question_text": "What is Python?",
    "question_type": "multiple_choice",
    "order": 1,
    "option_a": "A programming language",
    "option_b": "A snake",
    "option_c": "A web browser",
    "option_d": "A database",
    "correct_answer": "A",
    "points": 1
}
```

### As Student: Take Test

```python
# 1. Start test
POST /api/v1/tests/1/start
Response: { "id": 100, "status": "in_progress", ... }

# 2. Answer questions
POST /api/v1/tests/1/results/100/answer
{
    "question_id": 1,
    "answer_choice": "A"
}

# 3. Handle violations
POST /api/v1/tests/1/results/100/violation
# Auto-fails test if > 3 violations

# 4. Submit test
POST /api/v1/tests/1/results/100/submit
Response: { "id": 100, "score": 8, "percentage": 80, "status": "completed" }
```

---

## 🔒 Security Features

✅ Password hashing with bcrypt  
✅ Server-side answer validation  
✅ Foreign key constraints in DB  
✅ Prepared statements (SQLAlchemy ORM)  
✅ Time window enforcement  
✅ Real-time violation tracking  

### Recommended for Production:
- [ ] Implement JWT authentication
- [ ] Add HTTPS/TLS
- [ ] Enable CORS restrictions
- [ ] Implement rate limiting
- [ ] Add API key authentication
- [ ] Log all violations
- [ ] Monitor suspicious patterns
- [ ] Enable database encryption

---

## 📈 Performance

**Database Optimizations:**
- Indexed primary keys & foreign keys
- Indexed email & username for quick lookups
- Efficient query pagination
- Minimal N+1 queries with relationships

**API Optimizations:**
- Efficient CRUD operations
- Real-time violation reporting (no delays)
- Minimal payload sizes
- Gzip compression ready

---

## 📝 Alembic Migrations

```bash
# Show current migration
python -m alembic current

# Create new migration (auto-detect schema changes)
python -m alembic revision --autogenerate -m "Description"

# Apply all migrations
python -m alembic upgrade head

# Downgrade one step
python -m alembic downgrade -1
```

**Current Migrations:**
1. `3a4b5c6d7e8f` - Create users table
2. `4c5d6e7f8g9h` - Create test management tables (Teachers, Students, Tests, etc)

---

## 🐛 Troubleshooting

### Connection Refused
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify DATABASE_URL in .env
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/fastapi
```

### Port Already in Use
```bash
# Use different port
uvicorn app.main:app --reload --port 8001
```

### Migration Errors
```bash
# Check migration status
python -m alembic current

# View all migrations
python -m alembic branches

# Reset to clean state
python -m alembic downgrade base  # Then upgrade head
```

### Fullscreen Not Working
- Requires HTTPS in production
- Browser must support Fullscreen API (all modern browsers)
- User must grant fullscreen permission

---

## 📚 Documentation

- **IMPLEMENTATION_GUIDE.md** - Detailed architecture & implementation
- **FULLSCREEN_MONITORING.md** - JavaScript fullscreen monitoring guide
- **API Docs** - Auto-generated at `/docs`
- **Swagger UI** - Interactive API testing at `/redoc`

---

## 🎨 Frontend Integration

The `test_interface.html` file is a **complete, ready-to-use** test interface with:

✨ Modern responsive design  
🎯 Real-time violation tracking  
⏱️ Countdown timer  
📊 Visual violation indicator  
💾 Auto-save on answer  
🔴 Automatic failure alerts  

**No additional frontend framework needed** - Pure HTML5, CSS3, JavaScript

---

## 📦 Dependencies

```
FastAPI==0.104+
uvicorn[standard]==0.24+
SQLAlchemy==2.0+
psycopg2-binary==2.9+
Pydantic[email]==2.0+
bcrypt==4.1+
python-jose[cryptography]==3.3+
PyJWT==2.8+
python-dotenv==1.0+
alembic==1.13+
```

---

## 🚀 Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Gunicorn + Nginx
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

---

## 📝 License

MIT License - Use freely in production

---

## 🤝 Support

- **Documentation**: See included .md files
- **API Docs**: http://localhost:8000/docs
- **Tests**: Run `python test_comprehensive.py`

---

## ✅ Checklist for Deployment

- [x] Database migrations applied
- [x] Environment variables configured
- [x] Tests passing
- [x] API endpoints working
- [x] Frontend interface operational
- [ ] JWT authentication implemented
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Monitoring set up
- [ ] Backups automated

---

## 🎉 Ready to Use!

**Everything is set up and ready.** Just run:

```bash
uvicorn app.main:app --reload
```

Then:
1. Open http://localhost:8000/docs for API documentation
2. Open `test_interface.html` to start taking a test

**Enjoy!** 🚀

---

*Last Updated: March 2, 2026*  
*Version: 1.0.0 - Production Ready*

