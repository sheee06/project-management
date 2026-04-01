# Software Project Management Tool

A browser-based Python server application for managing software projects, issues, project documents, user logins, and PDF exports.

## Core Features

### Project Management
- Add, edit, delete projects
- View projects in a table
- Open a project to manage issues and documents

### Project Fields
- Project Name
- Project Description
- Start Date
- End Date
- Point of Contact
- Business Point of Contact

### Issue Management
- Add, edit, delete issues
- Fields:
  - SL Number
  - Issue Name
  - Issue Description

### Project Document Management
- Add, edit, delete document records
- Upload files
- Replace uploaded files
- Download files securely
- Document visibility restricted to the owner of the project

### User Management
- Login and logout
- Administrator can create new users
- Every project belongs to exactly one user
- Users can only see their own projects, issues, and uploaded documents

### PDF Export
- Export one project into PDF
- Export all projects owned by the current user into PDF

## Default Admin User

The application automatically creates this user during first startup if it does not already exist:

- Username: `Sheeba`
- Password: `Sheeba`

## Technology Stack

- Python
- Flask
- SQLite
- ReportLab

## Project Structure

- `app.py` - main Flask server application
- `requirements.txt` - Python dependencies
- `uploads/` - uploaded files
- `software_project_management_tool.db` - SQLite database created at runtime
- `Software_Project_Management_Tool_Design_Document.docx` - design document
- `Software_Project_Management_Tool_Design_Document.md` - markdown design document

## How to run

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Important behavior

- The application uses a local SQLite database file named `software_project_management_tool.db`.
- Uploaded files are stored in the `uploads/` folder.
- A user can only access their own projects and documents.
- Even the administrator uses the same project privacy rule; admin privileges are for user administration.

## Production note

For production use, place the app behind a production WSGI server such as Gunicorn or Waitress and set a strong `SPMT_SECRET_KEY` environment variable.
