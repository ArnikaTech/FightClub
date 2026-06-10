from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('manifest.json', core_views.manifest, name='manifest'),
    path('service-worker.js', core_views.service_worker, name='service_worker'),
]

# Third party
urlpatterns += []

# Apps
urlpatterns += [
    path('', include('apps.accounts.urls', namespace='accounts')),
    path('core/', include('apps.core.urls', namespace='core')),
    path('clubs/', include('apps.clubs.urls', namespace='clubs')),
    path('finance/', include('apps.finance.urls', namespace='finance')),
    path('students/', include('apps.students.urls', namespace='students')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
