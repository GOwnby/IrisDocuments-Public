from cgitb import html
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core import mail
from email.mime.image import MIMEImage
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *
import os

import datetime
import decimal
from decimal import *

from . import forms
from . import models as AccountModels
import Login.ClientFunctions as ClientFunctions
from ManageDocument import models as DocumentModels
from UserDashboard import models as UserDashboardModels
from SecureSign import settings
from ManageDocument.views import uploadToAWS

def FreeTrial(request):
    if request.method == 'POST':
        #form = forms.AccountForm(request.POST, extra=request.POST.get('extra_field_count'))
        form = forms.AccountForm(request.POST)

        if form.is_valid():

            form_username = form.cleaned_data['username']
            form_email = form.cleaned_data['email']
            form_password = form.cleaned_data['password']
            conf_pass = form.cleaned_data['confirm_password']
            #form_marketing_list = form.cleaned_data['marketing_list']

            if len(form_username) < 4:
                return render(request, "UserLengthPromotion.html")
            
            if len(form_email) < 4:
                return render(request, "EmailLengthPromotion.html")
            
            if len(form_password) < 4 or len(conf_pass) < 4:
                return render(request, "PasswordLengthPromotion.html")

            if not(conf_pass == form_password):
                return render(request, "MismatchPassPromotion.html")

            accountExists = False
            accountRegister = False
            accountVerified = False
            try:
                account = AccountModels.Account.objects.get(pk=form_email)
                accountExists = True
                if account.siteRegister == True:
                    accountRegister = True
                if account.verified == True:
                    accountVerified = True
            except Exception:
                accountExists = False

            
            try:
                accounts = AccountModels.Accounts.objects.get(pk=1)
                accounts.users += 1
                accounts.save()
            except Exception:
                # First Account Should be created with a correct email 
                accounts = AccountModels.Accounts(key=1, users=1)
                accounts.save()

            accountNumber = accounts.users

            accountNumber = str(accountNumber)
            lengthAccountNumber = len(accountNumber)
            if not accountExists:
                zeroes = 16 - lengthAccountNumber
                string = ''
                while zeroes != 0:
                    string = string + '0'
                    zeroes -= 1
                accountNumber = string + accountNumber

                subject = 'Finish Creating Your Account At Iris Documents'
                text_content = 'Click the link below to verify your email account with IrisDocuments.com'
                html_content = render_to_string('emailverifyaccountFreeTrial.html', {'text':text_content, 'userID':accountNumber})

                with mail.get_connection() as thisConnection:
                    email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    #email = mail.EmailMessage(subject, html_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    #email.content_subtype = 'html'
                    email.attach_alternative(html_content, 'text/html')
                    #file_path = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/stylesheets/images/irislogo_top_white.png')
                    #image = 'irislogo_top_white.png'
                    #img = MIMEImage(file_path, 'r')
                    #img.add_header('Content-ID', '<{name}>'.format(name=image))
                    #img.add_header('Content-Disposition', 'inline', filename=image)
                    #email.attach(img)
                    email.send()

                thisIP = ClientFunctions.get_client_ip(request)
                CURRENT_TIME = datetime.datetime.today()                
                CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                lastLoginTime = CURRENT_TIME
                newAccount = AccountModels.Account(userID=accountNumber, username=form_username, email=form_email, password=form_password, lastLoginTime=lastLoginTime, currentIP=thisIP, siteRegister=True)
                #, marketingList=form_marketing_list
                newAccount.save()
                newAccountLookupID = AccountModels.AccountLookupByID(userID = accountNumber, email = form_email)
                newAccountLookupID.save()
            
                initializeDocumentCount = DocumentModels.NumberOfDocumentsSent(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.NumberOfDocumentsReceived(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.NumberOfDocumentDrafts(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.NumberOfDocumentsCompleted(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.Documents(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.Templates(userID = accountNumber, templates = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = UserDashboardModels.ShowAlerts(userID = accountNumber)
                initializeDocumentCount.save()

                return HttpResponseRedirect('/CreateAccount/NewUser/')
            elif not accountRegister:
                subject = 'Finish Creating Your Account At Iris Documents'
                text_content = 'Click the link below to verify your email account with IrisDocuments.com'
                html_content = render_to_string('emailverifyaccountFreeTrial.html', {'text':text_content, 'userID':accountNumber})

                with mail.get_connection() as thisConnection:
                    email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    email.attach_alternative(html_content, 'text/html')

                thisIP = ClientFunctions.get_client_ip(request)
                CURRENT_TIME = datetime.datetime.today()                
                CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                lastLoginTime = CURRENT_TIME
                newAccount = AccountModels.Account.objects.get(pk=form_email)
                newAccount.password = form_password
                newAccount.lastLoginTime = lastLoginTime
                newAccount.currentIP = thisIP
                newAccount.siteRegister = True
                newAccount.save()

                return HttpResponseRedirect('/CreateAccount/NewUser/')
            elif not accountVerified:
                subject = 'Finish Creating Your Account At Iris Documents'
                text_content = 'Click the link below to verify your email account with IrisDocuments.com'
                html_content = render_to_string('emailverifyaccountFreeTrial.html', {'text':text_content, 'userID':accountNumber})

                with mail.get_connection() as thisConnection:
                    email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    email.attach_alternative(html_content, 'text/html')
                    email.send()
            else:
                return HttpResponseRedirect('/CreateAccount/DuplicateUser/') # User not created, return Duplicate User notification page
        return HttpResponse('Bad Request')

    form = forms.AccountForm()
    return render(request, "CreateAccountPromotion.html", {'form':form})

def VerifyUserFreeTrial(request, userID):
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    trialEndDay = 0
    trialSkipMonth = False
    if date.day >= 28:
        trialEndDay = 1
        trialSkipMonth = True
    else:
        trialEndDay = date.day

    userEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    user = AccountModels.Account.objects.get(pk=userEmail)
    user.verified = True
    user.trialEndDay = trialEndDay
    user.trialDate = currentDate
    user.subscriptionType = 1
    user.documentsAvailable = 10
    user.templatesAvailable = 5
    user.save()

    response = HttpResponseRedirect('/UserDashboard/Update/Update3/')
    response.set_cookie('user', userID)
    return response

def CreateAccount(request):

    if request.method == 'POST':
        #form = forms.AccountForm(request.POST, extra=request.POST.get('extra_field_count'))
        form = forms.AccountForm(request.POST)

        if form.is_valid():

            form_username = form.cleaned_data['username']
            form_email = form.cleaned_data['email']
            form_password = form.cleaned_data['password']
            conf_pass = form.cleaned_data['confirm_password']
            #form_marketing_list = form.cleaned_data['marketing_list']

            if len(form_username) < 4:
                return render(request, "UserLength.html")
            
            if len(form_email) < 4:
                return render(request, "EmailLength.html")
            
            if len(form_password) < 4 or len(conf_pass) < 4:
                return render(request, "PasswordLength.html")

            if not(conf_pass == form_password):
                return render(request, "MismatchPass.html")

            accountExists = False
            accountRegister = False
            accountVerified = False
            try:
                account = AccountModels.Account.objects.get(pk=form_email)
                accountExists = True
                if account.siteRegister == True:
                    accountRegister = True
                if account.verified == True:
                    accountVerified = True
            except Exception:
                accountExists = False

            
            try:
                accounts = AccountModels.Accounts.objects.get(pk=1)
                accounts.users += 1
                accounts.save()
            except Exception:
                accounts = AccountModels.Accounts(key=1, users=1)
                accounts.save()

            accountNumber = accounts.users

            accountNumber = str(accountNumber)
            lengthAccountNumber = len(accountNumber)
            if not accountExists:
                zeroes = 16 - lengthAccountNumber
                string = ''
                while zeroes != 0:
                    string = string + '0'
                    zeroes -= 1
                accountNumber = string + accountNumber

                subject = 'Finish Creating Your Account At Iris Documents'
                text_content = 'Click the link below to verify your email account with IrisDocuments.com'
                html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

                with mail.get_connection() as thisConnection:
                    email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    #email = mail.EmailMessage(subject, html_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    #email.content_subtype = 'html'
                    email.attach_alternative(html_content, 'text/html')
                    #file_path = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/stylesheets/images/irislogo_top_white.png')
                    #image = 'irislogo_top_white.png'
                    #img = MIMEImage(file_path, 'r')
                    #img.add_header('Content-ID', '<{name}>'.format(name=image))
                    #img.add_header('Content-Disposition', 'inline', filename=image)
                    #email.attach(img)
                    email.send()

                thisIP = ClientFunctions.get_client_ip(request)
                CURRENT_TIME = datetime.datetime.today()                
                CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                lastLoginTime = CURRENT_TIME
                newAccount = AccountModels.Account(userID=accountNumber, username=form_username, email=form_email, password=form_password, lastLoginTime=lastLoginTime, currentIP=thisIP, siteRegister=True, documentsAvailable=10)
                #, marketingList=form_marketing_list
                newAccount.save()
                newAccountLookupID = AccountModels.AccountLookupByID(userID = accountNumber, email = form_email)
                newAccountLookupID.save()
            
                initializeDocumentCount = DocumentModels.NumberOfDocumentsSent(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.NumberOfDocumentsReceived(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.NumberOfDocumentDrafts(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.NumberOfDocumentsCompleted(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.Documents(userID = accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = DocumentModels.Templates(userID = accountNumber, templates = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = UserDashboardModels.ShowAlerts(userID = accountNumber)
                initializeDocumentCount.save()

                return HttpResponseRedirect('/CreateAccount/NewUser/')
            elif not accountRegister:
                subject = 'Finish Creating Your Account At Iris Documents'
                text_content = 'Click the link below to verify your email account with IrisDocuments.com'
                html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

                with mail.get_connection() as thisConnection:
                    email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    email.attach_alternative(html_content, 'text/html')
                    email.send()

                thisIP = ClientFunctions.get_client_ip(request)
                CURRENT_TIME = datetime.datetime.today()                
                CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                lastLoginTime = CURRENT_TIME
                newAccount = AccountModels.Account.objects.get(pk=form_email)
                newAccount.password = form_password
                newAccount.lastLoginTime = lastLoginTime
                newAccount.currentIP = thisIP
                newAccount.siteRegister = True
                newAccount.save()

                return HttpResponseRedirect('/CreateAccount/NewUser/')
            elif not accountVerified:
                subject = 'Finish Creating Your Account At Iris Documents'
                text_content = 'Click the link below to verify your email account with IrisDocuments.com'
                html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

                with mail.get_connection() as thisConnection:
                    email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                    email.attach_alternative(html_content, 'text/html')
                    email.send()
            else:
                return HttpResponseRedirect('/CreateAccount/DuplicateUser/') # User not created, return Duplicate User notification page
        return HttpResponse('Bad Request')

    form = forms.AccountForm()
    return render(request, "CreateAccountv2.html", {'form':form})

def NewCreateAccount(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    if request.method == 'POST':
        form_email = request.POST.get('cemail', '')
        form_username = request.POST.get('cname', '')
        form_password = request.POST.get('cpwd', '')
        conf_pass = request.POST.get('cpwdconfirm', '')

        if len(form_username) < 4:
            return HttpResponseRedirect('/CreateAccount/1/')
            #return render(request, "UserLength.html")
            
        if len(form_email) < 4:
            return HttpResponseRedirect('/CreateAccount/2/')
            #return render(request, "EmailLength.html")
            
        if len(form_password) < 4 or len(conf_pass) < 4:
            return HttpResponseRedirect('/CreateAccount/3/')
            #return render(request, "PasswordLength.html")

        if not(conf_pass == form_password):
            return HttpResponseRedirect('/CreateAccount/4/')
            #return render(request, "MismatchPass.html")

        accountExists = False
        accountRegister = False
        accountVerified = False
        try:
            account = AccountModels.Account.objects.get(pk=form_email)
            accountExists = True
            if account.siteRegister == True:
                accountRegister = True
            if account.verified == True:
                accountVerified = True
        except Exception:
            accountExists = False

            
        try:
            accounts = AccountModels.Accounts.objects.get(pk=1)
            accounts.users += 1
            accounts.save()
        except Exception:
            accounts = AccountModels.Accounts(key=1, users=1)
            accounts.save()

        accountNumber = accounts.users

        accountNumber = str(accountNumber)
        lengthAccountNumber = len(accountNumber)
        if not accountExists:
            zeroes = 16 - lengthAccountNumber
            string = ''
            while zeroes != 0:
                string = string + '0'
                zeroes -= 1
            accountNumber = string + accountNumber

            subject = 'Finish Creating Your Account At Iris Documents'
            text_content = 'Click the link below to verify your email account with IrisDocuments.com'
            html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                #email = mail.EmailMessage(subject, html_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                #email.content_subtype = 'html'
                email.attach_alternative(html_content, 'text/html')
                #file_path = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/stylesheets/images/irislogo_top_white.png')
                #image = 'irislogo_top_white.png'
                #img = MIMEImage(file_path, 'r')
                #img.add_header('Content-ID', '<{name}>'.format(name=image))
                #img.add_header('Content-Disposition', 'inline', filename=image)
                #email.attach(img)
                email.send()

            thisIP = ClientFunctions.get_client_ip(request)
            CURRENT_TIME = datetime.datetime.today()                
            CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
            lastLoginTime = CURRENT_TIME
            newAccount = AccountModels.Account(userID=accountNumber, username=form_username, email=form_email, password=form_password, lastLoginTime=lastLoginTime, currentIP=thisIP, siteRegister=True, documentsAvailable=10)
            #, marketingList=form_marketing_list
            newAccount.save()
            newAccountLookupID = AccountModels.AccountLookupByID(userID = accountNumber, email = form_email)
            newAccountLookupID.save()
            
            initializeDocumentCount = DocumentModels.NumberOfDocumentsSent(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.NumberOfDocumentsReceived(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.NumberOfDocumentDrafts(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.NumberOfDocumentsCompleted(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.Documents(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.Templates(userID = accountNumber, templates = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = UserDashboardModels.ShowAlerts(userID = accountNumber)
            initializeDocumentCount.save()

            return HttpResponseRedirect('/CreateAccount/NewUser/')
        elif not accountRegister:
            subject = 'Finish Creating Your Account At Iris Documents'
            text_content = 'Click the link below to verify your email account with IrisDocuments.com'
            html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                email.attach_alternative(html_content, 'text/html')
                email.send()

            thisIP = ClientFunctions.get_client_ip(request)
            CURRENT_TIME = datetime.datetime.today()                
            CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
            lastLoginTime = CURRENT_TIME
            newAccount = AccountModels.Account.objects.get(pk=form_email)
            newAccount.password = form_password
            newAccount.lastLoginTime = lastLoginTime
            newAccount.currentIP = thisIP
            newAccount.siteRegister = True
            newAccount.save()

            return HttpResponseRedirect('/CreateAccount/NewUser/')
        elif not accountVerified:
            subject = 'Finish Creating Your Account At Iris Documents'
            text_content = 'Click the link below to verify your email account with IrisDocuments.com'
            html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                email.attach_alternative(html_content, 'text/html')
                email.send()
        else:
            return HttpResponseRedirect('/CreateAccount/DuplicateUser/') # User not created, return Duplicate User notification page

    if mobile:
        return render(request, "NewCreateAccountAMP.html")
    return render(request, "NewCreateAccount.html")

def CreateAccountError(request, error):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    if request.method == 'POST':
        form_email = request.POST.get('cemail', '')
        form_username = request.POST.get('cname', '')
        form_password = request.POST.get('cpwd', '')
        conf_pass = request.POST.get('cpwdconfirm', '')

        if len(form_username) < 4:
            return HttpResponseRedirect('/CreateAccount/1/')
            #return render(request, "UserLength.html")
            
        if len(form_email) < 4:
            return HttpResponseRedirect('/CreateAccount/2/')
            #return render(request, "EmailLength.html")
            
        if len(form_password) < 4 or len(conf_pass) < 4:
            return HttpResponseRedirect('/CreateAccount/3/')
            #return render(request, "PasswordLength.html")

        if not(conf_pass == form_password):
            return HttpResponseRedirect('/CreateAccount/4/')
            #return render(request, "MismatchPass.html")

        accountExists = False
        accountRegister = False
        accountVerified = False
        try:
            account = AccountModels.Account.objects.get(pk=form_email)
            accountExists = True
            if account.siteRegister == True:
                accountRegister = True
            if account.verified == True:
                accountVerified = True
        except Exception:
            accountExists = False

            
        try:
            accounts = AccountModels.Accounts.objects.get(pk=1)
            accounts.users += 1
            accounts.save()
        except Exception:
            accounts = AccountModels.Accounts(key=1, users=1)
            accounts.save()

        accountNumber = accounts.users

        accountNumber = str(accountNumber)
        lengthAccountNumber = len(accountNumber)
        if not accountExists:
            zeroes = 16 - lengthAccountNumber
            string = ''
            while zeroes != 0:
                string = string + '0'
                zeroes -= 1
            accountNumber = string + accountNumber

            subject = 'Finish Creating Your Account At Iris Documents'
            text_content = 'Click the link below to verify your email account with IrisDocuments.com'
            html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                #email = mail.EmailMessage(subject, html_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                #email.content_subtype = 'html'
                email.attach_alternative(html_content, 'text/html')
                #file_path = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/stylesheets/images/irislogo_top_white.png')
                #image = 'irislogo_top_white.png'
                #img = MIMEImage(file_path, 'r')
                #img.add_header('Content-ID', '<{name}>'.format(name=image))
                #img.add_header('Content-Disposition', 'inline', filename=image)
                #email.attach(img)
                email.send()

            thisIP = ClientFunctions.get_client_ip(request)
            CURRENT_TIME = datetime.datetime.today()                
            CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
            lastLoginTime = CURRENT_TIME
            newAccount = AccountModels.Account(userID=accountNumber, username=form_username, email=form_email, password=form_password, lastLoginTime=lastLoginTime, currentIP=thisIP, siteRegister=True, documentsAvailable=10)
            #, marketingList=form_marketing_list
            newAccount.save()
            newAccountLookupID = AccountModels.AccountLookupByID(userID = accountNumber, email = form_email)
            newAccountLookupID.save()
            
            initializeDocumentCount = DocumentModels.NumberOfDocumentsSent(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.NumberOfDocumentsReceived(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.NumberOfDocumentDrafts(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.NumberOfDocumentsCompleted(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.Documents(userID = accountNumber, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = DocumentModels.Templates(userID = accountNumber, templates = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = UserDashboardModels.ShowAlerts(userID = accountNumber)
            initializeDocumentCount.save()

            return HttpResponseRedirect('/CreateAccount/NewUser/')
        elif not accountRegister:
            subject = 'Finish Creating Your Account At Iris Documents'
            text_content = 'Click the link below to verify your email account with IrisDocuments.com'
            html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                email.attach_alternative(html_content, 'text/html')
                email.send()

            thisIP = ClientFunctions.get_client_ip(request)
            CURRENT_TIME = datetime.datetime.today()                
            CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
            lastLoginTime = CURRENT_TIME
            newAccount = AccountModels.Account.objects.get(pk=form_email)
            newAccount.password = form_password
            newAccount.lastLoginTime = lastLoginTime
            newAccount.currentIP = thisIP
            newAccount.siteRegister = True
            newAccount.save()

            return HttpResponseRedirect('/CreateAccount/NewUser/')
        elif not accountVerified:
            subject = 'Finish Creating Your Account At Iris Documents'
            text_content = 'Click the link below to verify your email account with IrisDocuments.com'
            html_content = render_to_string('emailverifyaccountTest.html', {'text':text_content, 'userID':accountNumber})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
                email.attach_alternative(html_content, 'text/html')
                email.send()
        else:
            return HttpResponseRedirect('/CreateAccount/DuplicateUser/') # User not created, return Duplicate User notification page

    if mobile:
        return render(request, "NewCreateAccountAMP.html")

    errorText = ''
    if error == 1:
        errorText = 'Please enter your full name.'
    elif error == 2:
        errorText = 'Please enter your full email address.'
    elif error == 3:
        errorText = 'Please enter use a longer password.'
    elif error == 3:
        errorText = 'The passwords do not match.'

    return render(request, "NewCreateAccountError.html", {'errorText':errorText})

def NewUser(request):
    return render(request, "CheckEmail.html")

def VerifyUser(request, userID):
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    trialEndDay = 0
    trialSkipMonth = False
    if date.day >= 28:
        trialEndDay = 1
        trialSkipMonth = True
    else:
        trialEndDay = date.day

    userEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    user = AccountModels.Account.objects.get(pk=userEmail)
    user.verified = True
    user.trialEndDay = trialEndDay
    user.trialDate = currentDate
    user.subscriptionType = 9
    user.documentsAvailable = 10
    user.templatesAvailable = 5
    user.save()

    response = HttpResponseRedirect('/UserDashboard/')
    response.set_cookie('user', userID)
    return response

def AddPassword(request, userID):
    if request.method == 'POST':
        form = forms.VerifyPasswordForm(request.POST)
        if form.is_valid():

            form_username = form.cleaned_data['username']
            form_password = form.cleaned_data['password']
            conf_pass = form.cleaned_data['confirm_password']

            if not(conf_pass == form_password):
                return render(request, 'MismatchPassVerify.html', {'userID':userID})

            if form_password == conf_pass:
                userEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
                user = AccountModels.Account.objects.get(pk=userEmail)
                user.username = form_username
                user.password = form_password
                user.verified = True
                user.save()

                response = HttpResponseRedirect('/UserDashboard/')
                response.set_cookie('user', userID)
                return response
    form = forms.VerifyPasswordForm()
    return render(request, "TakePassv2.html", {'userID':userID, 'form':form})

def ChangePassword(request):
    thisUser = request.COOKIES.get('user')

    if request.method == 'POST':
        OldPass = request.POST.get('OldPass', None)
        COldPass = request.POST.get('COldPass', None)
        NewPass = request.POST.get('NewPass', None)
        CNewPass = request.POST.get('CNewPass', None)

        if (OldPass == COldPass) and (OldPass != None):
            if (NewPass == CNewPass) and (NewPass != None):
                thisAcc = AccountModels.Account.objects.get(pk=thisUser)
                thisAcc.password = NewPass
                thisAcc.save()

                return HttpResponseRedirect('/UserDashboard/Settings/Update/1/')

    return HttpResponseRedirect('/UserDashboard/Settings/')

def ChangeWallet(request):
    thisUser = request.COOKIES.get('user')

    if request.method == 'POST':
        cNum = request.POST.get('CNum', None)
        cvc = request.POST.get('CVC', None)
        month = request.POST.get('month', None)
        year = request.POST.get('year', None)
        fname = request.POST.get('FName', None)
        lname = request.POST.get('LName', None)
        address = request.POST.get('Address', None)
        city = request.POST.get('City', None)
        zip = request.POST.get('Zip', None)
        state = request.POST.get('State', None)
        country = request.POST.get('Country', None)

        thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
        thisAcc = AccountModels.Account.objects.get(pk=thisUserEmail)
        thisAcc.cNum = cNum
        thisAcc.cMonth = month
        thisAcc.cYear = year
        thisAcc.cvc = cvc
        thisAcc.fName = fname
        thisAcc.lName = lname
        thisAcc.address = address
        thisAcc.city = city
        thisAcc.zip = zip
        thisAcc.state = state
        thisAcc.country = country
        thisAcc.save()

        return HttpResponseRedirect('/UserDashboard/Settings/Update/2/')

    return HttpResponseRedirect('/UserDashboard/Settings/')

def ChangeBrand(request):
    if request.method == 'POST':
        form = forms.UploadBrandForm(request.POST, request.FILES)
        form.is_valid()
        userID = request.COOKIES.get('user')
        thisFileuuid = uploadToAWS(request.FILES['brandFile'], 'brands/users')
        userEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        user = AccountModels.Account.objects.get(pk=userEmail)
        user.brandFileuuid = thisFileuuid
        user.brandFileType = ((request.FILES['brandFile'].name).split("."))[1]
        user.addBrand = True
        user.save()

        return HttpResponseRedirect('/UserDashboard/Settings/Update/5/')

    return HttpResponseRedirect('/')

def ChangeCompanyBrand(request):
    if request.method == 'POST':
        form = forms.UploadBrandForm(request.POST, request.FILES)
        form.is_valid()
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=request.COOKIES.get('user')).companyID
        thisFileuuid = uploadToAWS(request.FILES['brandFile'], 'brands/companys')
        company = AccountModels.Company.objects.get(pk=companyID)
        company.brandFileuuid = thisFileuuid
        company.brandFileType = ((request.FILES['brandFile'].name).split("."))[1]
        company.addBrand = True
        company.save()

        return HttpResponseRedirect('/UserDashboard/CompanyDashboard/Settings/2/')

    return HttpResponseRedirect('/')

def RemoveWallet(request):
    thisUser = request.COOKIES.get('user')
    thisAccEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
    thisAcc = AccountModels.Account.objects.get(pk=thisAccEmail)

    thisAcc.cNum = ''
    thisAcc.cvc = ''
    thisAcc.cMonth = ''
    thisAcc.cYear = ''
    thisAcc.fName = ''
    thisAcc.lName = ''
    thisAcc.address = ''
    thisAcc.city = ''
    thisAcc.zip = ''
    thisAcc.state = ''
    thisAcc.country = ''

    thisAcc.save()

    return HttpResponseRedirect('/UserDashboard/Settings/Update/3/')
 
def AddDocuments(request):
    if request.method == 'POST':
        numDocs = request.POST.get('numDocs', None)
        amount = 0.25 * float(numDocs)

        thisUser = request.COOKIES.get('user')
        thisAccEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
        account = AccountModels.Account.objects.get(pk=thisAccEmail)

        amount = Decimal(amount)

        ctx = decimal.getcontext()
        ctx.rounding = decimal.ROUND_HALF_DOWN

        amount = round(amount, 2)

        creditCard = apicontractsv1.creditCardType()
        creditCard.cardNumber = account.cNum
        creditCard.expirationDate = account.cYear + '-' + account.cMonth
     
        payment = apicontractsv1.paymentType()
        payment.creditCard = creditCard
     
        # Create order information
        account.invoiceNum += 1
        account.save()
        order = apicontractsv1.orderType()
        order.invoiceNumber = str(account.invoiceNum)
        order.description = "Iris Documents"

        # Set the customer's Bill To address
        customerAddress = apicontractsv1.customerAddressType()
        customerAddress.firstName = account.fName
        customerAddress.lastName = account.lName
        customerAddress.address = account.address
        customerAddress.city = account.city
        customerAddress.state = account.state
        customerAddress.zip = account.zip
        customerAddress.country = account.country

        # Set the customer's identifying information
        customerData = apicontractsv1.customerDataType()
        customerData.type = "individual"
        customerData.email = account.email

        # setup individual line items
        line_item_1 = apicontractsv1.lineItemType()
        line_item_1.itemId = "0"
        line_item_1.name = "Iris Documents"
        line_item_1.description = "Your documents at IrisDocuments.com"
        line_item_1.quantity = numDocs
        line_item_1.unitPrice = str(amount)

        # build the array of line items
        line_items = apicontractsv1.ArrayOfLineItem()
        line_items.lineItem.append(line_item_1)
     
        transactionrequest = apicontractsv1.transactionRequestType()
        transactionrequest.transactionType ="authCaptureTransaction"
        transactionrequest.amount = amount
        transactionrequest.payment = payment
        transactionrequest.order = order
        transactionrequest.billTo = customerAddress
        transactionrequest.customer = customerData
        transactionrequest.lineItems = line_items

        merchantAuth = apicontractsv1.merchantAuthenticationType()
        merchantAuth.name = settings.api_login_name
        merchantAuth.transactionKey = settings.transaction_key     
     
        createtransactionrequest = apicontractsv1.createTransactionRequest()
        createtransactionrequest.merchantAuthentication = merchantAuth
        createtransactionrequest.refId = 'Iris Documents'
     
        createtransactionrequest.transactionRequest = transactionrequest
        createtransactioncontroller = createTransactionController(createtransactionrequest)
        createtransactioncontroller.execute()
     
        response = createtransactioncontroller.getresponse()

        if (response.messages.resultCode=="Ok"):
            account.documentsAvailable += int(numDocs)
            account.save()
            return HttpResponseRedirect('/UserDashboard/Settings/Update/6/')

    return HttpResponseRedirect('/UserDashboard/Settings/Error/2/')

def DownloadTermsAndConditions(request):
    path = 'TermsAndConditions.pdf'
    file_path = os.path.join(settings.STATIC_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

def DownloadPrivacyPolicy(request):
    path = 'PrivacyPolicy.pdf'
    file_path = os.path.join(settings.STATIC_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404