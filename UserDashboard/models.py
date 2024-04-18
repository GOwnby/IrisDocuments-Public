from time import time
from django.db import models

class Alert(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    date = models.DateField(auto_now=False)
    hour = models.IntegerField(default=0)
    alert = models.TextField(max_length=128, default='')

class ShowAlerts(models.Model):
    userID = models.CharField(primary_key=True, max_length=16, default='')
    alert1 = models.TextField(max_length=128, default='')
    alert2 = models.TextField(max_length=128, default='')
    alert3 = models.TextField(max_length=128, default='')
    new = models.BooleanField(default=False)