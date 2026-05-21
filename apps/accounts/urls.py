from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/password/', views.PasswordChangeView.as_view(), name='password_change'),

    path('messages/', views.InboxView.as_view(), name='inbox'),
    path('messages/sent/', views.SentView.as_view(), name='sent_messages'),
    path('messages/compose/', views.ComposeView.as_view(), name='compose_message'),
    path('messages/<int:pk>/', views.ThreadView.as_view(), name='message_thread'),
    path('messages/<int:pk>/reply/', views.ReplyView.as_view(), name='reply_message'),
    path('messages/bulk/', views.BulkMessageView.as_view(), name='bulk_message'),
]
