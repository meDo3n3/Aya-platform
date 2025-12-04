# hifztracker/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts import views as acc_views

urlpatterns = [
    path('', acc_views.landing_page, name='landing'),
    path('go/', acc_views.go, name='go'),
    
    path('admin/', admin.site.urls),
    ]

# hifztracker/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts import views as acc_views

urlpatterns = [
    path('', acc_views.landing_page, name='landing'),
    path('go/', acc_views.go, name='go'),
    
    path('admin/', admin.site.urls),

    # Main Accounts URLs (Namespaced)
    path('accounts/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),

    # Tracker URLs
    path('tracker/', include('apps.tracker.urls')),

    # Include Accounts URLs at root for direct access (login, register, etc.)
    # This allows /login/ instead of /accounts/login/
    path('', include(('apps.accounts.urls', 'accounts'), namespace='public_auth')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)