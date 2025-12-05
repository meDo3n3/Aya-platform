# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    إنشاء Profile لمرة واحدة عند إنشاء User جديد.
    """
    if created:
        # أنشئ البروفايل إن لم يوجد
        profile, _ = Profile.objects.get_or_create(user=instance)

        # لو تم إنشاء حساب لمعلّم من الأدمن مباشرة و role اتضبط لاحقًا،
        # هنسيبه كما هو الآن (سيتم التعامل في سيجنال Profile).
        # لكن لو البروفايل اتعمل وفيه role=TEACHER وغير Approved،
        # تأكد أن الحساب يبدأ غير مفعّل.
        if profile.role == Profile.ROLE_TEACHER and profile.teacher_status != Profile.TEACHER_APPROVED:
            if instance.is_active:
                instance.is_active = False
                instance.save(update_fields=["is_active"])


@receiver(post_save, sender=Profile)
def activate_user_when_teacher_status_changes(sender, instance: Profile, **kwargs):
    """
    تفعيل/تعطيل المستخدم تلقائياً بناءً على حالة اعتماد المعلّم.
    - المعلّم APPROVED => user.is_active=True
    - المعلّم غير Approved => user.is_active=False
    الطلاب عادة يبقوا مفعّلين دائماً (يمكن تعديل المنطق لو عندك شروط أخرى).
    """
    user = instance.user

    # لو البروفايل لمعلّم
    if instance.role == Profile.ROLE_TEACHER:
        should_be_active = (instance.teacher_status == Profile.TEACHER_APPROVED)
        if user.is_active != should_be_active:
            user.is_active = should_be_active
            user.save(update_fields=["is_active"])

    # لو طالب: عادة نتركه كما هو.
    # إن أردت فرض التفعيل التلقائي للطلاب، يمكنك إضافة منطق هنا.
