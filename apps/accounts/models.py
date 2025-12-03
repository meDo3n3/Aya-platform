# apps/accounts/models.py

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.templatetags.static import static

# ==============================================================================
# Core Models (Halaqa, Surah, Profile)
# ==============================================================================

class Halaqa(models.Model):
    """
    Represents a Quran memorization circle (Halaqa).
    Students belong to a Halaqa, and Teachers manage it.
    """
    name = models.CharField(max_length=150, unique=True)
    juz_from = models.PositiveSmallIntegerField(null=True, blank=True)
    juz_to = models.PositiveSmallIntegerField(null=True, blank=True)
    teachers = models.ManyToManyField(
        "Profile",
        related_name="halaqat_as_teacher",
        blank=True,
        limit_choices_to={"role": "teacher"},
    )

    def __str__(self):
        return self.name

class Surah(models.Model):
    """
    Represents a Surah in the Quran.
    Used to validate and normalize Surah names in tasks.
    """
    name = models.CharField(max_length=64, unique=True)
    juz_from = models.PositiveSmallIntegerField()
    juz_to = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

class Profile(models.Model):
    """
    Extends the built-in User model to add role-based fields (Student/Teacher).
    """
    ROLE_STUDENT = "student"
    ROLE_TEACHER = "teacher"
    ROLE_CHOICES = ((ROLE_STUDENT, "Student"), (ROLE_TEACHER, "Teacher"))

    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_CHOICES = ((GENDER_MALE, "Male"), (GENDER_FEMALE, "Female"))

    TEACHER_PENDING = "pending"
    TEACHER_APPROVED = "approved"
    TEACHER_REJECTED = "rejected"
    TEACHER_STATUS_CHOICES = (
        (TEACHER_PENDING, "Pending"),
        (TEACHER_APPROVED, "Approved"),
        (TEACHER_REJECTED, "Rejected"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    halaqa = models.ForeignKey(
        Halaqa, null=True, blank=True, on_delete=models.SET_NULL, related_name="students"
    )
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=True, blank=True)
    photo = models.ImageField(upload_to="avatars/", null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    guardian_phone = models.CharField(max_length=30, null=True, blank=True)
    institution = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    certificate = models.FileField(upload_to="certificates/", null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    app_notifications = models.BooleanField(default=True)
    teacher_status = models.CharField(
        max_length=10, choices=TEACHER_STATUS_CHOICES, default=TEACHER_PENDING
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def avatar_url(self):
        if self.photo:
            try:
                return self.photo.url
            except Exception:
                pass
        g = (self.gender or "").lower()
        default_path = "img/avatars/female.png" if g == "female" else "img/avatars/male.png"
        return static(default_path)

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

# ==============================================================================
# Abstract Base Classes (Tasks & Submissions)
# ==============================================================================

class BaseTask(models.Model):
    """
    Abstract base model for tasks (Recitation & Review).
    """
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        limit_choices_to={"role": Profile.ROLE_TEACHER},
    )
    surah = models.ForeignKey(Surah, on_delete=models.PROTECT, verbose_name="السورة")
    start_ayah = models.PositiveIntegerField("من آية", blank=True, null=True)
    end_ayah = models.PositiveIntegerField("إلى آية", blank=True, null=True)
    deadline = models.DateTimeField("الموعد النهائي", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-deadline", "-id"]

class BaseSubmission(models.Model):
    """
    Abstract base model for submissions.
    """
    STATUS_CHOICES = [
        ("submitted", "تم التسليم"),
        ("reviewing", "قيد المراجعة"),
        ("graded", "تم التصحيح"),
    ]
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        limit_choices_to={"role": Profile.ROLE_STUDENT},
    )
    audio = models.FileField(upload_to="submissions/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    rules = models.PositiveSmallIntegerField(null=True, blank=True)
    hifdh = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

# ==============================================================================
# Task Models (Recitation, Review)
# ==============================================================================

class Recitation(BaseTask):
    """
    Represents a Recitation (Hifz) task.
    """
    halaqa = models.ForeignKey(Halaqa, on_delete=models.CASCADE, related_name="recitations")
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name="created_recitations",
        limit_choices_to={"role": Profile.ROLE_TEACHER},
    )
    
    def __str__(self):
        return f"تسميع {self.surah.name} (من {self.start_ayah} إلى {self.end_ayah}) – {self.halaqa.name}"

class Review(BaseTask):
    """
    Represents a Review (Muraja'ah) task.
    """
    halaqa = models.ForeignKey(Halaqa, on_delete=models.CASCADE, related_name="reviews")
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name="created_reviews",
        limit_choices_to={"role": Profile.ROLE_TEACHER},
    )
    
    def __str__(self):
        return f"مراجعة {self.surah.name} – {self.halaqa.name}"

# ==============================================================================
# Submission Models
# ==============================================================================

class RecitationSubmission(BaseSubmission):
    """
    Represents a student's submission for a Recitation task.
    """
    recitation = models.ForeignKey(Recitation, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="recitation_submissions",
        limit_choices_to={"role": Profile.ROLE_STUDENT},
    )

    class Meta(BaseSubmission.Meta):
        unique_together = ("recitation", "student")
        
    def __str__(self):
        return f"{self.student.user.username} → {self.recitation}"

class ReviewSubmission(BaseSubmission):
    """
    Represents a student's submission for a Review task.
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="review_submissions",
        limit_choices_to={"role": Profile.ROLE_STUDENT},
    )

    class Meta(BaseSubmission.Meta):
        unique_together = ("review", "student")

    def __str__(self):
        return f"{self.student.user.username} → {self.review}"

# ==============================================================================
# Helper Models (Attendance, Notification, PasswordReset)
# ==============================================================================

class Attendance(models.Model):
    """
    Tracks student attendance.
    """
    STATUS_CHOICES = [("present","حاضر"),("absent","غائب"),("late","متأخر")]
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={"role": Profile.ROLE_STUDENT})
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="present")

    class Meta:
        unique_together = ("student","date")
        ordering = ["-date"]

class Notification(models.Model):
    """
    Stores system notifications for users.
    """
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"إشعار لـ {self.recipient.user.username}"

class PasswordResetCode(models.Model):
    """
    Stores OTP codes for password reset functionality.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.created_at >= timezone.now() - datetime.timedelta(minutes=15)

    def __str__(self):
        return f"{self.user.username} - {self.code}"