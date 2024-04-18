"""SecureSign URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include, path
from .admin import admin_site
from Home import views as HomeView
from CreateAccount import views as CreateAccountView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from Home.sitemaps import StaticViewSitemap
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.http import HttpResponse

sitemaps = {
    'static': StaticViewSitemap
}

urlpatterns = [
    path('admin/Login/', auth_views.LoginView.as_view(template_name='AdminLogin.html'), name='login'), 
    path('admin/', admin_site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
    path('', HomeView.index, name='index'),
    path('robots.txt', TemplateView.as_view(template_name="Home/robots.txt", content_type='text/plain')),
    path('ChatPage/', HomeView.Chat, name='Chat'),
    path('OpenChat/', HomeView.OpenChat, name='OpenChat'),
    path('CloseChat/', HomeView.CloseChat, name='CloseChat'),
    path('OpenPublicChat/', HomeView.OpenPublicChat, name='OpenPublicChat'),
    path('TicketSent/', HomeView.TicketSent, name='index'),
    path('Contact/', HomeView.Contact, name='Contact'),
    path('TermsOfService/', HomeView.Terms, name='Terms'),
    path('Contact/SubmitTicket/', HomeView.SubmitTicket, name='SubmitTicket'),
    path('GettingStarted/', HomeView.GettingStarted, name='GettingStarted'),
    path('TutorialDocumentSending/', HomeView.TutorialDocumentSending, name='TutorialDocumentSending'),
    path('TutorialTemplateCreation/', HomeView.TutorialTemplateCreation, name='TutorialTemplateCreation'),
    path('FreeForSigners/', HomeView.FreeForSigners, name='FreeForSigners'),
    path('PlansAndPricing/', HomeView.PlansAndPricing, name='PlansAndPricing'),
    path('NewCompanySignup/', HomeView.NewCompanySignup, name='NewCompanySignup'),
    path('Showcase/', HomeView.Showcase, name='Showcase'),
    path('FAQ/', HomeView.FAQ, name='FAQ'),
    path('UserDashboard/', include('UserDashboard.urls')),
    path('ManageDocument/', include('ManageDocument.urls')),
    path('CreateAccount/', include('CreateAccount.urls')),
    path('Login/', include('Login.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#handler400 = 'Home.views.error_404_view'
#handler403 = 'Home.views.error_404_view'
#handler404 = 'Home.views.error_404_view'