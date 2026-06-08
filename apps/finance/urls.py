from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path('add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/add/', views.ExpenseCreateView.as_view(), name='expense_add'),
    path('report/', views.ReportView.as_view(), name='report'),

    path('<int:pk>/edit/', views.PaymentEditView.as_view(), name='payment_edit'),
    path('<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    path('expenses/<int:pk>/edit/', views.ExpenseEditView.as_view(), name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),

    path('fee/<int:student_pk>/add/', views.FeeAddView.as_view(), name='fee_add'),
    path('fee/<int:pk>/edit/', views.FeeEditView.as_view(), name='fee_edit'),
    path('fee/<int:pk>/delete/', views.FeeDeleteView.as_view(), name='fee_delete'),
]