from django.urls import path

from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('add/', views.StudentCreateView.as_view(), name='student_add'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/edit/', views.StudentEditView.as_view(), name='student_edit'),

    path('<int:pk>/contact/add/', views.ContactCreateView.as_view(), name='contact_add'),
    path('contact/<int:contact_pk>/edit/', views.ContactEditView.as_view(), name='contact_edit'),
    path('contact/<int:contact_pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),

    path('<int:pk>/insurance/add/', views.InsuranceCreateView.as_view(), name='insurance_add'),

    path('attendance/', views.AttendanceView.as_view(), name='attendance'),
    path('attendance/save/', views.AttendanceSaveView.as_view(), name='attendance_save'),

    path('absentees/', views.AbsenteeListView.as_view(), name='absentees'),
]
