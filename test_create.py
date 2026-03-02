import urllib.request
import json

url = "http://127.0.0.1:3000/api/v1/tests?teacher_id=2"
data = {
    "title": "Math Test",
    "description": "Test description",
    "start_date": "2026-03-02T10:00:00.000Z",
    "end_date": "2026-03-03T10:00:00.000Z",
    "time_limit_minutes": 60,
    "max_fullscreen_violations": 3,
    "total_questions": 10
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    resp = urllib.request.urlopen(req)
    print("SUCCESS:", resp.status, resp.read().decode())
except urllib.error.HTTPError as e:
    print("ERROR:", e.code, e.read().decode())
except Exception as e:
    print("CONN ERROR:", e)
