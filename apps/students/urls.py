from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('add/', views.StudentCreateView.as_view(), name='student_add'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/edit/', views.StudentEditView.as_view(), name='student_edit'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('<int:pk>/activate/', views.StudentActivateView.as_view(), name='student_activate'),

    path('<int:pk>/insurance/add/', views.InsuranceCreateView.as_view(), name='insurance_add'),

    path('<int:pk>/contact/add/', views.ContactCreateView.as_view(), name='contact_add'),
    path('contact/<int:contact_pk>/edit/', views.ContactEditView.as_view(), name='contact_edit'),
    path('contact/<int:contact_pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),

    path('attendance/', views.AttendanceView.as_view(), name='attendance'),
    path('absentees/', views.AbsenteeListView.as_view(), name='absentees'),
    path('attendance/save/', views.AttendanceSaveView.as_view(), name='attendance_save'),
    path('attendance/toggle/<int:student_id>/', views.AttendanceToggleView.as_view(), name='attendance_toggle'),

    path('classes/', views.ClassGroupListView.as_view(), name='class_list'),
    path('classes/add/', views.ClassGroupCreateView.as_view(), name='class_add'),
    path('classes/<int:pk>/edit/', views.ClassGroupEditView.as_view(), name='class_edit'),
    path('classes/<int:pk>/delete/', views.ClassGroupDeleteView.as_view(), name='class_delete'),
    path('classes/<int:pk>/activate/', views.ClassGroupActivateView.as_view(), name='class_activate'),

    path('classes/<int:class_id>/shifts/', views.ShiftListView.as_view(), name='shift_list'),
    path('classes/<int:class_id>/shifts/add/', views.ShiftCreateView.as_view(), name='shift_add'),
    path('shifts/<int:pk>/edit/', views.ShiftEditView.as_view(), name='shift_edit'),
    path('shifts/<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift_delete'),
    path('shifts/<int:pk>/activate/', views.ShiftActivateView.as_view(), name='shift_activate'),

    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/add/', views.EnrollmentCreateView.as_view(), name='enrollment_add'),
    path('enrollments/<int:pk>/edit/', views.EnrollmentEditView.as_view(), name='enrollment_edit'),
    path('enrollments/<int:pk>/delete/', views.EnrollmentDeleteView.as_view(), name='enrollment_delete'),
    path('enrollments/<int:pk>/activate/', views.EnrollmentActivateView.as_view(), name='enrollment_activate'),
]