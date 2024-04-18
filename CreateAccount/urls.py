from django.urls import path

from . import views

urlpatterns = [
    path('', views.NewCreateAccount, name='index'),
    path('<int:error>/', views.CreateAccountError, name='CreateAccountError'),
    path('ChangePassword/', views.ChangePassword, name='ChangePassword'),
    path('ChangeWallet/', views.ChangeWallet, name='ChangeWallet'),
    path('ChangeBrand/', views.ChangeBrand, name='ChangeBrand'),
    path('ChangeCompanyBrand/', views.ChangeCompanyBrand, name='ChangeCompanyBrand'),
    path('RemoveWallet/', views.RemoveWallet, name='RemoveWallet'),
    path('NewUser/', views.NewUser, name='NewUser'),
    path('VerifyUser/<str:userID>/', views.VerifyUser, name='VerifyUser'),
    path('VerifyUser/<str:userID>/TakePass/', views.AddPassword, name='VerifyUserTakePass'),
    path('AddPassword/<str:userID>/', views.AddPassword, name='AddPassword'),
    path('AddDocuments/', views.AddDocuments, name='AddDocuments'),
    path('TermsAndConditions/', views.DownloadTermsAndConditions, name='TermsAndConditions'),
    path('PrivacyPolicy/', views.DownloadPrivacyPolicy, name='PrivacyPolicy'),
    path('VerifyUser/<str:userID>/FreeTrial/', views.VerifyUserFreeTrial, name='VerifyUserFreeTrial'),
]