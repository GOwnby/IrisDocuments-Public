from django.db import models
from django.db.models import JSONField

class Ticket(models.Model):
    key = models.IntegerField(primary_key=True, default=0)
    name = models.CharField(max_length=128)
    email = models.CharField(max_length=128)
    ticket = models.TextField()

class Tickets(models.Model):
    key = models.IntegerField(primary_key=True, default=1)
    tickets = models.IntegerField(default=0)

class Room(models.Model):
    """
    A room for people to chat in.
    """

    # Room title
    title = models.CharField(max_length=255)


    # If only "staff" users are allowed (is_staff on django's User)
    staff_only = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def group_name(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return "room-%s" % self.id

class SupportRoom(models.Model):
    """
    A room for people to chat in.
    """
    roomActive = models.BooleanField(default=True)
    forceDisconnect = models.BooleanField(default=False)

    # Room title
    title = models.CharField(max_length=255)

    userJoinedImmediate = models.BooleanField(default=False)
    userJoined = models.BooleanField(default=False)

    # If only "staff" users are allowed (is_staff on django's User)
    staff_only = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def group_name(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return "room-%s" % self.id

class Queue(models.Model):
    # Object primary key to find primary queue, always equals 1
    primaryKey = models.IntegerField(primary_key=True)

    isOpen = models.BooleanField(default=False)
    numQueued = models.IntegerField(default=0)
    shift = models.BooleanField(default=False)
    count = models.IntegerField(default=0)

    agentsAvailable = models.IntegerField(default=0)
    agentInfo = JSONField(default=dict())

class ChatUser(models.Model):
    queueNum = models.IntegerField(primary_key=True)
    inUse = models.BooleanField(default=False)
    shiftUser = models.BooleanField(default=False)