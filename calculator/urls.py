from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('calc/', views.calculator, name='calculator'),
    path('api/stock/search/', views.stock_search, name='stock_search'),
    path('api/stock/autofill/', views.stock_autofill, name='stock_autofill'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorites/<int:pk>/delete/', views.delete_favorite, name='delete_favorite'),
    path('tags/<int:pk>/delete/', views.delete_tag, name='delete_tag'),
    path('login/', views.AppLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    # 收藏的直达链接：/<用户名>/s/<股票代码>/（仅本人可见，放最后避免遮蔽上面的固定路由）
    path('<str:username>/s/<str:ticker>/', views.stock_detail, name='stock_detail'),
]
