# Quick Start Guide - Student Performance Checker

## 🚀 5-Minute Setup

### Step 1: Verify Setup
```bash
cd C:\python\task\fastapi-learning
python test_comprehensive.py
# Should output: [OK] All tests passed!
```

### Step 2: Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 3: Access API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Step 4: Test Interface
1. Open `test_interface.html` in modern browser (Chrome, Firefox, Edge)
2. Click "Start Test (Fullscreen)"
3. Answer questions
4. Submit test
5. View results

---

## 📝 Quick API Examples

### Using Curl or Postman

**Create Test:**
```bash
curl -X POST "http://localhost:8000/api/v1/tests/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Math Quiz",
    "description": "Basic math",
    "start_date": "2026-03-02T10:00:00",
    "end_date": "2026-03-02T18:00:00",
    "time_limit_minutes": 60,
    "max_fullscreen_violations": 3,
    "total_questions": 10
  }'
```

**Add Question:**
```bash
curl -X POST "http://localhost:8000/api/v1/tests/1/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is 2+2?",
    "question_type": "multiple_choice",
    "order": 1,
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6",
    "correct_answer": "B",
    "points": 1
  }'
```

**Start Test (as Student):**
```bash
curl -X POST "http://localhost:8000/api/v1/tests/1/start" \
  -H "Content-Type: application/json"
# Returns: { "id": 100, "status": "in_progress", ... }
```

**Submit Answer:**
```bash
curl -X POST "http://localhost:8000/api/v1/tests/1/results/100/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "answer_choice": "B"
  }'
```

**Report Violation:**
```bash
curl -X POST "http://localhost:8000/api/v1/tests/1/results/100/violation"
```

**Submit Test:**
```bash
curl -X POST "http://localhost:8000/api/v1/tests/1/results/100/submit"
# Returns: { "id": 100, "score": 8, "percentage": 80, "status": "completed" }
```

---

## 🎯 Typical Workflow

### As Teacher:
```
1. Create Test
   POST /api/v1/tests/
   
2. Add Questions
   POST /api/v1/tests/1/questions (repeat for each Q)
   
3. Share with students
   Send: test_interface.html + Test ID
   
4. View Results
   GET /api/v1/tests/1/results
```

### As Student:
```
1. Open test_interface.html
2. Enter Test ID
3. Click "Start Test (Fullscreen)"
4. Answer all questions
5. Click "Submit Test"
6. View your score immediately
```

---

## 🔒 Important Notes

### Fullscreen Mode
- **Required**: Modern browser (Chrome, Firefox, Edge)
- **Not allowed**: Safari iOS, older browsers
- **Block**: Alt+Tab, Escape key blocked

### Violations
- Max 3 fullscreen exits allowed (configurable)
- Each exit = 1 violation
- After 3 violations → Test fails automatically

### Time Windows
- Tests only accessible during defined period
- Cannot access before start_date
- Cannot access after end_date
- Server-side validation (can't bypass)

---

## 📊 Database

### Tables Overview
```
users          → Student/Teacher login
teachers       → Teacher profiles
tests          → Test definitions
questions      → Test questions
test_results   → Student attempts
student_answers → Question responses
fullscreen_violations → Violation tracking
students       → Student enrollment
```

### Check Data
```python
from app.database import SessionLocal
from app.models.test import Test

db = SessionLocal()
tests = db.query(Test).all()
for test in tests:
    print(f"{test.title} - {len(test.questions)} questions")
```

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
uvicorn app.main:app --reload --port 8001
```

### Database Connection Error
```bash
# Check PostgreSQL running
psql -U postgres -c "SELECT 1"

# Verify .env file
cat .env  # Should show DATABASE_URL

# Run migrations
python -m alembic upgrade head
```

### Fullscreen Not Working
- Try a different browser
- Ensure HTTP (localhost OK, HTTPS required in production)
- Check browser console for errors

### Test Not Showing Questions
- Check test time window: `curl http://localhost:8000/api/v1/tests/1`
- If outside window, will return 403 Forbidden

---

## 📚 File Guide

| File | Purpose |
|------|---------|
| `test_interface.html` | Student test UI |
| `app/models/test.py` | Database models |
| `app/schemas/test.py` | Validation schemas |
| `app/crud/test.py` | CRUD operations |
| `app/routers/tests.py` | API endpoints |
| `test_comprehensive.py` | Full test suite |
| `README_COMPLETE.md` | Full documentation |
| `IMPLEMENTATION_GUIDE.md` | Architecture guide |

---

## ✅ Validation Checklist

- [ ] `python test_comprehensive.py` passes
- [ ] `uvicorn app.main:app --reload` starts
- [ ] http://localhost:8000/docs loads
- [ ] `test_interface.html` opens
- [ ] Can create test via Swagger UI
- [ ] Can add questions
- [ ] Can start test in fullscreen
- [ ] Results calculate correctly

---

## 🎉 You're Ready!

Everything is set up. Just run:

```bash
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs

Enjoy! 🚀

