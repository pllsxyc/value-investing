from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.calculator, name='calculator'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorites/<int:pk>/delete/', views.delete_favorite, name='delete_favorite'),
    path('tags/<int:pk>/delete/', views.delete_tag, name='delete_tag'),
    path('login/', views.AppLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]
