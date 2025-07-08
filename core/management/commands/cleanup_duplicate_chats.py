from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import ChatRequest, Message

class Command(BaseCommand):
    help = 'Merges duplicate chat requests between the same customer and professional'

    def handle(self, *args, **kwargs):
        # Find duplicate chat requests (same customer and professional)
        duplicates = ChatRequest.objects.values('customer', 'professional').annotate(count=Count('id')).filter(count__gt=1)
        
        for duplicate in duplicates:
            customer_id = duplicate['customer']
            professional_id = duplicate['professional']
            # Get all chat requests for this customer-professional pair, ordered by created_at descending
            chat_requests = ChatRequest.objects.filter(customer_id=customer_id, professional_id=professional_id).order_by('-created_at')
            if chat_requests.count() > 1:
                # Keep the most recent chat request
                keep_chat = chat_requests.first()
                # Get IDs of chat requests to delete (exclude the one to keep)
                delete_chat_ids = chat_requests.exclude(id=keep_chat.id).values_list('id', flat=True)
                
                self.stdout.write(f"Merging {len(delete_chat_ids)} duplicate chat requests for customer {customer_id} and professional {professional_id}")
                
                # Move messages to the kept chat request
                for chat_id in delete_chat_ids:
                    messages = Message.objects.filter(chat_request_id=chat_id)
                    messages.update(chat_request=keep_chat)
                    self.stdout.write(f"Moved {messages.count()} messages from chat {chat_id} to chat {keep_chat.id}")
                
                # Delete the duplicate chat requests
                ChatRequest.objects.filter(id__in=delete_chat_ids).delete()
                self.stdout.write(f"Deleted {len(delete_chat_ids)} duplicate chat requests")
        
        self.stdout.write(self.style.SUCCESS("Duplicate chat cleanup completed."))