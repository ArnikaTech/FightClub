from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('manifest.json', views.manifest, name='manifest'),
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('social/add/', views.SocialLinkCreateView.as_view(), name='social_add'),
    path('social/<int:pk>/edit/', views.SocialLinkEditView.as_view(), name='social_edit'),
    path('social/<int:pk>/delete/', views.SocialLinkDeleteView.as_view(), name='social_delete'),
]
