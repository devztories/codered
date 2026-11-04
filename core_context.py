from django.conf import settings
from django.db.utils import OperationalError,ProgrammingError
def context(request):
 try:
  from contact.models import SiteSettings,SocialLink
  site=SiteSettings.objects.first(); socials=SocialLink.objects.filter(is_active=True)
 except (OperationalError,ProgrammingError): site=None; socials=[]
 return {'site_settings':site,'social_links':socials,'company_upi_id':settings.COMPANY_UPI_ID if hasattr(settings,'COMPANY_UPI_ID') else __import__('os').getenv('COMPANY_UPI_ID','')}
