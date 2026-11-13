import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students.db"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024  # 3 MB

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Demo records only. Confirm current eligibility and deadlines on the official portal.
SCHOLARSHIPS = [
    {
        "name": "National Scholarship Portal schemes",
        "audience": "School and college students",
        "description": "Browse central and state scholarship schemes. Eligibility, benefits and dates vary by scheme.",
        "url": "https://scholarships.gov.in/",
        "type": "General"
    },
    {
        "name": "Tamil Nadu State Scholarship information",
        "audience": "Eligible Tamil Nadu students",
        "description": "Check current state scholarship announcements and application guidance through official government sources.",
        "url": "https://www.tn.gov.in/",
        "type": "State"
    },
    {
        "name": "AICTE Scholarship information",
        "audience": "Eligible technical education students",
        "description": "Review current AICTE scholarship notices and scheme conditions on the official website.",
        "url": "https://www.aicte-india.org/",
        "type": "Technical"
    }
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                mobile TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                photo TEXT DEFAULT '',
                student_type TEXT DEFAULT '',
                course TEXT DEFAULT '',
                marks REAL,
                district TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def current_student():
    student_id = session.get("student_id")
    if not student_id:
        return None
    with get_db() as conn:
        return conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("student_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    query = request.args.get("q", "").strip().lower()
    scholarships = SCHOLARSHIPS
    if query:
        scholarships = [
            item for item in SCHOLARSHIPS
            if query in (item["name"] + " " + item["audience"] + " " + item["description"] + " " + item["type"]).lower()
        ]
    return render_template("index.html", scholarships=scholarships, query=query, student=current_student())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([name, email, mobile, password, confirm]):
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")
        if not email or "@" not in email:
            flash("Enter a valid email address.", "error")
            return render_template("register.html")
        if not mobile.isdigit() or len(mobile) != 10:
            flash("Enter a valid 10-digit mobile number.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        photo_name = ""
        photo = request.files.get("photo")
        if photo and photo.filename:
            if not allowed_file(photo.filename):
                flash("Photo must be PNG, JPG, JPEG or WEBP.", "error")
                return render_template("register.html")
            safe_name = secure_filename(photo.filename)
            photo_name = f"{os.urandom(8).hex()}_{safe_name}"
            photo.save(UPLOAD_FOLDER / photo_name)

        try:
            with get_db() as conn:
                cur = conn.execute(
                    """INSERT INTO students (name, email, mobile, password_hash, photo)
                       VALUES (?, ?, ?, ?, ?)""",
                    (name, email, mobile, generate_password_hash(password), photo_name)
                )
                student_id = cur.lastrowid
            session["student_id"] = student_id
            flash("Account created. Please complete your student profile.", "success")
            return redirect(url_for("profile"))
        except sqlite3.IntegrityError:
            flash("This email is already registered. Please sign in.", "error")
            return render_template("register.html")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as conn:
            student = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
        if student and check_password_hash(student["password_hash"], password):
            session.clear()
            session["student_id"] = student["id"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    student = current_student()
    if request.method == "POST":
        student_type = request.form.get("student_type", "").strip()
        course = request.form.get("course", "").strip()
        district = request.form.get("district", "").strip()
        marks_text = request.form.get("marks", "").strip()

        if student_type not in ("school", "college"):
            flash("Choose School Student or College Student.", "error")
            return render_template("profile.html", student=student)
        if not course:
            flash("Enter your class or course.", "error")
            return render_template("profile.html", student=student)
        marks = None
        if marks_text:
            try:
                marks = float(marks_text)
                if not 0 <= marks <= 100:
                    raise ValueError
            except ValueError:
                flash("Marks must be between 0 and 100.", "error")
                return render_template("profile.html", student=student)

        with get_db() as conn:
            conn.execute(
                "UPDATE students SET student_type=?, course=?, district=?, marks=? WHERE id=?",
                (student_type, course, district, marks, student["id"])
            )
        flash("Profile saved successfully.", "success")
        return redirect(url_for("dashboard"))
    return render_template("profile.html", student=student)

@app.route("/dashboard")
@login_required
def dashboard():
    student = current_student()
    if not student["student_type"] or not student["course"]:
        flash("Complete your student profile to see scholarship suggestions.", "warning")
        return redirect(url_for("profile"))

    matches = []
    for item in SCHOLARSHIPS:
        audience = item["audience"].lower()
        if student["student_type"] == "school" and ("school" in audience or "both" in audience):
            matches.append(item)
        elif student["student_type"] == "college" and ("college" in audience or "both" in audience or "technical" in audience):
            matches.append(item)

    return render_template("dashboard.html", student=student, scholarships=matches)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("home"))

@app.errorhandler(413)
def too_large(_error):
    flash("Photo is too large. Maximum size is 3 MB.", "error")
    return redirect(url_for("register"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
