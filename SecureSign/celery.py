from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from celery import shared_task

from django.conf import settings
from requests import request
from .settings import BROKER_URL

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SecureSign.settings')

import django
django.setup()

app = Celery('SecureSign', broker=BROKER_URL)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
logger = get_task_logger(__name__)

# Runs once everyday before regular support time to delete all Support Rooms so that they do not grow at infinitium (10 Rooms for each Support User that connects by cookie)
# SecureSign.celery.task_reset_support
from Home.models import SupportRoom
@shared_task(expires=15)
def task_reset_support():
    SupportRoom.objects.all().delete()

from UserDashboard.views import morningCheckSubscribers
from UserDashboard.views import morningCheckSubscribersCompany
from UserDashboard.views import morningCheckDescribers
from UserDashboard.views import morningCheckDescribersCompany
from UserDashboard.views import morningCheckFreeTrial
from ManageDocument import models as DocumentModels
from CreateAccount import models as AccountModels
import time
import uuid
from django.core.cache import cache
from hashlib import md5
from contextlib import contextmanager
# Runs once everyday to check if there are any subscriptions to be updated
# SecureSign.celery.task_check_subscription_changes
# Run each task below individually seems to be a better option
LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes

@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)

@shared_task(expires=45)
def task_check_subscription_changes():
    morningCheckFreeTrial()
    time.sleep(600)
    morningCheckDescribers()
    time.sleep(600)
    morningCheckDescribersCompany()
    time.sleep(600)
    morningCheckSubscribers()
    time.sleep()
    morningCheckSubscribersCompany()

# Runs once per hour to check if tasks are running as expected
# To be run only during testing -- Updates a integer value on a particular account
# SecureSign.celery.task_check_tasks
# memlock does not work
@shared_task(expires=45)
def task_check_tasks():
    thisName = "TaskCheckTasks"
    currentDate = datetime.datetime.now(timezone('UTC'))
    currentHour = currentDate.hour
    feed_url = "TaskCheckTasks" + str(currentHour)
    feed_url_hexdigest = md5((feed_url).encode()).hexdigest()
    lock_id = '{0}-lock-{1}'.format(thisName, feed_url_hexdigest)
    logger.debug('Importing feed: %s', feed_url)

    account = AccountModels.Account.objects.get(pk="gracenownby@gmail.com")
    with memcache_lock(lock_id, currentDate) as acquired:
        if acquired:
            print('Checking Task Checker...')
            account.documentsAvailable += 1
            account.save()

# Runs once everyday to check if there are any subscriptions to be updated
# SecureSign.celery.task_check_free_trial
@shared_task(expires=45)
def task_check_free_trial():
    print('Checking Free Trial...')
    morningCheckFreeTrial()

# Runs once everyday to check if there are any subscriptions to be updated
# SecureSign.celery.task_check_describers
@shared_task(expires=45)
def task_check_describers():
    print('Checking Personal Describers...')
    morningCheckDescribers()

# Runs once everyday to check if there are any subscriptions to be updated
# SecureSign.celery.task_check_describers_company
@shared_task(expires=45)
def task_check_describers_company():
    print('Checking Company Describers...')
    morningCheckDescribersCompany()

# Runs once everyday to check if there are any subscriptions to be updated
# SecureSign.celery.task_check_subscribers
@shared_task(expires=45)
def task_check_subscribers():
    print('Checking Personal Subscribers...')
    morningCheckSubscribers()

# Runs once everyday to check if there are any subscriptions to be updated
# SecureSign.celery.task_check_subscribers_company
@shared_task(expires=45)
def task_check_subscribers_company():
    print('Checking Company Subscribers...')
    morningCheckSubscribersCompany()

import datetime
from django.template.loader import render_to_string
from django.core import mail
from pytz import timezone
# Runs this task every hour to check if there are any documents to be sent (Reveals pointer to user)
# SecureSign.celery.task_check_document_alerts
@shared_task(expires=45)
def task_check_document_alerts():
    currentDate = datetime.datetime.now(timezone('UTC'))
    currentHour = currentDate.hour
    currentDate = str(currentDate.year) + '-' + str(currentDate.month) + '-' + str(currentDate.day)
    for each in DocumentModels.AlertActual.objects.filter(date=currentDate):
        if each.hour == currentHour:
            userID = each.userIDdocumentRequestID[:16]
            requestID = each.userIDdocumentRequestID[16:]

            numberOfDocumentsReceivedObj = DocumentModels.NumberOfDocumentsReceived.objects.get(pk=userID)
            numberOfDocumentsReceivedObj.documents += 1
            numberOfDocumentsReceivedObj.save()

            keyToKey = userID + '_' + str(numberOfDocumentsReceivedObj.documents)
            documentReceived = DocumentModels.DocumentsReceived(userIDNonce=keyToKey, documentKey=requestID)
            documentReceived.save()
            
            thisEmail = AccountModels.AccountLookupByID.objects.get(pk=userID).email
            document = DocumentModels.Document.objects.get(pk=requestID)
            sentFromUserID = document.createdBy
            thisPermission = document.associatedWith[thisEmail]
            sentFromUser = AccountModels.AccountLookupByID.objects.get(pk=sentFromUserID)
            sentFromUserEmail = sentFromUser.email
            sentFromUser = AccountModels.Account.objects.get(pk=sentFromUserEmail)
            sentFromUsername = sentFromUser.username
            sentFromUser = sentFromUsername + ' at email address ' + sentFromUserEmail

            if thisPermission == 'sign':
                subject = sentFromUsername + ' has requested that you sign a document'
                text_content = sentFromUser + ' has requested that you sign a document at IrisDocuments.com'
                if each.newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':userID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':userID})
            elif thisPermission == 'edit':
                subject = sentFromUsername + ' has requested that you edit a document'
                text_content = sentFromUser + ' has requested that you edit a document at IrisDocuments.com'
                if each.newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':userID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':userID})
            elif thisPermission == 'view':
                subject = sentFromUsername + ' has requested that you view a document'
                text_content = sentFromUser + ' has requested that you view a document at IrisDocuments.com'
                if each.newAcc:
                    html_content = render_to_string('email.html', {'text':text_content, 'requestID':requestID, 'userID':userID})
                else:
                    html_content = render_to_string('emailverified.html', {'text':text_content, 'requestID':requestID, 'userID':userID})

            with mail.get_connection() as thisConnection:
                email = mail.EmailMultiAlternatives(subject, text_content, 'notify@alerts.irisdocuments.com', [thisEmail], connection=thisConnection)
                email.attach_alternative(html_content, 'text/html')
                email.send()
            
            # Delete the Document Alert
            each.delete()

from UserDashboard import models as UserDashboardModels
# Alerts not implemented in this version
# SecureSign.celery.task_check_alerts
@shared_task(expires=45)
def task_check_alerts():
    currentDate = datetime.date()
    currentHour = datetime.datetime.now().hour
    for each in UserDashboardModels.Alert.objects.filter(date=currentDate):
        if each.hour == currentHour:
            userID = each.userID
            
            userAlerts = UserDashboardModels.ShowAlerts.objects.get(pk=userID)
            userAlerts.alert1 = each.alert
            userAlerts.alert2 = userAlerts.alert1
            userAlerts.alert3 = userAlerts.alert2
            userAlerts.new = True
            userAlerts.save()