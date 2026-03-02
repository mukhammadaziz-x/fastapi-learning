"""Quick test: start server in a thread, then test the API."""
import threading
import time
import json
import urllib.request
import uvicorn

def run_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=3001, log_level="error")

# Start server in background thread
t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

# Test 1: Health
try:
    resp = urllib.request.urlopen("http://127.0.0.1:3001/health")
    print("HEALTH:", resp.read().decode())
except Exception as e:
    print("HEALTH ERROR:", e)

# Test 2: Create test
data = {
    "title": "Math Test",
    "description": "Test description",
    "start_date": "2026-03-02T10:00:00",
    "end_date": "2026-03-03T10:00:00",
    "time_limit_minutes": 60,
    "max_fullscreen_violations": 3,
    "total_questions": 10
}
req = urllib.request.Request(
    "http://127.0.0.1:3001/api/v1/tests?teacher_id=2",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    resp = urllib.request.urlopen(req)
    print("CREATE TEST:", resp.status, resp.read().decode())
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"CREATE TEST ERROR {e.code}: {body}")
except Exception as e:
    print("CREATE TEST CONN ERROR:", e)
