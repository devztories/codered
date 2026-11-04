from django.conf import settings
from django.db import models
class ChatConversation(models.Model): user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True); session_key=models.CharField(max_length=64,blank=True); mode=models.CharField(max_length=10,choices=[('ai','AI'),('human','Human Admin')],default='ai'); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
class ChatMessage(models.Model): conversation=models.ForeignKey(ChatConversation,on_delete=models.CASCADE,related_name='messages'); sender=models.CharField(max_length=10,choices=[('user','User'),('ai','AI'),('admin','Admin')]); content=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)
