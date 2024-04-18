from django.db import models
from django.db.models import JSONField
import os
from uuid import uuid4

def path_and_rename_users(instance, filename):
    upload_to = 'brands/users/'
    ext = filename.split('.')[-1]
    if ( (ext == 'png') or (ext == 'jpeg') or (ext == 'jpg') ):
        # get filename
        if instance.pk:
            filename = '{}.{}'.format(instance.pk, ext)
            checkAndRemove(upload_to, filename)
        else:
            # set filename as random string
            filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(upload_to, filename)
        
def path_and_rename_company(instance, filename):
    upload_to = 'brands/companys/'
    ext = filename.split('.')[-1]
    if ( (ext == 'png') or (ext == 'jpeg') or (ext == 'jpg') ):
        # get filename
        if instance.pk:
            filename = '{}.{}'.format(instance.pk, ext)
            checkAndRemove(upload_to, filename)
        else:
            # set filename as random string
            filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(upload_to, filename)

def checkAndRemove(upload_to, filename):
    size = len(filename)
    filename = filename[:size-4]
    try:
        os.remove(upload_to + filename + '.png')
    except:
        try:
            os.remove(upload_to + filename + '.jpg')
        except:
            try:
                os.remove(upload_to + filename + '.jpeg')
            except:
                pass

class Accounts(models.Model):
    key = models.IntegerField(primary_key=True, default=1)
    users = models.IntegerField(default=0)

class Account(models.Model):
    userID = models.CharField(max_length=16)
    username = models.CharField(max_length=100)
    email = models.CharField(primary_key=True, max_length=128)
    password = models.CharField(max_length=100)
    lastLoginTime = models.CharField(max_length=16)
    currentIP = models.CharField(max_length=32)

    companyID = models.CharField(max_length=32,default='')
    companyPermission = models.CharField(max_length=32,default='')
    dateAddedToCompany = models.CharField(max_length=32, default='')
    companyUserNonce = models.IntegerField(default=0)

    cNum = models.CharField(max_length=32,default='')
    cvc = models.CharField(max_length=32,default='')
    cMonth = models.CharField(max_length=32,default='')
    cYear = models.CharField(max_length=32,default='')
    fName = models.CharField(max_length=32,default='')
    lName = models.CharField(max_length=32,default='')
    address = models.CharField(max_length=32,default='')
    city = models.CharField(max_length=32,default='')
    zip = models.CharField(max_length=32,default='')
    state = models.CharField(max_length=32,default='')
    country = models.CharField(max_length=32,default='')
    invoiceNum = models.IntegerField(default=1000)

    subscriptionType = models.IntegerField(default=0)
    logoBranding = models.BooleanField(default=False)
    subDay = models.IntegerField(default=0)
    subDate = models.CharField(max_length=32,default='')
    addBrand = models.BooleanField(default=False)

    deSubDay = models.IntegerField(default=0)
    deSubDate = models.CharField(max_length=32,default='')

    trialEndDay = models.IntegerField(default=0)
    trialDate = models.CharField(max_length=32,default='')

    signatureFileuuid = models.CharField(max_length=32, default='default')
    brandFileuuid = models.CharField(max_length=32, default='')
    brandFileType = models.CharField(max_length=32, default='')
    verified = models.BooleanField(default=False)
    siteRegister = models.BooleanField(default=False)
    #marketingList = models.BooleanField(default=False)
    sentComplete = models.BooleanField(default=False)
    newReceived = models.BooleanField(default=False)

    documentsAvailable = models.IntegerField(default=0)
    templatesAvailable = models.IntegerField(default=0)

    expansionSlot = models.JSONField(default=dict())

class AccountLookupByID(models.Model):
    userID = models.CharField(max_length=32, primary_key=True)
    email = models.CharField(max_length=128)

class Companys(models.Model):
    key = models.IntegerField(primary_key=True, default=1)
    companys = models.IntegerField(default=0)

class Company(models.Model):
    companyID = models.CharField(primary_key=True, max_length=32, default='')
    dateCreated = models.CharField(max_length=32, default='')
    createdBy = models.CharField(max_length=128, default='')
    IPCreated = models.CharField(max_length=32, default='')

    subscriptionType = models.IntegerField(default=0)
    logoBranding = models.BooleanField(default=False)
    subDay = models.IntegerField(default=0)
    subDate = models.CharField(max_length=32,default='')
    addBrand = models.BooleanField(default=False)

    deSubDay = models.IntegerField(default=0)
    deSubDate = models.CharField(max_length=32,default='')

    brandFileuuid = models.CharField(max_length=32, default='')
    brandFileType = models.CharField(max_length=32, default='')
    numUsers = models.IntegerField(default=1)
    associatedWith = models.JSONField(default=dict())

    latest = JSONField(default={0:"d",1:"d",2:"d",3:"d",4:"d",5:"d",6:"d",7:"d",8:"d",9:"d"})

    documentsAvailable = models.IntegerField(default=0)
    documentsUsed = models.IntegerField(default=0)
    templatesAvailable = models.IntegerField(default=0)
    templatesUsed = models.IntegerField(default=0)
    membersAvailable = models.IntegerField(default=0)
    membersUsed = models.IntegerField(default=0)

    expansionSlot = models.JSONField(default=dict())

class CompanyLookupByAccountID(models.Model):
    userID = models.CharField(primary_key=True, max_length=32, default='')
    companyID = models.CharField(max_length=32, default='')

class CompanyDocuments(models.Model):
    companyID = models.CharField(primary_key=True, max_length=32, default='')
    documents = models.IntegerField(default=0)

class CompanyDocument(models.Model):
    companyIDNonce = models.CharField(primary_key=True, max_length=32, default='')
    companyID = models.CharField(max_length=32, default='')
    documentID = models.CharField(max_length=32, default='')

    title = models.TextField(max_length=128, default='')
    author = models.TextField(max_length=128, default='')
    createdDate = models.DateField(auto_now_add=True)

class CompanyTemplates(models.Model):
    companyID = models.CharField(primary_key=True, max_length=32, default='')
    templates = models.IntegerField(default=0)

class CompanyTemplate(models.Model):
    companyIDNonce = models.CharField(primary_key=True, max_length=32, default='')
    companyID = models.CharField(max_length=32, default='')
    templateID = models.CharField(max_length=32, default='')

    title = models.TextField(max_length=128, default='')
    author = models.TextField(max_length=128, default='')
    createdDate = models.DateField(auto_now_add=True)


#class Brand(models.Model):
#    userKey = models.CharField(primary_key=True, max_length=32, default='')
#    brand = models.FileField(upload_to=path_and_rename_users)

#class CompanyBrand(models.Model):
#    companyKey = models.CharField(primary_key=True, max_length=32, default='')
#    brand = models.FileField(upload_to=path_and_rename_company)

class Last25LoggedIn(models.Model):
    key = models.IntegerField(primary_key=True,default=1)
    users = models.JSONField(default=dict())
    lastUserAdded = models.IntegerField(default=0)
