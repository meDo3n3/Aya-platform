# apps/accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # --- Authentication ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('go/', views.go, name='go'),

    # --- Student URLs ---
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('settings/', views.student_settings_view, name='student_settings'),
    
    # --- START: New and Updated URLs for Recording ---
    path("recitations/<int:pk>/start/", views.recitation_start, name="recitation_start"),
    path("reviews/<int:pk>/start/", views.review_start, name="review_start"), # ADD THIS
    path('submit_task/<str:task_type>/<int:task_id>/', views.submit_task, name='submit_task'),
    # --- END: New and Updated URLs for Recording ---

    # --- Teacher URLs ---
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/halaqat/", views.teacher_halaqat, name="teacher_halaqat"),
    path("teacher/halaqa/<int:halaqa_id>/", views.halaqa_details_view, name='halaqa_details'),
    path("teacher/students/", views.teacher_students, name="teacher_students"),
    path('student/<int:student_id>/unassign/', views.unassign_student_from_halaqa, name='unassign_student'),
    path('teacher/submissions/', views.teacher_submissions, name='teacher_submissions'),
    path('teacher/settings/', views.teacher_settings_view, name='teacher_settings'),
    path('teacher/halaqa/add_task/', views.add_halaqa_task, name='add_halaqa_task'),
    path('teacher/student/add_task/', views.add_student_task, name='add_student_task'),
    path('halaqa/<int:halaqa_id>/send-notification/', views.send_halaqa_notification, name='send_halaqa_notification'),
    path('teacher/submission/<str:submission_type>/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),


    
    # --- API URLs ---
    path('api/halaqa/<int:halaqa_id>/surahs/', views.get_halaqa_surahs, name='get_halaqa_surahs'),
    path('api/submission/<str:submission_type>/<int:submission_id>/', views.get_submission_details, name='get_submission_details'),
    path('api/logout-other-devices/', views.logout_other_devices_view, name='logout_other_devices'),
    path('api/delete-account/', views.delete_account_view, name='delete_account'),





    path(
        "recitation/<str:task_type>/<int:task_id>/",
        views.recitation_record,
        name="recitation_record",
    ),
    path(
        "submit/<str:task_type>/<int:task_id>/",
        views.submit_task,
        name="submit_task",
    ),

    # --- Forgot Password ---
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-code/', views.verify_reset_view, name='verify_code'),
    
    # Student Approval
    path('get-pending-requests/', views.get_pending_requests, name='get_pending_requests'),
    path('process-join-request/', views.process_join_request, name='process_join_request'),
]


