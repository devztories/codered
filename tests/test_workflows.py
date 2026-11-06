from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import Category
from orders.models import Order
from payments.models import Payment
from decimal import Decimal
User=get_user_model()
class PaymentCertificateTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user(email='customer@example.com',password='StrongPass!123',name='Customer')
  self.category=Category.objects.create(name='Python')
  self.order=Order.objects.create(user=self.user,title='Demo app',amount=Decimal('1000'))
 def test_manual_submission_does_not_unlock_certificate(self):
  p=Payment.objects.create(order=self.order,user=self.user,amount=Decimal('1000'),method='upi',status='submitted')
  self.assertEqual(self.order.status,'pending')
  self.assertFalse(self.order.payments.filter(status='verified').exists())
 def test_verified_payment_updates_order(self):
  p=Payment.objects.create(order=self.order,user=self.user,amount=Decimal('1000'),method='upi',status='verified')
  self.order.refresh_from_db()
  self.assertEqual(self.order.status,'paid')
  self.assertTrue(self.order.payments.filter(status='verified').exists())
 def test_certificate_request_requires_verified_payment_and_completion(self):
  self.client.force_login(self.user)
  self.order.stage = "completed"
  self.order.save(update_fields=["stage", "updated_at"])
  response=self.client.post(reverse('orders:certificate_request',args=[self.order.order_id]))
  self.assertEqual(response.status_code,302)
  self.order.refresh_from_db()
  self.assertEqual(self.order.certificate_request_status, "not_requested")
  Payment.objects.create(order=self.order,user=self.user,amount=Decimal('1000'),method='upi',status='verified')
  response=self.client.post(reverse('orders:certificate_request',args=[self.order.order_id]))
  self.assertEqual(response.status_code,302)
  self.order.refresh_from_db()
  self.assertEqual(self.order.certificate_request_status, "requested")

class AuthenticationRoutingTests(TestCase):
 def test_anonymous_project_request_redirects_to_namespaced_login(self):
  response=self.client.get(reverse('orders:request'))
  self.assertRedirects(response, '/accounts/login/?next=/orders/new/', fetch_redirect_response=False)

