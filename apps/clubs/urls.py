from django.urls import path

from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.ClubListView.as_view(), name='club_list'),
    path('add/', views.ClubCreateView.as_view(), name='club_add'),
    path('<int:pk>/', views.ClubDetailView.as_view(), name='club_detail'),
    path('<int:pk>/edit/', views.ClubEditView.as_view(), name='club_edit'),
    path('<int:pk>/delete/', views.ClubDeleteView.as_view(), name='club_delete'),
    path('<int:pk>/activate/', views.ClubActivateView.as_view(), name='club_activate'),
    path('get-cities/<int:province_id>/', views.get_cities, name='get_cities'),

    path('coaches/', views.CoachListView.as_view(), name='coach_list'),
    path('coaches/add/', views.CoachCreateView.as_view(), name='coach_add'),
    path('coaches/<int:pk>/edit/', views.CoachEditView.as_view(), name='coach_edit'),
    path('coaches/<int:pk>/delete/', views.CoachDeleteView.as_view(), name='coach_delete'),

    path('provinces/<int:pk>/delete/', views.ProvinceDeleteView.as_view(), name='province_delete'),
    path('cities/<int:pk>/delete/', views.CityDeleteView.as_view(), name='city_delete'),
    path('provinces/', views.ProvinceListView.as_view(), name='province_list'),
    path('provinces/add/', views.ProvinceCreateView.as_view(), name='province_add'),
    path('provinces/<int:pk>/edit/', views.ProvinceEditView.as_view(), name='province_edit'),
    path('cities/', views.CityListView.as_view(), name='city_list'),
    path('cities/add/', views.CityCreateView.as_view(), name='city_add'),
    path('cities/<int:pk>/edit/', views.CityEditView.as_view(), name='city_edit'),
]