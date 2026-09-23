import os, re, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")
DB_PATH = os.path.join(os.path.dirname(__file__), "student_management.db")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

COURSES = ["Python", "Java", "AI&ML", "Data Science", "Full Stack"]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS students(
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE,
            email TEXT UNIQUE,
            course TEXT NOT NULL,
            attendance INTEGER DEFAULT 0
        )
    """)
    db.commit()
    db.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def validate(name, mobile, email, course, student_id=None):
    if not name.strip() or len(name.strip()) < 3 or not name.strip().replace(" ", "").isalpha():
        return "Name must be at least 3 characters and contain only letters and spaces."
    if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in "6789":
        return "Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return "Enter a valid email address."
    if course not in COURSES:
        return "Select a valid course."
    db = get_db()
    sql = "SELECT student_id FROM students WHERE (mobile=? OR email=?)"
    params = [mobile, email]
    if student_id is not None:
        sql += " AND student_id != ?"
        params.append(student_id)
    if db.execute(sql, params).fetchone():
        return "That mobile number or email is already registered."
    return None

@app.route("/")
def home():
    return redirect(url_for("dashboard") if session.get("logged_in") else url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            flash("Welcome back, admin.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    present = db.execute("SELECT COUNT(*) FROM students WHERE attendance=1").fetchone()[0]
    absent = total - present
    pct = round(present / total * 100, 1) if total else 0
    recent = db.execute("SELECT * FROM students ORDER BY student_id DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", total=total, present=present, absent=absent, pct=pct, recent=recent)

@app.route("/students")
@login_required
def students():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        rows = db.execute("""SELECT * FROM students
            WHERE CAST(student_id AS TEXT)=? OR name LIKE ? OR mobile LIKE ? OR email LIKE ? OR course LIKE ?
            ORDER BY student_id DESC""", (q, f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM students ORDER BY student_id DESC").fetchall()
    return render_template("students.html", students=rows, q=q)

@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name=request.form.get("name","").strip()
        mobile=request.form.get("mobile","").strip()
        email=request.form.get("email","").strip()
        course=request.form.get("course","").strip()
        error=validate(name,mobile,email,course)
        if error:
            flash(error,"error")
        else:
            db=get_db()
            db.execute("INSERT INTO students(name,mobile,email,course) VALUES(?,?,?,?)",(name,mobile,email,course))
            db.commit()
            flash("Student registered successfully.","success")
            return redirect(url_for("students"))
    return render_template("student_form.html", student=None, courses=COURSES, page_title="Register Student")

@app.route("/students/<int:sid>/edit", methods=["GET","POST"])
@login_required
def edit_student(sid):
    db=get_db()
    student=db.execute("SELECT * FROM students WHERE student_id=?",(sid,)).fetchone()
    if not student:
        flash("Student not found.","error")
        return redirect(url_for("students"))
    if request.method=="POST":
        name=request.form.get("name","").strip()
        mobile=request.form.get("mobile","").strip()
        email=request.form.get("email","").strip()
        course=request.form.get("course","").strip()
        error=validate(name,mobile,email,course,sid)
        if error:
            flash(error,"error")
        else:
            db.execute("UPDATE students SET name=?,mobile=?,email=?,course=? WHERE student_id=?",(name,mobile,email,course,sid))
            db.commit()
            flash("Student details updated.","success")
            return redirect(url_for("students"))
    return render_template("student_form.html", student=student, courses=COURSES, page_title="Update Student")

@app.route("/students/<int:sid>/delete", methods=["POST"])
@login_required
def delete_student(sid):
    db=get_db()
    db.execute("DELETE FROM students WHERE student_id=?",(sid,))
    db.commit()
    flash("Student deleted if the record existed.","success")
    return redirect(url_for("students"))

@app.route("/students/<int:sid>/attendance", methods=["POST"])
@login_required
def attendance(sid):
    value=request.form.get("attendance","")
    if value not in ("0","1"):
        flash("Choose Present or Absent.","error")
    else:
        db=get_db()
        db.execute("UPDATE students SET attendance=? WHERE student_id=?",(int(value),sid))
        db.commit()
        flash("Attendance updated.","success")
    return redirect(request.referrer or url_for("students"))

@app.route("/attendance")
@login_required
def attendance_report():
    rows=get_db().execute("SELECT student_id,name,course,attendance FROM students ORDER BY student_id DESC").fetchall()
    return render_template("attendance.html", students=rows)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
