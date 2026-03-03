from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(max_length=50, unique=True)
    mobile = models.CharField(max_length=10)
    password = models.CharField(max_length=128)  # Store hashed password in production
    
    # Class mapping fields
    department = models.CharField(max_length=100)
    year = models.IntegerField()
    semester = models.IntegerField()
    section = models.CharField(max_length=10)
    
    # Centralized Face Embedding in MongoDB
    face_embedding = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loginid} ({self.department} {self.year}-{self.semester} {self.section})"

class Attendance(models.Model):
    student_id = models.CharField(max_length=100)
    date = models.DateField(default=timezone.localdate)
    period = models.CharField(max_length=10)
    classification = models.CharField(max_length=20, default="Present")
    
    # Track the location/class where attendance was marked
    department = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    semester = models.IntegerField(blank=True, null=True)
    section = models.CharField(max_length=10, blank=True, null=True)
    is_lab = models.BooleanField(default=False)
    
    timestamp = models.DateTimeField(default=timezone.now) # Fixed default to now without call evaluation

    class Meta:
        # Cannot use unique_together safely on same student id if we want labs/theory overriding. 
        # But per period it should be fine.
        unique_together = ("student_id", "date", "period")

    def __str__(self):
        return f"{self.student_id} - {self.period} - {self.timestamp}"
