from socket import AddressInfo
from django.contrib.admin import AdminSite
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.urls import path
from django.core import mail
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from email.mime.image import MIMEImage
from django.contrib.sites.models import Site
import math

from Home import models

import sys
sys.path.append("..") # Adds higher directory to python modules path.

from CreateAccount import models as AccountModels
from Home import models as HomeModels
from ManageDocument import models as DocumentModels

import os

class MyAdminSite(AdminSite):
    site_header = 'Iris Documents Administration'
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('', self.Landing),
            path('Login/', self.Login),
            path('Home/', self.AdminHome),
            path('Map/', self.Map),
            path('ManageDatabase/', self.ManageDatabase),
            path('Support/<int:page>/', self.Support),
            path('Support/<int:page>/<int:numTicket>/', self.SupportTicket),
            path('Support/Submit/', self.SupportSubmit)
        ]
        return my_urls + urls
    
    def SupportSubmit(self, request):
        if request.method == 'POST':
            email = request.POST['email']
            ticket = request.POST['ticket']

            subject = 'Support Request'
            text_content = ticket
            html_content = render_to_string('email.html', {'text':text_content})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'support@support.irisdocuments.com', [email], connection=thisConnection)
                email.mixed_subtype = 'related'
                email.attach_alternative(html_content, 'text/html')
                img_dir = 'static/stylesheets/images/'
                image = 'irislogo_top.png'
                file_path = os.path.join(img_dir, image)
                with open(file_path, 'r') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<{name}>'.format(name=image))
                    img.add_header('Content-Disposition', 'inline', filename=image)
                email.attach(img)
                #email.send()

        return HttpResponseRedirect('/admin/Support/')

    def Support(self, request, page):

        tickets = models.Tickets.objects.get(pk=1).tickets
        pages = math.ceil(tickets/10)

        ticket = (page*10) - 10

        ticketNames = []
        ticketEmails = []
        count = 0
        while count < 10:
            try:
                thisTicket = models.Ticket.objects.get(pk=(ticket+count))
                ticketNames.append(thisTicket.name)
                ticketEmails.append(thisTicket.email)
            except Exception:
                pass
            count += 1

        nextPage = []
        if pages > page:
            nextPage.append('Next Page')
            nextPage.append(str(page+1))

        lastPage = []
        if pages > (page+1):
            lastPage.append('Last Page')
            lastPage.append(str(pages))

        return TemplateResponse(request, "Support.html", {'ticketNames':ticketNames, 'ticketEmails':ticketEmails, 'nextPage':nextPage, 'lastPage':lastPage, 'page':page})

    def SupportTicket(self, request, page, numTicket):

        tickets = models.Tickets.objects.get(pk=1).tickets
        pages = math.ceil(tickets/10)

        numTicket -= 10
        while page > 0:
            numTicket += 10
            page -= 1

        ticket = (page*10) - 10

        ticketNames = []
        ticketEmails = []
        count = 0
        while count < 10:
            try:
                thisTicket = models.Ticket.objects.get(pk=(ticket+count))
                ticketNames.append(thisTicket.name)
                ticketEmails.append(thisTicket.email)
            except Exception:
                pass
            count += 1

        nextPage = []
        if pages > page:
            nextPage.append('Next Page')
            nextPage.append(str(page+1))

        lastPage = []
        if pages > (page+1):
            lastPage.append('Last Page')
            lastPage.append(str(pages))
        
        ticketInfo = []
        thisTicket = models.Ticket.objects.get(pk=numTicket)
        ticketInfo.append(thisTicket.name)
        ticketInfo.append(thisTicket.email)
        ticketInfo.append(thisTicket.ticket)

        return TemplateResponse(request, "Support.html", {'ticketNames':ticketNames, 'ticketEmails':ticketEmails, 'nextPage':nextPage, 'lastPage':lastPage, 'page':page, 'ticketInfo':ticketInfo})

    def Login(self, request):
        context = dict(
           # Include common variables for rendering the admin template.
           self.each_context(request)
        )
        return TemplateResponse(request, "AdminLogin.html", context)

    def Landing(self, request):
        context = dict(
           # Include common variables for rendering the admin template.
           self.each_context(request)
        )
        response = TemplateResponse(request, "Landing.html", context)
        response.set_cookie('SupportUser', 'Not Connected')
        return response

    def AdminHome(self, request):
        context = dict(
           # Include common variables for rendering the admin template.
           self.each_context(request)
        )
        return TemplateResponse(request, "Landing.html", context)

    def Map(self, request):

        last25LoggedObj = AccountModels.Last25LoggedIn.objects.get(pk=1)

        count = 1
        users = []
        while count <= 25:
            try:
                users.append(last25LoggedObj.users[count])
                count += 1
            except Exception:
                count += 1
                break

        #database = IP2Location.IP2Location("../IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-SAMPLE.BIN")
        
        latitudes = []
        longitudes = []
        for each in users:
            email = AccountModels.AccountLookupByID.objects.get(pk=each).email
            account = AccountModels.Account.objects.get(pk=email)

            #rec = database.get_all(account.currentIP)

            #latitudes.append(float(rec.latitude))
            #longitudes.append(float(rec.longitude))
        

        return TemplateResponse(request, "AdminIndex.html", {'latitudes':latitudes,'longitudes':longitudes})

    def ManageDatabase(self, request):

        context = dict(
           # Include common variables for rendering the admin template.
           self.each_context(request)
        )
        return TemplateResponse(request, "ManageDatabase.html", context)


admin_site = MyAdminSite(name='myadmin')

admin_site.register(Site)

admin_site.register(AccountModels.Accounts)
admin_site.register(AccountModels.Account)
admin_site.register(AccountModels.AccountLookupByID)
admin_site.register(AccountModels.Companys)
admin_site.register(AccountModels.Company)
admin_site.register(AccountModels.CompanyLookupByAccountID)
admin_site.register(AccountModels.CompanyDocuments)
admin_site.register(AccountModels.CompanyDocument)
admin_site.register(AccountModels.CompanyTemplates)
admin_site.register(AccountModels.CompanyTemplate)

admin_site.register(HomeModels.Ticket)
admin_site.register(HomeModels.Tickets)
admin_site.register(HomeModels.Room)
admin_site.register(HomeModels.SupportRoom)
admin_site.register(HomeModels.ChatUser)
admin_site.register(HomeModels.Queue)

admin_site.register(DocumentModels.DocumentsSent)
admin_site.register(DocumentModels.NumberOfDocumentsSent)
admin_site.register(DocumentModels.DocumentDrafts)
admin_site.register(DocumentModels.NumberOfDocumentDrafts)
admin_site.register(DocumentModels.DocumentsReceived)
admin_site.register(DocumentModels.NumberOfDocumentsReceived)
admin_site.register(DocumentModels.DocumentsCompleted)
admin_site.register(DocumentModels.NumberOfDocumentsCompleted)
admin_site.register(DocumentModels.Document)
admin_site.register(DocumentModels.Documents)
admin_site.register(DocumentModels.DocumentSigningBoxes)
admin_site.register(DocumentModels.Template)
admin_site.register(DocumentModels.Templates)
admin_site.register(DocumentModels.AdditionalFile)
admin_site.register(DocumentModels.DocumentAlert)
admin_site.register(DocumentModels.AlertActual)

from django_celery_beat.models import (
    PeriodicTask, PeriodicTasks,
    IntervalSchedule, CrontabSchedule,
    SolarSchedule, ClockedSchedule
)

admin_site.register(IntervalSchedule)
admin_site.register(CrontabSchedule)
admin_site.register(SolarSchedule)
admin_site.register(ClockedSchedule)
admin_site.register(PeriodicTask)