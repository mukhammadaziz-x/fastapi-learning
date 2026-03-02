"""To'liq API test — barcha endpointlarni tekshiradi."""
import requests
import json
import sys

BASE = "http://localhost:9000"
errors = []
passed = []


def test(name, method, url, json_data=None, headers=None, expect_status=None):
    try:
        r = getattr(requests, method)(BASE + url, json=json_data, headers=headers, timeout=10)
        if expect_status and r.status_code != expect_status:
            errors.append(f"FAIL {name}: expected {expect_status}, got {r.status_code} — {r.text[:300]}")
        else:
            passed.append(f"OK   {name}: {r.status_code}")
        return r
    except Exception as e:
        errors.append(f"FAIL {name}: {e}")
        return None


print("=" * 55)
print("  EduPlatform — Full API Test")
print("=" * 55)

# 1. Health
test("Health", "get", "/health", expect_status=200)

# 2. Admin Login
r = test("Admin Login", "post", "/api/v1/auth/login",
         {"username": "admin", "password": "admin123"}, expect_status=200)

if not r or r.status_code != 200:
    print("\n  ADMIN LOGIN FAILED — test to'xtadi.")
    sys.exit(1)

data = r.json()
TOKEN = data["access_token"]
AUTH = {"Authorization": f"Bearer {TOKEN}"}

# 3. Auth me
test("Auth Me", "get", "/api/v1/auth/me", headers=AUTH, expect_status=200)

# 4. Register teacher
r2 = test("Register Teacher", "post", "/api/v1/auth/register",
          {"email": "t_teacher@test.com", "username": "t_teacher", "password": "test123",
           "full_name": "Test Teacher", "role": "teacher"})

# 5. Register student
r3 = test("Register Student", "post", "/api/v1/auth/register",
          {"email": "t_student@test.com", "username": "t_student", "password": "test123",
           "full_name": "Test Student", "role": "student"})

# 6. List users
test("List Users", "get", "/api/v1/users/", headers=AUTH, expect_status=200)

# 7. Search users
test("Search Users", "get", "/api/v1/users/search?q=test", headers=AUTH, expect_status=200)

# Find IDs
student_id = teacher_id = None
ur = requests.get(BASE + "/api/v1/users/", headers=AUTH)
if ur.status_code == 200:
    for u in ur.json():
        if u["role"] == "student" and not student_id:
            student_id = u["id"]
        if u["role"] == "teacher" and not teacher_id:
            teacher_id = u["id"]

# 8. Create subject
r4 = test("Create Subject", "post", "/api/v1/subjects/",
          {"name": "Matematika", "code": "MATH_T1", "description": "Test fan",
           "default_exam_type": "multiple_choice", "semester": 1, "credit_hours": 4},
          headers=AUTH)
subject_id = r4.json().get("id") if r4 and r4.status_code == 201 else None

# 9. List subjects
test("List Subjects", "get", "/api/v1/subjects/", headers=AUTH, expect_status=200)

# 10. Get subject detail
if subject_id:
    test("Get Subject", "get", f"/api/v1/subjects/{subject_id}", headers=AUTH, expect_status=200)

# 11. Create group
r5 = test("Create Group", "post", "/api/v1/groups/",
          {"name": "Test Guruh", "description": "Test guruh"}, headers=AUTH)
group_id = r5.json().get("id") if r5 and r5.status_code == 201 else None

# 12. List groups
test("List Groups", "get", "/api/v1/groups/", headers=AUTH, expect_status=200)

# 13. Add member to group
if group_id and student_id:
    test("Add Group Member", "post", f"/api/v1/groups/{group_id}/members",
         {"user_ids": [student_id]}, headers=AUTH)

# 14. Enroll student
if student_id and subject_id:
    test("Enroll Student", "post", "/api/v1/enrollments/",
         {"student_id": student_id, "subject_id": subject_id}, headers=AUTH)

# 15. List enrollments
if subject_id:
    test("Subject Enrollments", "get", f"/api/v1/enrollments/subject/{subject_id}",
         headers=AUTH, expect_status=200)

# 16. Create assignment
assignment_id = None
if subject_id:
    r6 = test("Create Assignment", "post", "/api/v1/assignments/", {
        "title": "Test Imtihon", "description": "Birinchi test", "subject_id": subject_id,
        "assignment_type": "quiz", "exam_type": "multiple_choice",
        "start_date": "2026-01-01T00:00:00", "end_date": "2026-12-31T23:59:59",
        "time_limit_minutes": 30, "max_attempts": 3, "is_published": True
    }, headers=AUTH)
    assignment_id = r6.json().get("id") if r6 and r6.status_code == 201 else None

# 17. Add question
question_id = None
if assignment_id:
    r7 = test("Add Question", "post", f"/api/v1/assignments/{assignment_id}/questions", {
        "question_text": "2+2 nechiga teng?", "question_type": "multiple_choice",
        "options": ["3", "4", "5", "6"], "correct_answer": "4", "points": 10, "order_number": 1
    }, headers=AUTH)
    question_id = r7.json().get("id") if r7 and r7.status_code == 201 else None

# 18. List assignments
test("List Assignments", "get", "/api/v1/assignments/", headers=AUTH, expect_status=200)

# 19. Get assignment detail
if assignment_id:
    test("Get Assignment", "get", f"/api/v1/assignments/{assignment_id}", headers=AUTH, expect_status=200)

# --- STUDENT FLOW ---
rs = requests.post(BASE + "/api/v1/auth/login",
                   json={"username": "t_student", "password": "test123"})
if rs.status_code == 200:
    SAUTH = {"Authorization": "Bearer " + rs.json()["access_token"]}

    # 20. Student sees assignments
    test("Student List Assignments", "get", "/api/v1/assignments/", headers=SAUTH, expect_status=200)

    # 21. Start submission
    submission_id = None
    if assignment_id:
        r8 = test("Start Submission", "post", "/api/v1/submissions/start",
                   {"assignment_id": assignment_id}, headers=SAUTH)
        submission_id = r8.json().get("id") if r8 and r8.status_code == 201 else None

    # 22. Submission status
    if submission_id:
        test("Submission Status", "get", f"/api/v1/submissions/{submission_id}/status",
             headers=SAUTH, expect_status=200)

    # 23. Submit answer
    if submission_id and question_id:
        test("Submit Answer", "post", f"/api/v1/submissions/{submission_id}/answer",
             {"question_id": question_id, "answer_choice": "4", "answer_time_seconds": 5},
             headers=SAUTH, expect_status=200)

    # 24. Report violation
    if submission_id:
        test("Report Violation", "post", f"/api/v1/submissions/{submission_id}/violation",
             {"violation_type": "tab_switch", "details": "Test violation"},
             headers=SAUTH)

    # 25. Finalize submission
    if submission_id:
        test("Finalize Submission", "post", f"/api/v1/submissions/{submission_id}/submit",
             headers=SAUTH)

    # 26. My submissions
    test("My Submissions", "get", "/api/v1/submissions/my", headers=SAUTH, expect_status=200)

    # 27. Submission detail
    if submission_id:
        test("Submission Detail", "get", f"/api/v1/submissions/{submission_id}",
             headers=SAUTH, expect_status=200)

    # 28. Leaderboard
    test("Leaderboard", "get", "/api/v1/leaderboard", headers=SAUTH, expect_status=200)

    # 29. My rank
    test("My Rank", "get", "/api/v1/leaderboard/my-rank", headers=SAUTH, expect_status=200)

    # 30. My analytics
    test("My Analytics", "get", "/api/v1/analytics/my", headers=SAUTH, expect_status=200)
else:
    errors.append("FAIL Student Login: could not login")

# --- TEACHER FLOW ---
rt = requests.post(BASE + "/api/v1/auth/login",
                   json={"username": "t_teacher", "password": "test123"})
if rt.status_code == 200:
    TAUTH = {"Authorization": "Bearer " + rt.json()["access_token"]}
    test("Teacher Dashboard", "get", "/api/v1/dashboard/teacher", headers=TAUTH, expect_status=200)
else:
    errors.append("FAIL Teacher Login: could not login")

# --- ADMIN DASHBOARD ---
test("Admin Dashboard", "get", "/api/v1/dashboard/admin", headers=AUTH, expect_status=200)

# --- PAGES ---
test("Home Page", "get", "/", expect_status=200)
test("Admin HTML", "get", "/dashboard/admin", expect_status=200)
test("Teacher HTML", "get", "/dashboard/teacher", expect_status=200)
test("Student HTML", "get", "/dashboard/student", expect_status=200)
test("Swagger Docs", "get", "/docs", expect_status=200)

# --- CLEANUP: delete test data ---
# (optional — not critical)

# --- RESULTS ---
print()
print("=" * 55)
print(f"  ✅ PASSED: {len(passed)}")
print(f"  ❌ FAILED: {len(errors)}")
print("=" * 55)

for p in passed:
    print(f"  {p}")

if errors:
    print()
    print("  ──── XATOLIKLAR ────")
    for e in errors:
        print(f"  {e}")

print()
