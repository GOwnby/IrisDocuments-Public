from django.db import models
from django.db.models import JSONField
import os
from uuid import uuid4


def path_and_rename(instance, filename):
    upload_to = 'documents/'
    ext = filename.split('.')[-1]
    # get filename
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join(upload_to, filename)

def path_and_renameTemplate(instance, filename):
    upload_to = 'templates/'
    ext = filename.split('.')[-1]
    # get filename
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join(upload_to, filename)

def path_and_rename_files(instance, filename):
    upload_to = 'files/'
    ext = filename.split('.')[-1]
    instance.ext = ext
    # get filename
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join(upload_to, filename)

class DocumentsSent(models.Model):
    userIDNonce = models.CharField(primary_key=True, max_length=32, default='')
    documentKey = models.CharField(max_length=32, default='')

class NumberOfDocumentsSent(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    documents = models.IntegerField(default=0)

class DocumentDrafts(models.Model):
    userIDNonce = models.CharField(primary_key=True, max_length=32, default='')
    documentKey = models.CharField(max_length=32, default='')

class NumberOfDocumentDrafts(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    documents = models.IntegerField(default=0)

class DocumentsReceived(models.Model):
    userIDNonce = models.CharField(primary_key=True, max_length=32, default='')
    documentKey = models.CharField(max_length=32, default='')

class NumberOfDocumentsReceived(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    documents = models.IntegerField(default=0)

class DocumentsCompleted(models.Model):
    userIDNonce = models.CharField(primary_key=True, max_length=32, default='')
    documentKey = models.CharField(max_length=32, default='')

class NumberOfDocumentsCompleted(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    documents = models.IntegerField(default=0)

class Document(models.Model):
    requestID = models.CharField(primary_key=True, max_length=32, default='')
    templateID = models.CharField(max_length=32, default='')
    createdBy = models.CharField(max_length=32, default='')
    notify = models.BooleanField(default=False)
    createdDate = models.CharField(max_length=32, default='')
    completedDate = models.CharField(max_length=32, default='')
    lastEditedBy = models.CharField(max_length=32, default='')
    lastEditedDate = models.CharField(max_length=32, default='')
    title = models.TextField(max_length=128, default='')
    additionalFile = models.BooleanField(default=False)
    fileuuid = models.CharField(max_length=32, default='')
    audituuid = models.CharField(max_length=32, default='')
    
    ofType = models.CharField(max_length=32, default='user')

    fingerprintCreated = models.CharField(max_length=64, default='')
    fingerprintCompleted = models.CharField(max_length=64, default='')

    associatedWith = JSONField(default=dict())
    signatureData = JSONField(default=dict())
    signed = JSONField(default=dict())

    createdFromTemplate = models.BooleanField(default=False)
    isSent = models.BooleanField(default=False)
    isComplete = models.BooleanField(default=False)
    draftNum = models.IntegerField(default=0)

    expansionSlot = models.JSONField(default=dict())
class Documents(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    documents = models.IntegerField(default=0)
class DocumentSigningBoxes(models.Model):
    requestIDuserID = models.CharField(primary_key=True, max_length=48, default='')
    fileuuid = models.CharField(max_length=32, default='')
class Template(models.Model):
    requestID = models.CharField(primary_key=True, max_length=32, default='')
    createdBy = models.CharField(max_length=32, default='')
    createdDate = models.CharField(max_length=32, default='')
    title = models.TextField(max_length=128, default='')
    fileuuid = models.CharField(max_length=32, default='')

    ofType = models.CharField(max_length=32, default='user')

    associatedWith = JSONField(default=dict())
    signatureData = JSONField(default=dict())

    isFinished = models.BooleanField(default=False)
    num = models.IntegerField(default=0)

    expansionSlot = models.JSONField(default=dict())

class Templates(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    templates = models.IntegerField(default=0)

class AdditionalFile(models.Model):
    docRequestID = models.CharField(primary_key=True, max_length=32, default='')
    #file = models.FileField(upload_to=path_and_rename_files)
    fileuuid = models.CharField(max_length=32, default='')
    ext = models.CharField(max_length=8, default='')

# Represents a pointer from the creator userID and document ID to the possibly several actual alerts
class DocumentAlert(models.Model):
    userIDdocumentRequestID = models.CharField(primary_key=True, max_length=40, default='')
    date = models.DateField(auto_now=False)
    hour = models.IntegerField(default=0)

# Represents an alert to a receiving userID and the document to update their models/dashboard with
class AlertActual(models.Model):
    userIDdocumentRequestID = models.CharField(primary_key=True, max_length=40, default='')
    date = models.DateField(auto_now=False)
    hour = models.IntegerField(default=0)
    newAcc = models.BooleanField(default=False)