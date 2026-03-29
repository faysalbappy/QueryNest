from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import re

app = Flask(__name__)
app.secret_key = 'querynest_secret_key_2026'

DB_PATH = 'querynest.db'

# ─── Database ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur  = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL CHECK(role IN ('student','admin'))
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            faq_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            question  TEXT NOT NULL,
            answer    TEXT NOT NULL,
            keywords  TEXT,
            category  TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            notice_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            description  TEXT NOT NULL,
            publish_date TEXT NOT NULL
        )
    ''')

    # ── Module 2: Academic Info Tables ────────────────────────────────────────
    cur.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT NOT NULL,
            title       TEXT NOT NULL,
            credits     REAL NOT NULL,
            semester    TEXT NOT NULL,
            type        TEXT NOT NULL CHECK(type IN ('Theory','Lab'))
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS exam_routine (
            exam_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            exam_date   TEXT NOT NULL,
            exam_time   TEXT NOT NULL,
            room        TEXT NOT NULL,
            exam_type   TEXT NOT NULL CHECK(exam_type IN ('Midterm','Final'))
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mark_distribution (
            mark_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            component   TEXT NOT NULL,
            marks       INTEGER NOT NULL,
            description TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS lab_schedule (
            lab_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            day         TEXT NOT NULL,
            time        TEXT NOT NULL,
            room        TEXT NOT NULL,
            instructor  TEXT NOT NULL
        )
    ''')

    # Seed admin
    cur.execute("SELECT * FROM users WHERE role='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (name, password, role) VALUES (?,?,?)",
            ('admin', generate_password_hash('admin123'), 'admin')
        )

    # Seed FAQs (expanded for better chatbot coverage)
    cur.execute("SELECT COUNT(*) FROM faqs")
    if cur.fetchone()[0] == 0:
        sample_faqs = [
            ('What is the credit hour for SWE courses?',
             'Most SWE theory courses carry 3 credit hours. Lab courses carry 1.5 credit hours.',
             'credit hour credits course', 'Academic'),
            ('How is the grading policy structured?',
             'DIU Grading Scale:\n- A+ = 90-100 (GPA 4.00)\n- A  = 85-89  (GPA 3.75)\n- A- = 80-84  (GPA 3.50)\n- B+ = 75-79  (GPA 3.25)\n- B  = 70-74  (GPA 3.00)\n- B- = 65-69  (GPA 2.75)\n- C+ = 60-64  (GPA 2.50)\n- C  = 55-59  (GPA 2.25)\n- D  = 50-54  (GPA 2.00)\n- F  = below 50 (Fail)',
             'grade grading marks result gpa cgpa', 'Academic'),
            ('When is the exam routine published?',
             'The exam routine is published 2 weeks before semester finals. Check the Academic Info page for the current schedule.',
             'exam routine schedule date published', 'Exam'),
            ('What is the passing mark?',
             'The minimum passing mark is 50 out of 100. Below 50 means F grade and you must retake the course.',
             'pass fail minimum mark score', 'Academic'),
            ('How many absences are allowed?',
             'Students must maintain at least 75% attendance to sit for final exams. More than 25% absences = dropped from course.',
             'absent attendance class allowed percentage', 'Academic'),
            ('What is the mark distribution for theory courses?',
             'Theory Course Marks:\n- Attendance: 10\n- Assignment/Quiz: 10\n- Midterm Exam: 30\n- Final Exam: 50\nTotal: 100 marks',
             'mark distribution theory assignment quiz midterm final', 'Exam'),
            ('What is the mark distribution for lab courses?',
             'Lab Course Marks:\n- Lab Performance: 30\n- Lab Report: 20\n- Lab Test/Viva: 50\nTotal: 100 marks',
             'mark distribution lab report viva performance', 'Exam'),
            ('What courses are available this semester?',
             'Current SWE courses: Data Structures, Algorithm Design, Database Management, Software Engineering, Computer Networks, and their labs. See the Academic Info page for details.',
             'course available semester swe subject syllabus', 'Academic'),
            ('What is the project guideline for SWE courses?',
             'SWE Project Rules:\n- Teams of 3-4 students\n- Topic approved by supervisor\n- Proposal: Week 4\n- Progress report: Week 8\n- Final presentation: Week 16\nSee the Lab & Projects page for full details.',
             'project guideline team supervisor proposal presentation', 'Lab'),
            ('How do I contact my teacher?',
             'Contact your course teacher through the department office or via the official DIU student email. Faculty details are on the DIU website.',
             'teacher contact faculty instructor professor', 'Academic'),
        ]
        cur.executemany(
            "INSERT INTO faqs (question, answer, keywords, category) VALUES (?,?,?,?)",
            sample_faqs
        )

    # Seed notices
    cur.execute("SELECT COUNT(*) FROM notices")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO notices (title, description, publish_date) VALUES (?,?,?)",
            [
                ('Mid-term Exam Schedule Released',
                 'Mid-term exams will begin from March 15, 2026. Check the department notice board for room assignments.',
                 '2026-03-08'),
                ('Lab Report Submission Deadline',
                 'All pending lab reports must be submitted by March 12, 2026. Late submissions will not be accepted.',
                 '2026-03-07'),
                ('Scholarship Application Open',
                 'Applications for the merit-based scholarship are now open. Deadline: March 20, 2026.',
                 '2026-03-05'),
            ]
        )

    # Seed courses (syllabus)
    cur.execute("SELECT COUNT(*) FROM courses")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO courses (code, title, credits, semester, type) VALUES (?,?,?,?,?)",
            [
                ('SWE101',  'Introduction to Programming',     3.0, 'Spring 2026', 'Theory'),
                ('SWE101L', 'Introduction to Programming Lab', 1.5, 'Spring 2026', 'Lab'),
                ('SWE201',  'Data Structures',                 3.0, 'Spring 2026', 'Theory'),
                ('SWE201L', 'Data Structures Lab',             1.5, 'Spring 2026', 'Lab'),
                ('SWE301',  'Algorithm Design & Analysis',     3.0, 'Spring 2026', 'Theory'),
                ('SWE302',  'Database Management System',      3.0, 'Spring 2026', 'Theory'),
                ('SWE302L', 'Database Management Lab',         1.5, 'Spring 2026', 'Lab'),
                ('SWE401',  'Software Engineering',            3.0, 'Spring 2026', 'Theory'),
                ('SWE402',  'Computer Networks',               3.0, 'Spring 2026', 'Theory'),
                ('SWE402L', 'Computer Networks Lab',           1.5, 'Spring 2026', 'Lab'),
            ]
        )

    # Seed exam routine
    cur.execute("SELECT COUNT(*) FROM exam_routine")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO exam_routine (course_code, course_name, exam_date, exam_time, room, exam_type) VALUES (?,?,?,?,?,?)",
            [
                ('SWE201', 'Data Structures',     '2026-04-10', '09:00 AM - 11:00 AM', 'Room 301', 'Midterm'),
                ('SWE301', 'Algorithm Design',    '2026-04-11', '11:00 AM - 01:00 PM', 'Room 302', 'Midterm'),
                ('SWE302', 'Database Management', '2026-04-12', '09:00 AM - 11:00 AM', 'Room 303', 'Midterm'),
                ('SWE401', 'Software Engineering','2026-04-13', '02:00 PM - 04:00 PM', 'Room 301', 'Midterm'),
                ('SWE402', 'Computer Networks',   '2026-04-14', '09:00 AM - 11:00 AM', 'Room 304', 'Midterm'),
                ('SWE201', 'Data Structures',     '2026-06-10', '09:00 AM - 12:00 PM', 'Room 301', 'Final'),
                ('SWE301', 'Algorithm Design',    '2026-06-11', '09:00 AM - 12:00 PM', 'Room 302', 'Final'),
                ('SWE302', 'Database Management', '2026-06-12', '09:00 AM - 12:00 PM', 'Room 303', 'Final'),
                ('SWE401', 'Software Engineering','2026-06-13', '02:00 PM - 05:00 PM', 'Room 301', 'Final'),
                ('SWE402', 'Computer Networks',   '2026-06-14', '09:00 AM - 12:00 PM', 'Room 304', 'Final'),
            ]
        )

    # Seed mark distribution
    cur.execute("SELECT COUNT(*) FROM mark_distribution")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO mark_distribution (component, marks, description) VALUES (?,?,?)",
            [
                ('Attendance',        10, 'Based on class attendance percentage'),
                ('Assignment / Quiz', 10, 'In-class quizzes and home assignments'),
                ('Midterm Exam',      30, 'Written exam at mid-semester'),
                ('Final Exam',        50, 'Comprehensive exam at end of semester'),
            ]
        )

    # Seed lab schedule
    cur.execute("SELECT COUNT(*) FROM lab_schedule")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO lab_schedule (course_code, course_name, day, time, room, instructor) VALUES (?,?,?,?,?,?)",
            [
                ('SWE101L', 'Intro to Programming Lab', 'Sunday',    '08:00 AM - 10:30 AM', 'Lab 101', 'Dr. Iqbal'),
                ('SWE201L', 'Data Structures Lab',      'Monday',    '11:00 AM - 01:30 PM', 'Lab 102', 'Mr. Karim'),
                ('SWE302L', 'Database Management Lab',  'Tuesday',   '02:00 PM - 04:30 PM', 'Lab 103', 'Ms. Nusrat'),
                ('SWE402L', 'Computer Networks Lab',    'Wednesday', '08:00 AM - 10:30 AM', 'Lab 104', 'Dr. Hasan'),
            ]
        )

    conn.commit()
    conn.close()


# ─── Module 2: Chatbot Keyword Matching ───────────────────────────────────────

def chatbot_response(user_message):
    """
    Keyword-based FAQ matching logic:
    1. Normalize the user message (lowercase, remove punctuation).
    2. For every FAQ, count how many words overlap between the
       user message and that FAQ's keywords + question words.
    3. Return the FAQ with the highest score.
    4. If score is 0, return a fallback message.
    """
    clean = re.sub(r'[^\w\s]', '', user_message.lower())
    words = set(clean.split())

    conn = get_db()
    faqs = conn.execute("SELECT * FROM faqs").fetchall()
    conn.close()

    best_faq   = None
    best_score = 0

    for faq in faqs:
        kw_words  = set((faq['keywords'] or '').lower().split())
        q_words   = set(re.sub(r'[^\w\s]', '', faq['question'].lower()).split())
        faq_words = kw_words | q_words

        score = len(words & faq_words)
        if score > best_score:
            best_score = score
            best_faq   = faq

    if best_faq and best_score >= 1:
        return {
            'answer':   best_faq['answer'],
            'question': best_faq['question'],
            'category': best_faq['category'],
            'matched':  True
        }
    return {
        'answer':   "Sorry, I couldn't find an answer to that. Try rephrasing, or browse the Academic Info page.",
        'question': None,
        'category': None,
        'matched':  False
    }


# ─── Decorators ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── Public Routes ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    conn    = get_db()
    notices = conn.execute(
        "SELECT * FROM notices ORDER BY publish_date DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return render_template('home.html', notices=notices)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name     = request.form['name'].strip()
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id']   = user['user_id']
            session['user_name'] = user['name']
            session['role']      = user['role']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('admin_dashboard') if user['role'] == 'admin' else url_for('home'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name    = request.form['name'].strip()
        pw      = request.form['password']
        confirm = request.form['confirm_password']
        if len(name) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return render_template('register.html')
        if len(pw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if pw != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        conn     = get_db()
        existing = conn.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
        if existing:
            conn.close()
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        conn.execute(
            "INSERT INTO users (name, password, role) VALUES (?,?,?)",
            (name, generate_password_hash(pw), 'student')
        )
        conn.commit(); conn.close()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─── Student Routes ───────────────────────────────────────────────────────────

@app.route('/notices')
@login_required
def notices():
    conn        = get_db()
    all_notices = conn.execute(
        "SELECT * FROM notices ORDER BY publish_date DESC"
    ).fetchall()
    conn.close()
    return render_template('notices.html', notices=all_notices)


# ─── Module 2: Chatbot ────────────────────────────────────────────────────────

@app.route('/chatbot')
@login_required
def chatbot():
    conn = get_db()
    faqs = conn.execute("SELECT question, category FROM faqs LIMIT 6").fetchall()
    conn.close()
    return render_template('chatbot.html', suggestions=faqs)

@app.route('/chatbot/ask', methods=['POST'])
@login_required
def chatbot_ask():
    data    = request.get_json()
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'answer': 'Please type a question first.', 'matched': False})
    return jsonify(chatbot_response(message))


# ─── Module 2: Academic Info ──────────────────────────────────────────────────

@app.route('/academic')
@login_required
def academic():
    conn     = get_db()
    courses  = conn.execute("SELECT * FROM courses ORDER BY code").fetchall()
    midterms = conn.execute(
        "SELECT * FROM exam_routine WHERE exam_type='Midterm' ORDER BY exam_date"
    ).fetchall()
    finals   = conn.execute(
        "SELECT * FROM exam_routine WHERE exam_type='Final' ORDER BY exam_date"
    ).fetchall()
    marks    = conn.execute("SELECT * FROM mark_distribution").fetchall()
    conn.close()
    return render_template('academic.html',
                           courses=courses, midterms=midterms,
                           finals=finals, marks=marks)





# ─── Admin Routes ─────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn    = get_db()
    faqs    = conn.execute("SELECT * FROM faqs").fetchall()
    notices = conn.execute("SELECT * FROM notices ORDER BY publish_date DESC").fetchall()
    conn.close()
    return render_template('admin_dashboard.html', faqs=faqs, notices=notices)

@app.route('/admin/faq/add', methods=['GET', 'POST'])
@admin_required
def faq_add():
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            "INSERT INTO faqs (question, answer, keywords, category) VALUES (?,?,?,?)",
            (request.form['question'], request.form['answer'],
             request.form['keywords'], request.form['category'])
        )
        conn.commit(); conn.close()
        flash('FAQ added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('faq_form.html', faq=None, action='Add')

@app.route('/admin/faq/edit/<int:faq_id>', methods=['GET', 'POST'])
@admin_required
def faq_edit(faq_id):
    conn = get_db()
    faq  = conn.execute("SELECT * FROM faqs WHERE faq_id=?", (faq_id,)).fetchone()
    if request.method == 'POST':
        conn.execute(
            "UPDATE faqs SET question=?, answer=?, keywords=?, category=? WHERE faq_id=?",
            (request.form['question'], request.form['answer'],
             request.form['keywords'], request.form['category'], faq_id)
        )
        conn.commit(); conn.close()
        flash('FAQ updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('faq_form.html', faq=faq, action='Edit')

@app.route('/admin/faq/delete/<int:faq_id>')
@admin_required
def faq_delete(faq_id):
    conn = get_db()
    conn.execute("DELETE FROM faqs WHERE faq_id=?", (faq_id,))
    conn.commit(); conn.close()
    flash('FAQ deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/notice/add', methods=['GET', 'POST'])
@admin_required
def notice_add():
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            "INSERT INTO notices (title, description, publish_date) VALUES (?,?,?)",
            (request.form['title'], request.form['description'], request.form['publish_date'])
        )
        conn.commit(); conn.close()
        flash('Notice posted!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('notice_form.html', notice=None, action='Add')

@app.route('/admin/notice/edit/<int:notice_id>', methods=['GET', 'POST'])
@admin_required
def notice_edit(notice_id):
    conn   = get_db()
    notice = conn.execute("SELECT * FROM notices WHERE notice_id=?", (notice_id,)).fetchone()
    if request.method == 'POST':
        conn.execute(
            "UPDATE notices SET title=?, description=?, publish_date=? WHERE notice_id=?",
            (request.form['title'], request.form['description'],
             request.form['publish_date'], notice_id)
        )
        conn.commit(); conn.close()
        flash('Notice updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('notice_form.html', notice=notice, action='Edit')

@app.route('/admin/notice/delete/<int:notice_id>')
@admin_required
def notice_delete(notice_id):
    conn = get_db()
    conn.execute("DELETE FROM notices WHERE notice_id=?", (notice_id,))
    conn.commit(); conn.close()
    flash('Notice deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
