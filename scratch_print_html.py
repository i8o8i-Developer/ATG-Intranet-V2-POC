import os
import django
import sys

# Setup Django
sys.path.append(r"c:\Users\i8o8i\Desktop\INTRANET\ReBuild\INTRANET")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Backend.settings")
django.setup()

from Backend.Apps.MainApp.models import HtmlTemplate

template = HtmlTemplate.objects.filter(name__icontains="ATG Common Offer").first()
if template:
    print("Found Template:", template.name)
    print("----- HTML BODY -----")
    print(template.body_html)
else:
    print("Template Not Found.")
