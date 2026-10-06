from app import app
from database import init_db

# Initialize database schema on startup if not already initialized
init_db()

# Expose app for WSGI servers (Gunicorn / Waitress / uWSGI)
if __name__ == "__main__":
    app.run()
