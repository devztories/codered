from io import BytesIO

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import qrcode
from pathlib import Path

from orders.models import Order
from .models import Certificate, CertificateDesignSettings


class CertificateForm(forms.Form):
    recipient_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    project_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    completion_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))


@login_required
def index(request):
    orders = Order.objects.filter(user=request.user).filter(stage__in=["completed", "delivered"]).order_by("-created_at")
    certs = Certificate.objects.filter(user=request.user).select_related("order").order_by("-created_at")
    return render(request, "certificates/index.html", {"orders": orders, "certificates": certs})


@login_required
def generate(request, order_id):
    order = get_object_or_404(Order, user=request.user, order_id=order_id)
    if not order.payments.filter(status="verified").exists():
        messages.warning(request, "Complete your payment first to generate the certificate.")
        return redirect("payments:pay", order_id=order.order_id)
    if order.stage not in {"completed", "delivered"}:
        messages.info(request, "Your project certificate will be available after the project is marked completed.")
        return redirect("orders:detail", order_id=order.order_id)

    project_request = order.request
    group_names = []
    if project_request and project_request.request_type == "academic_custom" and project_request.academic_team_type == "group":
        group_names = [line.strip() for line in project_request.group_member_names.splitlines() if line.strip()]

    if group_names:
        existing = {c.recipient_name.casefold(): c for c in Certificate.objects.filter(order=order, revoked=False)}
        created = []
        for name in group_names:
            cert = existing.get(name.casefold())
            if not cert:
                cert = Certificate.objects.create(order=order, user=request.user, recipient_name=name,
                    project_name=order.title, completion_date=timezone.localdate())
            created.append(cert)
        messages.success(request, f"{len(created)} individual group certificates are ready.")
        return redirect("certificates:index")

    existing = Certificate.objects.filter(order=order, user=request.user, revoked=False).first()
    if existing:
        return redirect("certificates:download", certificate_id=existing.certificate_id)
    form = CertificateForm(request.POST or None, initial={
        "recipient_name": request.user.get_full_name() or getattr(request.user, "name", "") or request.user.get_username(),
        "project_name": order.title,
        "completion_date": timezone.localdate(),
    })
    if request.method == "POST" and form.is_valid():
        cert = Certificate.objects.create(order=order, user=request.user, **form.cleaned_data)
        return redirect("certificates:download", certificate_id=cert.certificate_id)
    return render(request, "certificates/form.html", {"form": form, "order": order})


@login_required
def download(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id, user=request.user, revoked=False)
    if not certificate.order.payments.filter(status="verified").exists():
        messages.warning(request, "Complete your payment first to download this certificate.")
        return redirect("payments:pay", order_id=certificate.order.order_id)

    image = _certificate_image(request, certificate)
    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG", optimize=True)
    image_buffer.seek(0)
    buffer = BytesIO()
    # Export as a true A4 portrait PDF (210 x 297 mm).
    image_buffer.seek(0)
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    pdf.drawImage(
        ImageReader(image_buffer),
        0,
        0,
        width=page_width,
        height=page_height,
        preserveAspectRatio=False,
        mask="auto",
    )
    pdf.showPage()
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{certificate.certificate_id}.pdf"'
    return response



def _certificate_image(request, certificate):
    """Render certificate details over the CodeRed black/red blank A4 artwork."""
    image_path = Path(__file__).resolve().parent / "assets" / "certificate_template.png"
    if not image_path.is_file():
        raise FileNotFoundError(f"Certificate artwork not found: {image_path}")

    image = Image.open(image_path).convert("RGB")
    settings_obj = CertificateDesignSettings.current()
    w, h = image.size
    sx, sy = w / 1055.0, h / 1491.0
    scale = (sx + sy) / 2
    draw = ImageDraw.Draw(image)

    white = "#f7f7f7"
    red = "#ff1724"
    gold = "#e7b83f"
    muted = "#d9d9df"

    def load_font(filename, size):
        candidates = [
            Path(__file__).resolve().parent / "assets" / filename,
            Path("/usr/share/fonts/truetype/dejavu") / filename,
            Path("/usr/share/fonts/truetype/liberation2") / filename,
        ]
        fp = next((candidate for candidate in candidates if candidate.exists()), None)
        if fp:
            return ImageFont.truetype(str(fp), max(8, int(size * scale)))
        return ImageFont.load_default()

    regular = load_font("DejaVuSans.ttf", 19)
    bold = load_font("DejaVuSans-Bold.ttf", 23)
    script = load_font("certificate_script.otf", 76)
    small = load_font("DejaVuSans.ttf", 15)
    small_bold = load_font("DejaVuSans-Bold.ttf", 16)

    def text_width(text, font):
        box = draw.textbbox((0, 0), str(text), font=font)
        return box[2] - box[0]

    def fit_font(text, font, max_width, min_size=12):
        path = getattr(font, "path", None)
        if not path:
            return font
        size = font.size
        while size > min_size and text_width(text, font) > max_width * sx:
            size -= 1
            font = ImageFont.truetype(path, size)
        return font

    def centered(text, y, font, fill=white, max_width=850):
        text = str(text or "")
        font = fit_font(text, font, max_width)
        width = text_width(text, font)
        x = (w - width) // 2
        draw.text((x, int(y * sy)), text, font=font, fill=fill)

    def centered_in_box(text, x1, x2, y, font, fill=white):
        text = str(text or "")
        font = fit_font(text, font, x2 - x1)
        width = text_width(text, font)
        x = int((x1 + x2) * sx / 2 - width / 2)
        draw.text((x, int(y * sy)), text, font=font, fill=fill)

    def wrap_lines(text, font, max_width):
        words = str(text or "").split()
        lines, line = [], ""
        for word in words:
            candidate = (line + " " + word).strip()
            if text_width(candidate, font) <= max_width * sx:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    def centered_paragraph(text, top, font, fill=white, max_width=820, line_gap=31, max_lines=4):
        lines = wrap_lines(text, font, max_width)[:max_lines]
        for index, line in enumerate(lines):
            centered(line, top + index * line_gap, font, fill, max_width)

    # Main editable content, positioned in the open center area of the artwork.
    centered(settings_obj.intro_text, 610, small_bold, muted, 650)
    centered(certificate.recipient_name, 650, script, red, 850)
    draw.line((int(150 * sx), int(725 * sy), int(905 * sx), int(725 * sy)),
              fill=gold, width=max(1, int(2 * scale)))
    centered(settings_obj.completion_text, 760, regular, white, 820)
    centered(f"“{certificate.project_name}”", 805, bold, white, 900)
    centered_paragraph(settings_obj.body_text, 855, regular, muted, 820, 31, 4)

    # Issue date and mentor details flank the central decorative seal.
    date_text = certificate.completion_date.strftime("%d %B %Y")
    date_font = fit_font(date_text, bold, 300)
    draw.text((int(105 * sx), int(1005 * sy)), date_text, font=date_font, fill=white)
    draw.line((int(95 * sx), int(1048 * sy), int(365 * sx), int(1048 * sy)),
              fill=red, width=max(2, int(3 * scale)))
    centered_in_box(settings_obj.issue_date_label, 95, 365, 1058, small, muted)

    signatory_name = (settings_obj.mentor_signature_text or "").strip()
    signature_added = False
    if settings_obj.mentor_signature_image:
        try:
            with settings_obj.mentor_signature_image.open("rb") as signature_file:
                signature = Image.open(signature_file).convert("RGBA")
                max_size = (max(1, int(250 * sx)), max(1, int(92 * sy)))
                signature.thumbnail(max_size, Image.Resampling.LANCZOS)
                signature_x = int(810 * sx - signature.width / 2)
                signature_y = int(940 * sy + (92 * sy - signature.height) / 2)
                image.paste(signature, (signature_x, signature_y), signature)
                signature_added = True
        except (OSError, ValueError):
            signature_added = False
    if not signature_added and signatory_name and signatory_name.casefold() != "project mentor":
        centered_in_box(signatory_name, 675, 945, 995, script, white)
    draw.line((int(675 * sx), int(1048 * sy), int(945 * sx), int(1048 * sy)),
              fill=red, width=max(2, int(3 * scale)))
    centered_in_box(settings_obj.mentor_title, 675, 945, 1058, small_bold, white)
    centered_in_box(settings_obj.company_name, 675, 945, 1087, small, muted)

    # Verification QR and certificate identifiers in the lower information band.
    verify_url = request.build_absolute_uri(
        f"/certificates/verify/{certificate.certificate_id}/"
    )
    qr = qrcode.QRCode(
        version=None,
        box_size=6,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = int(82 * scale)
    qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qx, qy = int(105 * sx), int(1300 * sy)
    image.paste(qr_image, (qx, qy))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (int(101 * sx), int(1296 * sy), int(105 * sx) + qr_size + int(8 * sx),
         int(1300 * sy) + qr_size + int(8 * sy)),
        radius=max(3, int(5 * scale)),
        outline=red,
        width=max(2, int(3 * scale)),
    )
    centered_in_box(settings_obj.verification_label, 85, 245, 1390, small, white)

    id_x = int(285 * sx)
    draw.text((id_x, int(1320 * sy)),
              f"Certificate ID  :  {certificate.certificate_id}",
              font=small, fill=white)
    draw.text((id_x, int(1360 * sy)),
              f"Company ID      :  {settings_obj.company_id}",
              font=small, fill=white)

    centered(
        f"{settings_obj.website}     |     {settings_obj.location}",
        1435, small, white, 760
    )
    return image


@login_required
def preview(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id,
                                    user=request.user, revoked=False)
    if not certificate.order.payments.filter(status="verified").exists():
        raise Http404("Certificate is not available.")
    image = _certificate_image(request, certificate)
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return HttpResponse(output.getvalue(), content_type="image/png")

def verify(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    valid = not certificate.revoked and certificate.order.payments.filter(status="verified").exists()
    return render(request, "certificates/verify.html", {"certificate": certificate, "valid": valid})
