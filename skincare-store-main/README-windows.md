````markdown
# Novacell (Windows) — Quick Start

## Prerequisites
- Python 3.9+ (installed and on `PATH`)
- Node.js + npm
- PostgreSQL (local) — install using the official installer or Chocolatey
- VS Code (optional)

## PostgreSQL on Windows (examples)

- Install PostgreSQL using the official installer from https://www.postgresql.org/download/windows/ or use Chocolatey: `choco install postgresql`
- Ensure PostgreSQL server is running (Services or pg_ctl). Example (PowerShell, if PostgreSQL was installed as a service):
   ```powershell
   Start-Service -Name postgresql
   ```
   Or use the pgAdmin/installer-provided service name shown in Services.

## Backend (Django with PostgreSQL)
1. Open PowerShell in `backend\`
2. Create & activate venv (PowerShell):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   Or for Command Prompt (cmd.exe):
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install Python deps:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create a `.env` file (there is a template). Example contents (PostgreSQL):
   ```text
   POSTGRES_DB=skincare_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=yourpassword
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   DJANGO_SECRET=change-me
   JWT_SECRET=change-me-jwt
   ```
5. Create database migrations and seed products (optional):
   ```powershell
   # create and apply migrations
   python manage.py makemigrations
   python manage.py migrate

   # seed sample products
   python seed_products.py
   ```
6. Run Django server:
   ```powershell
   python manage.py runserver 8000
   ```
   API base: http://localhost:8000/api/

## Frontend (React)
1. Open a new PowerShell in `frontend\`
2. Install node deps:
   ```powershell
   npm install
   ```
3. Run dev server:
   ```powershell
   npm start
   ```
   App: http://localhost:3000

## Notes
- This is a prototype. Passwords are stored plaintext in the database — for production use hashing.
- If CORS errors appear, ensure backend is running and `CORS_ALLOW_ALL_ORIGINS = True` is set in `skincare_backend/settings.py` for development only.

````
