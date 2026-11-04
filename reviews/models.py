from django.conf import settings
from django.db import models
from orders.models import Order
class Review(models.Model):
 user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); order=models.OneToOneField(Order,on_delete=models.CASCADE); rating=models.PositiveSmallIntegerField(choices=[(i,str(i)) for i in range(1,6)]); title=models.CharField(max_length=150); content=models.TextField(); image=models.ImageField(upload_to='reviews/',blank=True); is_approved=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
 def __str__(self): return self.title
