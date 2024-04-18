from django.urls import path

from . import views

urlpatterns = [
    path('', views.NewLogin, name='index'),
    path('ForgotPassword/', views.ForgotPassword, name='ForgotPassword'),
    path('ResetPassword/<str:userID>/', views.ResetPassword, name='ResetPassword'),
    path('AccountDNE/', views.AccountDNE, name='AccountDNE'),
    path('AccountDNE/PleaseWait/', views.AccountDNEWait, name='AccountDNEWait'),
]