import threading
import webbrowser
from waitress import serve
from app import app
from database import init_db

if __name__ == '__main__':
    init_db()
    print("==================================================")
    print("  AttendEasy Production Server (Waitress WSGI)")
    print("  Local Access: http://127.0.0.1:5000")
    print("  LAN / Wi-Fi Access: Available on your machine's IP")
    print("  Press Ctrl+C to stop.")
    print("==================================================")
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    serve(app, host="0.0.0.0", port=5000, threads=6)
