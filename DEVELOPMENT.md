# CODERED INVENTIONS — Local Development First

This package is intended to be completed and tested locally before any hosting or deployment work.

## Local run (Windows PowerShell)

```powershell
cd .\codered_inventions
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` (HTTP, not HTTPS). Local `.env.example` enables Django DEBUG mode so local development does not force HTTPS. Do not use this development setting for a public production server.

## Configure UPI QR payment

1. Sign in to `/admin/` with a staff account.
2. Open **Payments → Payment settings** and add the single payment-settings record.
3. Enter the UPI ID and payee name, upload the official UPI QR image, and add payment instructions.
4. On checkout, customers scan the QR, pay in their UPI app, enter the transaction/reference ID and upload the payment screenshot.
5. In **Payments**, staff inspect the transaction and receipt, then use the verification action only after confirming the credit in the merchant's UPI/bank account.
6. Only verified payments mark the related order as paid. Submitted screenshots alone never mark an order as paid or unlock payment-gated certificates.

There is no online payment gateway flow in this development build; payments use the configured QR/UPI details and manual verification.

## Data preservation

Do not delete `db.sqlite3`, `media/`, or existing project files when updating the code. Back up the database and media directory before applying schema changes. Run `makemigrations` and `migrate` against the existing database; do not delete the database to resolve migration issues.
