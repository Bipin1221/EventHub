import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.exceptions import ValidationError

from django.core.mail import EmailMessage
from django.conf import settings
from django.core.mail import EmailMessage

import logging

def generate_qr_code(ticket):
    """Generates and returns a QR code for the ticket."""
    qr_data = f"Ticket ID: {ticket.id}, User: {ticket.user.email}, Event: {ticket.event.title}"
    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")  # Specify the format (PNG)
    buffer.seek(0)

    filename = f"qr_{ticket.id}.png"  # Filename with ticket ID
    return ContentFile(buffer.getvalue(), filename)

from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
from io import BytesIO
import logging
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

logger = logging.getLogger(__name__)



# def generate_ticket_pdf(ticket):
#     """Generates a ticket PDF with event details and QR code for each ticket."""
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)

#     for _ in range(ticket.quantity):  # Generate a page for each ticket
#         p.setFont("Helvetica-Bold", 16)
#         p.drawString(100, 800, "Event Ticket")
#         p.setFont("Helvetica", 12)

#         # Ticket details
#         details = [
#             f"Event: {ticket.event.title}",
#             f"Date: {ticket.event.event_dates}",
#             f"Time: {ticket.event.time_start}",
#             f"Venue: {ticket.event.venue_name}",
#             f"Ticket Type: {ticket.ticket_type}",
#             f"Purchased By: {ticket.user.email}",
#             f"Purchase Date: {ticket.purchased_at.strftime('%Y-%m-%d %H:%M')}",
#             f"Quantity: {ticket.quantity}"
#         ]

#         y_position = 750  # Start position for text
#         for line in details:
#             p.drawString(100, y_position, line)
#             y_position -= 20

#         # Add QR code if available
#         if ticket.qr_code:
#             try:
#                 qr_image = Image.open(ticket.qr_code.path)
#                 qr_image = qr_image.resize((120, 120))  # Resize for better fitting
#                 qr_buffer = BytesIO()
#                 qr_image.save(qr_buffer, format='PNG')
#                 qr_buffer.seek(0)

#                 p.drawInlineImage(qr_buffer, 400, 650, width=120, height=120)
#             except FileNotFoundError:
#                 p.drawString(100, 600, "QR Code not available")

#         p.showPage()  # Create a new page for each ticket

#     p.save()
#     buffer.seek(0)
#     return buffer.getvalue()


from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

def generate_ticket_pdf(ticket):
    """Generates a PDF with ticket details and a QR code for each ticket purchased."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    for i in range(ticket.quantity):  # Create a separate page for each ticket
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, "Event Ticket")
        p.setFont("Helvetica", 12)

        # Ticket details
        details = [
            f"Event: {ticket.event.title}",
            f"Date: {ticket.event.event_dates}",
            f"Time: {ticket.event.time_start}",
            f"Venue: {ticket.event.venue_name}",
            f"Ticket Type: {ticket.ticket_type}",
            f"Purchased By: {ticket.user.email}",
            f"Purchase Date: {ticket.purchased_at.strftime('%Y-%m-%d %H:%M')}",
            f"Ticket Number: {i + 1} of {ticket.quantity}"  # Show ticket number
        ]

        y_position = 750  # Start position for text
        for line in details:
            p.drawString(100, y_position, line)
            y_position -= 20

        # Add QR code if available
        if ticket.qr_code and ticket.qr_code.path:
            try:
                qr_image = Image.open(ticket.qr_code.path)
                qr_image = qr_image.resize((120, 120))  # Resize for better fitting
                qr_path = ticket.qr_code.path

                # Embed the QR code image
                p.drawInlineImage(qr_path, 400, 650, width=120, height=120)
            except Exception as e:
                p.drawString(100, 600, f"QR Code not available ({str(e)})")

        p.showPage()  # Create a new page for each ticket

    p.save()
    buffer.seek(0)
    return buffer.getvalue()








# def generate_ticket_pdf(ticket):
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)
    
#     # Add quantity to ticket details
#     p.drawString(100, 670, f"Quantity: {ticket.quantity}")
    
#     # Generate a page for each ticket in the quantity
#     for _ in range(ticket.quantity):
#         # ... (existing code to add event details and QR code)
#         p.showPage()  # Create a new page for each ticket
    
#     p.save()
#     return buffer.getvalue()

def send_ticket_email(ticket):
    """Send a plain text ticket email with PDF attachment."""
    try:
        subject = f"Your {ticket.quantity} Ticket(s) for {ticket.event.title}"
        message = f"""
        Hello {ticket.user.name},

        You've purchased {ticket.quantity} ticket(s) for:
        Event: {ticket.event.title}
        Date: {ticket.event.event_dates}
        Time: {ticket.event.time_start}
        Venue: {ticket.event.venue_name}
        Ticket Type: {ticket.ticket_type}

        See the attached PDF for details. 
        """
        # ... (rest of the email code remains the same)
        
        # Create the email message
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ticket.user.email]
        )

        # Generate and attach PDF (ticket)
        ticket_pdf = generate_ticket_pdf(ticket)
        email.attach(
            f"ticket_{ticket.id}.pdf",  # Name the file
            ticket_pdf,  # Attach the raw PDF content (not a file object)
            'application/pdf'
        )

        # Send the email via SMTP
        email.send(fail_silently=False)

    except Exception as e:
        logger.error("Failed to send ticket email: %s", str(e))
        raise Exception("Failed to send ticket email")

# def send_bulk_ticket_email(tickets):  # Remove 'self' parameter
#     try:
#         if not tickets:
#             return

#         event = tickets[0].event
#         user = tickets[0].user
#         email = EmailMultiAlternatives(
#             subject=f"Your {len(tickets)} Tickets for {event.title}",
#             body="Your tickets are attached",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email]
#         )

#         # Create combined PDF
#         packet = BytesIO()
#         can = canvas.Canvas(packet, pagesize=letter)
        
#         for i, ticket in enumerate(tickets):
#             # Generate fresh QR code in memory
#             qr_buffer = BytesIO()
#             qr = qrcode.make(f"TICKET:{ticket.id}")
#             qr.save(qr_buffer, format='PNG')
#             qr_buffer.seek(0)
            
#             # Create new page for each ticket
#             can.setFont("Helvetica", 12)
#             can.drawString(100, 750, f"Ticket {i+1}/{len(tickets)}")
#             can.drawInlineImage(qr_buffer, 100, 650, width=150, height=150)
#             can.showPage()

#         can.save()
#         packet.seek(0)
        
#         email.attach(
#             f"tickets_{event.id}.pdf",
#             packet.getvalue(),
#             'application/pdf'
#         )
#         email.send()

#     except Exception as e:
#         logger.error(f"Email Error: {str(e)}")
#         raise ValidationError("Tickets created but email failed to send")