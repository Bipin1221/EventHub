import qrcode
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

def generate_qr_code(ticket):
    """Generate QR code with ticket details."""
    qr_data = (
        f"Ticket ID: {ticket.id}\n"
        f"Event: {ticket.event.title}\n"
        f"User: {ticket.user.email}\n"
        f"Type: {ticket.ticket_type}"
    )
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), f"qr_{ticket.id}.png")

def generate_ticket_pdf(tickets):
    """Generate PDF with one page per ticket."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    for ticket in tickets:
        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, "Event Ticket")
        
        # Ticket Details
        p.setFont("Helvetica", 12)
        details = [
            f"Event: {ticket.event.title}",
            f"Date: {ticket.event.event_dates}",
            f"Time: {ticket.event.time_start}",
            f"Venue: {ticket.event.venue_name}",
            f"Ticket Type: {ticket.ticket_type}",
            f"Purchased By: {ticket.user.email}",
            f"Purchase Date: {ticket.purchased_at.strftime('%Y-%m-%d %H:%M')}",
            f"Ticket ID: {ticket.id}"
        ]
        
        y = 750
        for line in details:
            p.drawString(100, y, line)
            y -= 20
        
        # QR Code
        if ticket.qr_code:
            try:
                img = Image.open(ticket.qr_code.path)
                img = img.resize((120, 120))
                p.drawInlineImage(img, 400, 650, width=120, height=120)
            except Exception as e:
                p.drawString(100, 600, f"QR Code Error: {str(e)}")
        
        p.showPage()
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def send_ticket_email(tickets):
    """Send email with attached PDF of tickets."""
    try:
        if not tickets:
            logger.warning("No tickets provided for email")
            return

        # Validate tickets belong to the same user/event
        user = tickets[0].user
        event = tickets[0].event
        for ticket in tickets[1:]:
            if ticket.user != user or ticket.event != event:
                raise ValueError("All tickets must belong to the same user and event")

        # Build email
        email = EmailMessage(
            subject=f"Your {len(tickets)} Ticket(s) for {event.title}",
            body=(
                f"Hello {user.name},\n\n"
                f"Attached are your {len(tickets)} ticket(s) for:\n"
                f"Event: {event.title}\n"
                f"Date: {event.event_dates}\n"
                f"Venue: {event.venue_name}\n\n"
                "Thank you for your purchase!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        # Attach PDF
        pdf = generate_ticket_pdf(tickets)
        email.attach(
            f"tickets_{event.id}.pdf",
            pdf,
            "application/pdf"
        )
        
        email.send(fail_silently=False)
        logger.info(f"Sent {len(tickets)} tickets to {user.email}")

    except Exception as e:
        logger.error(f"Failed to send tickets: {str(e)}", exc_info=True)
        raise Exception("Failed to send tickets")