from http.client import HTTPResponse
from django.shortcuts import render
from django.core import mail
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from PIL import Image
from django.http import HttpResponseRedirect
from django.conf import settings
from django.http import HttpResponse, Http404
import os
import io
import base64

import json
import uuid
import datetime
import re
from copy import deepcopy
import boto3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from PyPDF2 import PdfWriter, PdfReader

import shutil
import math
import ipinfo
from pytz import timezone

from yaml import DocumentEndToken

from CreateAccount import forms as AccountForms
from Login import forms as LoginForms
from . import models
from . import forms
from CreateAccount import models as AccountModels
from Login import ClientFunctions

# Upload User File to AWS (Handle request.FILES uses file.name)
def uploadToAWS(file, fileType):
    s3 = boto3.resource('s3', aws_access_key_id='', aws_secret_access_key='')
    deep_file = deepcopy(file)
    file_name_uuid = uuid.uuid4().hex[:20]
    fileText = os.path.splitext(file.name)
    file_path = str("static/files/" + fileType + "/" + file_name_uuid + fileText[1])
    s3.Bucket('iris1-static').put_object(Key=file_path, Body=deep_file)

    return file_name_uuid

# Upload Site File to AWS (Handle local file uses string)
def uploadToAWSsite(file, fileType):
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    file_name_uuid = uuid.uuid4().hex[:20]
    fileText = os.path.splitext(file)
    file_path = str("static/files/" + fileType + "/" + file_name_uuid + fileText[1])
    s3.upload_file(file, 'iris1-static', file_path)

    return file_name_uuid

def removeDraftFromMemory(userID):
    numberOfDocumentDrafts = models.NumberOfDocumentDrafts.objects.get(pk=userID)
    draftsKey = userID + '_' + str(1)
    documentDraftsObj = models.DocumentDrafts.objects.get(pk=draftsKey)
    newDocumentKey = documentDraftsObj.documentKey

    document = models.Document.objects.get(pk=newDocumentKey)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    documentFile = document.fileuuid + '.pdf'

    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)

    numberOfDocumentDrafts.documents -= 1
    numberOfDocumentDrafts.save()

    i = 1
    while i < 11:
        draftsKey = userID + '_' + str(i)
        newDraftsKey = userID + '_' + str(i + 1)
        documentDraftsObj = models.DocumentDrafts.objects.get(pk=newDraftsKey)
        newDocumentKey = documentDraftsObj.documentKey

        documentDraftsObj = models.DocumentDrafts.objects.get(pk=draftsKey)
        documentDraftsObj.documentKey = newDocumentKey
        documentDraftsObj.save()
        i += 1

def removeSentFromMemory(userID):
    numberOfDocumentSent = models.NumberOfDocumentSent.objects.get(pk=userID)
    sentKey = userID + '_' + str(1)
    documentSentObj = models.DocumentSent.objects.get(pk=sentKey)
    newDocumentKey = documentSentObj.documentKey

    document = models.Document.objects.get(pk=newDocumentKey)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    documentFile = document.fileuuid + '.pdf'

    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)

    numberOfDocumentSent.documents -= 1
    numberOfDocumentSent.save()

    i = 1
    while i < 26:
        sentKey = userID + '_' + str(i)
        newSentKey = userID + '_' + str(i + 1)
        documentSentObj = models.DocumentsSent.objects.get(pk=newSentKey)
        newDocumentKey = documentSentObj.documentKey

        documentSentObj = models.DocumentsSent.objects.get(pk=sentKey)
        documentSentObj.documentKey = newDocumentKey
        documentSentObj.save()
        i += 1


def uploaded(request):

    try:
        userID = request.COOKIES.get('user')
        email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        account = AccountModels.Account.objects.get(pk=email)
    except Exception:
        return HttpResponseRedirect('/')
        

    if request.method == 'POST':

        numberOfDocumentDrafts = models.NumberOfDocumentDrafts.objects.get(pk=userID)
        numberOfDocumentDrafts.documents += 1
        numberOfDocumentDrafts.save()

        if numberOfDocumentDrafts.documents > 11:
            removeDraftFromMemory(userID)

        num = numberOfDocumentDrafts.documents
        draftRequestID = userID + '_' + str(num)

        try:
            if request.FILES['additionalFile'] is not None:
                form = forms.UploadFilesForm(request.POST, request.FILES)
        except Exception:
            form = forms.UploadFileForm(request.POST, request.FILES)

        documentsAvailableBool = False
        companyDoc = False

        try:
            companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID).companyID
            company = AccountModels.Company.objects.get(pk=companyID)
            if (company.documentsAvailable - company.documentsUsed) > 0:
                companyDoc = True
                documentsAvailableBool = True
        except Exception:
            if (documentsAvailableBool == False) and (account.documentsAvailable > 0):
                account.documentsAvailable -= 1
                account.save()
                documentsAvailableBool = True
        else:
            if (documentsAvailableBool == False) and (account.documentsAvailable > 0):
                account.documentsAvailable -= 1
                account.save()
                documentsAvailableBool = True

        form.is_valid()
        documentPosted = False
        if documentsAvailableBool:
            title = form.cleaned_data['title']

            try:
                documentPosted = True

                documents = models.Documents.objects.get(pk=userID)
                documents.documents += 1
                documents.save()
                documentNonce = str(documents.documents)
                requestID = userID + '_' + documentNonce

                try:
                    if request.FILES['additionalFile'] is not None:
                        thisFileuuid = uploadToAWS(request.FILES['additionalFile'], 'files')
                        file = models.AdditionalFile(docRequestID=requestID,fileuuid=thisFileuuid)
                        file.save()
                        document.additionalFile = True
                        document.save()
                except Exception:
                    pass

                documentID = uuid.uuid4()
                fingerprintCreated = str(uuid.uuid4())
                date = datetime.datetime.today()
                #exampleActionStamp = '2021=12-30:23;59+59[1234567890123456]_0'
                timestampCreated = (str(date.year) + '=' + str(date.month) + '-' + str(date.day) + ':' + str(date.hour) +
                    ';' + str(date.minute) + '+' + str(date.second) + '[' + str(userID) + ']' + '_0')
                createdDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)

                thisFileuuid = uploadToAWS(request.FILES['docFile'], 'documents')
                if companyDoc:
                    document = models.Document(requestID = requestID, createdBy = userID, createdDate = createdDate, lastEditedBy = userID, lastEditedDate = createdDate,
                        title = title, ofType = 'company' , fileuuid = thisFileuuid, fingerprintCreated = fingerprintCreated, draftNum=num)
                    document.associatedWith[email] = 'edit'
                    document.save()

                    company.documentsUsed += 1
                    company.save()

                    documentDraft = models.DocumentDrafts(userIDNonce=draftRequestID, documentKey=requestID)
                    documentDraft.save()

                    companyDocuments = AccountModels.CompanyDocuments.objects.get(pk=companyID)
                    companyDocuments.documents += 1
                    companyDocuments.save()

                    companyRequestID = companyID + '_' + str(companyDocuments.documents)
                    companyDocumentObj = AccountModels.CompanyDocument(companyIDNonce=companyRequestID,companyID=companyID,documentID=requestID,title=title,author=account.username)
                    companyDocumentObj.save()

                    company.latest['9'] = company.latest['8']
                    company.latest['8'] = company.latest['7']
                    company.latest['7'] = company.latest['6']
                    company.latest['6'] = company.latest['5']
                    company.latest['5'] = company.latest['4']
                    company.latest['4'] = company.latest['3']
                    company.latest['3'] = company.latest['2']
                    company.latest['2'] = company.latest['1']
                    company.latest['1'] = company.latest['0']
                    company.latest['0'] = 'newdoc/' + document.title + '[by]' + document.createdBy + '>' + document.createdDate + '<' + document.requestID
                    company.save()

                else:
                    document = models.Document(requestID = requestID, createdBy = userID, createdDate = createdDate, lastEditedBy = userID, lastEditedDate = createdDate,
                        title = title, fileuuid = thisFileuuid, fingerprintCreated = fingerprintCreated, draftNum=num)
                    document.associatedWith[email] = 'edit'
                    document.save()

                    documentDraft = models.DocumentDrafts(userIDNonce=draftRequestID, documentKey=requestID)
                    documentDraft.save()
                return HttpResponseRedirect('/ManageDocument/' + requestID + '/verified/')
            except Exception:
                #templateKeyToTitle = form.cleaned_data['template']
                templateKey = request.POST.get('template')
                #templateKey = templateKeyToTitle[0]
                template = models.Template.objects.get(pk=templateKey)
                documentPosted = True

                documents = models.Documents.objects.get(pk=userID)
                documents.documents += 1
                documents.save()
                documentNonce = str(documents.documents)
                requestID = userID + '_' + documentNonce

                documentID = uuid.uuid4()
                fingerprintCreated = str(uuid.uuid4())
                date = datetime.datetime.today()
                #exampleActionStamp = '2021=12-30:23;59+59[1234567890123456]_0'
                timestampCreated = (str(date.year) + '=' + str(date.month) + '-' + str(date.day) + ':' + str(date.hour) +
                    ';' + str(date.minute) + '+' + str(date.second) + '[' + str(userID) + ']' + '_0')

                createdDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)

                s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
                templateFile = template.fileuuid + '.pdf'
                
                dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/templates/')
                template_file = (dirPath + templateFile)
                s3.download_file('iris1-static',  'static/files/templates/' + templateFile, template_file)

                thisFileuuid = uploadToAWSsite(template_file, 'documents')
                os.remove(template_file)
                if companyDoc:
                    document = models.Document(requestID = requestID, createdBy = userID, createdDate = createdDate, lastEditedBy = userID, lastEditedDate = createdDate,
                        title = title, ofType = 'company', fileuuid = thisFileuuid, fingerprintCreated = fingerprintCreated, draftNum=num,associatedWith=template.associatedWith,signatureData=template.signatureData,createdFromTemplate=True,templateID=templateKey)
                    document.associatedWith[email] = 'edit'
                    document.save()

                    company.documentsUsed += 1
                    company.save()

                    documentDraft = models.DocumentDrafts(userIDNonce=draftRequestID, documentKey=requestID)
                    documentDraft.save()

                    companyDocuments = AccountModels.CompanyDocuments.objects.get(pk=companyID)
                    companyDocuments.documents += 1
                    companyDocuments.save()

                    companyRequestID = companyID + '_' + str(companyDocuments.documents)
                    companyDocumentObj = AccountModels.CompanyDocument(companyIDNonce=companyRequestID,companyID=companyID,documentID=requestID,title=title,author=account.username)
                    companyDocumentObj.save()

                    company.latest['9'] = company.latest['8']
                    company.latest['8'] = company.latest['7']
                    company.latest['7'] = company.latest['6']
                    company.latest['6'] = company.latest['5']
                    company.latest['5'] = company.latest['4']
                    company.latest['4'] = company.latest['3']
                    company.latest['3'] = company.latest['2']
                    company.latest['2'] = company.latest['1']
                    company.latest['1'] = company.latest['0']
                    company.latest['0'] = 'newdoc/' + document.title + '[by]' + document.createdBy + '>' + document.createdDate + '<' + document.requestID
                    company.save()
                else:
                    document = models.Document(requestID = requestID, createdBy = userID, createdDate = createdDate, lastEditedBy = userID, lastEditedDate = createdDate,
                        title = title, fileuuid = thisFileuuid, fingerprintCreated = fingerprintCreated, draftNum=num,associatedWith=template.associatedWith,signatureData=template.signatureData,createdFromTemplate=True,templateID=templateKey)
                    document.associatedWith[email] = 'edit'
                    document.save()

                    documentDraft = models.DocumentDrafts(userIDNonce=draftRequestID, documentKey=requestID)
                    documentDraft.save()
                return HttpResponseRedirect('/ManageDocument/' + requestID + '/verified/' + templateKey + '/')
            finally:
                if not documentPosted:
                    numberOfDocumentDrafts.documents -= 1
                    numberOfDocumentDrafts.save()
                    return HttpResponseRedirect('/UserDashboard/Error/Error1/')
    elif account.subscriptionType == 0:
        return HttpResponseRedirect('/UserDashboard/Settings/ShowPage/Subscription/')
    return HttpResponseRedirect('/UserDashboard/')

def uploadedTemplate(request):

    try:
        userID = request.COOKIES.get('user')
        email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        account = AccountModels.Account.objects.get(pk=email)
    except Exception:
        return HttpResponseRedirect('/')

    templatesAvailableBool = False
    companyTemplate = False
    try:
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID).companyID
        company = AccountModels.Company.objects.get(pk=companyID)
        if (company.templatesAvailable - company.templatesUsed) > 0:
            companyTemplate = True
            templatesAvailableBool = True
    except Exception:
        if (templatesAvailableBool == False) and (account.templatesAvailable > 0):
            account.templatesAvailable -= 1
            account.save()
            templatesAvailableBool = True
    else:
        if (templatesAvailableBool == False) and (account.templatesAvailable > 0):
            account.templatesAvailable -= 1
            account.save()
            templatesAvailableBool = True

    if request.method == 'POST' and templatesAvailableBool:
        num = models.Templates.objects.get(pk=userID)

        form = forms.UploadTemplateForm(request.POST, request.FILES)

        form.is_valid()
        title = form.cleaned_data['title']

        templates = models.Templates.objects.get(pk=userID)
        templates.templates += 1
        num = templates.templates
        templates.save()
        templateNonce = str(templates.templates)
        requestID = userID + '_' + templateNonce

        date = datetime.datetime.today()
        createdDate = str(date.month) + '-' + str(date.day) + '-' + str(date.year)

        thisFileuuid = uploadToAWS(request.FILES['docFile'], 'templates')
        if companyTemplate:
            template = models.Template(requestID = requestID, createdBy = userID,createdDate=createdDate, num = num, title = title, fileuuid = thisFileuuid, ofType = 'company')
            template.save()

            company.templatesUsed += 1
            company.save()

            companyTemplates = AccountModels.CompanyTemplates.objects.get(pk=companyID)
            companyTemplates.templates += 1
            companyTemplates.save()

            companyRequestID = companyID + '_' + str(companyTemplates.templates)
            companyTemplateObj = AccountModels.CompanyTemplate(companyIDNonce=companyRequestID,companyID=companyID,templateID=requestID,title=title,author=account.username)
            companyTemplateObj.save()

            company.latest['9'] = company.latest['8']
            company.latest['8'] = company.latest['7']
            company.latest['7'] = company.latest['6']
            company.latest['6'] = company.latest['5']
            company.latest['5'] = company.latest['4']
            company.latest['4'] = company.latest['3']
            company.latest['3'] = company.latest['2']
            company.latest['2'] = company.latest['1']
            company.latest['1'] = company.latest['0']
            company.latest['0'] = 'temp/' + template.title + '[by]' + template.createdBy + '>' + template.createdDate + '<' + template.requestID
            company.save()
        else:
            template = models.Template(requestID = requestID, createdBy = userID, num = num, title = title, fileuuid = thisFileuuid)
            template.save()
        return HttpResponseRedirect('/ManageDocument/' + requestID + '/EditTemplate/')
    return HttpResponseRedirect('/UserDashboard/Settings/ShowPage/Subscription/')

def handle_uploaded(docFile, filename):
    with open(filename, 'wb') as destination:
        for chunk in docFile.chunks():
            destination.write(chunk)

def ManageDocumentWithTemplate(request, requestID, templateID):
    document = models.Document.objects.get(pk=requestID)
    thisUser = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email

    template = models.Template.objects.get(pk=templateID)
    templateUsers = template.associatedWith
    numUsers = 0
    for each in templateUsers:
        numUsers += 1

    numUsers = str(numUsers)
    if (document.createdBy == thisUser):
        form = forms.DocumentDateAndTime(timeChoices=returnDocumentTimeChoices(userEmail=thisUserEmail),allTimeChoices=returnDocumentAllTimeChoices(),ampmChoices=returnDocumentAMPMChoice())
        return render(request, 'ManageDocumentWithTemplate.html', {'username':thisUser, 'requestID':requestID, 'templateID':templateID, 'numUsers':numUsers, 'form':form, 'file':document.fileuuid})
    else:
        return HttpResponseRedirect('/')

def ManageDocument(request, requestID):
    thisUserID = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email

    additionalFile = ''
    try:
        document = models.Document.objects.get(pk=requestID)
        permission = document.associatedWith[thisUserEmail]
        additionalFile = document.additionalFile
    except Exception:
        if additionalFile:
            thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
            return render(request, 'PdfViewPlusFile.html', {'requestID':requestID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
        else:
            return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})

    if document.isComplete == True:
        if (permission == 'edit'):
            return render(request, 'PdfViewAndAudit.html', {'requestID':requestID, 'file':document.fileuuid})
        else:
            if additionalFile:
                thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
                return render(request, 'PdfViewPlusFile.html', {'requestID':requestID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
            else:
                return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})
    
    if document.isSent == True:
        if (permission == 'sign'):
            document = models.DocumentSigningBoxes.objects.get(pk=requestID+thisUserID)
            if additionalFile:
                thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
                return render(request, 'PdfSignPlusFile.html', {'requestID':requestID, 'userID':thisUserID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
            else:
                return render(request, 'PdfSign.html', {'requestID':requestID, 'userID':thisUserID, 'file':document.fileuuid})
        else:
            if additionalFile:
                thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
                return render(request, 'PdfViewPlusFile.html', {'requestID':requestID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
            else:
                return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})

    if (permission == 'edit'):
        form = forms.DocumentDateAndTime(timeChoices=returnDocumentTimeChoices(userEmail=thisUserEmail),allTimeChoices=returnDocumentAllTimeChoices(),ampmChoices=returnDocumentAMPMChoice())
        return render(request, 'ManageDocument.html', {'username':thisUserID, 'requestID':requestID, 'form':form, 'file':document.fileuuid})
    elif (permission == 'sign'):
        document = models.DocumentSigningBoxes.objects.get(pk=requestID+thisUserID)
        if additionalFile:
            thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
            return render(request, 'PdfSignPlusFile.html', {'requestID':requestID, 'userID':thisUserID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
        else:
            return render(request, 'PdfSign.html', {'requestID':requestID, 'userID':thisUserID, 'file':document.fileuuid})
    elif (permission == 'view'):
        if additionalFile:
            thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
            return render(request, 'PdfViewPlusFile.html', {'requestID':requestID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
        else:
            return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})
    elif (permission == 'x'):
        if additionalFile:
            thisAdditionalFile = models.AdditionalFile.objects.get(pk=requestID)
            return render(request, 'PdfViewPlusFile.html', {'requestID':requestID, 'file':document.fileuuid, 'additionalFile':thisAdditionalFile.fileuuid})
        else:
            return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})
    else:
        return HttpResponseRedirect('/')

def returnDocumentTimeChoices(userEmail):
    account = AccountModels.Account.objects.get(pk=userEmail)
    userIP = account.currentIP
    #userIP = '19.5.10.1'

    #database = IP2Location.IP2Location("home/ubuntu/django/IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-SAMPLE.BIN")
    #userLocationInfo = database.get_all(userIP)
    #from geopy.geocoders import Nominatim
    #geolocator = Nominatim(user_agent="app")
    #location = geolocator.geocode(userIP)
    #from tzwhere import tzwhere
    #tzwhere = tzwhere.tzwhere()
    #tz = tzwhere.tzNameAt(float(location.latitude), float(location.longitude))

    access_token = '5e07ecfdd4ebf6'
    handler = ipinfo.getHandler(access_token)
    details = handler.getDetails(userIP)
    now_utc = datetime.datetime.now(timezone('UTC'))
    now_local = now_utc.astimezone(timezone(details.timezone))


    if now_local.minute < 50:
        firstTimeChoice_firstHour = now_local.hour + 1
    else:
        firstTimeChoice_firstHour = now_local.hour + 2

    if firstTimeChoice_firstHour > 12:
        if firstTimeChoice_firstHour != 0:
            firstTimeChoice_firstHour = firstTimeChoice_firstHour - 12
        else:
            firstTimeChoice_firstHour = 1

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

def returnDocumentAllTimeChoices():
    timeChoices = []
    count = 1

    while count <= 12:
        newTuple = (count, str(count))
        timeChoices.append(newTuple)
        count += 1

    timeChoices = tuple(timeChoices)
    return timeChoices

def returnDocumentAMPMChoice():
    timeChoices = []
    newTuple = (1, 'AM')
    timeChoices.append(newTuple)
    newTuple = (2, 'PM')
    timeChoices.append(newTuple)

    timeChoices = tuple(timeChoices)
    return timeChoices

def ViewAudit(request, requestID):
    document = models.Document.objects.get(pk=requestID)
    thisUser = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
    permission = document.associatedWith[thisUserEmail]
    if document.isComplete == True:
        if (permission == 'edit'):
            return render(request, 'ViewAudit.html', {'requestID':requestID, 'file':document.audituuid})
    return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})

# Handle download in browser from S3
def DownloadAudit(request, requestID):
    path = 'documents/' + requestID + '_audit.pdf'
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

# Handle download in browser from S3
def DownloadDocument(request, requestID):
    path = 'documents/' + requestID + '.pdf'
    path_x = 'documents/' + requestID + '_x.pdf'
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    file_path_x = os.path.join(settings.MEDIA_ROOT, path_x)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    elif os.path.exists(file_path_x):
        with open(file_path_x, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

# Handle download in browser from S3
def DownloadAdditional(request, requestID):
    file = models.AdditionalFile.objects.get(pk=requestID)
    path = 'files/' + requestID + '.' + file.ext
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

def ManageTemplate(request, requestID):
    thisUser = request.COOKIES.get('user')
    template = models.Template.objects.get(pk=requestID)
    if len(thisUser) > 1:
        if template.isFinished:
            return render(request, 'ManageTemplateFinished.html', {'username':thisUser, 'requestID':requestID, 'file':template.fileuuid})
        else:
            return render(request, 'ManageTemplate.html', {'username':thisUser, 'requestID':requestID, 'file':template.fileuuid})
    else:
        return HttpResponseRedirect('/')

def PdfWithTemplateEditorNotify(request, requestID, usersAdded):
    document = models.Document.objects.get(pk=requestID)
    document.notify = True
    document.save()
    return PdfWithTemplateEditor(request, requestID, usersAdded)

def PdfWithTemplateEditor(request, requestID, templateID, usersAdded):
    document = models.Document.objects.get(pk=requestID)
    template = models.Template.objects.get(pk=templateID)
    num = document.draftNum
    sentFromUserID = request.COOKIES.get('user')

    try:
        rewriteDrafts(num, sentFromUserID)
    except Exception:
        pass

    numberOfDocumentsSentObj = models.NumberOfDocumentsSent.objects.get(pk=sentFromUserID)
    numberOfDocumentsSentObj.documents += 1
    numberOfDocumentsSentObj.save()

    keyToKey = sentFromUserID + '_' + str(numberOfDocumentsSentObj.documents)
    documentSent = models.DocumentsSent(userIDNonce=keyToKey, documentKey=requestID)
    documentSent.save()

    users = re.split(r'>', usersAdded)
    try:
        users.remove('')
    except ValueError:
        pass
    #databaseAssociationsJSON = document.associatedWith
    #databaseSignaturesJSON = document.signatureData
    #newAssociationsJSON = {}
    #newSignaturesJSON = {}
    emailsScanned = []
    userOccurences = {}
    count = 1
    for user in users:
        userSplit1 = re.split(r';', user) # [name;email-permission]
        thisUsername = userSplit1[0]
        #userSplit2 = re.split(r'-', userSplit1[1])
        thisEmail = userSplit1[1]
        #thisPermission = userSplit2[1]
        try:
            if emailsScanned.index(thisEmail) >= 0:
                userOccurences[thisEmail] += 1

                #newAssociationsJSON[thisUsername] = databaseAssociationsJSON['user' + str(count)]
                #newSignaturesJSON[thisEmail] = databaseSignaturesJSON['user' + str(count) + '@email.com']

                document.signatureData[thisEmail + str(userOccurences[thisEmail])] = document.signatureData['user' + str(count) + '@email.com' + str(userOccurences[thisEmail])]
                del document.associatedWith['user' + str(count) + '@email.com']
                document.save()

        except ValueError:
            emailsScanned.append(thisEmail)
            userOccurences[thisEmail] = 1
            newAcc = False
            try:
                userAcc = AccountModels.Account.objects.get(pk=thisEmail)
                if not userAcc.verified:
                    newAcc = True
            except Exception:
                newAcc = True
                accounts = AccountModels.Accounts.objects.get(pk=1)
                accounts.users += 1
                accounts.save()

                userID = accounts.users

                userID = str(userID)
                lengthAccountNumber = len(userID)
                if (lengthAccountNumber < 16):
                    zeroes = 16 - lengthAccountNumber
                    string = ''
                    while zeroes != 0:
                        string = string + '0'
                        zeroes -= 1
                    userID = string + userID

                account = AccountModels.Account(userID = userID, username = userID, email = thisEmail)
                account.save()
                newAccountLookupID = AccountModels.AccountLookupByID(userID = userID, email = thisEmail)
                newAccountLookupID.save()

                initializeDocumentCount = models.NumberOfDocumentsSent(userID = userID, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.NumberOfDocumentsReceived(userID =  userID, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.NumberOfDocumentDrafts(userID =  userID, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.NumberOfDocumentsCompleted(userID =  userID, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.Documents(userID =  userID, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.Templates(userID = userID, templates = 0)
                initializeDocumentCount.save()

                userAcc = AccountModels.Account.objects.get(pk=thisEmail)
                userAcc.newReceived = True
                userAcc.save()

            #newAssociationsJSON[thisUsername] = databaseAssociationsJSON['user' + str(count)]
            #newSignaturesJSON[thisEmail] = databaseSignaturesJSON['user' + str(count) + '@email.com']

            document.associatedWith[thisEmail] = document.associatedWith['user' + str(count) + '@email.com']
            document.signatureData[thisEmail + '1'] = document.signatureData['user' + str(count) + '@email.com' + '1']
            del document.associatedWith['user' + str(count) + '@email.com']
            del document.signatureData['user' + str(count) + '@email.com' + '1']
            document.signed[thisEmail] = False
            document.save()

            sentFromUser = AccountModels.AccountLookupByID.objects.get(pk=sentFromUserID)
            sentFromUserEmail = sentFromUser.email
            sentFromUser = AccountModels.Account.objects.get(pk=sentFromUserEmail)
            sentFromUsername = sentFromUser.username
            sentFromUser = sentFromUsername + ' at email address ' + sentFromUserEmail

            sentToUsername = userAcc.username
            sentToUserID = userAcc.userID

            numberOfDocumentsReceivedObj = models.NumberOfDocumentsReceived.objects.get(pk=sentToUserID)
            numberOfDocumentsReceivedObj.documents += 1
            numberOfDocumentsReceivedObj.save()

            keyToKey = sentToUserID + '_' + str(numberOfDocumentsReceivedObj.documents)
            documentReceived = models.DocumentsReceived(userIDNonce=keyToKey, documentKey=requestID)
            documentReceived.save()

            thisPermission = document.associatedWith[thisEmail]

            writeDocumentSigningBoxes(requestID=requestID,userID=sentToUserID)

            if thisPermission == 'sign':
                subject = sentFromUsername + ' has requested that you sign a document'
                text_content = sentFromUser + ' has requested that you sign a document at IrisDocuments.com'
                if newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
            elif thisPermission == 'edit':
                subject = sentFromUsername + ' has requested that you edit a document'
                text_content = sentFromUser + ' has requested that you edit a document at IrisDocuments.com'
                if newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
            elif thisPermission == 'view':
                subject = sentFromUsername + ' has requested that you view a document'
                text_content = sentFromUser + ' has requested that you view a document at IrisDocuments.com'
                if newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})


            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [thisEmail], connection=thisConnection)
                email.attach_alternative(html_content, 'text/html')
                email.send()

        count += 1

    return HttpResponseRedirect('/UserDashboard/Update/Update1/')

def PdfEditorNotify(request, requestID, usersAdded):
    document = models.Document.objects.get(pk=requestID)
    document.notify = True
    document.save()
    return PdfEditor(request, requestID, usersAdded)

def PdfEditor(request, requestID, usersAdded):
    document = models.Document.objects.get(pk=requestID)
    thisUser = request.COOKIES.get('user')
    try:
        company = AccountModels.CompanyLookupByAccountID.objects.get(pk=thisUser)
    except:
        pass

    form = forms.AddUserToFile()

    users = re.split(r'>', usersAdded)
    users.pop()
    emailsView = []
    emailsSign = []
    namesSign = []
    emailsEdit = []
    usersLength = len(users)
    for user in users:
        userSplit1 = re.split(r';', user) # [name;email-permission]
        thisUsername = userSplit1[0]
        userSplit2 = re.split(r'-', userSplit1[1])
        thisEmail = userSplit2[0]
        thisPermission = userSplit2[1]

        if (thisPermission == 'view'):
            emailsView.append(thisEmail)
        elif (thisPermission == 'sign'):
            emailsSign.append(thisEmail)
            namesSign.append(thisUsername)
        elif (thisPermission == 'edit'):
            emailsEdit.append(thisEmail)

    userEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
    user = AccountModels.Account.objects.get(pk=userEmail)
    personalBrand = user.addBrand
    companyBrand = False
    try:
        companyBrand = company.addBrand
    except:
        pass
    
    if companyBrand:
        brandID = company.companyID
        return render(request, 'PdfEditorWithCompanyBrandv2.html', {'username':thisUser, 'requestID':requestID, 'form':form, 'brandID':brandID,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':document.fileuuid})
    elif personalBrand:
        brandID = user.userID
        return render(request, 'PdfEditorWithBrandv2.html', {'username':thisUser, 'requestID':requestID, 'form':form, 'brandID':brandID,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':document.fileuuid})
    else:
        return render(request, 'PdfEditor.html', {'username':thisUser, 'requestID':requestID, 'form':form,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':document.fileuuid})

def PdfEditorLaterNotify(request, requestID, usersAdded, sendDate):
    document = models.Document.objects.get(pk=requestID)
    document.notify = True
    document.save()
    return PdfEditorLater(request, requestID, usersAdded, sendDate)

def PdfEditorLater(request, requestID, usersAdded, sendDate):
    document = models.Document.objects.get(pk=requestID)
    thisUser = request.COOKIES.get('user')
    try:
        company = AccountModels.CompanyLookupByAccountID.objects.get(pk=thisUser)
    except:
        pass

    form = forms.AddUserToFile()

    users = re.split(r'>', usersAdded)
    users.pop()
    emailsView = []
    emailsSign = []
    namesSign = []
    emailsEdit = []
    usersLength = len(users)
    for user in users:
        userSplit1 = re.split(r';', user) # [name;email-permission]
        thisUsername = userSplit1[0]
        userSplit2 = re.split(r'-', userSplit1[1])
        thisEmail = userSplit2[0]
        thisPermission = userSplit2[1]

        if (thisPermission == 'view'):
            emailsView.append(thisEmail)
        elif (thisPermission == 'sign'):
            emailsSign.append(thisEmail)
            namesSign.append(thisUsername)
        elif (thisPermission == 'edit'):
            emailsEdit.append(thisEmail)

    userEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
    user = AccountModels.Account.objects.get(pk=userEmail)
    personalBrand = user.addBrand
    companyBrand = False
    try:
        companyBrand = company.addBrand
    except:
        pass

    account = AccountModels.Account.objects.get(pk=userEmail)
    userIP = account.currentIP
    #database = IP2Location.IP2Location("home/ubuntu/django/IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-SAMPLE.BIN")
    #userLocationInfo = database.get_all(userIP)
    access_token = '5e07ecfdd4ebf6'
    handler = ipinfo.getHandler(access_token)
    details = handler.getDetails(userIP)
    now_utc = datetime.datetime.now(timezone('UTC'))
    now_local = now_utc.astimezone(timezone(details.timezone))
    
    if now_local.day == now_utc.day:
        timeDiff = now_utc.hour - now_local.hour
    else:
        if now_local.hour > 12:
            timeDiff = now_utc.hour + (24 - now_local.hour)
        else:
            timeDiff = -(now_local.hour + (24 - now_utc.hour))

    todayDate = datetime.datetime.now()
    date = sendDate.split('-')
    if int(date[4]) == 1:
        if int(date[3]) == 12:
            thisHour = 0
        else:
            thisHour = int(date[3])
    else:
        if int(date[3]) == 12:
            thisHour = int(date[3])
        else:
            thisHour = int(date[3]) + 12
    
    thisHour += timeDiff
    thisDay = int(date[2])
    thisMonth = int(date[1])
    thisYear = int(date[0])
    if thisHour >= 24:
        thisDay += 1 
        # Now check if day is too high for month in date[1]
        # Then check if month is too high for year in date[0]
        if thisDay >= 28: # Months ending with 28 days
            if thisMonth == 2:
                if (thisYear % 4) != 0:
                    thisDay = 1
                    thisMonth = 3
        elif thisDay >= 29: # Months ending with 29 days
            if thisMonth == 2:
                if (thisYear % 4) == 0:
                    thisDay = 1
                    thisMonth = 3
        elif thisDay >= 30: # Months ending with 30 days
            if thisMonth == 4:
                thisDay = 1
                thisMonth = 5
            elif thisMonth == 6:
                thisDay = 1
                thisMonth = 7
            elif thisMonth == 9:
                thisDay = 1
                thisMonth = 10
            elif thisMonth == 11:
                thisDay = 1
                thisMonth = 12
        elif thisDay >= 31: # Months ending with 31 days
            if thisMonth == 1:
                thisDay = 1
                thisMonth = 2
            elif thisMonth == 3:
                thisDay = 1
                thisMonth = 4
            elif thisMonth == 5:
                thisDay = 1
                thisMonth = 6
            elif thisMonth == 7:
                thisDay = 1
                thisMonth = 8
            elif thisMonth == 8:
                thisDay = 1
                thisMonth = 9
            elif thisMonth == 10:
                thisDay = 1
                thisMonth = 11
            elif thisMonth == 12:
                thisDay = 1
                thisMonth = 1
                thisYear += 1
        thisHour -= 24
    alertDate = str(thisYear) + '-' + str(thisMonth) + '-' + str(thisDay)
    documentAlert = models.DocumentAlert(userIDdocumentRequestID=thisUser+requestID,date=alertDate,hour=thisHour)
    documentAlert.save()
    if companyBrand:
        brandID = company.companyID
        return render(request, 'PdfEditorLaterWithCompanyBrandv2.html', {'username':thisUser, 'requestID':requestID, 'form':form, 'brandID':brandID,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':document.fileuuid})
    elif personalBrand:
        brandID = user.userID
        return render(request, 'PdfEditorLaterWithBrandv2.html', {'username':thisUser, 'requestID':requestID, 'form':form, 'brandID':brandID,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':document.fileuuid})
    else:
        return render(request, 'PdfEditorLater.html', {'username':thisUser, 'requestID':requestID, 'form':form,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':document.fileuuid})

def PdfTemplateEditor(request, requestID, usersAdded):
    template = models.Template.objects.get(pk=requestID)
    thisUser = request.COOKIES.get('user')
    try:
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=thisUser).companyID
        company = AccountModels.Company.objects.get(pk=companyID)
    except:
        pass

    form = forms.AddUserToFile()

    users = re.split(r'>', usersAdded)
    users.pop()
    emailsView = []
    emailsSign = []
    namesSign = []
    emailsEdit = []
    usersLength = len(users)
    for user in users:
        userSplit1 = re.split(r';', user) # [name;email-permission]
        thisUsername = userSplit1[0]
        userSplit2 = re.split(r'-', userSplit1[1])
        thisEmail = userSplit2[0]
        thisPermission = userSplit2[1]

        if (thisPermission == 'view'):
            emailsView.append(thisEmail)
        elif (thisPermission == 'sign'):
            emailsSign.append(thisEmail)
            namesSign.append(thisUsername)
        elif (thisPermission == 'edit'):
            emailsEdit.append(thisEmail)

    userEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUser).email
    user = AccountModels.Account.objects.get(pk=userEmail)
    personalBrand = user.addBrand
    companyBrand = False
    try:
        companyBrand = company.addBrand
    except:
        pass
    
    if companyBrand:
        brandID = company.companyID
        return render(request, 'PdfTemplateEditorWithBrand.html', {'username':thisUser, 'requestID':requestID, 'form':form, 'brandID':brandID,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':template.fileuuid, 'brandType':'c'})
    elif personalBrand:
        brandID = user.userID
        return render(request, 'PdfTemplateEditorWithBrand.html', {'username':thisUser, 'requestID':requestID, 'form':form, 'brandID':brandID,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':template.fileuuid, 'brandType':'p'})
    else:
        return render(request, 'PdfTemplateEditor.html', {'username':thisUser, 'requestID':requestID, 'form':form,\
            'emailsView':emailsView, 'emailsSign':emailsSign, 'namesSign':namesSign, 'emailsEdit':emailsEdit, 'file':template.fileuuid})


def CreatedDocument(request, title):
    documents = models.Documents.objects.get(pk=1)
    documents.documents += 1
    documents.save()

    documentNumber = str(documentNumber)
    thisUser = request.COOKIES.get('user')
    requestID = thisUser + documentNumber
    documentID = uuid.uuid4()
    fingerprintCreated = uuid.uuid4()
    date = datetime.datetime.today()
    #exampleActionStamp = '2021=12-30:23;59+59[1234567890123456]_0'
    timestampCreated = (date.year + '=' + date.month + '-' + date.day + ':' + date.hour + ';' + date.minute 
        + '+' + date.second + '[' + thisUser + ']' + '_0')

    document = models.Document(requestID = requestID, documentID = documentID, fingerprintCreated = fingerprintCreated,
        createdBy = thisUser, title = title, dateCreatedBy = timestampCreated)
    document.save()

    ManageDocument(request, requestID)

def DeleteDraft(request, requestID):
    userID = request.COOKIES.get('user')
    document = models.Document.objects.get(pk=requestID)

    if document.ofType == 'user':
        email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        account = AccountModels.Account.objects.get(pk=email)
        account.documentsAvailable += 1
        account.save()

    rewriteDrafts(document.draftNum, userID)
    documentFile = document.fileuuid + '.pdf'
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)
    document.delete()

    return HttpResponseRedirect('/UserDashboard/')

def DeleteTemplate(request, requestID):
    userID = request.COOKIES.get('user')
    template = models.Template.objects.get(pk=requestID)

    if template.ofType == 'user':
        email = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        account = AccountModels.Account.objects.get(pk=email)
        account.templatesAvailable += 1
        account.save()

    rewriteTemplates(template.num, userID)
    documentFile = template.fileuuid + '.pdf'
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    s3.delete_object(Bucket='iris1-static', Key='static/files/templates/' + documentFile)
    template.delete()

    return HttpResponseRedirect('/UserDashboard/')

def rewriteDrafts(num, userID):
    numberOfDocumentDraftsObj = models.NumberOfDocumentDrafts.objects.get(pk=userID)
    numberOfDocumentDrafts = numberOfDocumentDraftsObj.documents

    count = 1
    while (num + count <= numberOfDocumentDrafts):
        draftRequestID = userID + '_' + str(num + count - 1)
        nextDraftRequestID = userID + '_' + str(num + count)

        documentDraft = models.DocumentDrafts.objects.get(pk=draftRequestID)
        nextDocumentDraft = models.DocumentDrafts.objects.get(pk=nextDraftRequestID)
        documentDraft.documentKey = nextDocumentDraft.documentKey
        documentDraft.save()

        count += 1
    else:
        draftRequestID = userID + '_' + str(numberOfDocumentDrafts)
        documentDraft = models.DocumentDrafts.objects.get(pk=draftRequestID)
        documentDraft.delete()

        numberOfDocumentDraftsObj.documents -= 1
        numberOfDocumentDraftsObj.save()

def rewriteTemplates(num, userID):
    numberOfTemplatesObj = models.Templates.objects.get(pk=userID)
    numberOfTemplates = numberOfTemplatesObj.templates

    count = 1
    while (num + count <= numberOfTemplates):
        requestID = userID + '_' + str(num + count - 1)
        nextRequestID = userID + '_' + str(num + count)

        template = models.Template.objects.get(pk=requestID)
        nextTemplate = models.Template.objects.get(pk=nextRequestID)
        template.requestID = nextTemplate.requestID
        template.save()

        count += 1
    else:
        requestID = userID + '_' + str(num + 1)
        template = models.Template.objects.get(pk=requestID)
        template.delete()

        numberOfTemplatesObj.templates -= 1
        numberOfTemplatesObj.save()

# Handles userData plus textData or brandData
def addUsersToDocumentWithText(request, requestID, userData, textData):
    textAdded = True
    texts = re.split(r'\$', textData)
    if texts[0] == textData:
        texts = re.split(re.escape('*'), textData)
        textAdded = False

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    document = models.Document.objects.get(pk=requestID)
    documentFile = document.fileuuid + '.pdf'

    pdf_file = (dirPath + documentFile)
    pdf_file_x = (dirPath + document.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)

    if textAdded:
        textArray = []
        positionsArray = []
        for text in texts:
            trySplit = re.split(r'#%%', text)
            if len(trySplit) > 1:
                text = ''
                for each in trySplit:
                    text = text + '/' + each
            if len(text) > 1:
                positions = []
                userSplit1 = re.split(r'=', text)
                thisText = userSplit1[0]
                userSplit2 = re.split(r'-', userSplit1[1])
                positions.append(userSplit2[0])
                userSplit3 = re.split(r'&', userSplit2[1])
                positions.append(userSplit3[0])
                userSplit4 = re.split(r'<', userSplit3[1])
                positions.append(userSplit4[0])
                userSplit5 = re.split(r';', userSplit4[1])
                positions.append(userSplit5[0])
                userSplit6 = re.split(r'{', userSplit5[1])
                positions.append(userSplit6[0])
                textSize = userSplit6[1]

                textArray.append(thisText)
                positionsArray.append(positions)

        array = 0
        firstRun = True
        condition = 1
        for text in textArray:
            if firstRun:
                firstRun = False
                if text[0] == '$':
                    text = text[1:] 
                positions = positionsArray[array]
                array += 1
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                can.setFont('Helvetica', int(textSize))
                can.drawString(leftBottomX, (height - leftBottomY), text)
                can.save()
 
                #move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()

                os.remove(pdf_file)
            else:
                if text[0] == '$':
                    text = text[1:] 
                positions = positionsArray[array]
                array += 1

                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                can.setFont('Helvetica', int(textSize))
                can.drawString(leftBottomX, (height - leftBottomY), text)
                can.save()
 
                #move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)
    else:
        # Handle data if it is a brand
        # positions are same
        # Change html file to send userID or companyID with data from hidden div tag at the top of the page
        # if the PdfEditorWithCompanyBrand.html is loaded, send an extra identifier denoting this is a companyID
        # if the PdfEditorWithBrand.html is loaded, send an extra identifier denoting this is a userID
        brandArray = []
        positionsArray = []
        for text in texts:
            if len(text) > 1:
                positions = []
                userSplit1 = re.split(r'=', text)
                thisID = userSplit1[0]
                userSplit2 = re.split(r'-', userSplit1[1])
                positions.append(userSplit2[0])
                userSplit3 = re.split(r'&', userSplit2[1])
                positions.append(userSplit3[0])
                userSplit4 = re.split(r'<', userSplit3[1])
                positions.append(userSplit4[0])
                userSplit5 = re.split(r';', userSplit4[1])
                positions.append(userSplit5[0])
                userSplit6 = re.split(r'{', userSplit5[1])
                positions.append(userSplit6[0])
                brandType = userSplit6[1]

                brandArray.append(thisID)
                positionsArray.append(positions)

        dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')

        if brandType == 'p':
            dirPathBrand = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/files/brands/users/')
        else:
            dirPathBrand = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/files/brands/companys/')

        thisUserID = request.COOKIES.get('user')
        thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
        user = AccountModels.Account.objects.get(pk=thisUserEmail)
        array = 0
        firstRun = True
        condition = 1
        for text in brandArray:
            if firstRun:
                firstRun = False
                if text[0] == '*':
                    text = text[1:] 
                positions = positionsArray[array]
                brandFile = user.brandFileuuid + '.' + user.brandFileType
                brand = dirPathBrand + brandFile
        
                if brandType == 'p':
                    s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
                else:
                    s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)

                array += 1
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                # Move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()

                os.remove(pdf_file)
            else:
                if text[0] == '*':
                    text = text[1:] 
                positions = positionsArray[array]
                brandFile = user.brandFileuuid + '.' + user.brandFileType
                brand = dirPathBrand + brandFile
        
                if brandType == 'p':
                    s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
                else:
                    s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)
        
                array += 1
            
                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2

                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                # Move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)

    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)
    if condition == 1:
        thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    elif condition == 2:
        thisDocumentuuid = uploadToAWSsite(pdf_file, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass
        
    return addUsersToDocument(request, requestID, userData)

# Handles userData plus textData plus brandData
def addUsersToDocumentWithTextAndBrand(request, requestID, userData, textData, brandData):
    texts = re.split(r'\$', textData)
    brands = re.split(re.escape('*'), brandData)

    textArray = []
    positionsArray = []
    for text in texts:
        trySplit = re.split(r'#%%', text)
        if len(trySplit) > 1:
            text = ''
            for each in trySplit:
                text = text + '/' + each
        if len(text) > 1:
            positions = []
            userSplit1 = re.split(r'=', text)
            thisText = userSplit1[0]
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            userSplit6 = re.split(r'{', userSplit5[1])
            positions.append(userSplit6[0])
            textSize = userSplit6[1]

            textArray.append(thisText)
            positionsArray.append(positions)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    document = models.Document.objects.get(pk=requestID)
    documentFile = document.fileuuid + '.pdf'

    pdf_file = (dirPath + documentFile)
    pdf_file_x = (dirPath + document.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)

    array = 0
    firstRun = True
    condition = 1
    for text in textArray:
        if firstRun:
            firstRun = False
            if text[0] == '$':
                text = text[1:] 
            positions = positionsArray[array]
            array += 1
            
            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            can.setFont('Helvetica', int(textSize))
            can.drawString(leftBottomX, (height - leftBottomY), text)
            can.save()
 
            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)

            new_pdf = PdfReader(packet)

            output = PdfWriter()

            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()

            os.remove(pdf_file)
        else:
            if text[0] == '$':
                text = text[1:] 
            positions = positionsArray[array]
            array += 1
            
            try:
                existing_pdf = PdfReader(open(pdf_file, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 1
            except Exception:
                existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 2

            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            can.setFont('Helvetica', int(textSize))
            can.drawString(leftBottomX, (height - leftBottomY), text)
            can.save()
 
            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)

            new_pdf = PdfReader(packet)

            output = PdfWriter()

            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            if condition == 1:
                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file)
            elif condition == 2:
                outputStream = open(pdf_file, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file_x)

    brandArray = []
    positionsArray = []
    for text in brands:
        if len(text) > 1:
            positions = []
            userSplit1 = re.split(r'=', text)
            thisID = userSplit1[0]
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            userSplit6 = re.split(r'{', userSplit5[1])
            positions.append(userSplit6[0])
            brandType = userSplit6[1]

            brandArray.append(thisID)
            positionsArray.append(positions)

    if brandType == 'p':
        dirPathBrand = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/brands/users/')
    else:
        dirPathBrand = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/brands/companys/')

    array = 0
    thisUserID = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
    user = AccountModels.Account.objects.get(pk=thisUserEmail)
    for text in brandArray:
        if text[0] == '*':
            text = text[1:] 
        positions = positionsArray[array]
        brandFile = user.brandFileuuid + '.' + user.brandFileType
        brand = dirPathBrand + brandFile
        
        if brandType == 'p':
            s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
        else:
            s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)
        array += 1

        try:
            existing_pdf = PdfReader(open(pdf_file, "rb"))
            width = float(existing_pdf.pages[0].mediabox.width)
            height = float(existing_pdf.pages[0].mediabox.height)
            condition = 1
        except Exception:
            existing_pdf = PdfReader(open(pdf_file_x, "rb"))
            width = float(existing_pdf.pages[0].mediabox.width)
            height = float(existing_pdf.pages[0].mediabox.height)
            condition = 2

        packet = io.BytesIO()
        #packet.truncate(0)
        can = canvas.Canvas(packet)
        can.setPageSize((width,height))
        leftTopX = int(round( float(positions[0]) * width )) 
        leftTopY = int(round( float(positions[1]) * height ))
        rightBottomX = int(round( float(positions[2]) * width ))
        rightBottomY = int(round( float(positions[3]) * height ))
        leftBottomX = leftTopX
        leftBottomY = rightBottomY
        total_width = rightBottomX - leftTopX
        total_height = rightBottomY - leftTopY
        can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
        can.save()
 
        # Move to the beginning of the StringIO buffer
        #packet.truncate(0)
        packet.seek(0)

        new_pdf = PdfReader(packet)

        output = PdfWriter()
                
        pageNum = int(positions[4]) - 1
        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            if (i == pageNum):
                page.merge_page(new_pdf.pages[0])
            output.add_page(page)

        if condition == 1:
            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()
            os.remove(pdf_file)
        elif condition == 2:
            outputStream = open(pdf_file, "wb")
            output.write(outputStream)
            outputStream.close()
            os.remove(pdf_file_x)
        
    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)
    if condition == 1:
        thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    elif condition == 2:
        thisDocumentuuid = uploadToAWSsite(pdf_file, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass

    return addUsersToDocument(request, requestID, userData)

def addUsersToDocument(request, requestID, userData):
    document = models.Document.objects.get(pk=requestID)
    num = document.draftNum
    sentFromUserID = request.COOKIES.get('user')

    try:
        rewriteDrafts(num, sentFromUserID)
    except Exception:
        pass


    numberOfDocumentsSentObj = models.NumberOfDocumentsSent.objects.get(pk=sentFromUserID)
    numberOfDocumentsSentObj.documents += 1
    numberOfDocumentsSentObj.save()

    if numberOfDocumentsSentObj.documents > 26:
        removeSentFromMemory(userID)

    keyToKey = sentFromUserID + '_' + str(numberOfDocumentsSentObj.documents)
    documentSent = models.DocumentsSent(userIDNonce=keyToKey, documentKey=requestID)
    documentSent.save()

    users = re.split(r'>', userData)
    emailsScanned = []
    userOccurences = {}
    for user in users:
        if len(user) < 1:
            break
        positions = []
        userSplit1 = re.split(r'=', user)
        thisEmail = userSplit1[0]
        if userSplit1[1] == 'view':
            thisPermission = 'view'
        elif userSplit1[1] == 'edit':
            thisPermission = 'edit'
        else:
            thisPermission = 'sign'
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            positions.append(userSplit5[1])

        newAcc = False
        try:
            userAcc = AccountModels.Account.objects.get(pk=thisEmail)
            userID = userAcc.userID
            if not userAcc.verified:
                newAcc = True
        except Exception:
            newAcc = True
            accounts = AccountModels.Accounts.objects.get(pk=1)
            accounts.users += 1
            accounts.save()

            userID = accounts.users

            userID = str(userID)
            lengthAccountNumber = len(userID)
            if (lengthAccountNumber < 16):
                zeroes = 16 - lengthAccountNumber
                string = ''
                while zeroes != 0:
                    string = string + '0'
                    zeroes -= 1
                userID = string + userID

            account = AccountModels.Account(userID = userID, username = userID, email = thisEmail, documentsAvailable = 10)
            account.save()
            newAccountLookupID = AccountModels.AccountLookupByID(userID = userID, email = thisEmail)
            newAccountLookupID.save()

            initializeDocumentCount = models.NumberOfDocumentsSent(userID = userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.NumberOfDocumentsReceived(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.NumberOfDocumentDrafts(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.NumberOfDocumentsCompleted(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.Documents(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.Templates(userID = userID, templates = 0)
            initializeDocumentCount.save()

        try:
            if emailsScanned.index(thisEmail) >= 0:
                userOccurences[thisEmail] += 1

                #databaseJSON[thisEmail + str(userOccurences[thisEmail])] = positions
                document.signatureData[thisEmail + str(userOccurences[thisEmail])] = positions
                document.save()

        except ValueError:
            emailsScanned.append(thisEmail)
            userOccurences[thisEmail] = 1
            thisAcc = AccountModels.Account.objects.get(pk=thisEmail)
            thisAcc.newReceived = True
            thisAcc.save()

            #documentObj = models.Document.objects.get(pk=requestID)
            #documentObjAssociatedUsers = (documentObj.associatedWith).split('}')
            #documentObj.associatedWith = documentObjAssociatedUsers[0] + ',' + userID + ':' + thisPermission +  '}'
            #documentObj.save()

            numberOfDocumentsReceivedObj = models.NumberOfDocumentsReceived.objects.get(pk=userID)
            numberOfDocumentsReceivedObj.documents += 1
            numberOfDocumentsReceivedObj.save()

            keyToKey = userID + '_' + str(numberOfDocumentsReceivedObj.documents)
            documentReceived = models.DocumentsReceived(userIDNonce=keyToKey, documentKey=requestID)
            documentReceived.save()
            

            #databaseJSON = json.loads(document.associatedWith)
            #databaseJSON[thisEmail] = thisPermission
            document.associatedWith[thisEmail] = thisPermission
            #databaseJSON = json.loads(document.signatureData)
            #databaseJSON[thisEmail + '1'] = positions
            document.signatureData[thisEmail + '1'] = positions
            document.signed[thisEmail] = False
            document.save()

            sentFromUser = AccountModels.AccountLookupByID.objects.get(pk=sentFromUserID)
            sentFromUserEmail = sentFromUser.email
            sentFromUser = AccountModels.Account.objects.get(pk=sentFromUserEmail)
            sentFromUsername = sentFromUser.username
            sentFromUser = sentFromUsername + ' at email address ' + sentFromUserEmail
            sentToUser = AccountModels.Account.objects.get(pk=thisEmail)
            sentToUsername = sentToUser.username
            sentToUserID = sentToUser.userID


            if thisPermission == 'sign':
                subject = sentFromUsername + ' has requested that you sign a document'
                text_content = sentFromUser + ' has requested that you sign a document at IrisDocuments.com'
                if newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
            elif thisPermission == 'edit':
                subject = sentFromUsername + ' has requested that you edit a document'
                text_content = sentFromUser + ' has requested that you edit a document at IrisDocuments.com'
                if newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
            elif thisPermission == 'view':
                subject = sentFromUsername + ' has requested that you view a document'
                text_content = sentFromUser + ' has requested that you view a document at IrisDocuments.com'
                if newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':sentToUserID})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [thisEmail], connection=thisConnection)
                #email.mixed_subtype = 'related'
                email.attach_alternative(html_content, 'text/html')
                #file_path = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/stylesheets/images/irislogo_top_white.png')
                #image = 'irislogo_top_white.png'
                #img = MIMEImage(file_path, 'r')
                #img.add_header('Content-ID', '<{name}>'.format(name=image))
                #img.add_header('Content-Disposition', 'inline', filename=image)
                #email.attach(img)
                email.send()
                
    for eachEmail in emailsScanned:
        userID = AccountModels.Account.objects.get(pk=eachEmail).userID
        writeDocumentSigningBoxes(requestID, userID)
    document.isSent = True
    document.save()
    return HttpResponseRedirect('/UserDashboard/Update/Update1/')

# Handles userData plus textData or brandData
def addUsersToDocumentWithTextLater(request, requestID, userData, textData):
    textAdded = True
    texts = re.split(r'\$', textData)
    if texts[0] == textData:
        texts = re.split(re.escape('*'), textData)
        textAdded = False

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    document = models.Document.objects.get(pk=requestID)
    documentFile = document.fileuuid + '.pdf'

    pdf_file = (dirPath + documentFile)
    pdf_file_x = (dirPath + document.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)

    if textAdded:
        textArray = []
        positionsArray = []
        for text in texts:
            trySplit = re.split(r'#%%', text)
            if len(trySplit) > 1:
                text = ''
                for each in trySplit:
                    text = text + '/' + each
            if len(text) > 1:
                positions = []
                userSplit1 = re.split(r'=', text)
                thisText = userSplit1[0]
                userSplit2 = re.split(r'-', userSplit1[1])
                positions.append(userSplit2[0])
                userSplit3 = re.split(r'&', userSplit2[1])
                positions.append(userSplit3[0])
                userSplit4 = re.split(r'<', userSplit3[1])
                positions.append(userSplit4[0])
                userSplit5 = re.split(r';', userSplit4[1])
                positions.append(userSplit5[0])
                userSplit6 = re.split(r'{', userSplit5[1])
                positions.append(userSplit6[0])
                textSize = userSplit6[1]

                textArray.append(thisText)
                positionsArray.append(positions)

        array = 0
        condition = 1
        firstRun = True
        for text in textArray:
            if firstRun:
                firstRun = False
                if text[0] == '$':
                    text = text[1:] 
                positions = positionsArray[array]
                array += 1
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                can.setFont('Helvetica', int(textSize))
                can.drawString(leftBottomX, (height - leftBottomY), text)
                can.save()
 
                #move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()

                os.remove(pdf_file)
            else:
                if text[0] == '$':
                    text = text[1:] 
                positions = positionsArray[array]
                array += 1

                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2

                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                can.setFont('Helvetica', int(textSize))
                can.drawString(leftBottomX, (height - leftBottomY), text)
                can.save()
 
                #move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)   
    else:
        # Handle data if it is a brand
        # positions are same
        # Change html file to send userID or companyID with data from hidden div tag at the top of the page
        # if the PdfEditorWithCompanyBrand.html is loaded, send an extra identifier denoting this is a companyID
        # if the PdfEditorWithBrand.html is loaded, send an extra identifier denoting this is a userID
        brandArray = []
        positionsArray = []
        for text in texts:
            if len(text) > 1:
                positions = []
                userSplit1 = re.split(r'=', text)
                thisID = userSplit1[0]
                userSplit2 = re.split(r'-', userSplit1[1])
                positions.append(userSplit2[0])
                userSplit3 = re.split(r'&', userSplit2[1])
                positions.append(userSplit3[0])
                userSplit4 = re.split(r'<', userSplit3[1])
                positions.append(userSplit4[0])
                userSplit5 = re.split(r';', userSplit4[1])
                positions.append(userSplit5[0])
                userSplit6 = re.split(r'{', userSplit5[1])
                positions.append(userSplit6[0])
                brandType = userSplit6[1]

                brandArray.append(thisID)
                positionsArray.append(positions)

        if brandType == 'p':
            dirPathBrand = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/files/brands/users/')
        else:
            dirPathBrand = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/files/brands/companys/')


        thisUserID = request.COOKIES.get('user')
        thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
        user = AccountModels.Account.objects.get(pk=thisUserEmail)
        array = 0
        condition = 1
        firstRun = True
        for text in brandArray:
            if firstRun:
                firstRun = False
                if text[0] == '*':
                    text = text[1:] 
                positions = positionsArray[array]
                brandFile = user.brandFileuuid + '.' + user.brandFileType
                brand = dirPathBrand + brandFile
        
                if brandType == 'p':
                    s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
                else:
                    s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)
        
                array += 1
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                # Move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()

                os.remove(pdf_file)
            else:
                if text[0] == '*':
                    text = text[1:] 
                positions = positionsArray[array]
                try:
                    brand = (dirPathBrand + brandArray[array] + '.png')
                except:
                    try:
                        brand = (dirPathBrand + brandArray[array] + '.jpg')
                    except:
                        try:
                            brand = (dirPathBrand + brandArray[array] + '.jpeg')
                        except:
                            pass
        
                array += 1
            
                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2

                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                # Move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)         

    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)
    if condition == 1:
        thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    elif condition == 2:
        thisDocumentuuid = uploadToAWSsite(pdf_file, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass   
        
    return addUsersToDocumentLater(request, requestID, userData)

# Handles userData plus textData plus brandData
def addUsersToDocumentWithTextAndBrandLater(request, requestID, userData, textData, brandData):
    texts = re.split(r'\$', textData)
    brands = re.split(re.escape('*'), brandData)

    textArray = []
    positionsArray = []
    for text in texts:
        trySplit = re.split(r'#%%', text)
        if len(trySplit) > 1:
            text = ''
            for each in trySplit:
                text = text + '/' + each
        if len(text) > 1:
            positions = []
            userSplit1 = re.split(r'=', text)
            thisText = userSplit1[0]
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            userSplit6 = re.split(r'{', userSplit5[1])
            positions.append(userSplit6[0])
            textSize = userSplit6[1]

            textArray.append(thisText)
            positionsArray.append(positions)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')

    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    document = models.Document.objects.get(pk=requestID)
    documentFile = document.fileuuid + '.pdf'

    pdf_file = (dirPath + documentFile)
    pdf_file_x = (dirPath + document.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)

    array = 0
    firstRun = True
    condition = 1
    for text in textArray:
        if firstRun:
            firstRun = False
            if text[0] == '$':
                text = text[1:] 
            positions = positionsArray[array]
            array += 1
            
            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            can.setFont('Helvetica', int(textSize))
            can.drawString(leftBottomX, (height - leftBottomY), text)
            can.save()
 
            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)

            new_pdf = PdfReader(packet)

            output = PdfWriter()
                
            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()

            os.remove(pdf_file)
        else:
            if text[0] == '$':
                text = text[1:] 
            positions = positionsArray[array]
            array += 1
            
            try:
                existing_pdf = PdfReader(open(pdf_file, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 1
            except Exception:
                existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 2

            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            can.setFont('Helvetica', int(textSize))
            can.drawString(leftBottomX, (height - leftBottomY), text)
            can.save()
 
            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)

            new_pdf = PdfReader(packet)

            output = PdfWriter()
                
            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            if condition == 1:
                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file)
            elif condition == 2:
                outputStream = open(pdf_file, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file_x)   

    brandArray = []
    positionsArray = []
    for text in brands:
        if len(text) > 1:
            positions = []
            userSplit1 = re.split(r'=', text)
            thisID = userSplit1[0]
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            userSplit6 = re.split(r'{', userSplit5[1])
            positions.append(userSplit6[0])
            brandType = userSplit6[1]

            brandArray.append(thisID)
            positionsArray.append(positions)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')

    if brandType == 'p':
        dirPathBrand = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/brands/users/')
    else:
        dirPathBrand = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/brands/users/')


    array = 0
    thisUserID = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
    user = AccountModels.Account.objects.get(pk=thisUserEmail)
    for text in brandArray:
        if text[0] == '*':
            text = text[1:] 
        positions = positionsArray[array]
        brandFile = user.brandFileuuid + '.' + user.brandFileType
        brand = dirPathBrand + brandFile
        
        if brandType == 'p':
            s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
        else:
            s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)
        array += 1

        try:
            existing_pdf = PdfReader(open(pdf_file, "rb"))
            width = float(existing_pdf.pages[0].mediabox.width)
            height = float(existing_pdf.pages[0].mediabox.height)
            condition = 1
        except Exception:
            existing_pdf = PdfReader(open(pdf_file_x, "rb"))
            width = float(existing_pdf.pages[0].mediabox.width)
            height = float(existing_pdf.pages[0].mediabox.height)
            condition = 2

        packet = io.BytesIO()
        #packet.truncate(0)
        can = canvas.Canvas(packet)
        can.setPageSize((width,height))
        leftTopX = int(round( float(positions[0]) * width )) 
        leftTopY = int(round( float(positions[1]) * height ))
        rightBottomX = int(round( float(positions[2]) * width ))
        rightBottomY = int(round( float(positions[3]) * height ))
        leftBottomX = leftTopX
        leftBottomY = rightBottomY
        total_width = rightBottomX - leftTopX
        total_height = rightBottomY - leftTopY
        can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
        can.save()
 
        # Move to the beginning of the StringIO buffer
        #packet.truncate(0)
        packet.seek(0)

        new_pdf = PdfReader(packet)

        output = PdfWriter()
                
        pageNum = int(positions[4]) - 1
        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            if (i == pageNum):
                page.merge_page(new_pdf.pages[0])
            output.add_page(page)

        if condition == 1:
            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()
            os.remove(pdf_file)
        elif condition == 2:
            outputStream = open(pdf_file, "wb")
            output.write(outputStream)
            outputStream.close()
            os.remove(pdf_file_x)

    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)
    if condition == 1:
        thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    elif condition == 2:
        thisDocumentuuid = uploadToAWSsite(pdf_file, 'documents')
        document.fileuuid = thisDocumentuuid
        document.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass
        
    return addUsersToDocumentLater(request, requestID, userData)

def addUsersToDocumentLater(request, requestID, userData):
    document = models.Document.objects.get(pk=requestID)
    num = document.draftNum
    sentFromUserID = request.COOKIES.get('user')
    
    documentAlert = models.DocumentAlert.objects.get(pk=sentFromUserID+requestID)
    date = datetime.datetime.now()
    if documentAlert.date.year <= date.year:
        if documentAlert.date.month <= date.month:
            if documentAlert.date.day <= date.day:
                if documentAlert.hour <= date.hour:
                    return HttpResponseRedirect('/UserDashboard/Error/Error2/')

    if document.ofType == 'company':
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=sentFromUserID).companyID
        company = AccountModels.Company.objects.get(pk=companyID)
        company.documentsUsed += 1
        company.save()
        documents = AccountModels.CompanyDocuments.objects.get(pk=companyID)
        documents.documents += 1
        documents.save()
        companyRequestID = companyID + '_' + str(documents.documents)
        companyDocObj = AccountModels.CompanyDocument(companyIDNonce=companyRequestID, documentID=requestID)
        companyDocObj.save()

    try:
        rewriteDrafts(num, sentFromUserID)
    except Exception:
        pass


    numberOfDocumentsSentObj = models.NumberOfDocumentsSent.objects.get(pk=sentFromUserID)
    numberOfDocumentsSentObj.documents += 1
    numberOfDocumentsSentObj.save()

    if numberOfDocumentsSentObj.documents > 26:
        removeSentFromMemory(userID)

    keyToKey = sentFromUserID + '_' + str(numberOfDocumentsSentObj.documents)
    documentSent = models.DocumentsSent(userIDNonce=keyToKey, documentKey=requestID)
    documentSent.save()

    users = re.split(r'>', userData)
    emailsScanned = []
    userOccurences = {}
    for user in users:
        if len(user) < 1:
            break
        positions = []
        userSplit1 = re.split(r'=', user)
        thisEmail = userSplit1[0]
        if userSplit1[1] == 'view':
            thisPermission = 'view'
        elif userSplit1[1] == 'edit':
            thisPermission = 'edit'
        else:
            thisPermission = 'sign'
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            positions.append(userSplit5[1])

        newAcc = False
        try:
            userID = AccountModels.Account.objects.get(pk=thisEmail).userID
        except Exception:
            newAcc = True
            accounts = AccountModels.Accounts.objects.get(pk=1)
            accounts.users += 1
            accounts.save()

            userID = accounts.users

            userID = str(userID)
            lengthAccountNumber = len(userID)
            if (lengthAccountNumber < 16):
                zeroes = 16 - lengthAccountNumber
                string = ''
                while zeroes != 0:
                    string = string + '0'
                    zeroes -= 1
                userID = string + userID

            account = AccountModels.Account(userID = userID, username = userID, email = thisEmail)
            account.save()
            newAccountLookupID = AccountModels.AccountLookupByID(userID = userID, email = thisEmail)
            newAccountLookupID.save()

            initializeDocumentCount = models.NumberOfDocumentsSent(userID = userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.NumberOfDocumentsReceived(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.NumberOfDocumentDrafts(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.NumberOfDocumentsCompleted(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.Documents(userID =  userID, documents = 0)
            initializeDocumentCount.save()
            initializeDocumentCount = models.Templates(userID = userID, templates = 0)
            initializeDocumentCount.save()

        try:
            if emailsScanned.index(thisEmail) >= 0:
                userOccurences[thisEmail] += 1

                #databaseJSON[thisEmail + str(userOccurences[thisEmail])] = positions
                document.signatureData[thisEmail + str(userOccurences[thisEmail])] = positions
                document.save()

        except ValueError:
            emailsScanned.append(thisEmail)
            userOccurences[thisEmail] = 1
            thisAcc = AccountModels.Account.objects.get(pk=thisEmail)
            thisAcc.newReceived = True
            thisAcc.save()

            #documentObj = models.Document.objects.get(pk=requestID)
            #documentObjAssociatedUsers = (documentObj.associatedWith).split('}')
            #documentObj.associatedWith = documentObjAssociatedUsers[0] + ',' + userID + ':' + thisPermission +  '}'
            #documentObj.save()

            #numberOfDocumentsReceivedObj = models.NumberOfDocumentsReceived.objects.get(pk=userID)
            #numberOfDocumentsReceivedObj.documents += 1
            #numberOfDocumentsReceivedObj.save()

            #keyToKey = userID + '_' + str(numberOfDocumentsReceivedObj.documents)
            #documentReceived = models.DocumentsReceived(userIDNonce=keyToKey, documentKey=requestID)
            #documentReceived.save()

            alert = models.AlertActual(userIDdocumentRequestID=thisAcc.userID+requestID,date=documentAlert.date,hour=documentAlert.hour,newAcc=newAcc)
            alert.save()

            #databaseJSON = json.loads(document.associatedWith)
            #databaseJSON[thisEmail] = thisPermission
            document.associatedWith[thisEmail] = thisPermission
            #databaseJSON = json.loads(document.signatureData)
            #databaseJSON[thisEmail + '1'] = positions
            document.signatureData[thisEmail + '1'] = positions
            document.signed[thisEmail] = False
            document.save()
                
    for eachEmail in emailsScanned:
        userID = AccountModels.Account.objects.get(pk=eachEmail).userID
        writeDocumentSigningBoxes(requestID, userID)
    document.isSent = True
    document.save()
    return HttpResponseRedirect('/UserDashboard/Update/Update1/')

def writeDocumentSigningBoxes(requestID, userID):
    # get doc object > get user email > get signature datas associated with email > drawImage() at each positionX,Y
    document = models.Document.objects.get(pk=requestID)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')

    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    document = models.Document.objects.get(pk=requestID)
    documentFile = document.fileuuid + '.pdf'

    pdf_file = (dirPath + documentFile)
    pdf_file_x = (dirPath + document.fileuuid + '_x.pdf')

    #s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)


    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
    #signatureJSON = json.loads(document.signatureData)
    signatureJSON = document.signatureData
    #newInt = 1
    condition = 1
    firstRun = True
    for key in signatureJSON:
        searchResult = re.search(thisUserEmail, key)
        #thisKey = thisUserEmail + str(newInt)
        if searchResult and firstRun:
            firstRun = False
            positions = signatureJSON[key]
        
            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            leftTopY = int(round( float(positions[1]) * height ))
            rightBottomX = int(round( float(positions[2]) * width ))
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            total_width = rightBottomX - leftTopX
            total_height = rightBottomY - leftTopY
            #differential = leftTopY - leftBottomY
            #leftBottomY = leftBottomY - differential
            #can.roundRect(leftBottomX, (height - leftBottomY), total_width, total_height, 4, stroke=1, fill=0)
            can.setStrokeColor(colors.HexColor('#021a34'))
            can.setLineWidth(7)
            can.rect(leftBottomX, (height - leftBottomY), total_width, total_height, stroke=1, fill=0)
            size = math.ceil( ( total_width + total_height ) / 14)
            can.setFont("Times-Roman", size)
            can.setFillColor(colors.HexColor('#021a34'))
            can.drawCentredString((leftBottomX + (total_width/2)), (height - (leftBottomY - (total_height/2))), "Your Signature Here")
            can.save()

            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)
 
            new_pdf = PdfReader(packet)

            output = PdfWriter()

            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()

            os.remove(pdf_file)
        elif searchResult:
            positions = signatureJSON[key]
        
            try:
                existing_pdf = PdfReader(open(pdf_file, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 1
            except Exception:
                existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 2

            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            leftTopY = int(round( float(positions[1]) * height ))
            rightBottomX = int(round( float(positions[2]) * width ))
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            total_width = rightBottomX - leftTopX
            total_height = rightBottomY - leftTopY
            #differential = leftTopY - leftBottomY
            #leftBottomY = leftBottomY - differential
            #can.roundRect(leftBottomX, (height - leftBottomY), total_width, total_height, 4, stroke=1, fill=0)
            can.setStrokeColor(colors.HexColor('#021a34'))
            can.setLineWidth(12)
            can.rect(leftBottomX, (height - leftBottomY), total_width, total_height, stroke=1, fill=0)
            size = math.ceil( ( total_width + total_height ) / 14)
            can.setFont("Times-Roman", size)
            can.setFillColor(colors.HexColor('#021a34'))
            can.drawCentredString((leftBottomX + (total_width/2)), (height - (leftBottomY - (total_height/2))), "Your Signature Here")
            can.save()

            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)
 
            new_pdf = PdfReader(packet)

            output = PdfWriter()
                
            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            if condition == 1:
                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file)
            elif condition == 2:
                outputStream = open(pdf_file, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file_x)

    if condition == 1:
        thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
        documentBoxes = models.DocumentSigningBoxes(requestIDuserID=requestID + userID, fileuuid=thisDocumentuuid)
        documentBoxes.save()
    elif condition == 2:
        thisDocumentuuid = uploadToAWSsite(pdf_file, 'documents')
        documentBoxes = models.DocumentSigningBoxes(requestIDuserID=requestID + userID, fileuuid=thisDocumentuuid)
        documentBoxes.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass
    
def addUsersToTemplateWithText(request, requestID, userData, textData):
    textAdded = True
    texts = re.split(r'\$', textData)
    if texts[0] == textData:
        texts = re.split(re.escape('*'), textData)
        textAdded = False

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/templates/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    template = models.Template.objects.get(pk=requestID)
    templateFile = template.fileuuid + '.pdf'

    pdf_file = (dirPath + templateFile)
    pdf_file_x = (dirPath + template.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/templates/' + templateFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)

    if textAdded:
        textArray = []
        positionsArray = []
        for text in texts:
            trySplit = re.split(r'#%%', text)
            if len(trySplit) > 1:
                text = ''
                for each in trySplit:
                    text = text + '/' + each
            if len(text) > 1:
                positions = []
                userSplit1 = re.split(r'=', text)
                thisText = userSplit1[0]
                userSplit2 = re.split(r'-', userSplit1[1])
                positions.append(userSplit2[0])
                userSplit3 = re.split(r'&', userSplit2[1])
                positions.append(userSplit3[0])
                userSplit4 = re.split(r'<', userSplit3[1])
                positions.append(userSplit4[0])
                userSplit5 = re.split(r';', userSplit4[1])
                positions.append(userSplit5[0])
                userSplit6 = re.split(r'{', userSplit5[1])
                positions.append(userSplit6[0])
                textSize = userSplit6[1]

                textArray.append(thisText)
                positionsArray.append(positions)

        array = 0
        firstRun = True
        condition = 1
        for text in textArray:
            if firstRun:
                firstRun = False
                if text[0] == '$':
                    text = text[1:] 
                positions = positionsArray[array]
                array += 1
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                can.setFont('Helvetica', int(textSize))
                can.drawString(leftBottomX, (height - leftBottomY), text)
                can.save()
 
                #move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()

                os.remove(pdf_file)
            else:
                if text[0] == '$':
                    text = text[1:] 
                positions = positionsArray[array]
                array += 1

                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                can.setFont('Helvetica', int(textSize))
                can.drawString(leftBottomX, (height - leftBottomY), text)
                can.save()
 
                #move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)
    else:
        # Handle data if it is a brand
        # positions are same
        # Change html file to send userID or companyID with data from hidden div tag at the top of the page
        # if the PdfEditorWithCompanyBrand.html is loaded, send an extra identifier denoting this is a companyID
        # if the PdfEditorWithBrand.html is loaded, send an extra identifier denoting this is a userID
        brandArray = []
        positionsArray = []
        for text in texts:
            if len(text) > 1:
                positions = []
                userSplit1 = re.split(r'=', text)
                thisID = userSplit1[0]
                userSplit2 = re.split(r'-', userSplit1[1])
                positions.append(userSplit2[0])
                userSplit3 = re.split(r'&', userSplit2[1])
                positions.append(userSplit3[0])
                userSplit4 = re.split(r'<', userSplit3[1])
                positions.append(userSplit4[0])
                userSplit5 = re.split(r';', userSplit4[1])
                positions.append(userSplit5[0])
                userSplit6 = re.split(r'{', userSplit5[1])
                positions.append(userSplit6[0])
                brandType = userSplit6[1]

                brandArray.append(thisID)
                positionsArray.append(positions)

        dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/templates/')

        if brandType == 'p':
            dirPathBrand = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/files/brands/users/')
        else:
            dirPathBrand = (os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) + '/static/files/brands/companys/')

        thisUserID = request.COOKIES.get('user')
        thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
        user = AccountModels.Account.objects.get(pk=thisUserEmail)
        array = 0
        firstRun = True
        condition = 1
        for text in brandArray:
            if firstRun:
                firstRun = False
                if text[0] == '*':
                    text = text[1:] 
                positions = positionsArray[array]
                brandFile = user.brandFileuuid + '.' + user.brandFileType
                brand = dirPathBrand + brandFile
        
                if brandType == 'p':
                    s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
                else:
                    s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)

                array += 1
            
                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                # Move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()

                os.remove(pdf_file)
            else:
                if text[0] == '*':
                    text = text[1:] 
                positions = positionsArray[array]
                brandFile = user.brandFileuuid + '.' + user.brandFileType
                brand = dirPathBrand + brandFile
        
                if brandType == 'p':
                    s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
                else:
                    s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)
        
                array += 1
            
                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2

                packet = io.BytesIO()
                #packet.truncate(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                # Move to the beginning of the StringIO buffer
                #packet.truncate(0)
                packet.seek(0)

                new_pdf = PdfReader(packet)

                output = PdfWriter()
                
                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)

    s3.delete_object(Bucket='iris1-static', Key='static/files/templates/' + templateFile)
    if condition == 1:
        thisTemplateuuid = uploadToAWSsite(pdf_file_x, 'templates')
        template.fileuuid = thisTemplateuuid
        template.save()
    elif condition == 2:
        thisTemplateuuid = uploadToAWSsite(pdf_file, 'templates')
        template.fileuuid = thisTemplateuuid
        template.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass
        
    return addUsersToTemplate(request, requestID, userData)

def addUsersToTemplateWithTextAndBrand(request, requestID, userData, textData, brandData):
    texts = re.split(r'\$', textData)
    brands = re.split(re.escape('*'), brandData)

    textArray = []
    positionsArray = []
    for text in texts:
        trySplit = re.split(r'#%%', text)
        if len(trySplit) > 1:
            text = ''
            for each in trySplit:
                text = text + '/' + each
        if len(text) > 1:
            positions = []
            userSplit1 = re.split(r'=', text)
            thisText = userSplit1[0]
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            userSplit6 = re.split(r'{', userSplit5[1])
            positions.append(userSplit6[0])
            textSize = userSplit6[1]

            textArray.append(thisText)
            positionsArray.append(positions)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/templates/')
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    template = models.Template.objects.get(pk=requestID)
    templateFile = template.fileuuid + '.pdf'

    pdf_file = (dirPath + templateFile)
    pdf_file_x = (dirPath + template.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/templates/' + templateFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)
    
    array = 0
    firstRun = True
    condition = 1
    for text in textArray:
        if firstRun:
            firstRun = False
            if text[0] == '$':
                text = text[1:] 
            positions = positionsArray[array]
            array += 1
            
            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            can.setFont('Helvetica', int(textSize))
            can.drawString(leftBottomX, (height - leftBottomY), text)
            can.save()
 
            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)

            new_pdf = PdfReader(packet)

            output = PdfWriter()

            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()

            os.remove(pdf_file)
        else:
            if text[0] == '$':
                text = text[1:] 
            positions = positionsArray[array]
            array += 1
            
            try:
                existing_pdf = PdfReader(open(pdf_file, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 1
            except Exception:
                existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                width = float(existing_pdf.pages[0].mediabox.width)
                height = float(existing_pdf.pages[0].mediabox.height)
                condition = 2

            packet = io.BytesIO()
            #packet.truncate(0)
            can = canvas.Canvas(packet)
            can.setPageSize((width,height))
            leftTopX = int(round( float(positions[0]) * width )) 
            rightBottomY = int(round( float(positions[3]) * height ))
            leftBottomX = leftTopX
            leftBottomY = rightBottomY
            can.setFont('Helvetica', int(textSize))
            can.drawString(leftBottomX, (height - leftBottomY), text)
            can.save()
 
            #move to the beginning of the StringIO buffer
            #packet.truncate(0)
            packet.seek(0)

            new_pdf = PdfReader(packet)

            output = PdfWriter()

            pageNum = int(positions[4]) - 1
            for i in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[i]
                if (i == pageNum):
                    page.merge_page(new_pdf.pages[0])
                output.add_page(page)

            if condition == 1:
                outputStream = open(pdf_file_x, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file)
            elif condition == 2:
                outputStream = open(pdf_file, "wb")
                output.write(outputStream)
                outputStream.close()
                os.remove(pdf_file_x)

    brandArray = []
    positionsArray = []
    for text in brands:
        if len(text) > 1:
            positions = []
            userSplit1 = re.split(r'=', text)
            thisID = userSplit1[0]
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            userSplit6 = re.split(r'{', userSplit5[1])
            positions.append(userSplit6[0])
            brandType = userSplit6[1]

            brandArray.append(thisID)
            positionsArray.append(positions)

    thisUserID = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
    user = AccountModels.Account.objects.get(pk=thisUserEmail)
    if brandType == 'p':
        dirPathBrand = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/brands/users/')
        brandFile = user.brandFileuuid + '.' + user.brandFileType
        brand = dirPathBrand + brandFile
        s3.download_file('iris1-static',  'static/files/brands/users/' + brandFile, brand)
    else:
        dirPathBrand = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/brands/companys/')
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=thisUserID).companyID
        company = AccountModels.Company.objects.get(pk=companyID)
        brandFile = company.brandFileuuid + '.' + company.brandFileType
        brand = dirPathBrand + brandFile
        s3.download_file('iris1-static',  'static/files/brands/companys/' + brandFile, brand)

    array = 0
    for text in brandArray:
        if text[0] == '*':
            text = text[1:] 
        positions = positionsArray[array]
        array += 1

        try:
            existing_pdf = PdfReader(open(pdf_file, "rb"))
            width = float(existing_pdf.pages[0].mediabox.width)
            height = float(existing_pdf.pages[0].mediabox.height)
            condition = 1
        except Exception:
            existing_pdf = PdfReader(open(pdf_file_x, "rb"))
            width = float(existing_pdf.pages[0].mediabox.width)
            height = float(existing_pdf.pages[0].mediabox.height)
            condition = 2

        packet = io.BytesIO()
        #packet.truncate(0)
        can = canvas.Canvas(packet)
        can.setPageSize((width,height))
        leftTopX = int(round( float(positions[0]) * width )) 
        leftTopY = int(round( float(positions[1]) * height ))
        rightBottomX = int(round( float(positions[2]) * width ))
        rightBottomY = int(round( float(positions[3]) * height ))
        leftBottomX = leftTopX
        leftBottomY = rightBottomY
        total_width = rightBottomX - leftTopX
        total_height = rightBottomY - leftTopY
        can.drawImage(brand, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
        can.save()
 
        # Move to the beginning of the StringIO buffer
        #packet.truncate(0)
        packet.seek(0)

        new_pdf = PdfReader(packet)

        output = PdfWriter()
                
        pageNum = int(positions[4]) - 1
        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            if (i == pageNum):
                page.merge_page(new_pdf.pages[0])
            output.add_page(page)

        if condition == 1:
            outputStream = open(pdf_file_x, "wb")
            output.write(outputStream)
            outputStream.close()
            os.remove(pdf_file)
        elif condition == 2:
            outputStream = open(pdf_file, "wb")
            output.write(outputStream)
            outputStream.close()
            os.remove(pdf_file_x)
    
    s3.delete_object(Bucket='iris1-static', Key='static/files/templates/' + templateFile)
    if condition == 1:
        thisTemplateuuid = uploadToAWSsite(pdf_file_x, 'templates')
        template.fileuuid = thisTemplateuuid
        template.save()
    elif condition == 2:
        thisTemplateuuid = uploadToAWSsite(pdf_file, 'templates')
        template.fileuuid = thisTemplateuuid
        template.save()
    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass

    return addUsersToTemplate(request, requestID, userData)

def addUsersToTemplate(request, requestID, userData):
    template = models.Template.objects.get(pk=requestID)
    num = template.num
    userID = request.COOKIES.get('user')

    if template.ofType == 'company':
        companyID = AccountModels.CompanyLookupByAccountID.objects.get(pk=userID).companyID
        company = AccountModels.Company.objects.get(pk=companyID)
        company.templatesUsed += 1
        company.save()
        templates = AccountModels.CompanyTemplates.objects.get(pk=companyID)
        templates.templates += 1
        templates.save()
        companyRequestID = companyID + '_' + str(templates.templates)
        companyTemplateObj = AccountModels.CompanyTemplate(companyIDNonce=companyRequestID, templateID=requestID)
        companyTemplateObj.save()

    users = re.split(r'>', userData)
    emailsScanned = []
    userOccurences = {}
    for user in users:
        positions = []
        if len(user) < 2:
            return HttpResponseRedirect('/UserDashboard/')
        userSplit1 = re.split(r'=', user)
        thisEmail = userSplit1[0]
        if userSplit1[1] == 'view':
            thisPermission = 'view'
        elif userSplit1[1] == 'edit':
            thisPermission = 'edit'
        else:
            thisPermission = 'sign'
            userSplit2 = re.split(r'-', userSplit1[1])
            positions.append(userSplit2[0])
            userSplit3 = re.split(r'&', userSplit2[1])
            positions.append(userSplit3[0])
            userSplit4 = re.split(r'<', userSplit3[1])
            positions.append(userSplit4[0])
            userSplit5 = re.split(r';', userSplit4[1])
            positions.append(userSplit5[0])
            positions.append(userSplit5[1])

        try:
            if emailsScanned.index(thisEmail) >= 0:
                userOccurences[thisEmail] += 1

                #databaseJSON[thisEmail + str(userOccurences[thisEmail])] = positions
                template.signatureData[thisEmail + str(userOccurences[thisEmail])] = positions
                template.save()

        except ValueError:
            emailsScanned.append(thisEmail)
            userOccurences[thisEmail] = 1

            #databaseJSON = json.loads(template.associatedWith)
            #databaseJSON[thisEmail] = thisPermission
            template.associatedWith[thisEmail] = thisPermission
            #databaseJSON = json.loads(template.signatureData)
            #databaseJSON[thisEmail + '1'] = positions
            template.signatureData[thisEmail + '1'] = positions
            template.save()

    template.isFinished = True
    template.save()
    return HttpResponseRedirect('/UserDashboard/')

def Document(request, requestID):
    document = models.Document.objects.get(pk=requestID)

    if request.method == 'POST':
        form = LoginForms.LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                userDB = models.Account.objects.get(pk=email)
            except BaseException:
                return HttpResponse('Account does not exist')
            else:
                if userDB.email == email:
                    if userDB.password == password:
                        response = render(request, 'PdfSign.html', {'requestID':requestID, 'userID':userDB.userID})
                        thisIP = ClientFunctions.get_client_ip(request)
                        userDB.currentIP = thisIP
                        CURRENT_TIME = datetime.datetime.today()
                        CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                        userDB.lastLoginTime = CURRENT_TIME
                        userDB.save()
                        response.set_cookie('user', userDB.userID)
                        return response

    try:
        permissions = json.loads(models.Document.objects.get(pk=requestID).associatedWith)
        userID = request.COOKIES.get('user')
        userEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
        if permissions[userEmail] == 'edit':
            ManageDocument(request, requestID)
        elif permissions[userEmail] == 'sign':
            return render(request, 'PdfSign.html', {'requestID':requestID, 'userID':userID, 'file':document.fileuuid})
        elif permissions[userEmail] == 'view':
            return render(request, 'PdfView.html', {'requestID':requestID, 'file':document.fileuuid})
        else:
            return HttpResponseRedirect('/')
    except Exception:
        form = LoginForms.LoginForm()
        return render(request, 'LoginRedirectSign.html', {'requestID':requestID, 'form':form, 'file':document.fileuuid})

def DocumentNewAccount(request, requestID):

    if request.method == 'POST':
        #form = forms.AccountForm(request.POST, extra=request.POST.get('extra_field_count'))
        form = AccountForms.AccountForm(request.POST)

        if form.is_valid():

            form_username = form.cleaned_data['username']
            form_email = form.cleaned_data['email']
            form_password = form.cleaned_data['password']
            conf_pass = form.cleaned_data['confirm_password']
            if not(conf_pass == form_password):
                return HttpResponse('Passwords do not match')
            
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
            if (lengthAccountNumber < 16):
                zeroes = 16 - lengthAccountNumber
                string = ''
                while zeroes != 0:
                    string = string + '0'
                    zeroes -= 1
                accountNumber = string + accountNumber

                thisIP = ClientFunctions.get_client_ip(request)
                CURRENT_TIME = datetime.datetime.today()                
                CURRENT_TIME = str(CURRENT_TIME.day) + '-' + str(CURRENT_TIME.month) + '=' + str(CURRENT_TIME.year)
                lastLoginTime = CURRENT_TIME
                newAccount = AccountModels.Account(userID = accountNumber, username = form_username, email = form_email, password = form_password, lastLoginTime = lastLoginTime, currentIP = thisIP)
                newAccount.save()
                newAccountLookupID = AccountModels.AccountLookupByID(userID = accountNumber, email = form_email)
                newAccountLookupID.save()
            
                initializeDocumentCount = models.NumberOfDocumentsSent(userID =  accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.NumberOfDocumentsReceived(userID =  accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.NumberOfDocumentDrafts(userID =  accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.NumberOfDocumentsCompleted(userID =  accountNumber, documents = 0)
                initializeDocumentCount.save()
                initializeDocumentCount = models.Documents(userID =  accountNumber, documents = 0)
                initializeDocumentCount.save()

                response = HttpResponseRedirect('/ManageDocument/' + requestID + '/')
                response.set_cookie('user', newAccount.userID)
                return response
        return HttpResponse('Bad Request')

    form = AccountForms.AccountForm()
    return render(request, 'CreateAccountRedirectSign.html', {'form':form})

def SignedDocumentSubmission(request, requestID):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True
    # Send the user back to the dashboard to record a signature if they do not have one
    s3 = boto3.client('s3', aws_access_key_id='', aws_secret_access_key='')
    try:
        thisUserID = request.COOKIES.get('user')
        thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
        account = AccountModels.Account.objects.get(pk=thisUserEmail)

        dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/signatures/')
        signatureFile = account.signatureFileuuid + '.png'
        img_file = (dirPath + signatureFile)
        s3.download_file('iris1-static',  'static/files/signatures/' + signatureFile, img_file)
        fileObj = open(img_file, 'r')
        fileObj.close()
    except Exception:
        return HttpResponseRedirect('/UserDashboard/Error/Error3/')
    # get doc object > get user email > get signature datas associated with email > drawImage() at each positionX,Y

    document = models.Document.objects.get(pk=requestID)
    thisUserID = request.COOKIES.get('user')
    thisUserEmail = AccountModels.AccountLookupByID.objects.get(pk=thisUserID).email
    documentFile = document.fileuuid + '.pdf'

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    pdf_file = (dirPath + documentFile)
    pdf_file_x = (dirPath + document.fileuuid + '_x.pdf')

    s3.download_file('iris1-static',  'static/files/documents/' + documentFile, pdf_file)
    existing_pdf = PdfReader(open(pdf_file, "rb"))
    width = float(existing_pdf.pages[0].mediabox.width)
    height = float(existing_pdf.pages[0].mediabox.height)

    #signatureJSON = json.loads(document.signatureData)
    signatureJSON = document.signatureData
    dateString = ""
    hasRun = False
    emailSent = False
    condition = 1
    packet = io.BytesIO()

    try:
        for key in signatureJSON:
            #thisKey = thisUserEmail + str(newInt)
            searchResult = re.match(thisUserEmail, key)
            if searchResult and not hasRun:
                hasRun = True
                positions = signatureJSON[key]

                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2
            
                #packet = io.BytesIO()
                packet.truncate(0)
                packet.seek(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                #can.drawString(10, 100, "Hello world")
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                #differential = leftTopY - leftBottomY
                #leftBottomY = leftBottomY - differential
                can.drawImage(img_file, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                #move to the beginning of the StringIO buffer
                packet.seek(0)
 
                new_pdf = PdfReader(packet)

                output = PdfWriter()

                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)

                #associations = json.loads(document.associatedWith)
                #associations[thisUserEmail] = 'x'
                date = datetime.datetime.today()
                dateString = str(date.month) + str("-") + str(date.day) + str("-") + str(date.year)
                document.signed[thisUserEmail] = True
                document.signatureData[thisUserEmail + "1"] = dateString
                document.associatedWith[thisUserEmail] = "x"
                #document.associatedWith = json.dumps(associations)
                document.save()
            elif searchResult:
                positions = signatureJSON[key]

                try:
                    existing_pdf = PdfReader(open(pdf_file, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 1
                except Exception:
                    existing_pdf = PdfReader(open(pdf_file_x, "rb"))
                    width = float(existing_pdf.pages[0].mediabox.width)
                    height = float(existing_pdf.pages[0].mediabox.height)
                    condition = 2
            
                #packet = io.BytesIO()
                packet.truncate(0)
                packet.seek(0)
                can = canvas.Canvas(packet)
                can.setPageSize((width,height))
                #can.drawString(10, 100, "Hello world")
                leftTopX = int(round( float(positions[0]) * width )) 
                leftTopY = int(round( float(positions[1]) * height ))
                rightBottomX = int(round( float(positions[2]) * width ))
                rightBottomY = int(round( float(positions[3]) * height ))
                leftBottomX = leftTopX
                leftBottomY = rightBottomY
                total_width = rightBottomX - leftTopX
                total_height = rightBottomY - leftTopY
                #differential = leftTopY - leftBottomY
                #leftBottomY = leftBottomY - differential
                can.drawImage(img_file, leftBottomX, (height - leftBottomY), width=total_width, height=total_height, preserveAspectRatio=True, mask='auto')
                can.save()
 
                #move to the beginning of the StringIO buffer
                packet.seek(0)
 
                new_pdf = PdfReader(packet)

                output = PdfWriter()

                pageNum = int(positions[4]) - 1
                for i in range(len(existing_pdf.pages)):
                    page = existing_pdf.pages[i]
                    if (i == pageNum):
                        page.merge_page(new_pdf.pages[0])
                    output.add_page(page)

                if condition == 1:
                    outputStream = open(pdf_file_x, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file)
                elif condition == 2:
                    outputStream = open(pdf_file, "wb")
                    output.write(outputStream)
                    outputStream.close()
                    os.remove(pdf_file_x)

                #associations = json.loads(document.associatedWith)
                #associations[thisUserEmail] = 'x'
                date = datetime.datetime.today()
                dateString = str(date.month) + str("-") + str(date.day) + str("-") + str(date.year)
                document.signed[thisUserEmail] = True
                document.signatureData[thisUserEmail + "1"] = dateString
                document.associatedWith[thisUserEmail] = "x"
                #document.associatedWith = json.dumps(associations)
                document.save()
    except Exception:
        pass

    packet.close()
    s3.delete_object(Bucket='iris1-static', Key='static/files/documents/' + documentFile)

    try:
        thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
    except Exception:
        thisDocumentuuid = uploadToAWSsite(pdf_file, 'documents')
    document.fileuuid = thisDocumentuuid
    document.save()

    try:
        os.remove(pdf_file)
    except Exception:
        pass
    try:
        os.remove(pdf_file_x)
    except Exception:
        pass
        
    os.remove(img_file)
    checkAllSignatures(document, dateString, thisUserEmail)
    if mobile:
        return HttpResponseRedirect('/UserDashboard/')
    return HttpResponseRedirect('/UserDashboard/Update/Update2/')

def sendNotificationEmail(document, fromUserEmail):
    thisID = document.createdBy
    thisEmail = AccountModels.AccountLookupByID.objects.get(pk=document.createdBy).email
    thisAcc = AccountModels.Account.objects.get(pk=thisEmail)
    fromAccount = AccountModels.Account.objects.get(pk=fromUserEmail)
    sentFromUsername = fromAccount.username
    subject = sentFromUsername + ' has signed a document'
    text_content = thisAcc.username + ',\n\n' + sentFromUsername + ' has signed your document titled: '  + document.title
    html_content = render_to_string('emailNotify.html', {'subject':subject, 'text':text_content, 'requestID':document.requestID})

    with mail.get_connection() as thisConnection:
        email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [thisEmail], connection=thisConnection)
        email.attach_alternative(html_content, 'text/html')
        email.send()

def checkAllSignatures(document, dateString, thisUserEmail):
    allSigned = True
    for eachKey in document.signed:
        if (document.signed[eachKey] == False):
            allSigned = False

    if allSigned:
        document.isComplete =  True
        document.fingerprintCompleted = str(uuid.uuid4())
        document.completedDate = dateString
        document.save()
        creatorAccEmail = AccountModels.AccountLookupByID.objects.get(pk=document.createdBy).email
        creatorAcc = AccountModels.Account.objects.get(pk=creatorAccEmail)
        creatorAcc.sentComplete = True
        creatorAcc.save()
        if document.notify:
            sendNotificationEmail(document, thisUserEmail)
        createAudit(document)

def createAudit(document):
    #pdf_audit = pdf_file.split('.pdf')
    #pdf_audit = pdf_audit[0] + '_audit.pdf'

    packet = io.BytesIO()
    #packet.truncate(0)
    can = canvas.Canvas(packet)
    can.setPageSize(letter)
    can.setFont('Times-Roman', 14)

    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/stylesheets/images/irislogo_top.png')
    can.drawImage(dirPath, 50, 750, preserveAspectRatio=True, mask='auto')

    can.drawString(50, 710, 'Document Created')
    can.drawString(50, 699, 'Fingerprint: ' + document.fingerprintCreated)
    can.drawString(400, 705, 'Created On: ' + document.createdDate)

    count = 0
    signers = document.signed
    for each in signers:
        if (signers[each] == True) and (each != 'default'):
            count += 1
            account = AccountModels.Account.objects.get(pk=each)
            can.drawString(50, 690 - (count * 25), 'Document Signed By: ' + account.username)
            can.drawString(50, 679 - (count * 25), 'Email: ' + each)
            can.drawString(400, 685 - (count * 25), 'Signed On: ' + document.signatureData[each + '1'])


    can.drawString(50, 645 - (count * 25), 'Document Completed')
    can.drawString(50, 634 - (count * 25), 'Fingerprint: ' + document.fingerprintCompleted)
    can.drawString(400, 640 - (count * 25), 'Created On: ' + document.completedDate)


    can.save()

    new_pdf = PdfReader(packet)
    output = PdfWriter()

    for i in range(len(new_pdf.pages)):
        page = new_pdf.pages[i]
        output.add_page(page)
    
    dirPath = (os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__) ) ) ) + '/static/files/documents/')
    pdf_file_x = (dirPath + document.fileuuid + '_xx.pdf')

    outputStream = open(pdf_file_x, "wb")
    output.write(outputStream)
    outputStream.close()

    thisDocumentuuid = uploadToAWSsite(pdf_file_x, 'documents')
    document.audituuid = thisDocumentuuid
    document.save()
            
    os.remove(pdf_file_x)
    # Write pdf file
    #outputStream = open(pdf_audit, 'wb')
    #output.write(outputStream)
    #outputStream.close()