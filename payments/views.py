from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import FileResponse, Http404
from django.views.decorators.http import require_http_methods
from PIL import Image, UnidentifiedImageError

from orders.models import Order
from .models import Payment, PaymentSettings

MAX_RECEIPT_SIZE = 5 * 1024 * 1024
ALLOWED_RECEIPT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@login_required
@require_http_methods(["GET", "POST"])
def pay(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.status in {"paid", "completed", "delivered"}:
        messages.info(request, "This order is already marked as paid.")
        return redirect("orders:detail", order_id=order.order_id)

    if request.method == "POST":
        receipt = request.FILES.get("receipt")
        transaction_id = request.POST.get("transaction_id", "").strip()[:120]

        has_receipt = bool(receipt)
        has_utr = bool(transaction_id)
        if not has_receipt and not has_utr:
            messages.error(request, "Submit either a payment screenshot or the UPI UTR / transaction number.")
        elif receipt and receipt.size > MAX_RECEIPT_SIZE:
            messages.error(request, "The payment screenshot must be 5 MB or smaller.")
        elif receipt and getattr(receipt, "content_type", "") not in ALLOWED_RECEIPT_TYPES:
            messages.error(request, "Upload a JPG, PNG or WEBP payment screenshot.")
        elif receipt and not _is_valid_image(receipt):
            messages.error(request, "The uploaded file is not a valid image.")
        else:
            Payment.objects.create(
                order=order,
                user=request.user,
                amount=order.amount,
                method="upi",
                status="submitted",
                receipt=receipt,
                transaction_id=transaction_id,
            )
            return redirect(f"/orders/{order.order_id}/?payment_review=1")

    payment_settings = PaymentSettings.objects.first()
    upi_id = (payment_settings.upi_id if payment_settings else "") or settings.COMPANY_UPI_ID
    qr_code = bool(payment_settings and payment_settings.qr_code)
    return render(
        request,
        "payments/pay.html",
        {
            "order": order,
            "payment_settings": payment_settings,
            "upi_id": upi_id,
            "payment_ready": bool(upi_id or qr_code),
            "upi_name": (payment_settings.upi_name if payment_settings else "") or settings.COMPANY_UPI_NAME,
        },
    )


def _is_valid_image(uploaded_file):
    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as image:
            image.verify()
        uploaded_file.seek(0)
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        uploaded_file.seek(0)
        return False


@login_required
def download_qr(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    payment_settings = PaymentSettings.objects.first()
    if not payment_settings or not payment_settings.qr_code:
        raise Http404("Payment QR is not configured.")
    try:
        payment_settings.qr_code.open("rb")
    except (OSError, ValueError):
        raise Http404("Payment QR is unavailable.")
    filename = "CODERED-UPI-QR"
    suffix = (payment_settings.qr_code.name.rsplit(".", 1)[-1] or "png").lower()
    return FileResponse(payment_settings.qr_code, as_attachment=True, filename=f"{filename}.{suffix}")
