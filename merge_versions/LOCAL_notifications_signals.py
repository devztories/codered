from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from accounts.models import User, UserProfile
from contact.models import ContactMessage
from orders.models import Order, OrderUpdate, OrderWorkUpdate
from payments.models import Payment
from reviews.models import Review
from chatbot.models import ChatMessage

from .services import notify_admins, notify_customer


@receiver(post_save, sender=User)
def user_created_notification(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        notify_admins(
            "New customer registration",
            f"{instance.name or instance.email or instance.phone_number} created an account.",
            "/admin/",
        )


@receiver(pre_save, sender=Order)
def remember_order_status(sender, instance, **kwargs):
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).only(
            "status", "certificate_request_status"
        ).first()
        instance._notification_old_status = old.status if old else None
        instance._notification_old_certificate_status = (
            old.certificate_request_status if old else None
        )
    else:
        instance._notification_old_status = None
        instance._notification_old_certificate_status = None


@receiver(post_save, sender=Order)
def order_notifications(sender, instance, created, **kwargs):
    if created:
        if instance.request_id:
            title = "New project request"
            detail = f"{instance.user} submitted: {instance.title} ({instance.order_id})."
            customer_title = "Project request received"
            customer_message = (
                f"We received your request for {instance.title}. "
                "Our team will review it and update its status."
            )
        else:
            title = "New order"
            detail = f"{instance.user} placed {instance.order_id}: {instance.title}."
            customer_title = "Order created"
            customer_message = f"Your order {instance.order_id} has been created."
        notify_admins(title, detail, "/admin/")
        notify_customer(
            instance.user,
            customer_title,
            customer_message,
            f"/orders/{instance.order_id}/",
        )
        return

    old_status = getattr(instance, "_notification_old_status", None)
    if old_status and old_status != instance.status:
        label = instance.get_status_display()
        notify_customer(
            instance.user,
            "Project status updated",
            f"Your project {instance.order_id} is now: {label}.",
            f"/orders/{instance.order_id}/",
        )

    old_certificate = getattr(instance, "_notification_old_certificate_status", None)
    if old_certificate and old_certificate != instance.certificate_request_status:
        label = instance.get_certificate_request_status_display()
        notify_customer(
            instance.user,
            "Certificate status updated",
            f"Certificate request for {instance.order_id}: {label}.",
            f"/orders/{instance.order_id}/",
        )


@receiver(pre_save, sender=Payment)
def remember_payment_status(sender, instance, **kwargs):
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).only("status").first()
        instance._notification_old_status = old.status if old else None
    else:
        instance._notification_old_status = None


@receiver(post_save, sender=Payment)
def payment_notifications(sender, instance, created, **kwargs):
    order_url = f"/orders/{instance.order.order_id}/"
    if created and instance.status == "submitted":
        notify_admins(
            "Payment proof submitted",
            f"{instance.user} submitted payment proof for {instance.order.order_id} (Γé╣{instance.amount}).",
            "/admin/",
        )
        notify_customer(
            instance.user,
            "Payment proof received",
            f"We received your payment proof for {instance.order.order_id}. It is awaiting verification.",
            order_url,
        )
        return

    old_status = getattr(instance, "_notification_old_status", None)
    if old_status and old_status != instance.status:
        label = instance.get_status_display()
        notify_customer(
            instance.user,
            "Payment status updated",
            f"Payment for {instance.order.order_id} is now: {label}.",
            order_url,
        )


@receiver(post_save, sender=ContactMessage)
def contact_message_notification(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            "New website enquiry",
            f"{instance.name} sent an enquiry: {instance.subject}.",
            "/admin/",
        )


@receiver(post_save, sender=Review)
def review_notification(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            "New customer review",
            f"{instance.user} submitted a review: {instance.title}.",
            "/admin/",
        )


@receiver(post_save, sender=OrderWorkUpdate)
def work_update_notification(sender, instance, created, **kwargs):
    if created and instance.is_customer_visible:
        notify_customer(
            instance.order.user,
            "Project progress updated",
            f"{instance.order.order_id}: {instance.progress_percent}% complete. {instance.message}",
            f"/orders/{instance.order.order_id}/",
        )


@receiver(post_save, sender=OrderUpdate)
def order_message_notification(sender, instance, created, **kwargs):
    if created and instance.created_by_id:
        author = instance.created_by
        if author.is_staff or author.is_superuser:
            notify_customer(
                instance.order.user,
                "New message from CODERED INVENTIONS",
                instance.message,
                f"/orders/{instance.order.order_id}/",
            )
        else:
            notify_admins(
                "New customer message",
                f"{author} sent a message about {instance.order.order_id}: {instance.message[:180]}",
                "/admin/",
            )


@receiver(post_save, sender=ChatMessage)
def chat_message_notification(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = instance.conversation
    customer = conversation.user

    if instance.sender == "user":
        name = (
            customer.name or customer.email or customer.phone_number
            if customer else "Website visitor"
        )
        notify_admins(
            "New customer chat message",
            f"{name}: {instance.content[:220]}",
            "/admin/",
        )
    elif instance.sender == "admin" and customer:
        notify_customer(
            customer,
            "New message from CODERED INVENTIONS",
            instance.content,
            "/dashboard/",
        )
