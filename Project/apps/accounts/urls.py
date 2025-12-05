# apps/accounts/urls.py
# Updated for 2FA
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # --- Authentication ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-login/', views.verify_login_view, name='verify_login'),
    path('verify-code/', views.verify_reset_view, name='verify_code'),
    path('send-registration-otp/', views.send_registration_otp, name='send_registration_otp'),
    path('go/', views.go, name='go'),

    # --- Student URLs ---
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('settings/', views.student_settings_view, name='student_settings'),
    path('recitations/<int:pk>/start/', views.recitation_start, name='recitation_start'),
    path('reviews/<int:pk>/start/', views.review_start, name='review_start'),
    path('submit_task/<str:task_type>/<int:task_id>/', views.submit_task, name='submit_task'),
    path('recitation/<int:pk>/action/', views.recitation_action, name='recitation_action'),
    path('review/<int:pk>/action/', views.review_action, name='review_action'),

    # --- Teacher URLs ---
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/halaqat/', views.teacher_halaqat, name='teacher_halaqat'),
    path('teacher/halaqa/<int:halaqa_id>/', views.halaqa_details_view, name='halaqa_details'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/submissions/', views.teacher_submissions, name='teacher_submissions'),
    path('teacher/settings/', views.teacher_settings_view, name='teacher_settings'),

    # --- Teacher Actions (AJAX) ---
    path('teacher/halaqa/add_task/', views.add_halaqa_task, name='add_halaqa_task'),
    path('teacher/student/add_task/', views.add_student_task, name='add_student_task'),
    path('teacher/submission/<str:submission_type>/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('halaqa/<int:halaqa_id>/send-notification/', views.send_halaqa_notification, name='send_halaqa_notification'),
    path('student/<int:student_id>/unassign/', views.unassign_student_from_halaqa, name='unassign_student'),
    path('get-pending-requests/', views.get_pending_requests, name='get_pending_requests'),
    path('process-join-request/', views.process_join_request, name='process_join_request'),

    # --- API URLs ---
    path('api/halaqa/<int:halaqa_id>/surahs/', views.get_halaqa_surahs, name='get_halaqa_surahs'),
    path('api/submission/<str:submission_type>/<int:submission_id>/', views.get_submission_details, name='get_submission_details'),
    path('api/logout-other-devices/', views.logout_other_devices_view, name='logout_other_devices'),
    path('api/delete-account/', views.delete_account_view, name='delete_account'),
]
