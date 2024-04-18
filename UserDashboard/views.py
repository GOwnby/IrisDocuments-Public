from cmath import acos
from curses.ascii import HT
from time import time
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core import mail
from base64 import b64decode
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *

import urllib.parse
import decimal
from decimal import *
import math
import os
import json
import datetime
import math
from pytz import timezone
import ipinfo
import boto3

from . import forms as UserDashboardForms
from . import models as UserDashboardModels
from ManageDocument import models as DocumentModels
from ManageDocument import forms as DocumentForms
from CreateAccount  import models as AccountModels
from CreateAccount import forms as AccountForms
from Login import ClientFunctions
from SecureSign import settings
from ManageDocument.views import uploadToAWSsite

class DocumentObject:
    def __init__(self, nonce, title, dateLastEdited, requestID):
        self.nonce = nonce
        self.title = title
        self.dateLastEdited = dateLastEdited
        self.requestID = requestID

def AddPersonalSub(request):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/CreateAccount/')
            return response
    except Exception:
        response = HttpResponseRedirect('/CreateAccount/')
        return response
    return HttpResponseRedirect('/UserDashboard/Settings/ShowPage/Subscription/')
    
def AddBusinessSub(request):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/CreateAccount/')
            return response
    except Exception:
        response = HttpResponseRedirect('/CreateAccount/')
        return response
    return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')

def returnTemplateChoices(userID):
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates
    templateChoices = []
    count = 0

    newTuple = (0, 'None')
    templateChoices.append(newTuple)

    while count < 25:
        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)
            newTuple = (templateKey, DocumentModels.Template.objects.get(pk=templateKey).title)

            templateChoices.append(newTuple)

        count += 1

    templateChoices = tuple(templateChoices)
    return templateChoices

def returnTimeChoices(userEmail):
    account = AccountModels.Account.objects.get(pk=userEmail)
    userIP = account.currentIP

    #database = IP2Location.IP2Location("home/ubuntu/django/IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-SAMPLE.BIN")
    #userLocationInfo = database.get_all(userIP)
    access_token = '5e07ecfdd4ebf6'
    handler = ipinfo.getHandler(access_token)
    details = handler.getDetails(userIP)
    now_utc = datetime.datetime.now(timezone('UTC'))
    now_local = now_utc.astimezone(timezone(details.timezone))


    if now_local.minute < 50:
        firstTimeChoice_firstHour = now_local.hour + 1
    else:
        firstTimeChoice_firstHour = now_local.hour + 2

    timeChoices = []

    while firstTimeChoice_firstHour <= 12:
        newTuple = (firstTimeChoice_firstHour, str(firstTimeChoice_firstHour))
        timeChoices.append(newTuple)
        firstTimeChoice_firstHour += 1
    
    if len(timeChoices) == 0:
        newTuple = (0, 'None')
        timeChoices.append(newTuple)

    timeChoices = tuple(timeChoices)
    
    return timeChoices

def returnAllTimeChoices():
    timeChoices = []
    count = 1

    while count <= 12:
        newTuple = (count, str(count))
        timeChoices.append(newTuple)
        count += 1

    timeChoices = tuple(timeChoices)
    return timeChoices

def returnAMPMChoice():
    timeChoices = []
    newTuple = (1, 'AM')
    timeChoices.append(newTuple)
    newTuple = (2, 'PM')
    timeChoices.append(newTuple)

    timeChoices = tuple(timeChoices)
    return timeChoices

def index(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response

    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)

    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()
    #form3 = UserDashboardForms.AlertForm(timeChoices=returnTimeChoices(userEmail=email), allTimeChoices=returnAllTimeChoices(),ampmChoices=returnAMPMChoice())

    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = 0
    documentsSent = []
        
    while count < 5:

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = 0
    documentsReceived = []
        
    while count < 5:

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = 0
    documentsDrafts = []
        
    while count < 5:

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = 0
    templates = []
    while count < 5:

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    sentComplete = account.sentComplete
    newReceived = account.newReceived

    if mobile:
        return render(request, "UserDashboardAMP.html", {                
            'form1':form1,
            'form2':form2,
            'Title':title,
            'CreatedDate':createdDate,
            'LastEdited':editedDate,
            'Complete':completed,
            'ID':ID,
            'Page':page,
            'Designation':designation
            })

    if sentComplete:
        account.sentComplete = False
        account.save()
        return render(request, "UserDashboardSentComplete.html", {                
            'form1':form1,
            'form2':form2,
            'Title':title,
            'CreatedDate':createdDate,
            'LastEdited':editedDate,
            'Complete':completed,
            'ID':ID,
            'Page':page,
            'Designation':designation
            })
    elif newReceived:
        account.newReceived = False
        account.save()
        return render(request, "UserDashboardNewDocument.html", {                
            'form1':form1,
            'form2':form2,
            'Title':title,
            'CreatedDate':createdDate,
            'LastEdited':editedDate,
            'Complete':completed,
            'ID':ID,
            'Page':page,
            'Designation':designation
            })
    elif sentComplete and newReceived:
        account.sentComplete = False
        account.newReceived = False
        account.save()
        return render(request, "UserDashboardSentCompleteAndNew.html", {                
            'form1':form1,
            'form2':form2,
            'Title':title,
            'CreatedDate':createdDate,
            'LastEdited':editedDate,
            'Complete':completed,
            'ID':ID,
            'Page':page,
            'Designation':designation
            })
    else:
        return render(request, "UserDashboard.html", {                
            'form1':form1,
            'form2':form2,
            'Title':title,
            'CreatedDate':createdDate,
            'LastEdited':editedDate,
            'Complete':completed,
            'ID':ID,
            'Page':page,
            'Designation':designation
            })

def error(request, error):

    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response
    
    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)
    
    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()

    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = 0
    documentsSent = []
        
    while count < 5:

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = 0
    documentsReceived = []
        
    while count < 5:

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = 0
    documentsDrafts = []
        
    while count < 5:

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = 0
    templates = []
    while count < 5:

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    alertText = ''
    if error == 'Error1':
        alertText = 'Neither a file or template was selected. Please try again.'
    elif error == 'Error2':
        alertText = 'The document was scheduled to be sent at too early a time. Please try again.'
    elif error == 'Error3':
        alertText = 'Please add a signature to this account.'
    elif error == 'Error4':
        alertText = 'Reached an error while signing the document.'

    return render(request, 'UserDashboardError.html', {                
        'form1':form1,
        'form2':form2,
        'Title':title,
        'CreatedDate':createdDate,
        'LastEdited':editedDate,
        'Complete':completed,
        'ID':ID,
        'Page':page,
        'Designation':designation,
        'alertText':alertText
        })

def update(request, update):

    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response
    
    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)
    
    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()

    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = 0
    documentsSent = []
        
    while count < 5:

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = 0
    documentsReceived = []
        
    while count < 5:

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = 0
    documentsDrafts = []
        
    while count < 5:

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = 0
    templates = []
    while count < 5:

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    alertText = ''
    if update == 'Update1':
        alertText = 'The Document has been sent successfully.'
    elif update == 'Update2':
        alertText = 'The Document has been signed successfully.'
    elif update == 'Update3':
        alertText = 'The Personal Lite Subscription has been automatically added to your account.'
    elif update == 'Update4':
        alertText = 'Your account has been added to a new company.'

    return render(request, 'UserDashboardUpdate.html', {                
        'form1':form1,
        'form2':form2,
        'Title':title,
        'CreatedDate':createdDate,
        'LastEdited':editedDate,
        'Complete':completed,
        'ID':ID,
        'Page':page,
        'Designation':designation,
        'alertText':alertText
        })

def sent(request, pageNum):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response

    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)

    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()

    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = ((pageNum-1) * 5)
    documentsSent = []
        
    while count < (((pageNum-1) * 5) + 5):

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = 0
    documentsReceived = []
        
    while count < 5:

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = 0
    documentsDrafts = []
        
    while count < 5:

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = 0
    templates = []
        
    while count < 5:

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    return render(request, 'UserDashboardTabSent.html', {                
        'form1':form1,
        'form2':form2,
        'Title':title,
        'CreatedDate':createdDate,
        'LastEdited':editedDate,
        'Complete':completed,
        'ID':ID,
        'Page':page,
        'Designation':designation,
        'PageNum':pageNum
        })

def received(request, pageNum):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response

    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)

    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()


    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = 0
    documentsSent = []
        
    while count < 5:

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = ((pageNum-1) * 5)
    documentsReceived = []
        
    while count < (((pageNum-1) * 5) + 5):

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = 0
    documentsDrafts = []
        
    while count < 5:

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = 0
    templates = []
        
    while count < 5:

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    return render(request, 'UserDashboardTabReceived.html', {                
        'form1':form1,
        'form2':form2,
        'Title':title,
        'CreatedDate':createdDate,
        'LastEdited':editedDate,
        'Complete':completed,
        'ID':ID,
        'Page':page,
        'Designation':designation,
        'PageNum':pageNum
        })

def drafts(request, pageNum):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response

    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)

    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()

    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = 0
    documentsSent = []
        
    while count < 5:

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = 0
    documentsReceived = []
        
    while count < 5:

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = ((pageNum-1) * 5)
    documentsDrafts = []
        
    while count < (((pageNum-1) * 5) + 5):

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = 0
    templates = []
        
    while count < 5:

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    return render(request, 'UserDashboardTabDrafts.html', {                
        'form1':form1,
        'form2':form2,
        'Title':title,
        'CreatedDate':createdDate,
        'LastEdited':editedDate,
        'Complete':completed,
        'ID':ID,
        'Page':page,
        'Designation':designation,
        'PageNum':pageNum
        })

def templates(request, pageNum):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response

    email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=email)

    if account.subscriptionType == 3:
        form1 = DocumentForms.UploadFilesForm(templates=returnTemplateChoices(userID=userID))
    else:
        form1 = DocumentForms.UploadFileForm(templates=returnTemplateChoices(userID=userID))
    form2 = DocumentForms.UploadTemplateForm()

    numberOfDocumentsSent = DocumentModels.NumberOfDocumentsSent.objects.get(pk=userID).documents
    numberOfDocumentsReceived = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID).documents
    numberOfDocumentsDrafts = DocumentModels.NumberOfDocumentDrafts.objects.get(pk=userID).documents
    numberOfTemplates = DocumentModels.Templates.objects.get(pk=userID).templates

    numberOfDocumentsSentPages = str(math.ceil(numberOfDocumentsSent / 5))
    numberOfDocumentsReceivedPages = str(math.ceil(numberOfDocumentsReceived / 5))
    numberOfDocumentsDraftsPages = str(math.ceil(numberOfDocumentsDrafts / 5))
    numberOfTemplatesPages = str(math.ceil(numberOfTemplates / 5))

    page = []
    page.append(numberOfDocumentsSentPages)
    page.append(numberOfDocumentsReceivedPages)
    page.append(numberOfDocumentsDraftsPages)
    page.append(numberOfTemplatesPages)

    count = 0
    documentsSent = []
        
    while count < 5:

        if (numberOfDocumentsSent - count) > 0:
            documentKeySent = DocumentModels.DocumentsSent.objects.get(pk=(userID + '_' + str(numberOfDocumentsSent - count) ) ).documentKey

            documentsSent.append(DocumentModels.Document.objects.get(pk=documentKeySent))

        count += 1

    count = 0
    documentsReceived = []
        
    while count < 5:

        if (numberOfDocumentsReceived - count) > 0:
            documentKeyReceived = DocumentModels.DocumentsReceived.objects.get(pk=(userID + '_' + str(numberOfDocumentsReceived - count) ) ).documentKey

            documentsReceived.append(DocumentModels.Document.objects.get(pk=documentKeyReceived))

        count += 1

    count = 0
    documentsDrafts = []
        
    while count < 5:

        if (numberOfDocumentsDrafts - count) > 0:
            documentKeyDrafts = DocumentModels.DocumentDrafts.objects.get(pk=(userID + '_' + str(numberOfDocumentsDrafts - count) ) ).documentKey

            documentsDrafts.append(DocumentModels.Document.objects.get(pk=documentKeyDrafts))

        count += 1

    count = (((pageNum-1) * 5) + 5)
    templates = []
        
    while count < (((pageNum-1) * 5) + 5):

        if (numberOfTemplates - count) > 0:
            templateKey = userID + '_' + str(numberOfTemplates - count)

            templates.append(DocumentModels.Template.objects.get(pk=templateKey))

        count += 1

    title = []
    createdDate = []
    editedDate = []
    completed = []
    ID = []
    designation = []
    for each in documentsSent:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("sent")

    for each in documentsReceived:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("received")

    for each in documentsDrafts:
        title.append(each.title)
        createdDate.append(each.createdDate)
        editedDate.append(each.lastEditedDate)
        completed.append(str(each.isComplete))
        ID.append(each.requestID)
        designation.append("draft")

    for each in templates:
        title.append(each.title)
        createdDate.append(each.createdDate)
        ID.append(each.requestID)
        designation.append("template")

    return render(request, 'UserDashboardTabTemplates.html', {                
        'form1':form1,
        'form2':form2,
        'Title':title,
        'CreatedDate':createdDate,
        'LastEdited':editedDate,
        'Complete':completed,
        'ID':ID,
        'Page':page,
        'Designation':designation,
        'PageNum':pageNum
        })

def logout(request):
    response = HttpResponseRedirect('/')
    response.set_cookie('user', '')
    return response

def SaveSignature(request):
    if request.method == "POST":
        postData = request.POST.get('data')
        header, encoded = postData.split(",", 1)
        data = b64decode(encoded)
        dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/signatures/')
        userID = request.COOKIES.get('user')
        filePath = dirPath + userID + '.png'
        with open(filePath, 'wb') as f:
            f.write(data)
        thisFileuuid = uploadToAWSsite(filePath, 'signatures')

        email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        account = AccountModels.Account.objects.get(pk=email)

        if account.signatureFileuuid == 'default':
            account.signatureFileuuid = thisFileuuid
            account.save()
        else:
            s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
            s3.delete_object(Bucket='iris1-static', Key='static/files/signatures/' + account.signatureFileuuid + '.pdf')
            account.signatureFileuuid = thisFileuuid
            account.save()

        os.remove(filePath)
    return HttpResponseRedirect('/UserDashboard/')

def Settings(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)

        try:
            companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=account.userID).companyID
            company = AccountModels.Company.objects.get(pk=companyID)
            return render(request, 'SettingsUserWithCompany.html')
        except Exception:
            if account.deSubDay != 0:
                return returnSettings(request, account, 'renew')
            else:
                return returnSettings(request, account, '')
    else:
        return HttpResponseRedirect('/')

def returnSettings(request, account, option):
    if account.subscriptionType == 0 or account.subscriptionType == 9:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBranding' + option + '.html', {'form':form})
            return render(request, 'SettingsRegistered' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsWithBranding' + option + '.html', {'form':form})
        return render(request, 'Settings' + option + '.html')
    elif account.subscriptionType == 1:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBrandingShow2to3' + option + '.html', {'form':form})
            return render(request, 'SettingsRegisteredShow2to3' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsWithBrandingShow2to3' + option + '.html', {'form':form})
        return render(request, 'SettingsShow2to3' + option + '.html')
    elif account.subscriptionType == 2:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBrandingShow3' + option + '.html', {'form':form})
            return render(request, 'SettingsRegisteredShow3' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsWithBrandingShow3' + option + '.html', {'form':form})
        return render(request, 'SettingsShow3' + option + '.html')
    elif account.subscriptionType == 3:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBrandingShowNone' + option + '.html', {'form':form})
            return render(request, 'SettingsRegisteredShowNone' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsWithBrandingShowNone' + option + '.html', {'form':form})
        return render(request, 'SettingsShowNone' + option + '.html')

def ShowSubPage(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        return render(request, 'SettingsShowSub.html')
    else:
        return HttpResponseRedirect('/')

def RegisterCard(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)

        try:
            companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=account.userID).companyID
            company = AccountModels.Company.objects.get(pk=companyID)
            return render(request, 'SettingsUserWithCompany.html')
        except Exception:
            if account.deSubDay != 0:
                return returnRegisterCard(request, account, 'renew')
            else:
                return returnRegisterCard(request, account, '')
    else:
        return HttpResponseRedirect('/')

def returnRegisterCard(request, account, option):
    if account.subscriptionType == 0 or account.subscriptionType == 9:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBranding' + option + '.html', {'form':form})
            return render(request, 'SettingsRegistered' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsRegisterCardWithBrand' + option + '.html', {'alertText':'Please register a credit card to continue.', 'form':form})
        return render(request, 'SettingsRegisterCard' + option + '.html', {'alertText':'Please register a credit card to continue.'})
    elif account.subscriptionType == 1:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBrandingShow2to3' + option + '.html', {'form':form})
            return render(request, 'SettingsRegisteredShow2to3' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsRegisterCardWithBrandShow2to3' + option + '.html', {'alertText':'Please register a credit card to continue.', 'form':form})
        return render(request, 'SettingsRegisterCardShow2to3' + option + '.html', {'alertText':'Please register a credit card to continue.'})
    elif account.subscriptionType == 2:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBrandingShow3' + option + '.html', {'form':form})
            return render(request, 'SettingsRegisteredShow3' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsRegisterCardWithBrandShow3' + option + '.html', {'alertText':'Please register a credit card to continue.', 'form':form})
        return render(request, 'SettingsRegisterCardShow3' + option + '.html', {'alertText':'Please register a credit card to continue.'})
    elif account.subscriptionType == 3:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredWithBrandingShowNone' + option + '.html', {'form':form})
            return render(request, 'SettingsRegisteredShowNone' + option + '.html')
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsRegisterCardWithBrandShowNone' + option + '.html', {'alertText':'Please register a credit card to continue.', 'form':form})
        return render(request, 'SettingsRegisterCardShowNone' + option + '.html', {'alertText':'Please register a credit card to continue.'})

def SettingsUpdate(request, update):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)

        alertText = ''
        if update == '1':
            alertText = 'Your Password has been successfully updated.'
        elif update == '2':
            alertText = 'Your Credit Card information has been successfully updated.'
        elif update == '3':
            alertText = 'Your Credit Card information has been successfully removed.'
        elif update == '4':
            alertText = 'Your subscription has been successfully updated.'
        elif update == '5':
            alertText = 'Your brand has been successfully updated.'
        elif update == '6':
            alertText = 'Documents have been added to your account.'
        elif update == '7':
            alertText = 'Auto Renewal has been turned off for your account.'
        elif update == '8':
            alertText = 'Auto Renewal has been turned on for your account.'

        try:
            companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=account.userID).companyID
            company = AccountModels.Company.objects.get(pk=companyID)
            return render(request, 'SettingsUserWithCompanyError.html')
        except Exception:
            if account.deSubDay != 0:
                return returnUpdate(request, account, alertText, 'renew')
            else:
                return returnUpdate(request, account, alertText, '')
    else:
        return HttpResponseRedirect('/')

def returnUpdate(request, account, alertText, option):
    if account.subscriptionType == 0 or account.subscriptionType == 9:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorWithBranding' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredError' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorWithBranding' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsError' + option + '.html', {'alertText':alertText})
    elif account.subscriptionType == 1:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorWithBrandingShow2to3' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorShow2to3' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorWithBrandingShow2to3' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorShow2to3' + option + '.html', {'alertText':alertText})
    elif account.subscriptionType == 2:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorWithBrandingShow3' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorShow3' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorWithBrandingShow3' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorShow3' + option + '.html', {'alertText':alertText})
    elif account.subscriptionType == 3:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorWithBrandingShowNone' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorShowNone' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorWithBrandingShowNone' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorShowNone' + option + '.html', {'alertText':alertText})

def SettingsError(request, error):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)

        alertText = ''
        if error == '1':
            alertText = 'Your payment has failed. Please Try again.'
        elif error == '2':
            alertText = 'Payment Verification Failed. Please check your information using the Wallet tab.'
        elif error == '3':
            alertText = 'Please update your payment information using the Wallet tab.'

        try:
            companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=account.userID).companyID
            company = AccountModels.Company.objects.get(pk=companyID)
            return render(request, 'SettingsUserWithCompanyErrorRed.html')
        except Exception:
            if account.deSubDay != 0:
                return returnError(request, account, alertText, 'renew')
            else:
                return returnError(request, account, alertText, '')
    else:
        return HttpResponseRedirect('/')

def returnError(request, account, alertText, option):
    if account.subscriptionType == 0 or account.subscriptionType == 9:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorRedWithBranding' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorRed' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorRedWithBranding' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorRed' + option + '.html', {'alertText':alertText})
    elif account.subscriptionType == 1:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorRedWithBrandingShow2to3' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorRedShow2to3' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorRedWithBrandingShow2to3' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorRedShow2to3' + option + '.html', {'alertText':alertText})
    elif account.subscriptionType == 2:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorRedWithBrandingShow3' + option + '.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorRedShow3' + option + '.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorRedWithBrandingShow3' + option + '.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorRedShow3' + option + '.html', {'alertText':alertText})
    elif account.subscriptionType == 3:
        if len(account.cNum) > 1:
            if account.logoBranding == True:
                form = AccountForms.UploadBrandForm()
                return render(request, 'SettingsRegisteredErrorRedWithBrandingShowNone.html', {'alertText':alertText, 'form':form})
            return render(request, 'SettingsRegisteredErrorRedShowNone.html', {'alertText':alertText})
        if account.logoBranding == True:
            form = AccountForms.UploadBrandForm()
            return render(request, 'SettingsErrorRedWithBrandingShowNone.html', {'alertText':alertText, 'form':form})
        return render(request, 'SettingsErrorRedShowNone.html', {'alertText':alertText})

def TurnOffRenew(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)

        date = datetime.datetime.today()
        currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
        thisDay = date.day
        if thisDay >= 28:
            thisDay = 1
        account.deSubDay = thisDay
        account.deSubDate = currentDate
        account.save()

        return SettingsUpdate(request, '7')
    else:
        return HttpResponseRedirect('/')

def TurnOnRenew(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)

        account.deSubDay = 0
        account.deSubDate = ''
        account.save()

        return SettingsUpdate(request, '8')
    else:
        return HttpResponseRedirect('/')
    
def TurnOffRenewCompany(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=account.userID).companyID
        company = AccountModels.Company.objects.get(pk=companyID)

        date = datetime.datetime.today()
        currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
        thisDay = date.day
        if thisDay >= 28:
            thisDay = 1
        company.deSubDay = thisDay
        company.deSubDate = currentDate
        company.save()

        return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')
    else:
        return HttpResponseRedirect('/')

def TurnOnRenewCompany(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        accountEmail = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=accountEmail)
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=account.userID).companyID
        company = AccountModels.Company.objects.get(pk=companyID)

        company.deSubDay = 0
        company.deSubDate = ''
        company.save()

        return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')
    else:
        return HttpResponseRedirect('/')

def Subscription(request, choice):
    email = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
    account = AccountModels.Account.objects.get(pk=email)
    if len(account.cNum) < 1:
        return HttpResponseRedirect('/UserDashboard/Settings/RegisterCard/')
    addDocuments = 0
    addTemplates = 0
    amount = 0.0
    logoBranding = False
    if choice == 1:
        addDocuments = 10
        addTemplates = 5
        amount = 9.99
    elif choice == 2:
        addDocuments = 9999
        addTemplates = 10
        amount = 14.99
        logoBranding = True
    elif choice == 3:
        addDocuments = 9999
        addTemplates = 20
        amount = 19.99
        logoBranding = True
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
    order.description = "Iris Documents Subscription"

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
    if choice == 1:
        line_item_1.itemId = "1"
        line_item_1.name = "Personal Lite Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "9.99"
    elif choice == 2:
        line_item_1.itemId = "2"
        line_item_1.name = "Personal Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "14.99"
    elif choice == 3:
        line_item_1.itemId = "3"
        line_item_1.name = "Personal Pro Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "19.99"

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

    date = datetime.datetime.today()
  
    if date.day > 28:
        subDay = 1
    else:
        subDay = date.day

    if response is not None:   
        if (response.messages.resultCode=="Ok"):
            account.subscriptionType = choice
            account.subDay = subDay
            account.subDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
            account.documentsAvailable = addDocuments
            account.templatesAvailable = addTemplates
            account.logoBranding = logoBranding
            account.save()
            return HttpResponseRedirect('/UserDashboard/Settings/Update/4/')
        else:
            return HttpResponseRedirect('/UserDashboard/Settings/Error/1/')
            #return HttpResponse(response.messages.message.code + ' Credit Card Number: ' + creditCard.cardNumber + ' Exp: ' + creditCard.expirationDate + ' Name: ' + createtransactionrequest.refId + ' Amount: ' + str(amount))
    else:
        return HttpResponseRedirect('/UserDashboard/Settings/Error/2/')

def CompanyDashboard(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        try:
            companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=request.COOKIES.get('user')).companyID
            company = AccountModels.Company.objects.get(pk=companyID)
        except Exception:
            return render(request, 'CreateCompany.html')

        info = []
        info.append(company.documentsAvailable)
        info.append(company.documentsUsed)
        info.append(company.templatesAvailable)
        info.append(company.templatesUsed)
        info.append(company.membersAvailable)
        info.append(company.membersUsed)

        companyLatest = company.latest
        latestInfo = []
        latestDates = []
        latestLinks = []
        numInfos = 0
            
        for eachKey in companyLatest:
            value = companyLatest[eachKey]
            if value[0] == 'n':
                valueSplit = value.split('newdoc/')
                valueSplit = valueSplit[1].split('[by]')
                valueSplit2 = valueSplit[1].split('>')
                valueSplit3 = valueSplit2[1].split('<')
                accountEmail = AccountModels.AccountLookupByID.objects.get(pk=valueSplit2[0]).email
                account = AccountModels.Account.objects.get(pk=accountEmail)
                name = account.fName + " " + account.lName
                latestInfo.append('New Document: ' + valueSplit[0] + ' Created By: ' + name)
                latestDates.append('Created On: ' + valueSplit3[0])
                latestLinks.append('/ManageDocument/' + valueSplit3[1] + '/verified/')
                numInfos += 1
            elif value[0] == 't':
                valueSplit = value.split('temp/')
                valueSplit = valueSplit[1].split('[by]')
                valueSplit2 = valueSplit[1].split('>')
                valueSplit3 = valueSplit2[1].split('<')
                accountEmail = AccountModels.AccountLookupByID.objects.get(pk=valueSplit2[0]).email
                account = AccountModels.Account.objects.get(pk=accountEmail)
                name = account.fName + " " + account.lName
                latestInfo.append('New Template: ' + valueSplit[0] + ' Created By: ' + name)
                latestDates.append('Created On: ' + valueSplit3[0])
                latestLinks.append('/ManageDocument/' + valueSplit3[1] + '/EditTemplate/')
                numInfos += 1
            elif value[0] == 'u':
                valueSplit = value.split('user/')
                valueSplit = valueSplit[1].split('[by]')
                valueSplit2 = valueSplit[1].split('>')
                valueSplit3 = valueSplit2[1].split('<')
                latestInfo.append('New User: ' + valueSplit[0] + ' Added By: ' + valueSplit2[0])
                latestDates.append('Added On: ' + valueSplit3[0])
                latestLinks.append('/UserDashboard/CompanyDashboard/ManageMember/' + valueSplit3[1] + '/')
                numInfos += 1
        
        if numInfos == 0:
            return render(request, 'CompanyDashboard.html', {'CompanyID':companyID, 'Info':info, 'latestInfo':latestInfo,'lastestDates':latestDates,'latestLinks':latestLinks})
        else:
            return render(request, 'CompanyDashboard' + str(numInfos) + '.html', {'CompanyID':companyID, 'Info':info, 'latestInfo':latestInfo,'lastestDates':latestDates,'latestLinks':latestLinks})
    else:
        return HttpResponseRedirect('/')

def ManageCompanyMember(request, userID):
    requestUserID = request.COOKIES.get('user')
    requestUserEmail = AccountModels.AccountLookupByID.objects.get(pk=requestUserID).email
    requestUser = AccountModels.Account.objects.get(pk=requestUserEmail)
    requestUserPermission = requestUser.companyPermission

    accountEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=accountEmail)

    accountInfo = []
    accountInfo.append(account.username)
    accountInfo.append(account.email)
    accountInfo.append(account.companyPermission)
    accountInfo.append(account.dateAddedToCompany)
    accountInfo.append(account.userID)
    if requestUserPermission == 'Creator':
        return render(request, 'CreatorManageMember.html',{'accountInfo':accountInfo})
    elif requestUserPermission == 'Admin':
        if account.companyPermission == 'Member':
            return render(request, 'CreatorManageMember.html',{'accountInfo':accountInfo})
        return render(request, 'MemberManageMember.html',{'accountInfo':accountInfo})
    elif requestUserPermission == 'Member':
        return render(request, 'MemberManageMember.html',{'accountInfo':accountInfo})
    return HttpResponseRedirect('/')

def DeleteMember(request, userID):
    accountEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=accountEmail)
    companyIDObj = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID)
    company = AccountModels.Company.objects.get(pk=companyIDObj.companyID)

    companyUserNonce = account.companyUserNonce
    companyNumUsers = company.numUsers

    while companyUserNonce < companyNumUsers:
        company.associatedWith[account.companyUserNonce] = company.associatedWith[account.companyUserNonce + 1]
        companyUserNonce += 1

    company.numUsers -=  1
    company.save()

    account.companyID = ''
    account.companyPermission = ''
    account.companyUserNonce = 0
    account.save()

    return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')

def ChangeMember(request, userID):
    requestUserID = request.COOKIES.get('user')
    requestUserEmail = AccountModels.AccountLookupByID.objects.get(pk=requestUserID).email
    requestUser = AccountModels.Account.objects.get(pk=requestUserEmail)
    requestUserPermission = requestUser.companyPermission

    accountEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    account = AccountModels.Account.objects.get(pk=accountEmail)

    accountInfo = []
    accountInfo.append(account.username)
    accountInfo.append(account.email)
    accountInfo.append(account.companyPermission)
    accountInfo.append(account.dateAddedToCompany)
    accountInfo.append(account.userID)

    if requestUserPermission == 'Creator':
        if account.companyPermission == 'Admin':
            account.companyPermission = 'Member'
            account.save()
        elif account.companyPermission == 'Member':
            account.companyPermission = 'Admin'
            account.save()
        accountInfo = []
        accountInfo.append(account.username)
        accountInfo.append(account.email)
        accountInfo.append(account.companyPermission)
        accountInfo.append(account.dateAddedToCompany)
        accountInfo.append(account.userID)
        return render(request, 'CreatorManageMember.html',{'accountInfo':accountInfo})
    elif requestUserPermission == 'Admin':
        if account.companyPermission == 'Member':
            account.companyPermission = 'Admin'
            account.save()
            accountInfo = []
            accountInfo.append(account.username)
            accountInfo.append(account.email)
            accountInfo.append(account.companyPermission)
            accountInfo.append(account.dateAddedToCompany)
            accountInfo.append(account.userID)
            return render(request, 'CreatorManageMember.html',{'accountInfo':accountInfo})
        return render(request, 'MemberManageMember.html',{'accountInfo':accountInfo})
    elif requestUserPermission == 'Member':
        return render(request, 'MemberManageMember.html',{'accountInfo':accountInfo})
    return HttpResponseRedirect('/')


def CreateCompany(request):
    try: 
        userID = request.COOKIES.get('user')
        if len(userID) < 2:
            response = HttpResponseRedirect('/')
            return response
    except Exception:
        response = HttpResponseRedirect('/')
        return response

    if request.method == 'POST':
        companyName = request.POST.get('CompanyName', None)
        subscription = request.POST.get('subscription', None)
        email = AccountModels.AccountLookupByID.objects.get(pk=request.COOKIES.get('user')).email
        account = AccountModels.Account.objects.get(pk=email)

        if len(account.cNum) < 1:
            return HttpResponseRedirect('/UserDashboard/Settings/RegisterCard/')

        if (companyName != None) and (subscription != None):
            logoBranding = False
            if subscription == 'First':
                amount = 19.99
            elif subscription == 'Second':
                amount = 29.99
                logoBranding = True
            elif subscription == 'Third':
                amount = 49.99
                logoBranding = True
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
            order.description = "Iris Documents Subscription"

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
            if subscription == 'First':
                line_item_1.itemId = "3"
                line_item_1.name = "Business Lite Subscription"
                line_item_1.description = "Your subsciption to IrisDocuments.com"
                line_item_1.quantity = "1"
                line_item_1.unitPrice = "19.99"
            elif subscription == 'Second':
                line_item_1.itemId = "4"
                line_item_1.name = "Business Subscription"
                line_item_1.description = "Your subsciption to IrisDocuments.com"
                line_item_1.quantity = "1"
                line_item_1.unitPrice = "29.99"
            elif subscription == 'Third':
                line_item_1.itemId = "5"
                line_item_1.name = "Business Pro Subscription"
                line_item_1.description = "Your subsciption to IrisDocuments.com"
                line_item_1.quantity = "1"
                line_item_1.unitPrice = "49.99"

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

            if not(response.messages.resultCode=="Ok"):
                return HttpResponse(response.messages.message.code)

            try:
                companys = AccountModels.Companys.objects.get(pk=1)
                companys.companys += 1
                companys.save()
            except Exception:
                companys = AccountModels.Companys(key=1, companys=1)
                companys.save()

            companyNumber = companys.companys

            companyNumber = str(companyNumber)
            lengthCompanyNumber = len(companyNumber)
            if (lengthCompanyNumber < 16):
                zeroes = 16 - lengthCompanyNumber
                string = ''
                while zeroes != 0:
                    string = string + '0'
                    zeroes -= 1
                companyNumber = string + companyNumber

            userID = request.COOKIES.get('user')
            accountEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
            account = AccountModels.Account.objects.get(pk=accountEmail)
            account.companyID = companyNumber
            account.companyPermission = 'Creator'
            date = datetime.datetime.today()
            currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
            account.dateAddedToCompany = currentDate
            account.companyUserNonce = 1
            account.save()
            thisIP = ClientFunctions.get_client_ip(request)

            if date.day > 28:
                subDay = 1
            else:
                subDay = date.day

            if subscription == 'First':
                newCompany = AccountModels.Company(companyID=companyNumber,createdBy=email,subscriptionType=1,subDay=subDay,subDate=currentDate,dateCreated=currentDate,IPCreated=thisIP,documentsAvailable=9999,templatesAvailable=20,membersAvailable=50)
            elif subscription == 'Second':
                newCompany = AccountModels.Company(companyID=companyNumber,createdBy=email,subscriptionType=2,subDay=subDay,subDate=currentDate,dateCreated=currentDate,IPCreated=thisIP,documentsAvailable=9999,templatesAvailable=50,membersAvailable=100)
            elif subscription == 'Third':
                newCompany = AccountModels.Company(companyID=companyNumber,createdBy=email,subscriptionType=3,subDay=subDay,subDate=currentDate,dateCreated=currentDate,IPCreated=thisIP,documentsAvailable=9999,templatesAvailable=100,membersAvailable=250)
            
            newCompany.logoBranding = logoBranding
            newCompany.associatedWith[1] = userID
            newCompany.subDate = currentDate
            newCompany.save()

            newLookup = AccountModels.CompanyLookupByAccountID(userID=userID,companyID=companyNumber)
            newLookup.save()
            newLookup = AccountModels.CompanyDocuments(companyID=companyNumber,documents=0)
            newLookup.save()
            newLookup = AccountModels.CompanyTemplates(companyID=companyNumber,templates=0)
            newLookup.save()

            return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')

    return render(request, 'CreateCompany.html')

def AddMember(request):
    if request.method == 'POST':
        name = request.POST.get('Name', None)
        email = request.POST.get('Email', None)
        account = AccountModels.Account.objects.get(pk=email)
        newID = account.userID
        permission = request.POST.get('Permission', None)
        adderUser = request.COOKIES.get('user')
        adderUserAccEmail = AccountModels.AccountLookupByID.objects.get(pk=adderUser).email
        adderUserAcc = AccountModels.Account.objects.get(pk=adderUserAccEmail)
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=adderUser).companyID
        company = AccountModels.Company.objects.get(pk=companyID)

        subject = adderUserAcc.username + ' has added you their company.'
        text_content = adderUserAcc.username + ' has added you their company. \n\n Please click the link below to accept this invitation.'
        html_content = render_to_string('emailAddUserToCompany.html', {'subject':subject, 'text':text_content, 'name':name, 'email':email, 'permission':permission, 'adderUser':adderUser})

        with mail.get_connection() as thisConnection:
            email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [email], connection=thisConnection)
            email.attach_alternative(html_content, 'text/html')
            email.send()

    return HttpResponseRedirect('/UserDashboard/CompanyDashboard/Settings/1/')

def ConfirmMember(request, name, email, permission, adderUser):
    account = AccountModels.Account.objects.get(pk=email)
    newID = account.userID
    adderUserAccEmail = AccountModels.AccountLookupByID.objects.get(pk=adderUser).email
    adderUserAcc = AccountModels.Account.objects.get(pk=adderUserAccEmail)
    companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=adderUser).companyID
    company = AccountModels.Company.objects.get(pk=companyID)

    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)

    if ((name != None) and (email != None)) and (permission != None):
        company.numUsers += 1
        company.associatedWith[company.numUsers] = newID
        company.latest['9'] = company.latest['8']
        company.latest['8'] = company.latest['7']
        company.latest['7'] = company.latest['6']
        company.latest['6'] = company.latest['5']
        company.latest['5'] = company.latest['4']
        company.latest['4'] = company.latest['3']
        company.latest['3'] = company.latest['2']
        company.latest['2'] = company.latest['1']
        company.latest['1'] = company.latest['0']
        company.latest['0'] = 'user/' + account.username + '[by]' + adderUserAcc.username + '>' + currentDate + '<' + account.userID
        company.save()
        newLookup = AccountModels.CompanyLookupByAccountID(userID=newID,companyID=companyID)
        newLookup.save()

        account.companyID = company.companyID
        account.companyPermission = permission
        account.dateAddedToCompany = currentDate
        account.companyUserNonce = company.numUsers
        account.save()

    return HttpResponseRedirect('/UserDashboard/Settings/Update/Update4/')

def CompanySettings(request):
    if len(request.COOKIES.get('user', ''))  > 1:
        form = AccountForms.UploadBrandForm()
        return render(request, 'CompanySettings.html', {'form':form})
    return HttpResponseRedirect('/')

def CompanySettingsUpdate(request, update):
    alertText = ''
    if update == '1':
        alertText = "Please check the new member's email."
    elif update == '2':
        alertText = "The Company's Brand has been updated."

    if len(request.COOKIES.get('user', ''))  > 1:
        form = AccountForms.UploadBrandForm()
        return render(request, 'CompanySettingsUpdate.html', {'form':form, 'alertText':alertText})
    return HttpResponseRedirect('/')

def CompanyDocuments(request, filterType, page):
    userID = request.COOKIES.get('user')
    companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID).companyID

    numDocuments = AccountModels.CompanyDocuments.objects.get(pk=companyID).documents
    numPages = math.ceil(numDocuments/10)

    pages = []
    if page > 1:
        pages.append(str(page-1))
    pages.append(str(page))
    if numPages > page:
        pages.append(str(page+1))
    if numPages > page+1:
        pages.append(str(page+2)) 
    if numPages > page+2:
        pages.append(str(numPages)) 


    titles = []
    authors = []
    dates = []
    IDs = []
    if filterType == 'title':
        if numDocuments > 10:
            for each in AccountModels.CompanyDocument.objects.filter(companyID=companyID).order_by('title')[((10 * page)-10):(10 * page)]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.documentID)
        elif numDocuments > 0:
            for each in AccountModels.CompanyDocument.objects.filter(companyID=companyID).order_by('title')[:numDocuments]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.documentID)
        else:
            return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')
        return render(request, 'CompanyDocumentsByTitle.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})
    elif filterType == 'author':
        if numDocuments > 10:
            for each in AccountModels.CompanyDocument.objects.filter(companyID=companyID).order_by('author')[((10 * page)-10):(10 * page)]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.documentID)
        else:
            for each in AccountModels.CompanyDocument.objects.filter(companyID=companyID).order_by('author')[:numDocuments]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.documentID)
        return render(request, 'CompanyDocumentsByAuthor.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})
    elif filterType == 'date':
        if numDocuments > 10:
            for each in AccountModels.CompanyDocument.objects.filter(companyID=companyID).order_by('-createdDate')[((10 * page)-10):(10 * page)]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.documentID)
        else:
            for each in AccountModels.CompanyDocument.objects.filter(companyID=companyID).order_by('-createdDate')[:numDocuments]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.documentID)
        return render(request, 'CompanyDocumentsByDates.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})

    return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')

def CompanyTemplates(request, filterType, page):
    userID = request.COOKIES.get('user')
    companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID).companyID

    numTemplates = AccountModels.CompanyTemplates.objects.get(pk=companyID).templates
    numPages = math.ceil(numTemplates/10)

    pages = []
    if page > 1:
        pages.append(str(page-1))
    pages.append(str(page))
    if numPages > page:
        pages.append(str(page+1))
    if numPages > page+1:
        pages.append(str(page+2)) 
    if numPages > page+2:
        pages.append(str(numPages)) 


    titles = []
    authors = []
    dates = []
    IDs = []
    if filterType == 'title':
        if numTemplates > 10:
            for each in AccountModels.CompanyTemplate.objects.filter(companyID=companyID).order_by('title')[((10 * page)-10):(10 * page)]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.templateID)
        elif numTemplates > 0:
            for each in AccountModels.CompanyTemplate.objects.filter(companyID=companyID).order_by('title')[:numTemplates]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.templateID)
        else:
            return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')
        return render(request, 'CompanyTemplatesByTitle.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})
    elif filterType == 'author':
        if numTemplates > 10:
            for each in AccountModels.CompanyTemplate.objects.filter(companyID=companyID).order_by('author')[((10 * page)-10):(10 * page)]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.templateID)
        else:
            for each in AccountModels.CompanyTemplate.objects.filter(companyID=companyID).order_by('author')[:numTemplates]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.templateID)
        return render(request, 'CompanyTemplatesByAuthor.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})
    elif filterType == 'date':
        if numTemplates > 10:
            for each in AccountModels.CompanyTemplate.objects.filter(companyID=companyID).order_by('-createdDate')[((10 * page)-10):(10 * page)]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.templateID)
        else:
            for each in AccountModels.CompanyTemplate.objects.filter(companyID=companyID).order_by('-createdDate')[:numTemplates]:
                titles.append(each.title)
                authors.append(each.author)
                dates.append(each.createdDate)
                IDs.append(each.templateID)
        return render(request, 'CompanyTemplatesByDates.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})

    return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')

def CompanyMembers(request, filterType, page):
    userID = request.COOKIES.get('user')
    companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID).companyID

    numUsers = AccountModels.Company.objects.get(pk=companyID).numUsers
    numPages = math.ceil(numUsers/10)

    pages = []
    if page > 1:
        pages.append(str(page-1))
    pages.append(str(page))
    if numPages > page:
        pages.append(str(page+1))
    if numPages > page+1:
        pages.append(str(page+2)) 
    if numPages > page+2:
        pages.append(str(numPages)) 


    titles = [] #usernames - local variables for code replication simplification
    authors = [] #permissions 
    dates = []
    IDs = []
    if filterType == 'username':
        if numUsers > 10:
            for each in AccountModels.Account.objects.filter(companyID=companyID).order_by('username')[((10 * page)-10):(10 * page)]:
                titles.append(each.username)
                authors.append(each.companyPermission)
                dates.append(each.dateAddedToCompany)
                IDs.append(each.userID)
        else:
            for each in AccountModels.Account.objects.filter(companyID=companyID).order_by('username')[:numUsers]:
                titles.append(each.username)
                authors.append(each.companyPermission)
                dates.append(each.dateAddedToCompany)
                IDs.append(each.userID)
        return render(request, 'CompanyMembersByUsername.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})
    elif filterType == 'permission':
        if numUsers > 10:
            for each in AccountModels.Account.objects.filter(companyID=companyID).order_by('companyPermission')[((10 * page)-10):(10 * page)]:
                titles.append(each.username)
                authors.append(each.companyPermission)
                dates.append(each.dateAddedToCompany)
                IDs.append(each.userID)
        else:
            for each in AccountModels.Account.objects.filter(companyID=companyID).order_by('companyPermission')[:numUsers]:
                titles.append(each.username)
                authors.append(each.companyPermission)
                dates.append(each.dateAddedToCompany)
                IDs.append(each.userID)
        return render(request, 'CompanyMembersByPermission.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})
    elif filterType == 'date':
        if numUsers > 10:
            for each in AccountModels.Account.objects.filter(companyID=companyID).order_by('-dateAddedToCompany')[((10 * page)-10):(10 * page)]:
                titles.append(each.username)
                authors.append(each.companyPermission)
                dates.append(each.dateAddedToCompany)
                IDs.append(each.userID)
        else:
            for each in AccountModels.Account.objects.filter(companyID=companyID).order_by('-dateAddedToCompany')[:numUsers]:
                titles.append(each.username)
                authors.append(each.companyPermission)
                dates.append(each.dateAddedToCompany)
                IDs.append(each.userID)
        return render(request, 'CompanyMembersByDate.html', {'titles':titles,'authors':authors,'dates':dates,'IDs':IDs,'pages':pages})

    return HttpResponseRedirect('/UserDashboard/CompanyDashboard/')

def morningCheckSubscribers():
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    for each in AccountModels.Account.objects.filter(subDay=date.day):
        if not each.subDate == currentDate:
            each.subDate = currentDate
            each.save()
            print('Charging Personal Account ' + each.username)
            chargeAcc(each.email)

def morningCheckSubscribersCompany():
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    for each in AccountModels.Company.objects.filter(subDay=date.day):
        if not each.subDate == currentDate:
            each.subDate = currentDate
            each.save()
            print('Charging Company attached to Account ' + each.createdBy)
            chargeCompany(each.companyID)

def morningCheckDescribers():
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    for each in AccountModels.Account.objects.filter(deSubDay=date.day):
        if not each.deSubDate == currentDate:
            each.deSubDate = currentDate
            each.subDate = ''
            each.subDay = 0
            each.subscriptionType = 0
            each.deSubDay = 0
            each.documentsAvailable = 0
            each.templatesAvailable = 0
            each.save()

def morningCheckDescribersCompany():
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    for each in AccountModels.Company.objects.filter(deSubDay=date.day):
        if not each.deSubDate == currentDate:
            each.deSubDate = currentDate
            each.subDate = ''
            each.subDay = 0
            each.subscriptionType = 0
            each.deSubDay = 0
            each.documentsAvailable = 0
            each.templatesAvailable = 0
            each.membersAvailable = 0
            each.save()

def morningCheckFreeTrial():
    date = datetime.datetime.today()
    currentDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)
    for each in AccountModels.Account.objects.filter(trialEndDay=date.day):
        if not each.trialDate == currentDate:
            each.trialDate = currentDate
            each.trialEndDay = 0
            each.subscriptionType = 0
            each.documentsAvailable = 0
            each.templatesAvailable = 0
            each.save()

def chargeAcc(email):
    account = AccountModels.Account.objects.get(pk=email)
    addDocuments = 0
    addTemplates = 0
    amount = 0.0
    subType = account.subscriptionType
    if subType == 1:
        addDocuments = 10
        addTemplates = 5
        amount = 9.99
    elif subType == 2:
        addDocuments = 9999
        addTemplates = 10
        amount = 14.99
    elif subType == 3:
        addDocuments = 9999
        addTemplates = 20
        amount = 19.99
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
    order.description = "Iris Documents Subscription"

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
    if subType == 1:
        line_item_1.itemId = "1"
        line_item_1.name = "Personal Lite Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "9.99"
    elif subType == 2:
        line_item_1.itemId = "2"
        line_item_1.name = "Personal Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "14.99"
    elif subType == 3:
        line_item_1.itemId = "3"
        line_item_1.name = "Personal Pro Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "19.99"

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
        account.documentsAvailable = addDocuments
        account.save()
    else:
        account.documentsAvailable = 0
        account.templatesAvailable = 0
        account.save()

def chargeCompany(companyID):
    company = AccountModels.Company.objects.get(pk=companyID)
    account = AccountModels.Account.objects.get(pk=company.createdBy)
    addDocuments = 0
    addTemplates = 0
    addMembers = 0
    amount = 0.0
    subType = company.subscriptionType
    if subType == 1:
        addDocuments = 9999
        addTemplates = 20
        addMembers = 50
        amount = 19.99
    elif subType == 2:
        addDocuments = 9999
        addTemplates = 50
        addMembers = 100
        amount = 29.99
    elif subType == 3:
        addDocuments = 9999
        addTemplates = 100
        addMembers = 250
        amount = 49.99
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
    order.description = "Iris Documents Subscription"

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
    if subType == 1:
        line_item_1.itemId = "3"
        line_item_1.name = "Business Lite Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "19.99"
    elif subType == 2:
        line_item_1.itemId = "4"
        line_item_1.name = "Business Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "29.99"
    elif subType == 3:
        line_item_1.itemId = "5"
        line_item_1.name = "Business Pro Subscription"
        line_item_1.description = "Your subsciption to IrisDocuments.com"
        line_item_1.quantity = "1"
        line_item_1.unitPrice = "49.99"

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
        company.documentsAvailable = addDocuments
        company.documentsUsed = 0
        company.templatesAvailable = addTemplates
        company.membersAvailable = addMembers
        company.save()
    else:
        company.documentsAvailable = 0
        company.documentsUsed = 0
        company.templatesAvailable = 0
        company.membersAvailable = 0
        company.save()

def DownloadReturnPolicy(request):
    path = 'ReturnPolicy.pdf'
    file_path = os.path.join(settings.STATIC_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404