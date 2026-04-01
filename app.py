
import hashlib
import hmac
import io
import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from jinja2 import DictLoader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from werkzeug.utils import secure_filename

APP_NAME = "Software Project Management Tool"
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "software_project_management_tool.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SPMT_SECRET_KEY", "spmt-dev-secret-change-me")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB


TEMPLATES = {
    "base.html": """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title or app_name }}</title>
    <style>
        :root {
            --bg: #f6f8fb;
            --card: #ffffff;
            --nav1: #0f172a;
            --nav2: #1d4ed8;
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #e2e8f0;
            --secondary-dark: #cbd5e1;
            --success: #15803d;
            --danger: #dc2626;
            --danger-dark: #b91c1c;
            --text: #0f172a;
            --muted: #475569;
            --border: #d9e2ec;
            --shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        a { color: var(--primary); }
        .nav {
            background: linear-gradient(120deg, var(--nav1), var(--nav2));
            color: white;
            padding: 16px 24px;
            box-shadow: var(--shadow);
        }
        .nav-inner {
            max-width: 1260px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            flex-wrap: wrap;
        }
        .brand {
            color: white;
            text-decoration: none;
            font-size: 20px;
            font-weight: 700;
        }
        .nav-links {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .nav-links a, .nav-links span {
            color: white;
            text-decoration: none;
            font-size: 14px;
        }
        .nav-chip {
            padding: 8px 12px;
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
        }
        .container {
            max-width: 1260px;
            margin: 0 auto;
            padding: 24px;
        }
        .page-title {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            flex-wrap: wrap;
            margin: 6px 0 18px;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: var(--shadow);
            padding: 22px;
            margin-bottom: 20px;
        }
        .grid {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }
        .two-col {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 20px;
        }
        @media (max-width: 960px) {
            .two-col { grid-template-columns: 1fr; }
        }
        label {
            display: block;
            font-weight: 700;
            margin-bottom: 6px;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            font-size: 14px;
            background: white;
            transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #60a5fa;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
            transform: translateY(-1px);
        }
        textarea { min-height: 110px; resize: vertical; }
        .top-gap { margin-top: 18px; }
        .muted { color: var(--muted); }
        .small { font-size: 12px; }
        .actions {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-block;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            text-decoration: none;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
        }
        .btn:hover { transform: translateY(-1px); }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: var(--primary-dark); box-shadow: 0 14px 24px rgba(37, 99, 235, 0.2); }
        .btn-secondary { background: var(--secondary); color: var(--text); }
        .btn-secondary:hover { background: var(--secondary-dark); }
        .btn-danger { background: var(--danger); color: white; }
        .btn-danger:hover { background: var(--danger-dark); }
        .btn-success { background: var(--success); color: white; }
        .table-wrap {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        .table-shell {
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.85);
        }
        .table-shell table {
            margin: 0;
        }
        th, td {
            text-align: left;
            vertical-align: top;
            padding: 12px 10px;
            border-bottom: 1px solid var(--border);
        }
        th {
            background: #eff6ff;
            color: #1e40af;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-size: 12px;
        }
        .table-shell thead th {
            background: linear-gradient(180deg, #eff6ff, #dbeafe);
            color: #1e3a8a;
            border-bottom: 1px solid #c7d2fe;
        }
        .table-shell tbody tr:nth-child(odd) {
            background: var(--row-odd, #ffffff);
        }
        .table-shell tbody tr:nth-child(even) {
            background: var(--row-even, #f8fbff);
        }
        .table-shell tbody tr:hover {
            background: var(--row-hover, #eaf2ff);
        }
        .table-shell tbody tr:last-child td {
            border-bottom: none;
        }
        .table-projects {
            --row-odd: #ffffff;
            --row-even: #f3f8ff;
            --row-hover: #dfecff;
        }
        .table-issues {
            --row-odd: #fffef8;
            --row-even: #fff7e4;
            --row-hover: #feefc5;
        }
        .table-documents {
            --row-odd: #f8fffc;
            --row-even: #eafbf4;
            --row-hover: #d4f6e7;
        }
        .table-notes {
            --row-odd: #ffffff;
            --row-even: #f7f3ff;
            --row-hover: #ece4ff;
        }
        tr.clickable-row { cursor: pointer; }
        tr.clickable-row:hover { background: var(--row-hover, #f8fbff); }
        .table-title-text {
            display: block;
            font-size: 15px;
            line-height: 1.35;
            color: var(--text);
        }
        .table-subtext {
            display: block;
            margin-top: 4px;
            color: var(--muted);
            font-size: 12px;
        }
        .flash {
            padding: 12px 14px;
            border-radius: 10px;
            margin-bottom: 14px;
            border: 1px solid #a5f3fc;
            background: #ecfeff;
            color: #155e75;
        }
        .empty {
            padding: 18px;
            border: 1px dashed var(--border);
            border-radius: 12px;
            background: #fafcff;
            color: var(--muted);
        }
        .inline-form { display: inline; }
        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;
        }
        .section-copy {
            margin: 6px 0 0;
        }
        .pill {
            display: inline-block;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 12px;
            border-radius: 999px;
            padding: 4px 8px;
            font-weight: 700;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 14px;
        }
        .summary-item {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
            background: #fbfdff;
        }
        .summary-item strong {
            display: block;
            margin-top: 6px;
            font-size: 15px;
        }
        .note-form {
            padding: 20px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: linear-gradient(135deg, #f8fbff, #ffffff);
            margin-bottom: 16px;
        }
        .note-form textarea {
            min-height: 90px;
        }
        .auth-wrap {
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 40px 16px;
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.24), transparent 32%),
                radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.18), transparent 28%),
                linear-gradient(135deg, #eef4ff 0%, #f8fafc 48%, #e0f2fe 100%);
        }
        .auth-wrap::before,
        .auth-wrap::after {
            content: "";
            position: absolute;
            border-radius: 999px;
            filter: blur(10px);
            opacity: 0.85;
        }
        .auth-wrap::before {
            width: 280px;
            height: 280px;
            top: -100px;
            right: 8%;
            background: rgba(37, 99, 235, 0.18);
        }
        .auth-wrap::after {
            width: 220px;
            height: 220px;
            bottom: -80px;
            left: 6%;
            background: rgba(14, 165, 233, 0.18);
        }
        .auth-wrap .flash {
            width: 100%;
            max-width: 1040px;
            margin: 0 auto 18px;
            position: relative;
            z-index: 1;
        }
        .auth-layout {
            width: 100%;
            max-width: 1040px;
            display: grid;
            grid-template-columns: minmax(280px, 1.1fr) minmax(320px, 0.9fr);
            gap: 22px;
            align-items: stretch;
            position: relative;
            z-index: 1;
        }
        .auth-hero {
            padding: 34px;
            border-radius: 28px;
            background:
                linear-gradient(155deg, rgba(15, 23, 42, 0.96), rgba(29, 78, 216, 0.9)),
                linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0));
            box-shadow: 0 28px 60px rgba(15, 23, 42, 0.24);
            color: white;
            position: relative;
            overflow: hidden;
        }
        .auth-hero::after {
            content: "";
            position: absolute;
            inset: auto -40px -60px auto;
            width: 220px;
            height: 220px;
            border-radius: 999px;
            background: rgba(125, 211, 252, 0.18);
        }
        .auth-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.18);
            font-size: 12px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
        }
        .auth-hero h1 {
            margin: 18px 0 14px;
            font-size: clamp(32px, 4vw, 46px);
            line-height: 1.05;
        }
        .auth-hero p {
            max-width: 34rem;
            margin: 0;
            color: rgba(255,255,255,0.82);
            font-size: 15px;
            line-height: 1.6;
        }
        .auth-feature-list {
            display: grid;
            gap: 12px;
            margin: 28px 0 0;
            padding: 0;
            list-style: none;
        }
        .auth-feature-list li {
            padding: 14px 16px;
            border-radius: 16px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(8px);
        }
        .auth-feature-list strong {
            display: block;
            margin-bottom: 4px;
            font-size: 15px;
        }
        .auth-card {
            width: 100%;
            max-width: 460px;
            margin-left: auto;
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(217, 226, 236, 0.9);
            border-radius: 28px;
            box-shadow: 0 24px 55px rgba(15, 23, 42, 0.14);
            padding: 32px;
            backdrop-filter: blur(8px);
        }
        .auth-kicker {
            display: inline-block;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #1d4ed8;
            background: #dbeafe;
            border-radius: 999px;
            padding: 8px 12px;
            margin-bottom: 16px;
        }
        .auth-card h2 {
            margin: 0 0 8px;
            font-size: 30px;
        }
        .auth-card p {
            margin: 0;
        }
        .auth-form {
            margin-top: 24px;
        }
        .auth-submit {
            width: 100%;
            justify-content: center;
            padding: 12px 18px;
        }
        .auth-note {
            margin-top: 18px;
            padding-top: 18px;
            border-top: 1px solid rgba(217, 226, 236, 0.9);
            color: var(--muted);
            font-size: 13px;
        }
        .footer-note {
            padding: 12px 16px;
            background: #f8fafc;
            border-radius: 12px;
            color: var(--muted);
            font-size: 13px;
        }
        @media (max-width: 900px) {
            .auth-layout {
                grid-template-columns: 1fr;
            }
            .auth-card {
                max-width: none;
                margin-left: 0;
            }
        }
        @media (max-width: 640px) {
            .auth-wrap {
                padding: 20px 14px;
            }
            .auth-hero,
            .auth-card {
                padding: 24px;
                border-radius: 22px;
            }
            .auth-hero h1,
            .auth-card h2 {
                font-size: 28px;
            }
        }
    </style>
</head>
<body>
    {% if g.user %}
    <div class="nav">
        <div class="nav-inner">
            <a class="brand" href="{{ url_for('index') }}">{{ app_name }}</a>
            <div class="nav-links">
                <a class="nav-chip" href="{{ url_for('index') }}">My Projects</a>
                {% if g.user['is_admin'] %}
                    <a class="nav-chip" href="{{ url_for('manage_users') }}">User Administration</a>
                {% endif %}
                <span class="nav-chip">Signed in as {{ g.user['full_name'] or g.user['username'] }}{% if g.user['is_admin'] %} (Admin){% endif %}</span>
                <a class="nav-chip" href="{{ url_for('logout') }}">Logout</a>
            </div>
        </div>
    </div>
    {% endif %}
    <div class="{% if g.user %}container{% else %}auth-wrap{% endif %}">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    {% if g.user %}
    <script>
        document.querySelectorAll('[data-href]').forEach(function(row) {
            row.addEventListener('click', function(e) {
                if (e.target.closest('a, button, form, input, textarea, select, label')) return;
                window.location = row.dataset.href;
            });
        });
    </script>
    {% endif %}
</body>
</html>
""",
    "login.html": """
{% extends 'base.html' %}
{% block content %}
<div class="auth-layout">
    <section class="auth-hero">
        <span class="auth-badge">Project Workspace</span>
        <h1>Keep projects, issues, and documents moving.</h1>
        <p>One place for your team to stay aligned, track delivery, and keep every project artifact easy to find.</p>
        <ul class="auth-feature-list">
            <li>
                <strong>Track the full project picture</strong>
                Manage timelines, ownership, and progress in one shared workspace.
            </li>
            <li>
                <strong>Stay on top of issues</strong>
                Organize blockers, capture updates, and keep follow-through visible.
            </li>
            <li>
                <strong>Keep documents close</strong>
                Store project files and export clean PDF summaries when you need them.
            </li>
        </ul>
    </section>

    <section class="auth-card">
        <span class="auth-kicker">Welcome Back</span>
        <h2>Project Management Tool</h2>
        <p class="muted">Sign in to manage your Project.</p>
        <form class="auth-form" method="post">
            <div>
                <label for="username">Username</label>
                <input id="username" name="username" value="{{ request.form.get('username', '') }}" required autofocus>
            </div>
            <div class="top-gap">
                <label for="password">Password</label>
                <input id="password" name="password" type="password" required>
            </div>
            <div class="actions top-gap">
                <button class="btn btn-primary auth-submit" type="submit">Login</button>
            </div>
        </form>
        <div class="auth-note">
            Use your assigned account to access your projects, issue tracking, and shared documentation.
        </div>
    </section>
</div>
{% endblock %}
""",
    "index.html": """
{% extends 'base.html' %}
{% block content %}
<div class="page-title">
    <div>
        <h1 style="margin:0;">My Projects</h1>
        <p class="muted" style="margin:6px 0 0;">Only your own projects are visible in your workspace.</p>
    </div>
    <div class="actions">
        <a class="btn btn-secondary" href="{{ url_for('export_all_projects_pdf') }}">Export My Projects PDF</a>
        <a class="btn btn-primary" href="{{ url_for('add_project') }}">+ Add Project</a>
    </div>
</div>

<div class="card">
    <div class="table-wrap table-shell table-projects">
        <table>
            <thead>
                <tr>
                    <th>Project Name</th>
                    <th>Description</th>
                    <th>Start Date</th>
                    <th>End Date</th>
                    <th>Point of Contact</th>
                    <th>Business POC</th>
                    <th>Owner</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% if projects %}
                    {% for project in projects %}
                    <tr class="clickable-row" data-href="{{ url_for('project_detail', project_id=project['id']) }}">
                        <td>
                            <span class="table-title-text">{{ project['name'] }}</span>
                            <span class="table-subtext">Created {{ project['created_at'][:10] if project['created_at'] else '-' }}</span>
                        </td>
                        <td>{{ project['description'] or '-' }}</td>
                        <td>{{ project['start_date'] or '-' }}</td>
                        <td>{{ project['end_date'] or '-' }}</td>
                        <td>{{ project['point_of_contact'] or '-' }}</td>
                        <td>{{ project['business_point_of_contact'] or '-' }}</td>
                        <td>{{ project['owner_name'] }}</td>
                        <td>
                            <div class="actions">
                                <a class="btn btn-secondary" href="{{ url_for('edit_project', project_id=project['id']) }}">Edit</a>
                                <form class="inline-form" action="{{ url_for('delete_project', project_id=project['id']) }}" method="post" onsubmit="return confirm('Delete this project and all related issues/documents?');">
                                    <button class="btn btn-danger" type="submit">Delete</button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="8"><div class="empty">No projects available yet. Click <strong>Add Project</strong> to create your first one.</div></td>
                    </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
""",
    "project_form.html": """
{% extends 'base.html' %}
{% block content %}
<div class="page-title">
    <div>
        <h1 style="margin:0;">{{ heading }}</h1>
        <p class="muted" style="margin:6px 0 0;">Enter the project information below.</p>
    </div>
    <a class="btn btn-secondary" href="{{ url_for('index') }}">Back to Projects</a>
</div>

<div class="card">
    <form method="post">
        <div class="grid">
            <div>
                <label for="name">Project Name</label>
                <input id="name" name="name" value="{{ project['name'] if project else '' }}" required>
            </div>
            <div>
                <label for="point_of_contact">Point of Contact</label>
                <input id="point_of_contact" name="point_of_contact" value="{{ project['point_of_contact'] if project else '' }}">
            </div>
            <div>
                <label for="start_date">Start Date</label>
                <input id="start_date" type="date" name="start_date" value="{{ project['start_date'] if project else '' }}">
            </div>
            <div>
                <label for="end_date">End Date</label>
                <input id="end_date" type="date" name="end_date" value="{{ project['end_date'] if project else '' }}">
            </div>
            <div>
                <label for="business_point_of_contact">Business Point of Contact</label>
                <input id="business_point_of_contact" name="business_point_of_contact" value="{{ project['business_point_of_contact'] if project else '' }}">
            </div>
        </div>
        <div class="top-gap">
            <label for="description">Project Description</label>
            <textarea id="description" name="description">{{ project['description'] if project else '' }}</textarea>
        </div>
        <div class="actions top-gap">
            <button class="btn btn-primary" type="submit">Save Project</button>
            <a class="btn btn-secondary" href="{{ url_for('index') }}">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
""",
    "project_detail.html": """
{% extends 'base.html' %}
{% block content %}
<div class="page-title">
    <div>
        <h1 style="margin:0;">{{ project['name'] }}</h1>
        <p class="muted" style="margin:6px 0 0;">Project overview, issues, project documents, and PDF export.</p>
    </div>
    <div class="actions">
        <a class="btn btn-secondary" href="{{ url_for('index') }}">Back</a>
        <a class="btn btn-secondary" href="{{ url_for('export_project_pdf', project_id=project['id']) }}">Export Project PDF</a>
        <a class="btn btn-primary" href="{{ url_for('edit_project', project_id=project['id']) }}">Edit Project</a>
    </div>
</div>

<div class="card">
    <div class="summary-grid">
        <div class="summary-item"><span class="pill">Start Date</span><strong>{{ project['start_date'] or '-' }}</strong></div>
        <div class="summary-item"><span class="pill">End Date</span><strong>{{ project['end_date'] or '-' }}</strong></div>
        <div class="summary-item"><span class="pill">Point of Contact</span><strong>{{ project['point_of_contact'] or '-' }}</strong></div>
        <div class="summary-item"><span class="pill">Business POC</span><strong>{{ project['business_point_of_contact'] or '-' }}</strong></div>
    </div>
    <div class="top-gap">
        <span class="pill">Description</span>
        <p>{{ project['description'] or 'No description added.' }}</p>
    </div>
</div>

<div class="card">
    <div class="section-title">
        <div>
            <h2 style="margin:0;">Project Notes</h2>
            <p class="muted small section-copy">Add multiple notes to capture updates, reminders, and context for this project.</p>
        </div>
    </div>
    <form class="note-form" method="post" action="{{ url_for('add_project_note', project_id=project['id']) }}">
        <div class="grid">
            <div>
                <label for="note">Note</label>
                <input id="note" name="note" value="{{ request.form.get('note', '') }}" required>
            </div>
            <div>
                <label for="note_description">Note Description</label>
                <textarea id="note_description" name="note_description">{{ request.form.get('note_description', '') }}</textarea>
            </div>
        </div>
        <div class="actions top-gap">
            <button class="btn btn-primary" type="submit">Add Note</button>
        </div>
    </form>
    <div class="table-wrap table-shell table-notes">
        <table>
            <thead>
                <tr>
                    <th>Note</th>
                    <th>Note Description</th>
                    <th>Added On</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% if notes %}
                    {% for note in notes %}
                    <tr>
                        <td><span class="table-title-text">{{ note['note'] }}</span></td>
                        <td>{{ note['note_description'] or '-' }}</td>
                        <td>{{ note['created_at'] or '-' }}</td>
                        <td>
                            <form class="inline-form" action="{{ url_for('delete_project_note', project_id=project['id'], note_id=note['id']) }}" method="post" onsubmit="return confirm('Delete this note?');">
                                <button class="btn btn-danger" type="submit">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="4"><div class="empty">No notes added yet for this project.</div></td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>

<div class="two-col">
    <div class="card">
        <div class="section-title">
            <div>
                <h2 style="margin:0;">Issue List</h2>
                <p class="muted small section-copy">Track ownership and dates for every issue tied to this project.</p>
            </div>
            <a class="btn btn-primary" href="{{ url_for('add_issue', project_id=project['id']) }}">+ Add Issue</a>
        </div>
        <div class="table-wrap table-shell table-issues">
            <table>
                <thead>
                    <tr>
                        <th>SL Number</th>
                        <th>Issue Name</th>
                        <th>Owner</th>
                        <th>Date</th>
                        <th>Due Date</th>
                        <th>Issue Description</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% if issues %}
                        {% for issue in issues %}
                        <tr>
                            <td>{{ issue['sl_number'] }}</td>
                            <td><span class="table-title-text">{{ issue['name'] }}</span></td>
                            <td>{{ issue['owner'] or '-' }}</td>
                            <td>{{ issue['display_issue_date'] or '-' }}</td>
                            <td>{{ issue['due_date'] or '-' }}</td>
                            <td>{{ issue['description'] or '-' }}</td>
                            <td>
                                <div class="actions">
                                    <a class="btn btn-secondary" href="{{ url_for('edit_issue', project_id=project['id'], issue_id=issue['id']) }}">Edit</a>
                                    <form class="inline-form" action="{{ url_for('delete_issue', project_id=project['id'], issue_id=issue['id']) }}" method="post" onsubmit="return confirm('Delete this issue?');">
                                        <button class="btn btn-danger" type="submit">Delete</button>
                                    </form>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr><td colspan="7"><div class="empty">No issues added for this project.</div></td></tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="card">
        <div class="section-title">
            <div>
                <h2 style="margin:0;">Document List</h2>
                <p class="muted small section-copy">Keep uploaded documents easy to browse with a cleaner, color-coded list.</p>
            </div>
            <a class="btn btn-primary" href="{{ url_for('add_document', project_id=project['id']) }}">+ Add Document</a>
        </div>
        <div class="table-wrap table-shell table-documents">
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Description</th>
                        <th>File</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% if documents %}
                        {% for doc in documents %}
                        <tr>
                            <td><span class="table-title-text">{{ doc['title'] }}</span><span class="table-subtext">Uploaded: {{ doc['uploaded_at'] }}</span></td>
                            <td>{{ doc['description'] or '-' }}</td>
                            <td>
                                {% if doc['original_filename'] %}
                                    <a href="{{ url_for('download_document', document_id=doc['id']) }}">{{ doc['original_filename'] }}</a>
                                {% else %}
                                    -
                                {% endif %}
                            </td>
                            <td>
                                <div class="actions">
                                    <a class="btn btn-secondary" href="{{ url_for('edit_document', project_id=project['id'], document_id=doc['id']) }}">Edit</a>
                                    <form class="inline-form" action="{{ url_for('delete_document', project_id=project['id'], document_id=doc['id']) }}" method="post" onsubmit="return confirm('Delete this document record?');">
                                        <button class="btn btn-danger" type="submit">Delete</button>
                                    </form>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr><td colspan="4"><div class="empty">No documents uploaded for this project.</div></td></tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
""",
    "issue_form.html": """
{% extends 'base.html' %}
{% block content %}
<div class="page-title">
    <div>
        <h1 style="margin:0;">{{ heading }}</h1>
        <p class="muted" style="margin:6px 0 0;">Project: {{ project['name'] }}</p>
    </div>
    <a class="btn btn-secondary" href="{{ url_for('project_detail', project_id=project['id']) }}">Back to Project</a>
</div>

<div class="card">
    <form method="post">
        <div class="grid">
            <div>
                <label for="sl_number">SL Number</label>
                <input id="sl_number" name="sl_number" type="number" min="1" value="{{ request.form.get('sl_number', issue['sl_number'] if issue else '') }}" required>
            </div>
            <div>
                <label for="name">Issue Name</label>
                <input id="name" name="name" value="{{ request.form.get('name', issue['name'] if issue else '') }}" required>
            </div>
            <div>
                <label for="owner">Owner</label>
                <input id="owner" name="owner" value="{{ request.form.get('owner', issue['owner'] if issue else default_issue_owner) }}">
            </div>
            <div>
                <label for="issue_date">Date</label>
                <input id="issue_date" name="issue_date" type="date" value="{{ request.form.get('issue_date', issue['issue_date'] if issue else default_issue_date) }}">
            </div>
            <div>
                <label for="due_date">Due Date</label>
                <input id="due_date" name="due_date" type="date" value="{{ request.form.get('due_date', issue['due_date'] if issue else '') }}">
            </div>
        </div>
        <div class="top-gap">
            <label for="description">Issue Description</label>
            <textarea id="description" name="description">{{ request.form.get('description', issue['description'] if issue else '') }}</textarea>
        </div>
        <div class="actions top-gap">
            <button class="btn btn-primary" type="submit">Save Issue</button>
            <a class="btn btn-secondary" href="{{ url_for('project_detail', project_id=project['id']) }}">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
""",
    "document_form.html": """
{% extends 'base.html' %}
{% block content %}
<div class="page-title">
    <div>
        <h1 style="margin:0;">{{ heading }}</h1>
        <p class="muted" style="margin:6px 0 0;">Project: {{ project['name'] }}</p>
    </div>
    <a class="btn btn-secondary" href="{{ url_for('project_detail', project_id=project['id']) }}">Back to Project</a>
</div>

<div class="card">
    <form method="post" enctype="multipart/form-data">
        <div class="grid">
            <div>
                <label for="title">Document Title</label>
                <input id="title" name="title" value="{{ document['title'] if document else '' }}" required>
            </div>
            <div>
                <label for="file">Upload File{% if not document %} <span class="muted">(optional)</span>{% endif %}</label>
                <input id="file" name="file" type="file">
                {% if document and document['original_filename'] %}
                    <p class="small muted">Current file: {{ document['original_filename'] }}</p>
                {% endif %}
            </div>
        </div>
        <div class="top-gap">
            <label for="description">Document Description</label>
            <textarea id="description" name="description">{{ document['description'] if document else '' }}</textarea>
        </div>
        <div class="actions top-gap">
            <button class="btn btn-primary" type="submit">Save Document</button>
            <a class="btn btn-secondary" href="{{ url_for('project_detail', project_id=project['id']) }}">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
""",
    "manage_users.html": """
{% extends 'base.html' %}
{% block content %}
<div class="page-title">
    <div>
        <h1 style="margin:0;">User Administration</h1>
        <p class="muted" style="margin:6px 0 0;">Admin-only area. Create users for this multi-user application.</p>
    </div>
</div>

<div class="two-col">
    <div class="card">
        <div class="section-title">
            <h2 style="margin:0;">Create User</h2>
        </div>
        <form method="post">
            <div class="grid">
                <div>
                    <label for="full_name">Full Name</label>
                    <input id="full_name" name="full_name" required>
                </div>
                <div>
                    <label for="username">Username</label>
                    <input id="username" name="username" required>
                </div>
                <div>
                    <label for="password">Password</label>
                    <input id="password" name="password" type="password" required>
                </div>
                <div>
                    <label for="is_admin">Role</label>
                    <select id="is_admin" name="is_admin">
                        <option value="0">Standard User</option>
                        <option value="1">Administrator</option>
                    </select>
                </div>
            </div>
            <div class="actions top-gap">
                <button class="btn btn-primary" type="submit">Create User</button>
            </div>
        </form>
    </div>

    <div class="card">
        <div class="section-title">
            <h2 style="margin:0;">Existing Users</h2>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Full Name</th>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user['full_name'] }}</td>
                        <td>{{ user['username'] }}</td>
                        <td>{{ 'Administrator' if user['is_admin'] else 'Standard User' }}</td>
                        <td>{{ user['created_at'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="footer-note top-gap">
            Projects, issues, and uploaded documents remain private to the logged-in owner. Users cannot browse or download other users' project data.
        </div>
    </div>
</div>
{% endblock %}
""",
}

app.jinja_loader = DictLoader(TEMPLATES)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
    return hmac.compare_digest(candidate, digest)


def get_db():
    if "db" not in g:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_one(query, params=()):
    return get_db().execute(query, params).fetchone()


def fetch_all(query, params=()):
    return get_db().execute(query, params).fetchall()


def execute_db(query, params=()):
    db = get_db()
    cursor = db.execute(query, params)
    db.commit()
    return cursor


def ensure_column_exists(db, table_name: str, column_name: str, definition: str):
    existing_columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in existing_columns:
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_db():
    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            point_of_contact TEXT,
            business_point_of_contact TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            sl_number INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            owner TEXT,
            issue_date TEXT,
            due_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            UNIQUE (project_id, sl_number)
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT,
            original_filename TEXT,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS project_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            note_description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )

    ensure_column_exists(db, "issues", "owner", "TEXT")
    ensure_column_exists(db, "issues", "issue_date", "TEXT")
    ensure_column_exists(db, "issues", "due_date", "TEXT")
    db.execute(
        """
        UPDATE issues
        SET issue_date = substr(created_at, 1, 10)
        WHERE COALESCE(issue_date, '') = '' AND COALESCE(created_at, '') <> ''
        """
    )
    db.commit()

    sheeba = db.execute("SELECT id FROM users WHERE username = ?", ("Sheeba",)).fetchone()
    if not sheeba:
        db.execute(
            """
            INSERT INTO users (username, full_name, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Sheeba", "Sheeba", hash_password("Sheeba"), 1, utcnow()),
        )
        db.commit()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id:
        g.user = fetch_one(
            "SELECT id, username, full_name, is_admin, created_at FROM users WHERE id = ?",
            (user_id,),
        )


@app.context_processor
def inject_globals():
    return {"app_name": APP_NAME}


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        if not g.user["is_admin"]:
            flash("Administrator access is required for that page.")
            return redirect(url_for("index"))
        return view(**kwargs)
    return wrapped_view


def utcnow():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def today_ymd():
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_owned_project(project_id: int):
    return fetch_one(
        """
        SELECT p.*, u.full_name AS owner_name
        FROM projects p
        JOIN users u ON u.id = p.owner_id
        WHERE p.id = ? AND p.owner_id = ?
        """,
        (project_id, g.user["id"]),
    )


def get_owned_document(document_id: int):
    return fetch_one(
        """
        SELECT d.*, p.owner_id, p.name AS project_name
        FROM documents d
        JOIN projects p ON p.id = d.project_id
        WHERE d.id = ? AND p.owner_id = ?
        """,
        (document_id, g.user["id"]),
    )


def get_project_workspace(project_id: int):
    issues = fetch_all(
        """
        SELECT i.*, COALESCE(NULLIF(i.issue_date, ''), substr(i.created_at, 1, 10)) AS display_issue_date
        FROM issues i
        WHERE i.project_id = ?
        ORDER BY i.sl_number ASC, i.id ASC
        """,
        (project_id,),
    )
    documents = fetch_all(
        "SELECT * FROM documents WHERE project_id = ? ORDER BY uploaded_at DESC, id DESC",
        (project_id,),
    )
    notes = fetch_all(
        "SELECT * FROM project_notes WHERE project_id = ? ORDER BY created_at DESC, id DESC",
        (project_id,),
    )
    return issues, documents, notes


def render_project_detail_page(project):
    issues, documents, notes = get_project_workspace(project["id"])
    return render_template(
        "project_detail.html",
        title=f"{project['name']} | {APP_NAME}",
        project=project,
        issues=issues,
        documents=documents,
        notes=notes,
    )


def remove_file_if_present(filename: str | None):
    if not filename:
        return
    path = UPLOAD_FOLDER / filename
    if path.exists():
        path.unlink()


def save_uploaded_file(upload, owner_id: int):
    if not upload or not upload.filename:
        return None, None
    safe_name = secure_filename(upload.filename)
    unique_name = f"user_{owner_id}_{uuid.uuid4().hex}_{safe_name}"
    destination = UPLOAD_FOLDER / unique_name
    upload.save(destination)
    return unique_name, upload.filename


def build_pdf(projects, detailed_project=None, issues=None, documents=None, owner_name=None, notes=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=APP_NAME,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CardHeading", parent=styles["Heading2"], spaceAfter=8, textColor=colors.HexColor("#1d4ed8")))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#64748b")))
    styles["Title"].textColor = colors.HexColor("#0f172a")
    styles["Title"].spaceAfter = 12

    story = []
    story.append(Paragraph(APP_NAME, styles["Title"]))
    if detailed_project:
        story.append(Paragraph(f"Project Export for {escape_pdf(detailed_project['name'])}", styles["Heading2"]))
        story.append(Paragraph(f"Owner: {escape_pdf(owner_name or '')}", styles["SmallMuted"]))
        story.append(Spacer(1, 8))
        summary_rows = [
            ["Project Name", escape_pdf(detailed_project["name"])],
            ["Project Description", escape_pdf(detailed_project["description"] or "-")],
            ["Start Date", escape_pdf(detailed_project["start_date"] or "-")],
            ["End Date", escape_pdf(detailed_project["end_date"] or "-")],
            ["Point of Contact", escape_pdf(detailed_project["point_of_contact"] or "-")],
            ["Business Point of Contact", escape_pdf(detailed_project["business_point_of_contact"] or "-")],
        ]
        story.append(make_pdf_table(summary_rows, [1.9 * inch, 4.8 * inch], header=False))
        story.append(Spacer(1, 14))

        issue_rows = [["SL", "Issue Name", "Owner", "Date", "Due", "Issue Description"]]
        if issues:
            for issue in issues:
                issue_date = issue["issue_date"] or (issue["created_at"][:10] if issue["created_at"] else "-")
                issue_rows.append(
                    [
                        str(issue["sl_number"]),
                        escape_pdf(issue["name"]),
                        escape_pdf(issue["owner"] or "-"),
                        escape_pdf(issue_date or "-"),
                        escape_pdf(issue["due_date"] or "-"),
                        escape_pdf(issue["description"] or "-"),
                    ]
                )
        else:
            issue_rows.append(["-", "No issues", "-", "-", "-", "No issue records available for this project."])
        story.append(Paragraph("Issues", styles["CardHeading"]))
        story.append(make_pdf_table(issue_rows, [0.45 * inch, 1.2 * inch, 1.0 * inch, 0.8 * inch, 0.8 * inch, 2.95 * inch]))
        story.append(Spacer(1, 14))

        doc_rows = [["Title", "Description", "Original File", "Uploaded At"]]
        if documents:
            for item in documents:
                doc_rows.append(
                    [
                        escape_pdf(item["title"]),
                        escape_pdf(item["description"] or "-"),
                        escape_pdf(item["original_filename"] or "-"),
                        escape_pdf(item["uploaded_at"] or "-"),
                    ]
                )
        else:
            doc_rows.append(["No documents", "-", "-", "-"])
        story.append(Paragraph("Project Documents", styles["CardHeading"]))
        story.append(make_pdf_table(doc_rows, [1.55 * inch, 2.4 * inch, 1.65 * inch, 1.0 * inch]))
        story.append(Spacer(1, 14))

        note_rows = [["Note", "Description", "Added On"]]
        if notes:
            for note in notes:
                note_rows.append(
                    [
                        escape_pdf(note["note"]),
                        escape_pdf(note["note_description"] or "-"),
                        escape_pdf(note["created_at"] or "-"),
                    ]
                )
        else:
            note_rows.append(["No notes", "-", "-"])
        story.append(Paragraph("Project Notes", styles["CardHeading"]))
        story.append(make_pdf_table(note_rows, [1.6 * inch, 4.25 * inch, 1.35 * inch]))
    else:
        story.append(Paragraph(f"My Project Portfolio for {escape_pdf(owner_name or '')}", styles["Heading2"]))
        story.append(Paragraph(f"Generated at {utcnow()} UTC", styles["SmallMuted"]))
        story.append(Spacer(1, 8))
        rows = [[
            "Project Name",
            "Description",
            "Start",
            "End",
            "Point of Contact",
            "Business POC",
        ]]
        if projects:
            for project in projects:
                rows.append(
                    [
                        escape_pdf(project["name"]),
                        escape_pdf(project["description"] or "-"),
                        escape_pdf(project["start_date"] or "-"),
                        escape_pdf(project["end_date"] or "-"),
                        escape_pdf(project["point_of_contact"] or "-"),
                        escape_pdf(project["business_point_of_contact"] or "-"),
                    ]
                )
        else:
            rows.append(["No projects", "-", "-", "-", "-", "-"])
        story.append(make_pdf_table(rows, [1.45 * inch, 2.2 * inch, 0.8 * inch, 0.8 * inch, 1.1 * inch, 1.1 * inch]))

    doc.build(story)
    buffer.seek(0)
    return buffer


def escape_pdf(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def make_pdf_table(rows, widths, header=True):
    wrapped_rows = []
    for r_index, row in enumerate(rows):
        wrapped_row = []
        for cell in row:
            cell_text = str(cell)
            style_name = "BodyText"
            if r_index == 0 and header:
                style_name = "Heading5"
            wrapped_row.append(Paragraph(escape_pdf(cell_text), getSampleStyleSheet()[style_name]))
        wrapped_rows.append(wrapped_row)

    table = Table(wrapped_rows, colWidths=widths, repeatRows=1 if header else 0)
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff") if header else colors.HexColor("#f8fafc")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1d4ed8") if header else colors.HexColor("#0f172a")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#dbe3ee")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )
    if header and len(rows) > 1:
        style.add("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfdff")])
    table.setStyle(style)
    return table


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if not user or not verify_password(password, user["password_hash"]):
            flash("Invalid username or password.")
            return render_template("login.html", title=f"Login | {APP_NAME}")
        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome, {user['full_name']}!")
        return redirect(url_for("index"))

    return render_template("login.html", title=f"Login | {APP_NAME}")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    projects = fetch_all(
        """
        SELECT p.*, u.full_name AS owner_name
        FROM projects p
        JOIN users u ON u.id = p.owner_id
        WHERE p.owner_id = ?
        ORDER BY p.name COLLATE NOCASE
        """,
        (g.user["id"],),
    )
    return render_template("index.html", title=f"My Projects | {APP_NAME}", projects=projects)


@app.route("/projects/add", methods=["GET", "POST"])
@login_required
def add_project():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        point_of_contact = request.form.get("point_of_contact", "").strip()
        business_poc = request.form.get("business_point_of_contact", "").strip()

        if not name:
            flash("Project name is required.")
            return render_template("project_form.html", heading="Add Project", project=None)

        execute_db(
            """
            INSERT INTO projects (
                owner_id, name, description, start_date, end_date,
                point_of_contact, business_point_of_contact, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                g.user["id"],
                name,
                description,
                start_date,
                end_date,
                point_of_contact,
                business_poc,
                utcnow(),
            ),
        )
        flash("Project created successfully.")
        return redirect(url_for("index"))

    return render_template("project_form.html", title=f"Add Project | {APP_NAME}", heading="Add Project", project=None)


@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    return render_project_detail_page(project)


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        point_of_contact = request.form.get("point_of_contact", "").strip()
        business_poc = request.form.get("business_point_of_contact", "").strip()

        if not name:
            flash("Project name is required.")
            return render_template("project_form.html", heading="Edit Project", project=project)

        execute_db(
            """
            UPDATE projects
            SET name = ?, description = ?, start_date = ?, end_date = ?,
                point_of_contact = ?, business_point_of_contact = ?
            WHERE id = ? AND owner_id = ?
            """,
            (name, description, start_date, end_date, point_of_contact, business_poc, project_id, g.user["id"]),
        )
        flash("Project updated successfully.")
        return redirect(url_for("project_detail", project_id=project_id))

    return render_template("project_form.html", title=f"Edit Project | {APP_NAME}", heading="Edit Project", project=project)


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    documents = fetch_all("SELECT filename FROM documents WHERE project_id = ?", (project_id,))
    for doc in documents:
        remove_file_if_present(doc["filename"])

    execute_db("DELETE FROM projects WHERE id = ? AND owner_id = ?", (project_id, g.user["id"]))
    flash("Project deleted successfully.")
    return redirect(url_for("index"))


@app.route("/projects/<int:project_id>/issues/add", methods=["GET", "POST"])
@login_required
def add_issue(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    if request.method == "POST":
        sl_number = request.form.get("sl_number", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        owner = request.form.get("owner", "").strip()
        issue_date = request.form.get("issue_date", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not sl_number or not name:
            flash("SL Number and Issue Name are required.")
            return render_template(
                "issue_form.html",
                heading="Add Issue",
                project=project,
                issue=None,
                default_issue_owner=g.user["full_name"] or g.user["username"],
                default_issue_date=today_ymd(),
            )

        try:
            execute_db(
                """
                INSERT INTO issues (project_id, sl_number, name, description, owner, issue_date, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, int(sl_number), name, description, owner, issue_date, due_date, utcnow()),
            )
        except sqlite3.IntegrityError:
            flash("SL Number must be unique within a project.")
            return render_template(
                "issue_form.html",
                heading="Add Issue",
                project=project,
                issue=None,
                default_issue_owner=g.user["full_name"] or g.user["username"],
                default_issue_date=today_ymd(),
            )

        flash("Issue created successfully.")
        return redirect(url_for("project_detail", project_id=project_id))

    return render_template(
        "issue_form.html",
        title=f"Add Issue | {APP_NAME}",
        heading="Add Issue",
        project=project,
        issue=None,
        default_issue_owner=g.user["full_name"] or g.user["username"],
        default_issue_date=today_ymd(),
    )


@app.route("/projects/<int:project_id>/issues/<int:issue_id>/edit", methods=["GET", "POST"])
@login_required
def edit_issue(project_id, issue_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    issue = fetch_one("SELECT * FROM issues WHERE id = ? AND project_id = ?", (issue_id, project_id))
    if not issue:
        flash("Issue not found.")
        return redirect(url_for("project_detail", project_id=project_id))

    if request.method == "POST":
        sl_number = request.form.get("sl_number", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        owner = request.form.get("owner", "").strip()
        issue_date = request.form.get("issue_date", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not sl_number or not name:
            flash("SL Number and Issue Name are required.")
            return render_template(
                "issue_form.html",
                heading="Edit Issue",
                project=project,
                issue=issue,
                default_issue_owner=g.user["full_name"] or g.user["username"],
                default_issue_date=today_ymd(),
            )

        try:
            execute_db(
                """
                UPDATE issues
                SET sl_number = ?, name = ?, description = ?, owner = ?, issue_date = ?, due_date = ?
                WHERE id = ? AND project_id = ?
                """,
                (int(sl_number), name, description, owner, issue_date, due_date, issue_id, project_id),
            )
        except sqlite3.IntegrityError:
            flash("SL Number must be unique within a project.")
            return render_template(
                "issue_form.html",
                heading="Edit Issue",
                project=project,
                issue=issue,
                default_issue_owner=g.user["full_name"] or g.user["username"],
                default_issue_date=today_ymd(),
            )

        flash("Issue updated successfully.")
        return redirect(url_for("project_detail", project_id=project_id))

    return render_template(
        "issue_form.html",
        title=f"Edit Issue | {APP_NAME}",
        heading="Edit Issue",
        project=project,
        issue=issue,
        default_issue_owner=g.user["full_name"] or g.user["username"],
        default_issue_date=today_ymd(),
    )


@app.route("/projects/<int:project_id>/issues/<int:issue_id>/delete", methods=["POST"])
@login_required
def delete_issue(project_id, issue_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    execute_db("DELETE FROM issues WHERE id = ? AND project_id = ?", (issue_id, project_id))
    flash("Issue deleted successfully.")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/notes/add", methods=["POST"])
@login_required
def add_project_note(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    note = request.form.get("note", "").strip()
    note_description = request.form.get("note_description", "").strip()

    if not note:
        flash("Note is required.")
        return render_project_detail_page(project)

    execute_db(
        """
        INSERT INTO project_notes (project_id, note, note_description, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (project_id, note, note_description, utcnow()),
    )
    flash("Note added successfully.")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_project_note(project_id, note_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    cursor = execute_db("DELETE FROM project_notes WHERE id = ? AND project_id = ?", (note_id, project_id))
    if cursor.rowcount:
        flash("Note deleted successfully.")
    else:
        flash("Note not found.")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/documents/add", methods=["GET", "POST"])
@login_required
def add_document(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        upload = request.files.get("file")

        if not title:
            flash("Document title is required.")
            return render_template("document_form.html", heading="Add Document", project=project, document=None)

        filename, original_filename = save_uploaded_file(upload, g.user["id"])
        execute_db(
            """
            INSERT INTO documents (project_id, title, description, filename, original_filename, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, title, description, filename, original_filename, utcnow()),
        )
        flash("Document saved successfully.")
        return redirect(url_for("project_detail", project_id=project_id))

    return render_template("document_form.html", title=f"Add Document | {APP_NAME}", heading="Add Document", project=project, document=None)


@app.route("/projects/<int:project_id>/documents/<int:document_id>/edit", methods=["GET", "POST"])
@login_required
def edit_document(project_id, document_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    document = fetch_one("SELECT * FROM documents WHERE id = ? AND project_id = ?", (document_id, project_id))
    if not document:
        flash("Document not found.")
        return redirect(url_for("project_detail", project_id=project_id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        upload = request.files.get("file")

        if not title:
            flash("Document title is required.")
            return render_template("document_form.html", heading="Edit Document", project=project, document=document)

        filename = document["filename"]
        original_filename = document["original_filename"]

        if upload and upload.filename:
            new_filename, new_original = save_uploaded_file(upload, g.user["id"])
            remove_file_if_present(filename)
            filename = new_filename
            original_filename = new_original

        execute_db(
            """
            UPDATE documents
            SET title = ?, description = ?, filename = ?, original_filename = ?
            WHERE id = ? AND project_id = ?
            """,
            (title, description, filename, original_filename, document_id, project_id),
        )
        flash("Document updated successfully.")
        return redirect(url_for("project_detail", project_id=project_id))

    return render_template("document_form.html", title=f"Edit Document | {APP_NAME}", heading="Edit Document", project=project, document=document)


@app.route("/projects/<int:project_id>/documents/<int:document_id>/delete", methods=["POST"])
@login_required
def delete_document(project_id, document_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    document = fetch_one("SELECT * FROM documents WHERE id = ? AND project_id = ?", (document_id, project_id))
    if document:
        remove_file_if_present(document["filename"])
        execute_db("DELETE FROM documents WHERE id = ? AND project_id = ?", (document_id, project_id))
        flash("Document deleted successfully.")
    else:
        flash("Document not found.")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/documents/<int:document_id>/download")
@login_required
def download_document(document_id):
    document = get_owned_document(document_id)
    if not document:
        flash("Document not found.")
        return redirect(url_for("index"))

    if not document["filename"]:
        flash("No file is attached to this document entry.")
        return redirect(url_for("project_detail", project_id=document["project_id"]))

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        document["filename"],
        as_attachment=True,
        download_name=document["original_filename"] or document["filename"],
    )


@app.route("/projects/<int:project_id>/export/pdf")
@login_required
def export_project_pdf(project_id):
    project = get_owned_project(project_id)
    if not project:
        flash("Project not found.")
        return redirect(url_for("index"))

    issues = fetch_all("SELECT * FROM issues WHERE project_id = ? ORDER BY sl_number ASC, id ASC", (project_id,))
    documents = fetch_all("SELECT * FROM documents WHERE project_id = ? ORDER BY uploaded_at DESC, id DESC", (project_id,))
    notes = fetch_all("SELECT * FROM project_notes WHERE project_id = ? ORDER BY created_at DESC, id DESC", (project_id,))
    pdf_buffer = build_pdf(
        [],
        detailed_project=project,
        issues=issues,
        documents=documents,
        owner_name=g.user["full_name"],
        notes=notes,
    )

    safe_name = secure_filename(project["name"]) or "project"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{safe_name}_project_export.pdf",
    )


@app.route("/projects/export/pdf")
@login_required
def export_all_projects_pdf():
    projects = fetch_all(
        """
        SELECT p.*, u.full_name AS owner_name
        FROM projects p
        JOIN users u ON u.id = p.owner_id
        WHERE p.owner_id = ?
        ORDER BY p.name COLLATE NOCASE
        """,
        (g.user["id"],),
    )
    pdf_buffer = build_pdf(projects, owner_name=g.user["full_name"])
    safe_name = secure_filename(g.user["full_name"] or g.user["username"]) or "my_projects"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{safe_name}_my_projects_export.pdf",
    )


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_admin = 1 if request.form.get("is_admin") == "1" else 0

        if not full_name or not username or not password:
            flash("Full name, username, and password are required.")
        else:
            try:
                execute_db(
                    """
                    INSERT INTO users (username, full_name, password_hash, is_admin, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, full_name, hash_password(password), is_admin, utcnow()),
                )
                flash("User created successfully.")
                return redirect(url_for("manage_users"))
            except sqlite3.IntegrityError:
                flash("Username already exists.")

    users = fetch_all("SELECT * FROM users ORDER BY username COLLATE NOCASE")
    return render_template("manage_users.html", title=f"User Administration | {APP_NAME}", users=users)


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
