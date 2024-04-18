from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from . import models
import re
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from .models import Room
from .models import SupportRoom

def error_404_view(request, exception):
    return render(request, 'error_404.html')

def index(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    try: 
        userID = request.COOKIES.get('user')
        if len(userID) > 2:
            if mobile:
                template_name = "HomeV2AMPUser.html"
            else:
                template_name = "Homev2User.html"
            return render(request, template_name)
    except Exception:
        if mobile:
            template_name = "HomeAMP.html"
        else:
            template_name = "Homev2.html"
        return render(request, template_name)
    return render(request, 'Homev2.html')

@login_required
def Chat(request):
    # Get a list of rooms, ordered alphabetically
    rooms = Room.objects.order_by("title")

    # Render that in the index template
    return render(request, "chatPage.html", {
        "rooms": rooms,
    })

@login_required
def OpenChat(request):
    # Checks if the admin users has already logged in and set the cookie to its number and is refreshing the page
    previouslyConnected = request.COOKIES.get('SupportUser')

    # Hasnt connected
    if previouslyConnected == 'Not Connected':
        try:
            queueObj = models.Queue.objects.get(pk=1)
        except Exception:
            queueObj = models.Queue(primaryKey=1)
        queueObj.agentInfo[queueObj.agentsAvailable + 1] = 0
        queueObj.agentsAvailable += 1
        queueObj.save()
    
        userNum = queueObj.agentsAvailable
        loopStart = (userNum * 10) - 9
        loopEnd = loopStart + 9
        rooms = []
        while loopStart <= loopEnd:
            try:
                thisRoom = SupportRoom.objects.get(pk=loopStart)
            except Exception:
                thisRoom = SupportRoom(pk=loopStart)
                thisRoom.title = "room" + str(loopStart)
                thisRoom.save()
            rooms.append(thisRoom)
            loopStart += 1

        # Render that in the index template
        response = render(request, "OpenChat.html", {"rooms": rooms, "numUser":str(userNum)})
        response.set_cookie('SupportUser', str(userNum))
    else: # Has connected (refresh or returned without logging out or returned to landing page)
        userNum = int(previouslyConnected)
        loopStart = (userNum * 10) - 9
        loopEnd = loopStart + 9
        rooms = []
        while loopStart <= loopEnd:
            try:
                thisRoom = SupportRoom.objects.get(pk=loopStart)
                thisRoom.roomActive = True
            except Exception:
                thisRoom = SupportRoom(pk=loopStart)
                thisRoom.title = "room" + str(loopStart)
            thisRoom.save()
            rooms.append(thisRoom)
            loopStart += 1

        # Render that in the index template
        response = render(request, "OpenChat.html", {"rooms": rooms, "numUser":str(userNum)})
        response.set_cookie('SupportUser', str(userNum))
    return response

@login_required
def CloseChat(request):
    userNum = request.COOKIES.get('SupportUser')
    loopStart = (userNum * 10) - 9
    loopEnd = loopStart + 9
    while loopStart <= loopEnd:
        thisRoom = SupportRoom.objects.get(pk=loopStart)
        thisRoom.roomActive = False
        thisRoom.save()
        loopStart += 1
    
    return HttpResponseRedirect("/admin/")

def OpenPublicChat(request):
    # Get a list of rooms, ordered alphabetically
    rooms = SupportRoom.objects.order_by("title")

    # Render that in the index template
    return render(request, "OpenPublicChat.html", {
        "rooms": rooms,
    })

def Contact(request):
    return render(request, 'Contact.html')

def Terms(request):
    return render(request, 'Terms.html')

def GettingStarted(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    try: 
        if mobile:
            template_name = "GettingStartedAMP.html"
        else:
            template_name = "GettingStarted.html"
        return render(request, template_name)
    except Exception:
        if mobile:
            template_name = "GettingStartedAMP.html"
        else:
            template_name = "GettingStarted.html"
        return render(request, template_name)

def TutorialDocumentSending(request):
    return render(request, 'TutorialDocumentSending.html')

def TutorialTemplateCreation(request):
    return render(request, 'TutorialTemplateCreation.html')

def FreeForSigners(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    try: 
        if mobile:
            template_name = "FreeForSignersAMP.html"
        else:
            template_name = "FreeForSigners.html"
        return render(request, template_name)
    except Exception:
        if mobile:
            template_name = "FreeForSignersAMP.html"
        else:
            template_name = "FreeForSigners.html"
        return render(request, template_name)

def PlansAndPricing(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    try: 
        if mobile:
            template_name = "PlansAndPricingAMP.html"
        else:
            template_name = "NewPlansAndPricing.html"
        return render(request, template_name)
    except Exception:
        if mobile:
            template_name = "PlansAndPricingAMP.html"
        else:
            template_name = "NewPlansAndPricing.html"
        return render(request, template_name)

def NewCompanySignup(request):
    return render(request, 'NewCompanySignup.html')

def Showcase(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    if mobile:
        return render(request, 'ShowcaseAMP.html')
    return render(request, 'Showcase.html')

def FAQ(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    if mobile:
        return render(request, 'FAQAMP.html')
    return render(request, 'FAQ.html')

def SubmitTicket(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        ticket = request.POST['ticket']

        try:
            tickets = models.Tickets.objects.get(pk=1)
        except Exception:
            tickets = models.Tickets()

        if re.search(r'^https?:\/\/.*[\r\n]*', ticket, re.MULTILINE) is None:
            tickets.tickets += 1
            tickets.save()

            ticket = models.Ticket(key=tickets.tickets,name=name,email=email,ticket=ticket)
            ticket.save()

    return HttpResponseRedirect('/TicketSent/')

def TicketSent(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()

    mobile = False
    if ua.find("iphone") > 0:
        mobile = True

    if ua.find("android") > 0:
        mobile = True

    try: 
        userID = request.COOKIES.get('user')
        if len(userID) > 2:
            if mobile:
                template_name = "HomeV2AMPUserTicketSent.html"
            else:
                template_name = "Homev2UserTicketSent.html"
            return render(request, template_name)
    except Exception:
        if mobile:
            template_name = "HomeAMPTicketSent.html"
        else:
            template_name = "Homev2TicketSent.html"
        return render(request, template_name)
    return render(request, 'Homev2TicketSent.html')