import re

from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

from payments.models import Payment

from .models import Order, ProjectRequest


def _delete_stored_file(field_file):
    """Remove an uploaded file from storage; never block the delete if storage fails."""
    try:
        if field_file and field_file.name:
            field_file.storage.delete(field_file.name)
    except Exception:
        pass


@receiver(post_delete, sender=Order)
def remove_everything_related_to_deleted_order(sender, instance, **kwargs):
    """When an order is deleted (admin panel or Django admin) remove what it leaves behind.

    Payments, quotations, updates, work updates and assignments are already removed by
    the database cascade. The notifications that mention the order and the original
    project request are not, so they are removed here.
    """
    from notifications.models import Notification

    order_id = instance.order_id
    if order_id:
        mentions = rf"{re.escape(order_id)}(?!\d)"
        Notification.objects.filter(
            Q(url=f"/orders/{order_id}/")
            | Q(message__regex=mentions)
            | Q(title__regex=mentions)
        ).delete()

    if instance.request_id:
        ProjectRequest.objects.filter(pk=instance.request_id).delete()


@receiver(post_delete, sender=ProjectRequest)
def remove_request_reference_file(sender, instance, **kwargs):
    _delete_stored_file(instance.reference_file)


@receiver(post_delete, sender=Payment)
def remove_payment_receipt_file(sender, instance, **kwargs):
    _delete_stored_file(instance.receipt)
