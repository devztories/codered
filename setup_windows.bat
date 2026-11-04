@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py check
echo.
echo Create an admin account when prompted.
python manage.py createsuperuser
if errorlevel 1 echo Superuser creation skipped or failed; run it manually later.
python manage.py runserver
