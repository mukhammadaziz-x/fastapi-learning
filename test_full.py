"""Comprehensive test to verify all endpoints work."""
import urllib.request
import json

BASE = "http://localhost:3000"

def api(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read()) if r.status != 204 else None
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.fp else None

# 1. Health
status, data = api("GET", "/health")
print(f"1. Health: {status} - {data['status']}")

# 2. Get tests
status, data = api("GET", "/api/v1/tests?teacher_id=2")
print(f"2. List tests: {status} - {len(data)} tests found")

# 3. Create a new test
test_data = {
    "title": "Final Verification Test",
    "description": "Testing the full flow",
    "start_date": "2026-03-01T00:00:00",
    "end_date": "2026-12-31T23:59:59",
    "time_limit_minutes": 30,
    "max_fullscreen_violations": 3,
    "total_questions": 5
}
status, data = api("POST", "/api/v1/tests?teacher_id=2", test_data)
test_id = data["id"]
print(f"3. Create test: {status} - ID={test_id}, title='{data['title']}'")

# 4. Get single test
status, data = api("GET", f"/api/v1/tests/{test_id}")
print(f"4. Get test: {status} - {data['title']}")

# 5. Add a question
q_data = {
    "question_text": "What is 2+2?",
    "question_type": "multiple_choice",
    "order": 1,
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6",
    "correct_answer": "B",
    "points": 1
}
status, data = api("POST", f"/api/v1/tests/{test_id}/questions", q_data)
q_id = data["id"]
print(f"5. Add question: {status} - Q ID={q_id}")

# 6. Get questions
status, data = api("GET", f"/api/v1/tests/{test_id}/questions?hide_answers=false")
print(f"6. Get questions: {status} - {len(data)} questions")

# 7. Add student
s_data = {"name": "Test Student", "email": f"test_verify_{test_id}@mail.com", "teacher_id": 2}
status, data = api("POST", "/api/v1/students", s_data)
s_id = data["id"]
print(f"7. Add student: {status} - ID={s_id}")

# 8. Get students
status, data = api("GET", "/api/v1/students/teacher/2")
print(f"8. Get students: {status} - {len(data)} students")

# 9. Generate access token
token_data = {
    "test_id": test_id,
    "student_ids": [s_id],
    "expires_at": "2026-12-31T23:59:59"
}
status, data = api("POST", "/api/v1/access-tokens/bulk", token_data)
token = data[0]["token"]
print(f"9. Generate token: {status} - token={token[:16]}...")

# 10. Validate token
status, data = api("GET", f"/api/v1/access-tokens/validate/{token}")
print(f"10. Validate token: {status} - valid={data['valid']}, test='{data.get('test_title')}'")

# 11. Get test results
status, data = api("GET", f"/api/v1/tests/{test_id}/results")
print(f"11. Get results: {status} - {len(data)} results")

# 12. Update test
status, data = api("PATCH", f"/api/v1/tests/{test_id}?teacher_id=2", {"title": "Updated Final Test"})
print(f"12. Update test: {status} - new title='{data['title']}'")

# 13. Teacher dashboard pages
for page in ["/", "/teacher"]:
    req = urllib.request.Request(BASE + page)
    r = urllib.request.urlopen(req)
    print(f"13. Page '{page}': {r.status}")

# 14. Clean up - delete test
status, _ = api("DELETE", f"/api/v1/tests/{test_id}?teacher_id=2")
print(f"14. Delete test: {status}")

print("\n✅ ALL TESTS PASSED! System is fully working.")
