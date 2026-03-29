# 🤖 QueryNest — AI-Based Smart FAQ Chatbot for SWE Students

> SE331 | Group 03 | Lab Section: 40C1 | Spring 2026

QueryNest is a Flask-based web application providing SWE students with instant answers to department FAQs, notices, schedules, and academic information.

---

## 👥 Team Members

| Student ID         | Name                  | Responsibility              |
|--------------------|-----------------------|-----------------------------|
| 0242310005341181   | S.M. Rakib            | Backend, Auth, Chatbot Logic|
| 0242310005341342   | MD Rashed Hasan       | Database, Admin Panel       |
| 0242310005341238   | MD Faysal Anam Bappy  | Frontend, Feedback, Campus  |

---

## 🛠️ Tech Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Backend   | Python 3, Flask         |
| Frontend  | HTML, CSS, Bootstrap 5  |
| Database  | SQLite                  |
| Auth      | Werkzeug (bcrypt hash)  |

---

## ✅ Module 1 — Completed Features

- [x] Student Registration (username + password)
- [x] Student & Admin Login
- [x] Password Encryption (Werkzeug hashing)
- [x] Role-Based Access Control (Student / Admin)
- [x] Admin: Add, Edit, Delete FAQs
- [x] Admin: Add, Edit, Delete Notices
- [x] Students: View all Notices
- [x] Clean Bootstrap 5 Homepage UI



## 📁 Project Structure

```
QueryNest/
├── app.py                    ← Flask backend (all routes & logic)
├── requirements.txt          ← Python dependencies
├── .gitignore                ← Excludes .db, cache, venv
├── README.md                 ← This file
└── templates/
    ├── base.html             ← Shared navbar + layout
    ├── home.html             ← Homepage with notices preview
    ├── login.html            ← Login form
    ├── register.html         ← Student registration form
    ├── admin_dashboard.html  ← Admin: manage FAQs & Notices
    ├── faq_form.html         ← Add / Edit FAQ
    ├── notice_form.html      ← Add / Edit Notice
    └── notices.html          ← Student notice board
```
