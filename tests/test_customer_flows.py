import io
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.models import Category
from contact.models import ContactMessage
from orders.models import Order, ProjectRequest
from payments.models import Payment, PaymentSettings

User = get_user_model()
TMP_MEDIA = tempfile.mkdtemp()


def png_file(name="proof.png"):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(
    MEDIA_ROOT=TMP_MEDIA,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class CustomerFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(email="c@example.com", password="StrongPass!123", name="Cust")
        self.admin = User.objects.create_user(email="a@example.com", password="StrongPass!123", name="Admin", is_staff=True)
        self.category = Category.objects.create(name="Python")
        PaymentSettings.objects.create(upi_id="shop@upi", upi_name="Shop")
        self.order = Order.objects.create(user=self.user, title="Demo", amount=Decimal("1500"), status="awaiting_payment")
        self.client.force_login(self.user)

    # ---- request form -------------------------------------------------
    def test_request_form_saves_redirects_and_shows_in_admin(self):
        data = {"request_type": "business", "academic_team_type": "single", "title": "CRM App",
                "required_features": "Login, reports"}
        resp = self.client.post(reverse("orders:request"), data)
        order = Order.objects.get(title="CRM App")
        self.assertRedirects(resp, reverse("orders:detail", args=[order.order_id]), fetch_redirect_response=False)
        self.assertTrue(ProjectRequest.objects.filter(title="CRM App", user=self.user).exists())
        # refreshing the redirected page never re-posts; a repeated POST does not duplicate
        self.client.post(reverse("orders:request"), data)
        self.assertEqual(Order.objects.filter(title="CRM App").count(), 1)
        # admin panel lists it
        self.client.force_login(self.admin)
        page = self.client.get(reverse("control:module", args=["requests"]))
        self.assertContains(page, "CRM App")

    def test_contact_form_saves_and_redirects(self):
        self.client.logout()
        resp = self.client.post(reverse("contact"), {"name": "N", "email": "n@x.com", "subject": "Hi", "message": "Hello"})
        self.assertRedirects(resp, reverse("contact"), fetch_redirect_response=False)
        self.assertTrue(ContactMessage.objects.filter(subject="Hi").exists())
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("control:module", args=["messages"])), "Hi")

    def test_html_is_not_cacheable(self):
        resp = self.client.get(reverse("orders:request"))
        self.assertIn("no-store", resp["Cache-Control"])

    # ---- payment flow -------------------------------------------------
    def test_payment_requires_screenshot_and_transaction_id(self):
        url = reverse("payments:pay", args=[self.order.order_id])
        self.client.post(url, {"transaction_id": "UTR123"})
        self.client.post(url, {"receipt": png_file()})
        self.assertEqual(Payment.objects.count(), 0)

    def test_payment_submit_redirects_and_queue_status(self):
        url = reverse("payments:pay", args=[self.order.order_id])
        detail = reverse("orders:detail", args=[self.order.order_id])
        self.assertContains(self.client.get(detail), "Complete Your Payment")
        resp = self.client.post(url, {"transaction_id": "UTR123", "receipt": png_file()})
        self.assertRedirects(resp, detail, fetch_redirect_response=False)
        pay = Payment.objects.get()
        self.assertEqual((pay.status, pay.transaction_id), ("submitted", "UTR123"))
        page = self.client.get(detail)
        self.assertContains(page, "Your Payment in Queue")
        self.assertNotContains(page, "Complete Your Payment")
        # opening the QR page again goes to Order Detail
        self.assertRedirects(self.client.get(url), detail, fetch_redirect_response=False)
        # a second POST cannot create another payment
        self.client.post(url, {"transaction_id": "UTR999", "receipt": png_file()})
        self.assertEqual(Payment.objects.count(), 1)

    def test_verified_status_and_rejected_resubmission(self):
        url = reverse("payments:pay", args=[self.order.order_id])
        detail = reverse("orders:detail", args=[self.order.order_id])
        pay = Payment.objects.create(order=self.order, user=self.user, amount=self.order.amount, status="failed")
        page = self.client.get(detail)
        self.assertContains(page, "Complete Your Payment")
        self.assertContains(page, "could not be verified")
        self.assertEqual(self.client.get(url).status_code, 200)  # may submit again
        pay.status = "verified"
        pay.save()
        page = self.client.get(detail)
        self.assertNotContains(page, "Your Payment in Queue")
        self.assertNotContains(page, "Complete Your Payment")
        self.assertRedirects(self.client.get(url), detail, fetch_redirect_response=False)

    def test_logged_in_user_is_redirected_from_login_page(self):
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 302)
