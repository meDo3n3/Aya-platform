from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile, Halaqa 
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates 20 test students and assigns them to Halaqa 7.'

    def handle(self, *args, **options):
        # 1. البحث عن الحلقة (ID=7)
        try:
            halaqa = Halaqa.objects.get(id=7) 
        except Halaqa.DoesNotExist:
            self.stdout.write(self.style.ERROR('⚠️ لم يتم العثور على الحلقة رقم 7. تأكد من وجودها في قاعدة البيانات.'))
            return

        self.stdout.write(self.style.SUCCESS(f'بدء إنشاء 20 حساب طالب تجريبي في "{halaqa.name}"...'))

        arabic_male_names = ["أحمد", "محمد", "علي", "خالد", "يوسف", "عبدالله", "عمر"]
        arabic_female_names = ["فاطمة", "ليلى", "سارة", "نورة", "مريم", "زينب", "هند"]
        family_names = ["الغامدي", "الزهيري", "الجهني", "السالم", "الزهراني", "العساف", "العمري"]

        base_password = "test1234"
        initial_user_count = User.objects.count()

        for i in range(20):
            index = initial_user_count + i + 1 
            
            is_male = random.choice([True, False])
            
            if is_male:
                first_name = random.choice(arabic_male_names)
                gender = 'male' 
            else:
                first_name = random.choice(arabic_female_names)
                gender = 'female' 
            
            last_name = random.choice(family_names)
            username = f"student_{index}"
            email = f"student{index}@test.com"
            password = f"{base_password}{index}" 
            
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'is_active': True,
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                
                profile, profile_created = Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        'halaqa': halaqa, # التعيين للحلقة 7
                        'role': Profile.ROLE_STUDENT, 
                        'gender': gender, 
                        'teacher_status': Profile.TEACHER_APPROVED, 
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء الطالب: {first_name} {last_name} (اسم المستخدم: {username}) بكلمة سر: {password}'))
                elif profile_created:
                    self.stdout.write(self.style.WARNING(f'🔄 تم إنشاء ملف التعريف لمستخدم موجود مسبقًا وربطه بالحلقة 7: {username}.'))
                else:
                     self.stdout.write(self.style.WARNING(f'⚠️ الطالب موجود مسبقاً، تخطي الإنشاء: {first_name} {last_name} (اسم المستخدم: {username})'))


            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ حدث خطأ أثناء إنشاء الطالب رقم {i+1}: {e}'))
                self.stdout.write(self.style.ERROR(f'تفاصيل الخطأ: {e.args[0]}'))

        self.stdout.write(self.style.SUCCESS('\nتم الانتهاء من إنشاء جميع الحسابات التجريبية بنجاح!'))