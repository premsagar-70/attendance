import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FACE_RECOGNITION_BASED_ATTENDANCE_MANAGEMENT_SYSTEM_USING_DEEP_LEARNING.settings')
django.setup()

from django.db import transaction
from Students.models import UserProfile

try:
    with transaction.atomic():
        print("Transaction block reached")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")
