from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('AddPersonalSub/', views.AddPersonalSub, name='AddPersonalSub'),
    path('AddBusinessSub/', views.AddBusinessSub, name='AddBusinessSub'),
    path('Error/<str:error>/', views.error, name='error'),
    path('Update/<str:update>/', views.update, name='update'),
    path('Settings/', views.Settings, name='settings'),
    path('Settings/RegisterCard/', views.RegisterCard, name='RegisterCard'),
    path('Settings/Update/<str:update>/', views.SettingsUpdate, name='settingsUpdate'),
    path('Settings/Error/<str:error>/', views.SettingsError, name='settingsError'),
    path('Settings/Subscription/<int:choice>/', views.Subscription, name='subscription'),
    path('Settings/ShowPage/Subscription/', views.ShowSubPage, name='ShowSubPage'),
    path('Settings/DownloadReturnPolicy/', views.DownloadReturnPolicy, name="RefundPolicy"),
    path('Settings/TurnOffRenew/', views.TurnOffRenew, name="TurnOffRenew"),
    path('Settings/TurnOnRenew/', views.TurnOnRenew, name="TurnOnRenew"),
    path('Settings/TurnOffRenewCompany/', views.TurnOffRenewCompany, name="TurnOffRenewCompany"),
    path('Settings/TurnOnRenewCompany/', views.TurnOnRenewCompany, name="TurnOnRenewCompany"),
    path('CompanyDashboard/', views.CompanyDashboard, name='Company Dashboard'),
    path('CompanyDashboard/CreateCompany/', views.CreateCompany, name='Create Company'),
    path('CompanyDashboard/AddMember/', views.AddMember, name='Company Members'),
    path('CompanyDashboard/ConfirmMember/<str:name>/<str:email>/<str:permission>/<str:adderUser>/', views.ConfirmMember, name='Confirm Company Member'),
    path('CompanyDashboard/Settings/', views.CompanySettings, name='Company Settings'),
    path('CompanyDashboard/Settings/<str:update>/', views.CompanySettingsUpdate, name='Company Settings Update'),
    path('CompanyDashboard/Documents/<str:filterType>/<int:page>/', views.CompanyDocuments, name='Company Documents'),
    path('CompanyDashboard/Templates/<str:filterType>/<int:page>/', views.CompanyTemplates, name='Company Templates'),
    path('CompanyDashboard/Members/<str:filterType>/<int:page>/', views.CompanyMembers, name='Company Members'),
    path('CompanyDashboard/ManageMember/<str:userID>/', views.ManageCompanyMember, name='Manage Member'),
    path('CompanyDashboard/ManageMember/<str:userID>/ChangePermission/', views.ChangeMember, name='Change Member'),
    path('CompanyDashboard/ManageMember/<str:userID>/Delete/', views.DeleteMember, name='Delete Member'),
    path('Sent/<int:pageNum>/', views.sent, name="sent"),
    path('Received/<int:pageNum>/', views.received, name="sent"),
    path('Drafts/<int:pageNum>/', views.drafts, name="drafts"),
    path('Templates/<int:pageNum>/', views.templates, name="templates"),
    path('Logout/', views.logout, name='logout'),
    path('SaveSignature/', views.SaveSignature, name="SaveSignature")
]