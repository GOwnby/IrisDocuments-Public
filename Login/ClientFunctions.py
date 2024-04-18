from reportlab.pdfgen.canvas import Canvas

import ManageDocument.models as DocumentModels
import CreateAccount.models as AccountModels

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_stamp_less_than(timestamp1, timestamp2):
    #Year=month-day:hour;minute+second[userID]_action
    #exampleActionStamp = '2021=12-30:23;59+59[1234567890123456]_1'
    if ( int( timestamp1[0] + timestamp1[1] + timestamp1[2] + timestamp1[3] ) ) < ( int( timestamp2[0] + timestamp2[1] + timestamp2[2] + timestamp2[3] ) ):
        return 1
    elif ( int( timestamp1[0] + timestamp1[1] + timestamp1[2] + timestamp1[3] ) ) == ( int( timestamp2[0] + timestamp2[1] + timestamp2[2] + timestamp2[3] ) ):
        if ( int( timestamp1[5] + timestamp1[6] ) ) < ( int( timestamp2[5] + timestamp2[6] ) ):
            return 1
        elif ( int( timestamp1[5] + timestamp1[6] ) ) == ( int( timestamp2[5] + timestamp2[6] ) ):
            if ( int( timestamp1[8] + timestamp1[9] ) ) < ( int( timestamp2[8] + timestamp2[9] ) ):
                return 1
            elif ( int( timestamp1[8] + timestamp1[9] ) ) == ( int( timestamp2[8] + timestamp2[9] ) ):
                if ( int( timestamp1[11] + timestamp1[12] ) ) < ( int( timestamp2[11] + timestamp2[12] ) ):
                    return 1
                elif ( int( timestamp1[11] + timestamp1[12] ) ) == ( int( timestamp2[11] + timestamp2[12] ) ):
                    if ( int( timestamp1[14] + timestamp1[15] ) ) < ( int( timestamp2[14] + timestamp2[15] ) ):
                        return 1
                    elif ( int( timestamp1[14] + timestamp1[15] ) ) == ( int( timestamp2[14] + timestamp2[15] ) ):
                        if ( int( timestamp1[17] + timestamp1[18] ) ) < ( int( timestamp2[17] + timestamp2[18] ) ):
                            return 1
                        else:
                            return 0
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    return 0

def add_action_to_audit(canvas, nextX, nextY, document, actionTimestamp, actionIP):
    #exampleActionStamp = '2021=12-30:23;59+59[1234567890123456]_1'
    #newExample = '2021=12-30:23;59+59[1234567890]1'
    #example3 = '20211230235959123456789012345671' added 1 digit to userID
    actionUser = (actionTimestamp[20] + actionTimestamp[21] + actionTimestamp[22] + actionTimestamp[23] + actionTimestamp[24]
        + actionTimestamp[25] + actionTimestamp[26] + actionTimestamp[27] + actionTimestamp[28] + actionTimestamp[29]
        + actionTimestamp[30] + actionTimestamp[31] + actionTimestamp[32] + actionTimestamp[33] + actionTimestamp[34]
        + actionTimestamp[35])

    actionUserEmail = (AccountModels.AccountLookup.objects.get(pk=actionUser)).email
    actionUserObject = AccountModels.Account.objects.get(pk=actionUserEmail)
    actionUsername = actionUserObject.username
    action = actionTimestamp[38]
    
    date = ''

    month = actionTimestamp[5] + actionTimestamp[6]
    if month == '01':
        date += 'January '
    elif month == '02':
        date += 'February '
    elif month == '03':
        date += 'March '
    elif month == '04':
        date += 'April '
    elif month == '05':
        date += 'May '
    elif month == '06':
        date += 'June '
    elif month == '07':
        date += 'July '
    elif month == '08':
        date += 'August '
    elif month == '09':
        date += 'September '
    elif month == '10':
        date += 'October '
    elif month == '11':
        date += 'November '
    elif month == '12':
        date += 'December '

    day = actionTimestamp[8] + actionTimestamp[9]
    if day == '01':
        date += '1st, '
    elif day == '02':
        date += '2nd, '
    elif day == '03':
        date += '3rd, '
    elif day == '04':
        date += '4th, '
    elif day == '05':
        date += '5th, '
    elif day == '06':
        date += '6th, '
    elif day == '07':
        date += '7th, '
    elif day == '08':
        date += '8th, '
    elif day == '09':
        date += '9th, '
    elif day == '10':
        date += '10th, '
    elif day == '11':
        date += '11th, '
    elif day == '12':
        date += '12th, '
    elif day == '13':
        date += '13th, '
    elif day == '14':
        date += '14th, '
    elif day == '15':
        date += '15th, '
    elif day == '16':
        date += '16th, '
    elif day == '17':
        date += '17th, '
    elif day == '18':
        date += '18th, '
    elif day == '19':
        date += '19th, '
    elif day == '20':
        date += '20th, '
    elif day == '21':
        date += '21st, '
    elif day == '22':
        date += '22nd, '
    elif day == '23':
        date += '23rd, '
    elif day == '24':
        date += '24th, '
    elif day == '25':
        date += '25th, '
    elif day == '26':
        date += '26th, '
    elif day == '27':
        date += '27th, '
    elif day == '28':
        date += '28th, '
    elif day == '29':
        date += '29th, '
    elif day == '30':
        date += '30th, '
    elif day == '31':
        date += '31st, '

    date += (actionTimestamp[0] + actionTimestamp[1] + actionTimestamp[2] + actionTimestamp[3])

    time = ''
    hour = actionTimestamp[11] + actionTimestamp[12]
    if hour == '00':
        time += '12:xx am'
    elif hour == '01':
        time += '01:xx am'
    elif hour == '02':
        time += '02:xx am'
    elif hour == '03':
        time += '03:xx am'
    elif hour == '04':
        time += '04:xx am'
    elif hour == '05':
        time += '05:xx am'
    elif hour == '06':
        time += '06:xx am'
    elif hour == '07':
        time += '07:xx am'
    elif hour == '08':
        time += '08:xx am'
    elif hour == '09':
        time += '09:xx am'
    elif hour == '10':
        time += '10:xx am'
    elif hour == '11':
        time += '11:xx am'
    elif hour == '12':
        time += '12:xx pm'
    elif hour == '13':
        time += '01:xx pm'
    elif hour == '14':
        time += '02:xx pm'
    elif hour == '15':
        time += '03:xx pm'
    elif hour == '16':
        time += '04:xx pm'
    elif hour == '17':
        time += '05:xx pm'
    elif hour == '18':
        time += '06:xx pm'
    elif hour == '19':
        time += '07:xx pm'
    elif hour == '20':
        time += '08:xx pm'
    elif hour == '21':
        time += '09:xx pm'
    elif hour == '22':
        time += '10:xx pm'
    elif hour == '23':
        time += '11:xx pm'
    
    minute = actionTimestamp[14] + actionTimestamp[15]
    tryMinute = 0
    while tryMinute < 61:
        stringTryMinute = str(tryMinute)
        if len(tryMinute) == 1:
            time[3] = '0'
            time[4] = stringTryMinute
        elif len(tryMinute) == 2:
            time[3] = stringTryMinute[0]
            time[4] = stringTryMinute[1]
        tryMinute += 1

    if time[0] == '0':
        time = time[1] + time[2] + time[3] + time[4] + time[5] + time[6] + time[7]

    actionString = ''
    if action == 1:
        actionString = 'Document sent to ' + actionUsername + ' (' + actionUserEmail + ')'
    elif action == 2:
        actionString = 'Document viewed by ' + actionUsername + ' (' + actionUserEmail + ')'
    elif action == 3:
        actionString = 'Document signed by ' + actionUsername + ' (' + actionUserEmail + ')'

    canvas.drawString(nextX, nextY, actionString)
    nextX += 468
    canvas.drawString(nextX, nextY, date)
    nextX -= 468

    nextY -= 10
    canvas(nextX, nextY, actionIP)
    nextX += 468
    canvas(nextX, nextY, time)
    canvas -= 10
    canvas(nextX, nextY, 'Datacenter: United States / North Virginia 1')

def generate_audit(request, documentRequestID):
    document = DocumentModels.Document.objects.get(pk=documentRequestID)
    fileName = documentRequestID + 'audit.pdf'
    canvas = Canvas(fileName, pagesize=(612.0, 792.0))

    canvas.drawString(72, 594, 'Document Created')
    canvas.drawString(72, 584, 'Fingerprint:' + document.fingerprintCreated)
    canvas.drawString(540, 594, document.dateCreatedBy[document.createdBy])
    canvas.drawString(540, 584, document.timeCreatedBy[document.createdBy])
    canvas.drawString(540, 574, 'Datacenter: United States / North Virginia 1')
    
    actionTimestamps = []
    actionIPs = {}
    
    stamp = 0

    count = 0 
    while True:
        try:
            timestampAdded = document.timeAddedTo[count]
            count += 1
            actionTimestamps[stamp] = timestampAdded
            stamp += 1
            actionIP = document.actionAtIPList[timestampAdded]
            actionIPs[timestampAdded] = actionIP
        except Exception:
            break

    count = 0
    while True:
        try:
            timestampViewed = document.timeViewedBy[count]
            count += 1
            actionTimestamps[stamp] = timestampViewed
            stamp += 1
            actionIP = document.actionAtIPList[timestampViewed]
            actionIPs[timestampViewed] = actionIP
        except Exception:
            break

    count = 0
    while True:
        try:
            timestampSigned = document.timeSignedBy[count]
            count += 1
            actionTimestamps[stamp] = timestampSigned
            stamp += 1
            actionIP = document.actionAtIPList[timestampSigned]
            actionIPs[timestampSigned] = actionIP
        except Exception:
            break    
    
    orderedTimestamps = []
    count = 0
    numberTimeStamps = len(actionTimestamps)
    while count < numberTimeStamps:
        if count == 0:
            orderedTimestamps[count] = actionTimestamps[count]
        else:
            countOrder = 1
            while True:
                try:
                    if is_stamp_less_than(orderedTimestamps[count - countOrder], actionTimestamps[count]) > 0:
                        orderedTimestamps.insert( (count - countOrder + 1), actionTimestamps[count])
                        count += 1
                    countOrder += 1
                except Exception:
                    if is_stamp_less_than(orderedTimestamps[0], actionTimestamps[count]) == 0:
                        orderedTimestamps.insert(0, actionTimestamps[count])
                    break
        count += 1

    nextX = 72
    nextY = 524
    actionCount = 0
    actions = len(orderedTimestamps)
    while actionCount < actions:
        while nextY > 70:
            for timestamp in orderedTimestamps:
                add_action_to_audit(canvas, nextX, nextY, document, timestamp, actionIPs[timestamp])
                actionCount += 1
                nextY -= 50
        canvas.drawString(540, 20, 'Processed by IrisDocuments')
        canvas.showPage()
        nextY = 524
    