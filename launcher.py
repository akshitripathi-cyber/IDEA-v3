import threading
import time

from backend.app import app as flask_app
from frontend.main import Application

def run_backend():
    print("🚀 Starting backend...")
    flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def run_frontend():
    print("🎨 Starting frontend...")
    app = Application()
    app.run()

if __name__ == "__main__":
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    time.sleep(2)
    run_frontend()