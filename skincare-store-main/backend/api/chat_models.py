from django.db import models
from .models import AppUser


class Conversation(models.Model):
    """Model for chat conversations between two users."""
    user1 = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='conversations_as_user1'
    )
    user2 = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='conversations_as_user2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user1', 'user2']),
            models.Index(fields=['-updated_at']),
        ]
    
    def get_other_user(self, current_user_id):
        """Get the other user in the conversation."""
        return self.user2 if self.user1.id == current_user_id else self.user1
    
    def get_last_message(self):
        """Get the last message in this conversation."""
        return self.messages.first()
    
    def to_dict(self, current_user_id):
        """Convert conversation to dictionary."""
        other_user = self.get_other_user(current_user_id)
        last_message = self.get_last_message()
        
        return {
            'id': self.id,
            'other_user': {
                'id': other_user.id,
                'name': other_user.name,
                'email': other_user.email,
            },
            'last_message': last_message.to_dict() if last_message else None,
            'updated_at': self.updated_at.isoformat(),
            'created_at': self.created_at.isoformat(),
        }


class Message(models.Model):
    """Model for individual messages in a conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_read']),
        ]
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation.id,
            'sender': {
                'id': self.sender.id,
                'name': self.sender.name,
            },
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
        }
