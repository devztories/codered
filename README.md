# CODERED INVENTIONS — Complete Django Project

A modular Django website and customer project-management portal for CODERED INVENTIONS.

## Included modules

- Public website: Home, About, Services, Projects, FAQ, Contact and Payment Information
- Customer accounts: registration, email/phone login, profile and password reset
- Dynamic project categories, project catalogue and service management
- Project requests, quotations, order history and four-stage project tracking
- UPI QR payments with transaction ID and receipt upload, followed by manual admin verification
- Payment-gated project completion certificates with PDF generation and public verification
- Customer reviews, support chat, notifications and staff administration
- Responsive black/red/white branding and homepage section navigation

## Development-first workflow

Complete and verify the application locally before considering hosting. Deployment is intentionally deferred. See [DEVELOPMENT.md](DEVELOPMENT.md) for the exact local setup and UPI QR payment configuration.

## Requirements

- Python 3.10 or newer
- pip
- SQLite for local development
- PostgreSQL recommended for production

## Windows — first-time setup

1. Extract this ZIP.
2. Open the extracted `codered_inventions` folder in VS Code or Command Prompt.
3. Run `setup_windows.bat`, or execute these commands manually:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py runserver
```

If `.env` already exists, keep your own credentials; do not overwrite it.

Open website: http://127.0.0.1:8000/  
Admin: http://127.0.0.1:8000/admin/  
Login: http://127.0.0.1:8000/accounts/login/

## macOS / Linux — first-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py runserver
```

## Existing database / upgrading

**Back up `db.sqlite3` and the `media/` folder before replacing project files.**

Then activate your virtual environment and run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py sync_order_stage
```

The `sync_order_stage` command is a compatibility helper for an older database where the order tracking field was not migrated. If the field is already present, it does nothing. Do not delete your existing database to fix a migration error.

## Four-stage project tracking

Every new order starts at **Project Discussed**. The customer dashboard and order details display:

1. Project Discussed
2. Project Started
3. Completed
4. Delivered

Staff can change the current stage in Django Admin → Orders. The tracker reflects the saved order stage.

## Admin usage

Create a superuser, sign in at `/admin/`, and manage projects, categories, services, orders, payments, certificates, reviews, enquiries, chat conversations and related records. Only authorized staff should receive staff access.

## Environment configuration

For local development, edit `.env` only when needed. Never commit `.env` or expose API secrets in frontend code. Configure `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS`, SMTP settings, AI provider URL/model/API key, company UPI details and WhatsApp number.

## Important payment and certificate notes

- Manual UPI receipts remain submitted until a staff member verifies them.
- A certificate is available only when the corresponding order has a verified payment.
- Certificates are company-issued project completion certificates, not accredited academic qualifications.

## Production checklist

- Use a strong, unique `SECRET_KEY` and `DEBUG=False`.
- Configure HTTPS, secure cookies, allowed hosts and CSRF trusted origins.
- SQLite and local media storage are used during development.
- Configure SMTP and verify the UPI QR, UPI ID and manual payment-review workflow.
- Set up database/media backups, monitoring and log retention.
- Review privacy, terms, refund policy, permissions and upload limits.
- Deployment preparation is intentionally deferred until local development is complete.

## Tests and checks

```bash
python manage.py check
python manage.py test
```

Django tests require the dependencies in `requirements.txt` to be installed.

## Business and Academic Project Store

The catalogue supports two project types, configured from Django Admin:

- **Business Project** — custom business software and website requests.
- **Academic Project** — includes build-your-own requests and ready-made projects.

For a ready-made academic project, set `Project type = Academic`, enable `Ready-made project`, set its `Price`, and publish it. The public project detail page then offers **Buy now** (manual UPI QR payment) and, when enabled, **Add features / Customize**. A direct purchase creates an order at the listed price and opens the existing UPI payment flow.

For a new academic project, customers use **Build your own project** and submit the project name, features, budget, deadline, technologies and optional reference file. Business project requests use the same request form with the Business type. These custom requests enter admin review; the submitted budget is stored as a requested budget and is not treated as an approved payable amount.

### Upgrade an existing local copy

Back up `db.sqlite3` and `media/` first. Then activate the project's virtual environment and run:

```bat
python manage.py makemigrations catalog orders
python manage.py migrate
python manage.py check
```

In `/admin/`, edit or add Projects and set the project type, ready-made toggle, listed price, customization availability and publish status. The catalogue displays the configured project price to visitors.

## Custom Admin Control Panel

A custom responsive staff dashboard is available at `/control/` (sign in with a Django staff/superuser account). It includes overview metrics and custom module pages for Projects, Project Requests, Orders, Payments, Users, Categories, Enquiries, Reviews and Certificates. Record edit/view actions open the corresponding Django admin edit form; the `Full management` link opens the full Django admin list with its filters and bulk actions. The original Django admin remains available at `/admin/`.

To create an administrator locally:

```bash
python manage.py createsuperuser
```


## Notifications

See [NOTIFICATIONS_SETUP.md](NOTIFICATIONS_SETUP.md) for the customer/admin website notification system and WhatsApp Cloud API setup.
