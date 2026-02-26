"""Quick test: import the app and print its routes."""
import sys
try:
    from app.main import app
    print("SUCCESS: App loaded —", app.title)
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods and path:
            print(f"  {methods}  {path}")
except Exception as e:
    print(f"FAIL: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

