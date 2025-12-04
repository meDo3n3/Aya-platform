# apps/accounts/views.py

import json
import random
import types
from datetime import datetime, timedelta, date
from itertools import chain
from operator import attrgetter

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from django.db.models import Q, Count, Avg, Max, Sum, F, Subquery, OuterRef, IntegerField, ExpressionWrapper
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

try:
    from hijri_converter import Gregorian as _Gregorian
    HIJRI_OK = True
except ImportError:
    HIJRI_OK = False

from .models import (
    Profile, Halaqa, Surah,
    Recitation, RecitationSubmission,
    Review, ReviewSubmission,
    Attendance, Notification, PasswordResetCode
)

User = get_user_model()
DETAILED = getattr(settings, "DEBUG", False)

# ==============================================================================
# Helper Functions
# ==============================================================================

def start_of_sat_week(d):
    """Returns the Saturday of the current week (Mon=0..Sun=6 -> Sat=5)."""
    delta = (d.weekday() - 5) % 7
    return d - timedelta(days=delta)

def _range_len(obj):
    """Returns the number of ayahs in a task range."""
    try:
        s = int(getattr(obj, "start_ayah", 0) or 0)
        e = int(getattr(obj, "end_ayah", 0) or 0)
        return (e - s + 1) if (s and e and e >= s) else 0
    except Exception:
        return 0

# ==============================================================================
# Authentication Views
# ==============================================================================

def login_view(request):
    """
    Handles user login for both students and teachers.
    Checks for active status and teacher approval status.
    """
    if request.user.is_authenticated:
        if hasattr(request.user, "profile"):
            return redirect("accounts:teacher_dashboard" if request.user.profile.role == Profile.ROLE_TEACHER
                            else "accounts:student_dashboard")
        return redirect("home")

    if request.method == "POST":
        identifier  = (request.POST.get("username") or "").strip()
        password    = request.POST.get("password") or ""
        role        = request.POST.get("role") or ""
        remember_me = request.POST.get("remember-me")

        if not identifier or not password or not role:
            messages.error(request, "من فضلك املأ كل الحقول المطلوبة.")
            return render(request, "accounts/login.html", {"selected_role": role})

        try:
            user_obj = User.objects.get(Q(username__iexact=identifier) | Q(email__iexact=identifier))
        except User.DoesNotExist:
            messages.error(request, "لا يوجد حساب بهذه البيانات." if DETAILED else "بيانات الدخول غير صحيحة.")
            return render(request, "accounts/login.html", {"selected_role": role})

        profile, _ = Profile.objects.get_or_create(user=user_obj)

        if profile.role != role:
            messages.error(request, f"لا يمكنك تسجيل الدخول كـ '{role}' لأن حسابك مسجّل كـ '{profile.role}'.")
            return render(request, "accounts/login.html", {"selected_role": role})

        # Check account status
        if not user_obj.is_active:
            if hasattr(user_obj, 'profile'):
                if user_obj.profile.teacher_status == Profile.TEACHER_PENDING:
                    messages.warning(request, "لم يتم الموافقة عليك حتى الآن.")
                elif user_obj.profile.teacher_status == Profile.TEACHER_REJECTED:
                    messages.error(request, "عذراً، تم رفض طلب انضمامك.")
                    user_obj.delete()
                else:
                    messages.error(request, "تم تعطيل حسابك. يرجى التواصل مع الإدارة.")
            else:
                messages.error(request, "حسابك غير نشط.")
            return render(request, "accounts/login.html", {"selected_role": role})

        if profile.role == Profile.ROLE_TEACHER and profile.teacher_status != Profile.TEACHER_APPROVED:
            messages.error(request, "حساب المعلّم الخاص بك قيد المراجعة.")
            return render(request, "accounts/login.html", {"selected_role": role})

        user = authenticate(request, username=user_obj.username, password=password)
        if user is None:
            messages.error(request, "كلمة المرور غير صحيحة." if DETAILED else "بيانات الدخول غير صحيحة.")
            return render(request, "accounts/login.html", {"selected_role": role})

        login(request, user)
        request.session.set_expiry(1209600 if remember_me else 0)

        return redirect("accounts:teacher_dashboard" if profile.role == Profile.ROLE_TEACHER
                        else "accounts:student_dashboard")

    return render(request, "accounts/login.html", {"selected_role": "student"})

def logout_view(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج.")
    return redirect("accounts:login")

def register_view(request):
    """
    Handles user registration for students and teachers.
    """
    def ctx(extra=None):
        base = {"halaqas": Halaqa.objects.all().order_by("name")}
        if extra: base.update(extra)
        return base

    if request.method != "POST":
        return render(request, "accounts/register.html", ctx())

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    try:
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        pw1 = request.POST.get("password", "")
        pw2 = request.POST.get("password2", "")
        role = request.POST.get("role", "")
        birth_date_str = request.POST.get("birth_date", "").strip()
        gender = request.POST.get("gender") or None
        guardian_phone = request.POST.get("guardian_phone") or None
        halaqa_input = request.POST.get("halaqa") or None
        institution = request.POST.get("institution") or None
        bio = request.POST.get("bio") or None
        certificate = request.FILES.get("certificate")

        errors = []
        if not all([full_name, username, email, pw1, pw2, role, birth_date_str, gender]):
             errors.append("من فضلك أكمل جميع الحقول الإجبارية (*).")
        if pw1 != pw2:
            errors.append("كلمتا المرور غير متطابقتين.")
        if User.objects.filter(username__iexact=username).exists():
            errors.append("اسم المستخدم مستخدم من قبل.")
        if User.objects.filter(email__iexact=email).exists():
            errors.append("البريد الإلكتروني مسجل من قبل.")

        birth_date = None
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            errors.append("صيغة تاريخ الميلاد غير صحيحة.")
        
        halaqa_obj = None
        if role == Profile.ROLE_STUDENT:
            if not halaqa_input:
                errors.append("اختيار الحلقة مطلوب للطالب.")
            else:
                halaqa_obj = Halaqa.objects.filter(id=halaqa_input).first()
                if not halaqa_obj:
                    errors.append("الحلقة المحددة غير صالحة.")
        
        if errors:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': "<br>".join(errors)}, status=400)
            else:
                for error in errors: messages.error(request, error)
                return render(request, "accounts/register.html", ctx())

        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=pw1, first_name=full_name.split()[0], last_name=" ".join(full_name.split()[1:]))
            
            # Both roles start as inactive/pending
            user.is_active = False
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.full_name = full_name
            profile.gender = gender
            profile.birth_date = birth_date
            profile.teacher_status = Profile.TEACHER_PENDING

            if role == Profile.ROLE_STUDENT:
                profile.halaqa = halaqa_obj
                profile.guardian_phone = guardian_phone
            else:
                profile.institution = institution
                profile.bio = bio
                profile.certificate = certificate
            
            profile.save()

        if is_ajax:
            return JsonResponse({'status': 'success', 'role': role})
        
        messages.warning(request, "طلبك في قائمة انتظار الموافقة.")
        return redirect("accounts:login")

    except Exception as e:
        print(f"Registration Error: {e}")
        error_message = "حدث خطأ غير متوقع في الخادم."
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': error_message}, status=500)
        messages.error(request, error_message)
        return render(request, "accounts/register.html", ctx())


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            PasswordResetCode.objects.update_or_create(
                user=user, defaults={'code': otp, 'created_at': timezone.now()}
            )
            
            # --- التعديل هنا ---
            send_mail(
                subject='Password Reset OTP',
                message=f'Your OTP for password reset is: {otp}',
                from_email=settings.DEFAULT_FROM_EMAIL,  # استخدمنا الإيميل الافتراضي بدلاً من EMAIL_HOST_USER
                recipient_list=[email],
                fail_silently=False,
            )
            # ------------------

            request.session['reset_email'] = email
            return redirect('accounts:verify_code')
        except User.DoesNotExist:
            messages.error(request, 'البريد الإلكتروني غير موجود.')
    return render(request, 'accounts/forgot_password.html')


def verify_reset_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:forgot_password')
        
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        try:
            user = User.objects.get(email=email)
            reset_code = user.password_reset_code
            
            if reset_code.code == otp_code and reset_code.is_valid():
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    reset_code.delete()
                    del request.session['reset_email']
                    messages.success(request, 'تم تغيير كلمة المرور بنجاح.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'كلمتا المرور غير متطابقتين.')
            else:
                messages.error(request, 'الرمز غير صحيح أو منتهي الصلاحية.')
        except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
            messages.error(request, 'طلب غير صالح.')
            
    return render(request, 'accounts/verify_code.html')

# ==============================================================================
# General Views
# ==============================================================================

def landing_page(request):
    return render(request, 'landing_page.html')

def go(request):
    user = request.user
    role = getattr(user, 'role', None)
    if role is None and hasattr(user, 'profile'):
        role = getattr(user.profile, 'role', None)

    if role == 'student' or user.groups.filter(name__iexact='student').exists():
        return HttpResponseRedirect('/dashboard/')
    if role == 'teacher' or user.groups.filter(name__iexact='teacher').exists():
        return HttpResponseRedirect('/teacher/dashboard/')
    return HttpResponseRedirect('/login/')

def home_view(request):
    return render(request, "home.html")

# ==============================================================================
# Student Views
# ==============================================================================

@login_required(login_url="accounts:login")
def student_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != Profile.ROLE_STUDENT:
        return redirect("accounts:teacher_dashboard")

    now = timezone.now()
    today = timezone.localdate()
    
    # 1. Attendance
    Attendance.objects.get_or_create(student=profile, date=today, defaults={"status": "present"})
    start_date = today - timedelta(days=6)
    existing_attendance = Attendance.objects.filter(student=profile, date__gte=start_date, date__lte=today)
    attendance_map = {att.date: att for att in existing_attendance}
    week_attendance = []
    for i in range(7):
        day_date = start_date + timedelta(days=i)
        week_attendance.append(attendance_map.get(day_date, types.SimpleNamespace(date=day_date, status=None)))

    # 2. Fetch Tasks
    student_join_date = request.user.date_joined
    recitations = Recitation.objects.filter(halaqa=profile.halaqa, created_at__gte=student_join_date).select_related("halaqa", "created_by__user", "surah")
    reviews = Review.objects.filter(halaqa=profile.halaqa, created_at__gte=student_join_date).select_related("halaqa", "created_by__user", "surah")
    
    rec_subs = RecitationSubmission.objects.filter(student=profile, recitation__in=recitations)
    rev_subs = ReviewSubmission.objects.filter(student=profile, review__in=reviews)
    
    sub_map = {f"recitation_{s.recitation_id}": s for s in rec_subs}
    sub_map.update({f"review_{s.review_id}": s for s in rev_subs})

    all_tasks = []
    for r in recitations:
        setattr(r, "type", "recitation")
        setattr(r, "sub", sub_map.get(f"recitation_{r.id}"))
        setattr(r, "is_late", r.deadline and r.deadline < now and not r.sub)
        all_tasks.append(r)
    for rv in reviews:
        setattr(rv, "type", "review")
        setattr(rv, "sub", sub_map.get(f"review_{rv.id}"))
        setattr(rv, "is_late", rv.deadline and rv.deadline < now and not rv.sub)
        all_tasks.append(rv)

    all_tasks.sort(key=lambda x: x.created_at, reverse=True)

    for task in all_tasks:
        if task.sub and task.sub.status == 'graded':
            task.sub.score_percentage = (task.sub.score or 0) * 10
            task.sub.hifdh_percentage = (task.sub.hifdh or 0) * 20
            task.sub.rules_percentage = (task.sub.rules or 0) * 20
            
    # 3. Filter Tasks
    pending_tasks = [t for t in all_tasks if not t.sub or (t.sub.status == 'graded' and t.sub.score is not None and t.sub.score < 5)]
    submitted_tasks = [t for t in all_tasks if t.sub and t.sub.status == 'submitted']
    graded_tasks = [t for t in all_tasks if t.sub and t.sub.status == 'graded' and t.sub.score is not None and t.sub.score >= 5]
    
    # 4. Statistics
    week_ago = now - timedelta(days=7)
    all_graded_recitations = RecitationSubmission.objects.filter(student=profile, status="graded")
    all_graded_reviews = ReviewSubmission.objects.filter(student=profile, status="graded")
    count_graded = all_graded_recitations.count() + all_graded_reviews.count()
    total_score = (all_graded_recitations.aggregate(total=Sum('score'))['total'] or 0) + (all_graded_reviews.aggregate(total=Sum('score'))['total'] or 0)
    accuracy_pct = round((total_score / (count_graded * 10)) * 100) if count_graded > 0 else 0
    
    present_days = sum(1 for a in week_attendance if a.status == "present")
    presence_pct = round((present_days / 7) * 100) if week_attendance else 0
    
    successful_recitations = RecitationSubmission.objects.filter(student=profile, status="graded", score__gte=5).select_related('recitation__surah')
    ayah_count = sum((s.recitation.end_ayah - s.recitation.start_ayah + 1) for s in successful_recitations if s.recitation and s.recitation.start_ayah and s.recitation.end_ayah)
    
    weekly_hifdh_score = round(((RecitationSubmission.objects.filter(student=profile, created_at__gte=week_ago, status='graded').aggregate(avg=Avg('score'))['avg'] or 0) / 10) * 100)
    weekly_review_score = round(((ReviewSubmission.objects.filter(student=profile, created_at__gte=week_ago, status='graded').aggregate(avg=Avg('score'))['avg'] or 0) / 10) * 100)

    halaqa_teacher = profile.halaqa.teachers.first() if profile.halaqa else None

    ctx = {
        "profile": profile,
        "pending_tasks": pending_tasks,
        "submitted_tasks": submitted_tasks,
        "graded_tasks": graded_tasks,
        "week_attendance": week_attendance,
        "pending_tasks_count": len(pending_tasks),
        "accuracy_pct": accuracy_pct,
        "presence_pct": presence_pct,
        "ayah_count": ayah_count,
        "weekly_hifdh_score": weekly_hifdh_score,
        "weekly_review_score": weekly_review_score,
        "halaqa_teacher_name": halaqa_teacher.user.get_full_name() or halaqa_teacher.user.username if halaqa_teacher else "غير محدد",
        "now": now,
    }
    return render(request, "students/student_dashboard.html", ctx)

@login_required(login_url="accounts:login")
def student_settings_view(request):
    user = request.user
    profile = user.profile

    if profile.role != 'student':
        return redirect('accounts:teacher_dashboard')

    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            if full_name:
                parts = full_name.strip().split(' ', 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
                user.save()

            if request.FILES.get('avatar'):
                profile.photo = request.FILES['avatar']
            elif request.POST.get('remove_avatar') == 'true':
                profile.photo.delete(save=False)
                profile.photo = None
            
            halaqa_id = request.POST.get('halaqa')
            if halaqa_id:
                try:
                    profile.halaqa = Halaqa.objects.get(id=halaqa_id)
                except Halaqa.DoesNotExist:
                    pass
            
            profile.email_notifications = 'email_notifications' in request.POST
            profile.save()

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if current_password or new_password or confirm_password:
                if not (current_password and new_password and confirm_password):
                    return JsonResponse({'status': 'error', 'message': 'يرجى ملء جميع حقول كلمة المرور.'}, status=400)
                if not user.check_password(current_password):
                    return JsonResponse({'status': 'error', 'message': 'كلمة المرور الحالية غير صحيحة.'}, status=400)
                if new_password != confirm_password:
                    return JsonResponse({'status': 'error', 'message': 'كلمة المرور الجديدة غير متطابقة.'}, status=400)
                
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)

            return JsonResponse({'status': 'success', 'message': 'تم حفظ التغييرات بنجاح!', 'new_avatar_url': profile.avatar_url})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'حدث خطأ: {str(e)}'}, status=500)

    context = {
        'profile': profile,
        'halaqas': Halaqa.objects.all(),
        'default_avatar_url': static('images/default_avatar.png') 
    }
    return render(request, 'students/student_settings.html', context)

@login_required
def recitation_start(request, pk):
    task = get_object_or_404(Recitation, id=pk)
    return render(request, 'students/recitation_record.html', {'task': task, 'task_type': 'recitation'})

@login_required
def review_start(request, pk):
    task = get_object_or_404(Review, id=pk)
    return render(request, 'students/recitation_record.html', {'task': task, 'task_type': 'review'})

@require_POST
@login_required(login_url="accounts:login")
def submit_task(request, task_type, task_id):
    if request.user.profile.role != Profile.ROLE_STUDENT:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({"status": "error", "message": "لم يصل ملف الصوت."}, status=400)

    student = request.user.profile
    task = None
    submission = None

    try:
        if task_type == 'recitation':
            task = get_object_or_404(Recitation, id=task_id, halaqa=student.halaqa)
            submission, _ = RecitationSubmission.objects.update_or_create(
                recitation=task, student=student,
                defaults={'audio': audio_file, 'status': 'submitted', 'updated_at': timezone.now()}
            )
        elif task_type == 'review':
            task = get_object_or_404(Review, id=task_id, halaqa=student.halaqa)
            submission, _ = ReviewSubmission.objects.update_or_create(
                review=task, student=student,
                defaults={'audio': audio_file, 'status': 'submitted', 'updated_at': timezone.now()}
            )
        else:
            return JsonResponse({'status': 'error', 'message': 'نوع المهمة غير صالح.'}, status=400)
            
        setattr(task, "type", task_type)
        setattr(task, "sub", submission)
        setattr(task, "is_late", task.deadline and task.deadline < timezone.now() and not task.sub)

        task_card_html = render_to_string('students/partials/_task_item.html', {'task': task, 'sub': submission, 'request': request})
        
        pending_recitations = Recitation.objects.filter(halaqa=student.halaqa).exclude(submissions__student=student).count()
        pending_reviews = Review.objects.filter(halaqa=student.halaqa).exclude(submissions__student=student).count()
        new_pending_count = pending_recitations + pending_reviews

        return JsonResponse({
            'status': 'success',
            'message': 'تم التسليم بنجاح!',
            'task_card_html': task_card_html,
            'new_stats': {'pending_tasks_count': new_pending_count}
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
@login_required
def recitation_action(request, pk):
    profile = get_object_or_404(Profile, user=request.user, role=Profile.ROLE_STUDENT)
    recitation = get_object_or_404(Recitation, pk=pk, halaqa=profile.halaqa)
    if request.POST.get("action") == "retry":
        RecitationSubmission.objects.filter(recitation=recitation, student=profile).delete()
        messages.success(request, "تمت إعادة ضبط التسميع.")
    return redirect("accounts:student_dashboard")

@require_POST
@login_required
def review_action(request, pk):
    profile = get_object_or_404(Profile, user=request.user, role=Profile.ROLE_STUDENT)
    review = get_object_or_404(Review, pk=pk, halaqa=profile.halaqa)
    if request.POST.get("action") == "retry":
        ReviewSubmission.objects.filter(review=review, student=profile).delete()
        messages.success(request, "تمت إعادة ضبط المراجعة.")
    return redirect("accounts:student_dashboard")

# ==============================================================================
# Teacher Views
# ==============================================================================

@login_required(login_url="accounts:login")
def teacher_dashboard(request):
    if request.user.is_staff: return redirect('admin:index')
    profile = request.user.profile
    if profile.role != Profile.ROLE_TEACHER: return redirect("accounts:student_dashboard")
    if profile.teacher_status != Profile.TEACHER_APPROVED: return redirect("accounts:login")

    my_halaqat = Halaqa.objects.filter(teachers=profile).prefetch_related('students')
    
    pending_submissions_count = (
        RecitationSubmission.objects.filter(recitation__halaqa__in=my_halaqat, status='submitted').count() +
        ReviewSubmission.objects.filter(review__halaqa__in=my_halaqat, status='submitted').count()
    )
    
    total_students_count = Profile.objects.filter(halaqa__in=my_halaqat, role=Profile.ROLE_STUDENT).count()
    active_halaqat_count = my_halaqat.count()
    
    avg_performance_rec = RecitationSubmission.objects.filter(recitation__halaqa__in=my_halaqat, status='graded').aggregate(avg_score=Avg('score'))['avg_score'] or 0
    average_performance = round(avg_performance_rec * 10, 1) if avg_performance_rec else 0

    latest_rec_subs = RecitationSubmission.objects.filter(recitation__halaqa__in=my_halaqat, status='submitted').select_related('student__user', 'recitation')
    latest_rev_subs = ReviewSubmission.objects.filter(review__halaqa__in=my_halaqat, status='submitted').select_related('student__user', 'review')

    for sub in latest_rec_subs: sub.type = 'recitation'
    for sub in latest_rev_subs: sub.type = 'review'

    latest_submissions = sorted(chain(latest_rec_subs, latest_rev_subs), key=lambda x: x.created_at, reverse=True)[:5]
    
    halaqat_with_stats = []
    for halaqa in my_halaqat:
        last_recitation = Recitation.objects.filter(halaqa=halaqa).order_by('-created_at').first()
        last_review = Review.objects.filter(halaqa=halaqa).order_by('-created_at').first()
        halaqat_with_stats.append({
            'halaqa': halaqa,
            'student_count': halaqa.students.count(),
            'last_recitation_date': last_recitation.created_at if last_recitation else None,
            'last_review_date': last_review.created_at if last_review else None,
        })

    today_gregorian = date.today()
    if HIJRI_OK:
        hijri_date = _Gregorian(today_gregorian.year, today_gregorian.month, today_gregorian.day).to_hijri()
        formatted_hijri_date = f"{hijri_date.day_name('ar')}، {hijri_date.day} {hijri_date.month_name('ar')} {hijri_date.year}"
    else:
        formatted_hijri_date = today_gregorian.strftime("%Y-%m-%d")

    context = {
        'pending_submissions_count': pending_submissions_count,
        'total_students_count': total_students_count,
        'active_halaqat_count': active_halaqat_count,
        'average_performance': average_performance,
        'latest_submissions': latest_submissions,
        'halaqat_list': halaqat_with_stats,
        'today_date': formatted_hijri_date
    }
    return render(request, 'teachers/teacher_dashboard.html', context)

@login_required
def teacher_halaqat(request):
    profile = request.user.profile
    if profile.role != Profile.ROLE_TEACHER: return redirect("accounts:student_dashboard")

    my_halaqat_query = Halaqa.objects.filter(teachers=profile).annotate(student_count=Count('students', distinct=True))
    sort_option = request.GET.get('sort', 'name_asc')

    if sort_option == 'name_desc': my_halaqat_query = my_halaqat_query.order_by('-name')
    elif sort_option == 'students_desc': my_halaqat_query = my_halaqat_query.order_by('-student_count')
    elif sort_option == 'students_asc': my_halaqat_query = my_halaqat_query.order_by('student_count')
    else: my_halaqat_query = my_halaqat_query.order_by('name')

    halaqat_with_stats = []
    for halaqa in my_halaqat_query:
        avg_score = RecitationSubmission.objects.filter(recitation__halaqa=halaqa, status='graded').aggregate(avg=Avg('score'))['avg']
        halaqat_with_stats.append({
            'halaqa': halaqa,
            'student_count': halaqa.student_count,
            'completion_percentage': round((avg_score or 0) * 10, 1),
        })

    return render(request, 'teachers/halaqat.html', {'halaqat_list': halaqat_with_stats, 'current_sort': sort_option})

@login_required(login_url="accounts:login")
def halaqa_details_view(request, halaqa_id):
    halaqa = get_object_or_404(Halaqa, id=halaqa_id, teachers=request.user.profile)
    student_count = halaqa.students.count()
    
    avg_performance = round((RecitationSubmission.objects.filter(recitation__halaqa=halaqa, status='graded').aggregate(avg=Avg('score'))['avg'] or 0) * 10, 1)
    pending_submissions_halaqa = (
        RecitationSubmission.objects.filter(recitation__halaqa=halaqa, status='submitted').count() +
        ReviewSubmission.objects.filter(review__halaqa=halaqa, status='submitted').count()
    )

    recitations = Recitation.objects.filter(halaqa=halaqa).select_related('created_by__user')
    reviews = Review.objects.filter(halaqa=halaqa).select_related('created_by__user')
    for r in recitations: r.type = 'تسميع'
    for v in reviews: v.type = 'مراجعة'
    recent_tasks = sorted(chain(recitations, reviews), key=attrgetter('created_at'), reverse=True)[:30]

    avg_score_subquery = RecitationSubmission.objects.filter(student=OuterRef('pk'), status='graded').values('student').annotate(avg_s=Avg('score')).values('avg_s')
    late_tasks_subquery = Recitation.objects.filter(halaqa=halaqa, deadline__lt=timezone.now()).exclude(submissions__student=OuterRef('pk')).values('halaqa').annotate(count=Count('id')).values('count')

    students_list = halaqa.students.select_related('user').annotate(
        avg_score=Subquery(avg_score_subquery),
        late_submissions_count=Subquery(late_tasks_subquery)
    ).order_by('user__username')

    context = {
        'halaqa': halaqa,
        'student_count': student_count,
        'avg_performance': avg_performance,
        'recent_tasks': recent_tasks,
        'students_list': students_list,
        'pending_submissions_halaqa': pending_submissions_halaqa,
    }
    return render(request, 'teachers/halaqa_details.html', context)

@login_required
def teacher_students(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != Profile.ROLE_TEACHER: return redirect("accounts:student_dashboard")

    students_query = Profile.objects.filter(role=Profile.ROLE_STUDENT, halaqa__teachers=profile).distinct()
    halaqa_id = request.GET.get('halaqa')
    if halaqa_id: students_query = students_query.filter(halaqa__id=halaqa_id)
        
    students_query = students_query.annotate(
        last_submission_date=Max('recitation_submissions__created_at'),
        avg_performance=Avg('recitation_submissions__score', filter=Q(recitation_submissions__status='graded'))
    )

    sort_by = request.GET.get('sort', 'name_asc')
    if sort_by == 'name_desc': students_query = students_query.order_by('-user__username')
    elif sort_by == 'performance_desc': students_query = students_query.order_by('-avg_performance')
    elif sort_by == 'performance_asc': students_query = students_query.order_by('avg_performance')
    elif sort_by == 'submission_desc': students_query = students_query.order_by('-last_submission_date')
    else: students_query = students_query.order_by('user__username')

    context = {
        'students_list': students_query,
        'teacher_halaqas': Halaqa.objects.filter(teachers=profile),
    }
    return render(request, 'teachers/students.html', context)

@login_required
def teacher_submissions(request):
    teacher_profile = request.user.profile
    now = timezone.now()
    one_week_ago = now - timedelta(days=7)
    
    recitation_subs = RecitationSubmission.objects.filter(recitation__halaqa__teachers=teacher_profile).select_related('student__user', 'recitation', 'recitation__halaqa')
    review_subs = ReviewSubmission.objects.filter(review__halaqa__teachers=teacher_profile).select_related('student__user', 'review', 'review__halaqa')
    all_submissions_unfiltered = list(chain(recitation_subs, review_subs))
    
    task_type_filter = request.GET.get('type', 'all')
    if task_type_filter == 'recitation':
        all_submissions_filtered_by_type = [s for s in all_submissions_unfiltered if hasattr(s, 'recitation')]
    elif task_type_filter == 'review':
        all_submissions_filtered_by_type = [s for s in all_submissions_unfiltered if hasattr(s, 'review')]
    else:
        all_submissions_filtered_by_type = all_submissions_unfiltered

    all_submissions = sorted(all_submissions_filtered_by_type, key=lambda x: x.created_at, reverse=True)

    status_filter = request.GET.get('status', 'submitted')
    if status_filter in ['submitted', 'graded', 'reviewing']:
        submissions = [s for s in all_submissions if s.status == status_filter]
    else:
        submissions = all_submissions
        
    pending_count = sum(1 for s in all_submissions_unfiltered if s.status == 'submitted')
    completed_this_week_count = sum(1 for s in all_submissions_unfiltered if s.status == 'graded' and s.updated_at >= one_week_ago)
    needs_resubmission_count = sum(1 for s in all_submissions_unfiltered if s.status == 'reviewing')
    
    graded_submissions = [s for s in all_submissions_unfiltered if s.status == 'graded' and s.updated_at > s.created_at]
    total_grading_time = timedelta(0)
    average_grading_time = "N/A"
    if graded_submissions:
        for sub in graded_submissions: total_grading_time += sub.updated_at - sub.created_at
        average_seconds = total_grading_time.total_seconds() / len(graded_submissions)
        if average_seconds >= 86400: average_grading_time = f"{int(average_seconds // 86400)} يوم"
        elif average_seconds >= 3600: average_grading_time = f"{int(average_seconds // 3600)} ساعة"
        else: average_grading_time = f"{int(average_seconds // 60)} دقيقة"

    context = {
        'submissions': submissions,
        'pending_count': pending_count,
        'completed_this_week_count': completed_this_week_count,
        'needs_resubmission_count': needs_resubmission_count,
        'average_grading_time': average_grading_time,
        'active_filter': status_filter,
        'active_type_filter': task_type_filter,
        'teacher_halaqas': Halaqa.objects.filter(teachers=teacher_profile)
    } 
    return render(request, 'teachers/submissions.html', context)

@login_required
def teacher_settings_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            if username: user.username = username
            if email: user.email = email
            user.save()

            if request.FILES.get('avatar'):
                profile.photo = request.FILES['avatar']
            elif request.POST.get('remove_avatar') == 'true':
                profile.photo.delete(save=False)
                profile.photo = None
            
            profile.email_notifications = 'email_notifications' in request.POST
            profile.app_notifications = 'app_notifications' in request.POST
            profile.save()

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if current_password or new_password or confirm_password:
                if not (current_password and new_password and confirm_password):
                    return JsonResponse({'status': 'error', 'message': 'يرجى ملء جميع حقول كلمة المرور.'}, status=400)
                if not user.check_password(current_password):
                    return JsonResponse({'status': 'error', 'message': 'كلمة المرور الحالية غير صحيحة.'}, status=400)
                if new_password != confirm_password:
                    return JsonResponse({'status': 'error', 'message': 'كلمة المرور الجديدة غير متطابقة.'}, status=400)
                
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)

            return JsonResponse({'status': 'success', 'message': 'تم حفظ التغييرات بنجاح!', 'new_avatar_url': profile.avatar_url})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'حدث خطأ: {str(e)}'}, status=500)

    return render(request, 'teachers/teacher_settings.html', {'profile': profile})

# ==============================================================================
# Teacher Actions (AJAX)
# ==============================================================================

@login_required
@require_POST
def add_halaqa_task(request):
    try:
        halaqa_id   = request.POST.get('halaqa_id')
        task_type   = request.POST.get('task_type', 'recitation')
        surah_id    = request.POST.get('surah_id')
        start_ayah  = request.POST.get('start_ayah')
        end_ayah    = request.POST.get('end_ayah')
        deadline_s  = request.POST.get('deadline')

        halaqa = Halaqa.objects.get(id=halaqa_id, teachers=request.user.profile)
        surah  = get_object_or_404(Surah, pk=surah_id)
        deadline = parse_datetime(deadline_s) if deadline_s else None

        task_data = {'halaqa': halaqa, 'created_by': request.user.profile, 'surah': surah, 'start_ayah': start_ayah, 'end_ayah': end_ayah, 'deadline': deadline}

        if task_type == 'review': Review.objects.create(**task_data)
        else: Recitation.objects.create(**task_data)

        return JsonResponse({'status': 'success', 'message': f'تمت إضافة المهمة بنجاح لحلقة {halaqa.name}.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def add_student_task(request):
    try:
        halaqa_id   = request.POST.get('halaqa_id')
        student_id  = request.POST.get('student_id')
        task_type   = request.POST.get('task_type', 'recitation')
        surah_id    = request.POST.get('surah_id')
        start_ayah  = request.POST.get('start_ayah')
        end_ayah    = request.POST.get('end_ayah')
        deadline_s  = request.POST.get('deadline')

        halaqa  = get_object_or_404(Halaqa, id=halaqa_id, teachers=request.user.profile)
        student = get_object_or_404(Profile, id=student_id, role=Profile.ROLE_STUDENT)
        if student.halaqa_id != halaqa.id: return JsonResponse({'status': 'error', 'message': 'الطالب ليس ضمن هذه الحلقة.'}, status=400)

        surah    = get_object_or_404(Surah, pk=surah_id)
        deadline = parse_datetime(deadline_s) if deadline_s else None

        base = {'halaqa': halaqa, 'created_by': request.user.profile, 'surah': surah, 'start_ayah': start_ayah, 'end_ayah': end_ayah, 'deadline': deadline, 'assigned_to': student}
        if task_type == 'review': Review.objects.create(**base)
        else: Recitation.objects.create(**base)

        return JsonResponse({'status': 'success', 'message': f'تمت إضافة المهمة للطالب {student.user.username}.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
@login_required
@transaction.atomic
def grade_submission(request, submission_type, submission_id):
    try:
        if submission_type == 'recitation':
            submission = get_object_or_404(RecitationSubmission, pk=submission_id, recitation__halaqa__teachers=request.user.profile)
        elif submission_type == 'review':
            submission = get_object_or_404(ReviewSubmission, pk=submission_id, review__halaqa__teachers=request.user.profile)
        else:
            return JsonResponse({"status": "error", "message": "نوع تسليم غير صالح."}, status=400)

        data = json.loads(request.body.decode("utf-8"))
        hifdh = float(data.get("hifdh", 0))
        rules = float(data.get("rules", 0))
        notes = (data.get("notes") or "").strip()
        
        if not (0 <= hifdh <= 5) or not (0 <= rules <= 5): raise ValueError("قيم التقييم يجب أن تكون بين 0 و 5.")
            
        submission.hifdh = hifdh
        submission.rules = rules
        submission.score = hifdh + rules
        submission.notes = notes
        submission.status = "graded"
        submission.save()

        teacher = request.user.profile
        my_halaqat = Halaqa.objects.filter(teachers=teacher)
        pending_count = RecitationSubmission.objects.filter(recitation__halaqa__in=my_halaqat, status='submitted').count() + ReviewSubmission.objects.filter(review__halaqa__in=my_halaqat, status='submitted').count()
        avg_perf = round((RecitationSubmission.objects.filter(recitation__halaqa__in=my_halaqat, status='graded').aggregate(avg=Avg('score'))['avg'] or 0) * 10, 1)

        return JsonResponse({
            "status": "success", "message": "تم حفظ التقييم بنجاح!",
            "stats": {"pending_submissions_count": pending_count, "average_performance": avg_perf}
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@require_POST
@login_required(login_url="accounts:login")
def send_halaqa_notification(request, halaqa_id):
    profile = request.user.profile
    if profile.role != Profile.ROLE_TEACHER: return JsonResponse({'status': 'error', 'message': 'غير مصرح'}, status=403)

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        if not message: return JsonResponse({'status': 'error', 'message': 'الرسالة فارغة'}, status=400)

        halaqa = get_object_or_404(Halaqa, id=halaqa_id, teachers=profile)
        students = halaqa.students.all()
        if not students.exists(): return JsonResponse({'status': 'error', 'message': 'لا يوجد طلاب'}, status=400)

        Notification.objects.bulk_create([Notification(recipient=s, title=data.get('title', '') or f'رسالة من حلقة {halaqa.name}', message=message) for s in students])
        return JsonResponse({'status': 'success', 'message': f'تم الإرسال لـ {len(students)} طالب.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def unassign_student_from_halaqa(request, student_id):
    if request.user.profile.role != 'teacher': return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
    try:
        student = Profile.objects.get(id=student_id, role='student')
        if student.halaqa and request.user.profile in student.halaqa.teachers.all():
            student.halaqa = None
            student.save()
            return JsonResponse({'status': 'success', 'message': 'Student unassigned successfully.'})
        return JsonResponse({'status': 'error', 'message': 'Student not found in your halaqas.'}, status=404)
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'}, status=404)

@login_required
@require_POST
def get_pending_requests(request):
    user = request.user
    if not hasattr(user, 'profile') or user.profile.role != Profile.ROLE_TEACHER: return JsonResponse({'status': 'error', 'message': 'غير مصرح'}, status=403)

    pending_students = Profile.objects.filter(role=Profile.ROLE_STUDENT, halaqa__in=user.profile.halaqat_as_teacher.all(), teacher_status=Profile.TEACHER_PENDING).select_related('user', 'halaqa')
    data = [{'id': p.user.id, 'name': p.user.get_full_name() or p.user.username, 'email': p.user.email, 'halaqa': p.halaqa.name, 'date': p.user.date_joined.strftime('%Y-%m-%d'), 'avatar_url': p.avatar_url} for p in pending_students]
    return JsonResponse({'status': 'success', 'students': data})

@login_required
@require_POST
def process_join_request(request):
    user = request.user
    if not hasattr(user, 'profile') or user.profile.role != Profile.ROLE_TEACHER: return JsonResponse({'status': 'error', 'message': 'غير مصرح'}, status=403)

    student_id = request.POST.get('student_id')
    action = request.POST.get('action')
    if not student_id or action not in ['approve', 'reject']: return JsonResponse({'status': 'error', 'message': 'بيانات غير صالحة'}, status=400)

    try:
        student_user = User.objects.get(id=student_id)
        student_profile = student_user.profile
        if not user.profile.halaqat_as_teacher.filter(id=student_profile.halaqa.id).exists(): return JsonResponse({'status': 'error', 'message': 'ليس في حلقاتك'}, status=403)

        if action == 'approve':
            student_user.is_active = True
            student_user.save()
            student_profile.teacher_status = Profile.TEACHER_APPROVED
            student_profile.save()
            msg = 'تم قبول الطالب بنجاح'
        else:
            student_profile.teacher_status = Profile.TEACHER_REJECTED
            student_profile.save()
            msg = 'تم رفض الطالب'
        return JsonResponse({'status': 'success', 'message': msg})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ==============================================================================
# API Views
# ==============================================================================

@login_required
def get_halaqa_surahs(request, halaqa_id):
    try:
        halaqa = Halaqa.objects.get(id=halaqa_id, teachers=request.user.profile)
        if halaqa.juz_from and halaqa.juz_to:
            surahs = Surah.objects.filter(juz_from__lte=halaqa.juz_to, juz_to__gte=halaqa.juz_from).order_by("id")
        else:
            surahs = Surah.objects.none()
        return JsonResponse({'surahs': [{'id': s.id, 'name': s.name} for s in surahs]})
    except Halaqa.DoesNotExist:
        return JsonResponse({'error': 'Halaqa not found'}, status=404)

@login_required
def get_submission_details(request, submission_type, submission_id):
    try:
        if submission_type == 'recitation':
            sub = get_object_or_404(RecitationSubmission.objects.select_related('student__user', 'recitation__surah'), pk=submission_id, recitation__halaqa__teachers=request.user.profile)
            task = sub.recitation
        elif submission_type == 'review':
            sub = get_object_or_404(ReviewSubmission.objects.select_related('student__user', 'review__surah'), pk=submission_id, review__halaqa__teachers=request.user.profile)
            task = sub.review
        else:
            return JsonResponse({'error': 'Invalid type'}, status=400)

        data = {
            'student_name': sub.student.user.username,
            'avatar_url': sub.student.avatar_url,
            'recitation_title': str(task),
            'deadline': task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else 'غير محدد',
            'submitted_at': sub.created_at.strftime('%Y-%m-%d %H:%M'),
            'audio_url': sub.audio.url if sub.audio else '',
            'current_notes': sub.notes or '',
            'current_hifdh': sub.hifdh or 5,
            'current_rules': sub.rules or 5,
        }
        return JsonResponse(data)
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)

@require_POST
@login_required
def logout_other_devices_view(request):
    Session.objects.filter(get_decoded__user_id=request.user.id).exclude(session_key=request.session.session_key).delete()
    return JsonResponse({'status': 'success', 'message': 'تم تسجيل الخروج من جميع الأجهزة الأخرى.'})

@require_POST
@login_required
def delete_account_view(request):
    request.user.is_active = False
    request.user.save()
    return JsonResponse({'status': 'success', 'message': 'تم تعطيل حسابك بنجاح.'})
