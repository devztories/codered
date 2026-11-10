"""Model events that create customer/admin notifications."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models import UserProfile
from chatbot.models import ChatMessage
from contact.models import ContactMessage
from orders.models import Order, OrderUpdate, OrderWorkUpdate, ProjectRequest
from payments.models import Payment
from reviews.models import Review

from .services import notify_admins, notify_user


@receiver(post_save, sender=get_user_model(), dispatch_uid="notifications_new_user")
def user_registered(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        notify_admins(
            "New customer registration",
            f"{instance.name or instance.email or instance.phone_number} has created an account.",
            "/admin/",
        )


@receiver(post_save, sender=ProjectRequest, dispatch_uid="notifications_project_request")
def project_request_created(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            "New project request",
            f"{instance.title} was submitted by {instance.user}.",
            "/admin/",
        )
        notify_user(
            instance.user,
            "Request received",
            f"We received your project request: {instance.title}. Our team will review it.",
            "/dashboard/",
        )


@receiver(post_save, sender=Order, dispatch_uid="notifications_order_saved")
def order_saved(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            "New order",
            f"Order {instance.order_id} was created by {instance.user}.",
            "/admin/",
        )
        notify_user(
            instance.user,
            "Order created",
            f"Your order {instance.order_id} has been created successfully.",
            "/dashboard/",
        )
        return
    old = getattr(instance, "_notification_old_values", {})
    if old:
        if old.get("status") != instance.status:
            notify_user(
                instance.user,
                "Order status updated",
                f"Order {instance.order_id}: {old.get('status', '').replace('_', ' ').title()} ΓåÆ {instance.get_status_display()}.",
                "/dashboard/",
            )
        if old.get("stage") != instance.stage:
            notify_user(
                instance.user,
                "Project progress updated",
                f"Order {instance.order_id} is now at: {instance.get_stage_display()}.",
                "/dashboard/",
            )
        if old.get("certificate_request_status") != instance.certificate_request_status:
            if instance.certificate_request_status in ("requested", "sent"):
                notify_user(
                    instance.user,
                    "Certificate update",
                    f"Certificate status for order {instance.order_id}: {instance.get_certificate_request_status_display()}.",
                    "/dashboard/",
                )


@receiver(pre_save, sender=Order, dispatch_uid="notifications_order_previous")
def order_previous_values(sender, instance, **kwargs):
    if instance.pk:
        instance._notification_old_values = sender.objects.filter(pk=instance.pk).values(
            "status", "stage", "certificate_request_status"
        ).first() or {}


@receiver(pre_save, sender=Payment, dispatch_uid="notifications_payment_previous")
def payment_previous_status(sender, instance, **kwargs):
    instance._notification_old_status = None
    if instance.pk:
        instance._notification_old_status = sender.objects.filter(pk=instance.pk).values_list(
            "status", flat=True
        ).first()


@receiver(post_save, sender=Payment, dispatch_uid="notifications_payment_saved")
def payment_saved(sender, instance, created, **kwargs):
    old_status = getattr(instance, "_notification_old_status", None)
    if not created and old_status == instance.status:
        return
    if instance.status == "submitted":
        notify_admins(
            "Payment proof submitted",
            f"{instance.user} submitted payment for order {instance.order.order_id}.",
            "/admin/",
        )
        notify_user(
            instance.user, "Payment submitted",
            f"Your payment proof for order {instance.order.order_id} was received.",
            "/dashboard/",
        )
    elif instance.status == "verified":
        notify_user(
            instance.user, "Payment verified",
            f"Your payment for order {instance.order.order_id} has been verified.",
            "/dashboard/",
        )
    elif instance.status == "failed":
        notify_user(
            instance.user, "Payment needs attention",
            f"Your payment for order {instance.order.order_id} was rejected. Please check your dashboard.",
            "/dashboard/",
        )


@receiver(post_save, sender=OrderUpdate, dispatch_uid="notifications_order_update")
def order_update_created(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.created_by and (instance.created_by.is_staff or instance.created_by.is_superuser):
        notify_user(
            instance.order.user, "Message from CodeRed team",
            f"New update on order {instance.order.order_id}: {instance.message}",
            "/dashboard/",
        )
    else:
        notify_admins(
            "New customer order message",
            f"{instance.order.user} sent an update on order {instance.order.order_id}.",
            "/admin/",
        )


@receiver(post_save, sender=OrderWorkUpdate, dispatch_uid="notifications_work_update")
def work_update_created(sender, instance, created, **kwargs):
    if created and instance.is_customer_visible:
        notify_user(
            instance.order.user, "Project progress update",
            f"{instance.order.order_id}: {instance.progress_percent}% complete. {instance.message}",
            "/dashboard/",
        )


@receiver(post_save, sender=ContactMessage, dispatch_uid="notifications_contact_message")
def contact_message_created(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            "New website enquiry",
            f"{instance.name} sent an enquiry: {instance.subject}.",
            "/admin/",
        )


@receiver(post_save, sender=Review, dispatch_uid="notifications_review_created")
def review_created(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            "New customer review",
            f"{instance.user} submitted a review: {instance.title}.",
            "/admin/",
        )


@receiver(post_save, sender=ChatMessage, dispatch_uid="notifications_chat_message")
def chat_message_created(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = instance.conversation
    if instance.sender == "user":
        notify_admins(
            "New chatbot message",
            f"{conversation.user or 'Website visitor'}: {instance.content[:180]}",
            "/admin/",
        )
    elif instance.sender == "admin" and conversation.user_id:
        notify_user(
            conversation.user, "Reply from CodeRed support",
            instance.content[:500], "/dashboard/",
        )
