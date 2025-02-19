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
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image

def generate_ticket_pdf(tickets):
    """Generate a well-structured ticket PDF with event images and sponsor logos."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    for ticket in tickets:
        # Draw the header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(100, 750, ticket.event.user.name)
        p.setFont("Helvetica", 10)
        p.drawString(100, 735, "Present this entire page at the Venue")

        
        # Draw Event Details
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 650, ticket.event.title)
        
        p.setFont("Helvetica", 12)
        details = [
            f"Date: {ticket.event.event_dates}",
            f"Time: {ticket.event.time_start.strftime('%I:%M %p')}",
            f"Venue: {ticket.event.venue_name}",
            f"Ticket Type: {ticket.ticket_type}",
            f"Purchased By: {ticket.user.email}",
            f"Purchase Date: {ticket.purchased_at.strftime('%Y-%m-%d %H:%M')}",
            f"Ticket ID: {ticket.id}",
        ]

        y_position = 620
        for line in details:
            p.drawString(100, y_position, line)
            y_position -= 20

       
        if ticket.qr_code:
            try:
                qr_image = Image.open(ticket.qr_code.path)
                qr_image = qr_image.resize((120, 120))
               

                p.drawInlineImage(qr_image, 400, 600, width=120, height=120)
            except Exception as e:
                p.drawString(400, 580, f"QR Code Error: {str(e)}")

        p.showPage()  # Move to next page for the next ticket
    
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