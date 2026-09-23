STUDENT MANAGEMENT SYSTEM - FLASK FRONTEND

1. Install Python 3.10+.
2. Extract this folder.
3. Open a terminal inside the project folder.
4. Create and activate a virtual environment (recommended):
   Windows:
     py -m venv venv
     venv\Scripts\activate
   macOS/Linux:
     python3 -m venv venv
     source venv/bin/activate
5. Install dependencies:
     pip install -r requirements.txt
6. Set admin credentials (recommended):
   PowerShell:
     $env:ADMIN_USERNAME="your-admin"
     $env:ADMIN_PASSWORD="your-strong-password"
     $env:FLASK_SECRET_KEY="a-long-random-secret"
   These environment variables are optional for local testing; defaults are admin / change-me.
7. Run:
     python app.py
8. Open http://127.0.0.1:5000

SQLite database is created automatically as student_management.db.
If you already have a student_management.db, place it in this project folder to use its records.
This is a local learning project. Before public deployment, add CSRF protection, secure secret management,
rate limiting, and production server configuration. Do not expose Flask debug mode publicly.
