# Student Performance Checker - Complete Guide

## Overview
A comprehensive FastAPI-based testing platform with:
- ✅ Fullscreen violation detection & enforcement
- ✅ Real-time test monitoring
- ✅ Student performance tracking
- ✅ Teacher dashboard
- ✅ Time-limited access links
- ✅ PostgreSQL database with Alembic migrations

---

## Architecture

### Database Models
```
Teachers (Учителя)
├── Tests (Тесты)
│   ├── Questions (Вопросы)
│   └── TestResults (Результаты)
│       ├── StudentAnswers (Ответы студентов)
│       └── FullscreenViolations (Нарушения)
└── Students (Студенты)
    └── TestResults
```

### API Endpoints

#### Test Management (Teacher)
- `POST /api/v1/tests/` - Create test
- `GET /api/v1/tests/{test_id}` - Get test details
- `GET /api/v1/tests/` - List teacher's tests
- `PATCH /api/v1/tests/{test_id}` - Update test
- `DELETE /api/v1/tests/{test_id}` - Delete test

#### Questions
- `POST /api/v1/tests/{test_id}/questions` - Add question
- `GET /api/v1/tests/{test_id}/questions` - Get questions
- `DELETE /api/v1/tests/{test_id}/questions/{question_id}` - Delete question

#### Test Taking (Student)
- `POST /api/v1/tests/{test_id}/start` - Start test
- `POST /api/v1/tests/{test_id}/results/{result_id}/answer` - Submit answer
- `POST /api/v1/tests/{test_id}/results/{result_id}/violation` - Report fullscreen violation
- `POST /api/v1/tests/{test_id}/results/{result_id}/submit` - Submit test
- `GET /api/v1/tests/{test_id}/results/{result_id}` - Get result

#### Analytics (Teacher)
- `GET /api/v1/tests/{test_id}/results` - Get all results for test

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python -m alembic upgrade head
```

### 3. Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Access Test Interface
Open `test_interface.html` in a modern browser

---

## Key Features

### 1. Fullscreen Monitoring
- Detects when student exits fullscreen mode
- Tracks violations in real-time
- Automatic test failure after 3 violations
- Visual warnings to student

### 2. Time-Limited Tests
- Tests have `start_date` and `end_date`
- Students can only access tests during this window
- Teacher can modify time windows

### 3. Test Security
- Multiple choice questions with hidden correct answers
- Server-side answer validation
- Real-time violation recording
- Session-based test locking (student can't retake)

### 4. Performance Metrics
- Score calculation per question
- Percentage calculation
- Violation tracking
- Time-to-completion tracking

---

## Example Usage

### Create a Test (as Teacher)
```python
# Start with ID 1 as current teacher
POST /api/v1/tests/
{
    "title": "Math Quiz",
    "description": "Basic arithmetic",
    "start_date": "2026-03-02T10:00:00",
    "end_date": "2026-03-02T11:00:00",
    "total_questions": 10,
    "time_limit_minutes": 60,
    "max_fullscreen_violations": 3
}
```

### Add Questions
```python
POST /api/v1/tests/1/questions
{
    "question_text": "What is 2 + 2?",
    "question_type": "multiple_choice",
    "order": 1,
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6",
    "correct_answer": "B",
    "points": 1
}
```

### Student Takes Test
1. Open `test_interface.html`
2. Enter Test ID and Student ID
3. Click "Start Test (Fullscreen)"
4. Answer questions
5. Click "Submit Test"
6. View instant results

---

## Database Schema

### Test Status Values
- `pending` - Not started
- `in_progress` - Currently taking test
- `completed` - Successfully submitted
- `failed` - Failed due to violations

### Question Types
- `multiple_choice` - A, B, C, D options
- `short_answer` - Text response
- `essay` - Long text response

### Violation Types
- `left_fullscreen` - Exited fullscreen mode
- `tab_switch` - Switched browser tabs
- `window_focus_lost` - Lost window focus

---

## Fullscreen Monitoring Details

### How It Works
1. **Entry**: Student clicks "Start Test (Fullscreen)"
2. **Monitoring**: JavaScript detects:
   - `fullscreenchange` events
   - `visibilitychange` events (tab switch)
   - Window focus loss
3. **Violation**: Each incident increments counter
4. **Threshold**: 3+ violations → automatic failure
5. **Reporting**: Each violation sent to server immediately

### Client-Side Events
```javascript
// Fullscreen exit
document.addEventListener('fullscreenchange', handleFullscreenChange);

// Tab switch
document.addEventListener('visibilitychange', handleVisibilityChange);

// Block Escape key
document.addEventListener('keydown', handleKeyPress);
```

---

## Security Considerations

⚠️ **Important**: This is a demonstration. For production:
1. Implement JWT authentication
2. Validate all requests on server
3. Use HTTPS only
4. Implement rate limiting
5. Add CORS restrictions
6. Log all violations
7. Implement IP monitoring
8. Add proctoring features (optional)

---

## Testing

### Test CRUD Operations
```bash
python test_crud.py
```

### Test PostgreSQL Connection
```python
from app.database import SessionLocal
from app.models.test import Test

db = SessionLocal()
tests = db.query(Test).all()
print(f"Total tests: {len(tests)}")
```

---

## Project Structure
```
fastapi-learning/
├── app/
│   ├── models/
│   │   ├── user.py      # User model
│   │   └── test.py      # Test-related models
│   ├── schemas/
│   │   ├── user.py      # User schemas
│   │   └── test.py      # Test schemas
│   ├── crud/
│   │   ├── user.py      # User CRUD
│   │   └── test.py      # Test CRUD
│   ├── routers/
│   │   ├── users.py     # User endpoints
│   │   └── tests.py     # Test endpoints
│   ├── database.py      # DB configuration
│   └── main.py          # FastAPI app
├── alembic/
│   ├── versions/
│   │   ├── 3a4b5c6d7e8f_create_users_table.py
│   │   └── 4c5d6e7f8g9h_create_test_tables.py
│   └── env.py
├── test_interface.html  # Student test UI
├── requirements.txt
├── .env
└── README.md
```

---

## Performance Notes

- Database queries optimized with indexes
- Eager loading for relationships
- Pagination support (default limit: 100)
- Real-time violation tracking
- Minimal network overhead

---

## Troubleshooting

### Fullscreen not working
- Browser must support Fullscreen API
- HTTPS required in production
- User must allow fullscreen permission

### Migrations failing
```bash
# Check migration status
python -m alembic current

# Downgrade to previous
python -m alembic downgrade -1

# Create new migration
python -m alembic revision --autogenerate -m "Description"
```

### Port already in use
```bash
# Use different port
uvicorn app.main:app --reload --port 8001
```

---

## Future Enhancements

- [ ] Real-time analytics dashboard
- [ ] Student progress tracking
- [ ] Adaptive difficulty questions
- [ ] AI-powered proctoring
- [ ] Mobile app support
- [ ] Question banking system
- [ ] Advanced reporting
- [ ] Multi-language support
- [ ] Video proctoring integration
- [ ] API rate limiting

---

## Support & Documentation

- API Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`
- Fullscreen Guide: See `FULLSCREEN_MONITORING.md`

---

## License
MIT - Feel free to use and modify

---

**Last Updated**: March 2, 2026

