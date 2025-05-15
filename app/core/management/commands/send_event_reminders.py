from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Interest, Notification, Events, Ticket, User
from datetime import timedelta
from django.core.mail import EmailMessage
from django.conf import settings
from Events.utils import send_event_notification



class Command(BaseCommand):
    help = "Send event reminders one day before the event."

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        next_day = today + timedelta(days=1)
        events = Events.objects.filter(event_dates=next_day)

        for event in events:
            # Notify the Organizer
            try:
                Notification.objects.create(
                    recipient=event.user,
                    event=event,
                    message=f"Hi {event.user.name}, is everything set and ready for tomorrow's event? The attendees are very eager and excited for it!"
                )
                send_event_notification(event.user, event, "reminder")
            except Exception as e:
                print(f"Error sending notification to organizer: {e}")
               
            
            

            Ticketbuyers= Ticket.objects.filter(event=event)
            for buyer in Ticketbuyers:
                Notification.objects.create(
                    recipient=buyer.user,
                    event=event,
                    message=f"You haven't lost the ticket of tommorrows '{event.title}' you showed interest in is tomorrow."
                )
                send_event_notification(buyer.user, event, "ticket")

                
            # Notify all Attendees who showed interest
            
            interested_users = Interest.objects.filter(event=event)
            for interest in interested_users:      
                Notification.objects.create(
                recipient=interest.user,
                event=event,
                message=f"Reminder: Don't miss out!! The event '{event.title}' you showed interest in is tomorrow."
                )
        

        
        self.stdout.write(self.style.SUCCESS(f"Reminders sent for events happening on {next_day}"))
