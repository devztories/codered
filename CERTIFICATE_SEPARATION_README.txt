CODERED INVENTIONS - CERTIFICATE SEPARATION

WEBSITE
- Certificate generation, preview, download, verification pages and design settings have been removed from the Django website.
- Customer Order Details retains a lightweight Request Certificate action after project completion and verified payment.
- The request only updates certificate_request_status and timestamps on the existing Order row. No PDF/image is created or uploaded.
- Admin dashboard has a Certificate Requests queue. Admin changes delivery status to Sent after sending the file manually through WhatsApp.
- The standalone generator is in certificate_generator/ and is not imported by Django.

OFFLINE GENERATOR
See certificate_generator/README.md.

MIGRATIONS
The certificate request fields already exist in orders migration 0003_certificate_request_workflow.py. No new database migration is needed for this separation.

VALIDATION
Python syntax compilation and a sample offline PDF generation were successful. Django system checks could not be run in this environment because Django is not installed. Run python manage.py check and python manage.py test in the project's configured environment before deployment.
