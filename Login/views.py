from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core import mail

import datetime

from . import forms
from . import ClientFunctions
import CreateAccount.models as models

def login(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                userDB = models.Account.objects.get(pk=email)
            except BaseException:
                return HttpResponseRedirect('/Login/AccountDNE/')
            else:
                if userDB.password == password:
                    response = HttpResponseRedirect('/UserDashboard/')
                    thisIP = ClientFunctions.get_client_ip(request)
                    userDB.currentIP = thisIP
                    CURRENT_TIME = datetime.datetime.today()
                    CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                    userDB.lastLoginTime = CURRENT_TIME
                    userDB.save()
                    response.set_cookie('user', userDB.userID)

                    try:
                        lastLoggedIn = models.Last25LoggedIn.objects.get(pk=1)
                        lastLoggedIn.lastUserAdded += 1
                        lastLoggedIn.save()

                        if lastLoggedIn.lastUserAdded > 25:
                            lastLoggedIn.lastUserAdded = 1
                            lastLoggedIn.users[lastLoggedIn.lastUserAdded] = userDB.userID
                        else:
                            lastLoggedIn.users[lastLoggedIn.lastUserAdded] = userDB.userID

                        lastLoggedIn.save()     
                    except Exception:
                        lastLoggedIn = models.Last25LoggedIn(key=1,users={1:userDB.userID},lastUserAdded=1)
                        lastLoggedIn.save()

                    return response
                else:
                    return HttpResponseRedirect('/Login/AccountDNE/')
            
    form = forms.LoginForm()
    return render(request, "login.html", {'form':form})

def NewLogin(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('pwd', '')

        try:
            userDB = models.Account.objects.get(pk=email)
        except Exception:
            return HttpResponseRedirect('/')
        else:
            if userDB.password == password:
                if userDB.verified == False:
                    return HttpResponseRedirect('/')
                response = HttpResponseRedirect('/UserDashboard/')
                thisIP = ClientFunctions.get_client_ip(request)
                userDB.currentIP = thisIP
                CURRENT_TIME = datetime.datetime.today()
                CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                userDB.lastLoginTime = CURRENT_TIME
                userDB.save()
                response.set_cookie('user', userDB.userID)

                try:
                    lastLoggedIn = models.Last25LoggedIn.objects.get(pk=1)
                    lastLoggedIn.lastUserAdded += 1
                    lastLoggedIn.save()

                    if lastLoggedIn.lastUserAdded > 25:
                        lastLoggedIn.lastUserAdded = 1
                        lastLoggedIn.users[lastLoggedIn.lastUserAdded] = userDB.userID
                    else:
                        lastLoggedIn.users[lastLoggedIn.lastUserAdded] = userDB.userID

                    lastLoggedIn.save()     
                except Exception:
                    lastLoggedIn = models.Last25LoggedIn(key=1,users={1:userDB.userID},lastUserAdded=1)
                    lastLoggedIn.save()

                return response
            else:
                return HttpResponseRedirect('/')
    
    if mobile:
        return render(request, "loginAMP.html")
    return render(request, "login.html")

def ForgotPassword(request):
    if request.method == 'POST':
        form_email = request.POST.get('cemail', '')

        try:
            account = models.Account.objects.get(pk=form_email)
            accountNumber = account.userID
        except Exception:
            return HttpResponseRedirect("/")
        
        subject = 'Reset your password at Iris Documents'
        text_content = 'Click the link below to reset your password at IrisDocuments.com'
        html_content = render_to_string('emailForgotPassword.html', {'text':text_content, 'userID':accountNumber})

        with mail.get_connection() as thisConnection:
            email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [form_email], connection=thisConnection)
            email.attach_alternative(html_content, 'text/html')
            email.send()

        return render(request, "PasswordCheckEmail.html")
    return render(request, "ForgotPassword.html")

def ResetPassword(request, userID):
    if request.method == 'POST':
        form_cpwd = request.POST.get('cpwd', '')
        form_cpwdconfirm = request.POST.get('cpwdconfirm', '')

        if form_cpwd != form_cpwdconfirm:
            return HttpResponseRedirect("/Login/ResetPassword/" + userID + "/")

        try:
            accountEmail = models.AccountLookupByID.objects.get(pk=userID).email
            account = models.Account.objects.get(pk=accountEmail)
            account.password = form_cpwd
            account.save()
        except Exception:
            return HttpResponseRedirect("/")
        return render(request, "PasswordReset.html")

    return render(request, "ResetPassword.html", {'userID':userID})

def AccountDNE(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                userDB = models.Account.objects.get(pk=email)
            except BaseException:
                return HttpResponseRedirect('/Login/AccountDNE/PleaseWait/')
            else:
                if userDB.password == password:
                    response = HttpResponseRedirect('/UserDashboard/')
                    thisIP = ClientFunctions.get_client_ip(request)
                    #Hard coded IP for Localhost server development
                    userDB.currentIP = thisIP
                    CURRENT_TIME = datetime.datetime.today()
                    CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                    userDB.lastLoginTime = CURRENT_TIME
                    userDB.save()
                    response.set_cookie('user', userDB.userID)

                    try:
                        lastLoggedIn = models.Last25LoggedIn.objects.get(pk=1)
                        lastLoggedIn.lastUserAdded += 1
                        lastLoggedIn.save()

                        if lastLoggedIn.lastUserAdded > 25:
                            lastLoggedIn.lastUserAdded = 1
                            lastLoggedIn.users[lastLoggedIn.lastUserAdded] = userDB.userID
                        else:
                            lastLoggedIn.users[lastLoggedIn.lastUserAdded] = userDB.userID

                        lastLoggedIn.save()     
                    except Exception:
                        lastLoggedIn = models.Last25LoggedIn(key=1,users={1:userDB.userID},lastUserAdded=1)
                        lastLoggedIn.save()

                    return response
                else:
                    return HttpResponseRedirect('/Login/AccountDNE/PleaseWait/')
            
    form = forms.LoginForm()
    return render(request, "AccountDNE.html", {'form':form})

def AccountDNEWait(request):
    return render(request, 'AccountDNEWait.html')