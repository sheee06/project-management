# Software Project Management Tool - Design Document

## 1. Purpose

Software Project Management Tool is a browser-based Python application for managing software projects, issues, project notes, and project documents in a multi-user environment.

This version adds:

- secure login support
- administrator account provisioning during startup
- admin-managed user creation
- per-user project isolation
- project notes for project-specific updates and reminders
- PDF export for project data

## 2. Business Requirements

The application shall support the following:

1. Users can log in through a browser.
2. A default administrator account shall be provisioned during application startup.
3. Administrator users can create additional users.
4. Each user can create, update, delete, and view only their own projects.
5. Each project can contain issues, notes, and project documents.
6. Issues can be added, updated, and deleted.
7. Project notes can be added and deleted.
8. Project documents can be added, updated, deleted, uploaded, and downloaded.
9. Users cannot see or download other users' project data.
10. The application can export project details to PDF.

## 3. Solution Overview

The solution is implemented as a Flask web application using SQLite for persistence and ReportLab for PDF generation.

### Major modules

- Web UI and routing: Flask
- Authentication and sessions: Flask session + password hashing
- Database: SQLite
- File storage: local uploads directory
- PDF export: ReportLab

## 4. Application Name

The application name is:

**Software Project Management Tool**

This name appears in:
- browser page title
- login page
- navigation bar
- generated PDF exports
- design and readme documentation

## 5. User Roles

### 5.1 Administrator
Administrator users can:

- log in
- create other users
- manage their own projects
- manage notes within their own projects
- export their own project data to PDF

Administrator users cannot browse other users' projects in this implementation.

### 5.2 Standard User
Standard users can:

- log in
- manage their own projects
- manage project notes within their projects
- manage issues within their projects
- manage project documents within their projects
- export their own project data to PDF

## 6. Functional Design

This section describes the primary user workflows, the data captured by each workflow, and the main business rules applied by the application.

## 6.1 Login

### Features
- login page at `/login`
- logout endpoint
- session-based login
- default admin user auto-created during startup

### Security behavior
- passwords are stored as hashes, not plain text
- failed login shows an error message
- unauthenticated users are redirected to login

## 6.2 User Administration

### Features
- admin-only page at `/admin/users`
- create new users
- assign role:
  - Standard User
  - Administrator

### Fields
- Full Name
- Username
- Password
- Role

## 6.3 Project Management

### Features
- add project
- edit project
- delete project
- list projects in table format
- open project details page

### Project fields
- Project Name
- Project Description
- Start Date
- End Date
- Point of Contact
- Business Point of Contact

### Ownership
Every project is linked to exactly one owner user.

## 6.4 Project Notes

### Features
- add multiple notes from the project details page
- list notes in reverse chronological order
- delete notes directly from the notes table
- include project notes in single-project PDF exports

### Note fields
- Note
- Note Description
- Added On

### Behavior
Each note is associated with exactly one project and is visible only to the owner of that project.

## 6.5 Issue Management

### Features
- add issue
- edit issue
- delete issue

### Issue fields
- SL Number
- Issue Name
- Issue Description

### Rule
`SL Number` must be unique within the same project.

## 6.6 Project Document Management

### Features
- add document record
- edit document record
- delete document record
- upload file
- replace file
- download file

### Document fields
- Document Title
- Document Description
- Uploaded File
- Original File Name
- Upload Timestamp

### Security
A document can only be downloaded by the owner of the associated project.

## 6.7 PDF Export

### Features
- export one project as PDF
- export all projects owned by the current user as PDF

### Single-project PDF includes
- project summary
- project notes table
- issues table
- project documents table

### Portfolio PDF includes
- project list summary table for the logged-in user

## 7. Non-Functional Design

### 7.1 Security
- session-based authentication
- hashed passwords
- route protection using decorators
- project ownership checks on every project, issue, note, document, download, and export route

### 7.2 Usability
- browser-based interface
- responsive layout
- direct action buttons for add, edit, delete, export
- flash messages for user feedback

### 7.3 Maintainability
- all HTML templates kept in a template dictionary for simple deployment
- database helper functions isolated
- route structure grouped by entity

### 7.4 Simplicity
The application uses SQLite and local uploads for ease of setup and local execution.

## 8. Technical Architecture

## 8.1 Runtime Components

1. **Browser**
   - sends HTTP requests
   - renders HTML pages

2. **Flask Application**
   - handles routes
   - enforces authentication
   - applies ownership rules
   - renders UI
   - generates PDFs

3. **SQLite Database**
   - stores users, projects, issues, notes, documents

4. **Uploads Folder**
   - stores physical files uploaded for project documents

## 8.2 Request Flow

1. User logs in.
2. Flask stores `user_id` in session.
3. User requests a page.
4. `before_request` loads the current user into `g.user`.
5. Protected route checks login.
6. Project-specific route checks ownership by filtering on `owner_id`.
7. Result is displayed or rejected.
8. For PDF export, the app reads the user-owned data and generates a PDF in memory.

## 9. Data Model

## 9.1 Users Table

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| username | TEXT | Unique |
| full_name | TEXT | Display name |
| password_hash | TEXT | PBKDF2 hash |
| is_admin | INTEGER | 1 = admin, 0 = standard |
| created_at | TEXT | UTC timestamp |

## 9.2 Projects Table

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| owner_id | INTEGER | FK to users.id |
| name | TEXT | Required |
| description | TEXT | Optional |
| start_date | TEXT | Optional |
| end_date | TEXT | Optional |
| point_of_contact | TEXT | Optional |
| business_point_of_contact | TEXT | Optional |
| created_at | TEXT | UTC timestamp |

## 9.3 Issues Table

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| project_id | INTEGER | FK to projects.id |
| sl_number | INTEGER | Required, unique within project |
| name | TEXT | Required |
| description | TEXT | Optional |
| created_at | TEXT | UTC timestamp |

## 9.4 Documents Table

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| project_id | INTEGER | FK to projects.id |
| title | TEXT | Required |
| description | TEXT | Optional |
| filename | TEXT | Stored file name on disk |
| original_filename | TEXT | Original uploaded name |
| uploaded_at | TEXT | UTC timestamp |

## 9.5 Project Notes Table

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| project_id | INTEGER | FK to projects.id |
| note | TEXT | Required |
| note_description | TEXT | Optional |
| created_at | TEXT | UTC timestamp |

## 10. Authorization Model

Authorization is owner-based.

- The logged-in user can only access projects where `projects.owner_id = current_user.id`.
- Issue operations only work when the parent project belongs to the logged-in user.
- Project note operations only work when the parent project belongs to the logged-in user.
- Document operations and downloads only work when the parent project belongs to the logged-in user.
- PDF exports only include data owned by the logged-in user.

This prevents cross-user data exposure.

## 11. Persistence Design

### Structured data
Stored in local SQLite database file:

`software_project_management_tool.db`

### Uploaded files
Stored in local directory:

`uploads/`

### File naming
Uploaded files are renamed using:
- user identifier
- UUID
- safe original filename

This avoids collisions and reduces risk from unsafe file names.

## 12. Main Routes

| Route | Method | Description |
|---|---|---|
| `/login` | GET, POST | Login |
| `/logout` | GET | Logout |
| `/` | GET | User project list |
| `/projects/add` | GET, POST | Add project |
| `/projects/<id>` | GET | Project detail |
| `/projects/<id>/edit` | GET, POST | Edit project |
| `/projects/<id>/delete` | POST | Delete project |
| `/projects/<id>/issues/add` | GET, POST | Add issue |
| `/projects/<id>/issues/<issue_id>/edit` | GET, POST | Edit issue |
| `/projects/<id>/issues/<issue_id>/delete` | POST | Delete issue |
| `/projects/<id>/notes/add` | POST | Add project note |
| `/projects/<id>/notes/<note_id>/delete` | POST | Delete project note |
| `/projects/<id>/documents/add` | GET, POST | Add document |
| `/projects/<id>/documents/<document_id>/edit` | GET, POST | Edit document |
| `/projects/<id>/documents/<document_id>/delete` | POST | Delete document |
| `/documents/<document_id>/download` | GET | Secure download |
| `/projects/<id>/export/pdf` | GET | Export one project to PDF |
| `/projects/export/pdf` | GET | Export all user projects to PDF |
| `/admin/users` | GET, POST | Admin user management |

## 13. Startup Behavior

During application startup:

1. Database tables are created if they do not already exist.
2. A default administrator account is created if not already present.
3. Upload folder is created if missing.

## 14. Error Handling

The application uses flash messages for:
- invalid login
- duplicate username
- duplicate SL number in a project
- missing required project notes
- missing required fields
- missing or inaccessible projects/documents

## 15. Limitations

Current design intentionally keeps the implementation simple.

### Current limitations
- no password reset workflow
- no user delete/edit workflow
- no project sharing between users
- no audit trail
- local file storage only
- local SQLite database only
- no CSRF protection yet
- no API layer

## 16. Recommended Future Enhancements

1. Add password change and reset capability
2. Add issue priority and status
3. Add search and filtering
4. Add dashboard metrics
5. Add PostgreSQL support for production
6. Add role-based administration beyond simple admin flag
7. Add backup and restore tooling
8. Add activity history / audit logging
9. Add email notifications
10. Add document preview

## 17. Deployment Notes

For production:
- use Gunicorn or Waitress
- place behind reverse proxy
- set a strong `SPMT_SECRET_KEY`
- use HTTPS
- consider PostgreSQL instead of SQLite
- store uploads on managed storage if needed

## 18. Summary

This design delivers a practical multi-user project management application with:

- browser-based access
- secure login
- admin user management
- per-user project isolation
- project notes
- issue and document management
- PDF export
- simple local deployment
