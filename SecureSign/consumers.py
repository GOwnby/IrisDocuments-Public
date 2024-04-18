from django.conf import settings

from channels.generic.websocket import AsyncJsonWebsocketConsumer
#from asgiref.sync import sync_to_async
import asyncio
from channels.db import database_sync_to_async
import re

from Home.exceptions import ClientError
from Home.utils import get_room_or_error
from Home.utils import get_OpenRoom_or_error
from Home import models

class AlertSupportAgent(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        await self.accept()
        # Store which rooms the user has joined on this connection
        self.rooms = set()

    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        #loop = asyncio.get_event_loop()
        #try:
            #loop.run_until_complete(self.receiveFunction(content))
        #finally:
            #loop.close()
        await self.receiveFunction(content)

    async def receiveFunction(self, content):
        # Messages will have a "command" key we can switch on, otherwise its a force disconnect all users from a room
        command = content.get("command", None)

        if command is not None:
            userNum = int(command)

            loopStart = (userNum * 10) - 9
            loopEnd = loopStart + 9
            while loopStart <= loopEnd:
                if await self.getSupportRoomUserJoinedImmediate(loopStart):
                    await self.send_json({"new":str(loopStart)})
                    await self.setSupportRoomUserJoinedImmediateFalse(loopStart)
                loopStart += 1
        else:
            disconnect = content.get("dc", None)
            roomID = int(disconnect)

            await self.setSupportRoomForceDisconnectTrue(roomID)
            await self.setSupportRoomUserJoinedFalse(roomID)

    @database_sync_to_async
    def getSupportRoomUserJoined(self, roomID):
        return models.SupportRoom.objects.get(pk=roomID).userJoined

    @database_sync_to_async
    def getSupportRoomUserJoinedImmediate(self, roomID):
        return models.SupportRoom.objects.get(pk=roomID).userJoinedImmediate

    @database_sync_to_async
    def setSupportRoomUserJoinedFalse(self, roomID):
        room = models.SupportRoom.objects.get(pk=roomID)
        room.userJoined = False
        room.save()
    
    @database_sync_to_async
    def setSupportRoomUserJoinedImmediateFalse(self, roomID):
        room = models.SupportRoom.objects.get(pk=roomID)
        room.userJoinedImmediate = False
        room.save()

    @database_sync_to_async
    def setSupportRoomForceDisconnectTrue(self, roomID):
        room = models.SupportRoom.objects.get(pk=roomID)
        room.forceDisconnect = True
        room.save()

        

class RoomManagementDaemon(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        await self.accept()
        # Store which rooms the user has joined on this connection
        self.rooms = set()

    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        #loop = asyncio.get_event_loop()
        #try:
            #loop.run_until_complete(self.receiveFunction(content))
        #finally:
            #loop.close()
        await self.receiveFunction(content)

    async def receiveFunction(self, content):
        """
        Called by receive_json when a message is received, function and websocket and kept running until this function returns a response
        """
        try:
            queueObj = await self.getQueueObj()
        except Exception:
            await self.createQueueObj()
            queueObj = await self.getQueueObj()

        # Messages will have a "command" key we can switch on, otherwise its a ready check
        command = content.get("command", None)

        if command is not None:
            if command == "join":
                if await self.getQueueIsOpen():
                    await self.incrementNumQueued()
                    try:
                        chatUserObj = await self.getChatUserNewObj()
                    except Exception:
                        await self.createChatUserObj()
                        chatUserObj = await self.getChatUserNewObj()
                    await self.setChatUserTrue()

                    await self.send_json({"queue":str(await self.getQueueNumQueued())})
                else:
                    count = 1
                    end = await self.getQueueObjAgentsAvailable()
                    end = end * 10
                    continueLoop = True
                    # Find Support agent with least number of connected users for this user to connect to 
                    least = 10
                    connectToAgent = 0
                    while (count <= end):
                        try:
                            connectedUsers = await self.getQueueObjAgentInfo(str(count))
                            if connectedUsers < least:
                                least = connectedUsers
                                connectToAgent = count
                            count += 1
                        except Exception:
                            if connectToAgent == 0:
                                continueLoop = False
                            break

                    if connectToAgent != 0:
                        end = connectToAgent * 10
                        count = end - 9

                    while (count <= end) and continueLoop:
                        if not await self.getSupportRoomUserJoined(count) and await self.getSupportRoomObjRoomActive(count):
                            await self.send_json({"join":str(count)})
                            await self.setSupportRoomUserJoinedTrue(count)
                            await self.setSupportRoomUserJoinedImmediateTrue(count)
                            continueLoop = False
                        count += 1

                    if continueLoop:
                        await self.openQueue()
                        await self.setQueue()
                        try:
                            chatUserObj = await self.getChatUserNewObj()
                        except Exception:
                            await self.createChatUserObj()
                        await self.setChatUserTrue()

                        await self.send_json({"queue":str(await self.getQueueNumQueued())})
            else:
                numUser = int(command)

                if numUser == 1:
                    enableShift = False
                    count = 1
                    end = await self.getQueueObjAgentsAvailable()
                    #end = end * 10
                    continueLoop = True
                    # Find Support agent with least number of connected users for this user to connect to 
                    least = 10
                    connectToAgent = 0
                    while (count <= end):
                        try:
                            connectedUsers = await self.getQueueObjAgentInfo(str(count))
                            if connectedUsers < least:
                                least = connectedUsers
                                connectToAgent = count
                            count += 1
                        except Exception:
                            if connectToAgent == 0:
                                continueLoop = False
                            break

                    if connectToAgent != 0:
                        end = connectToAgent * 10
                        count = end - 9

                    while (count <= end) and continueLoop:
                        if not await self.getSupportRoomUserJoined(count) and await self.getSupportRoomObjRoomActive(count):
                            await self.send_json({"join":str(count)})
                            await self.setSupportRoomUserJoinedTrue(count)
                            await self.setSupportRoomUserJoinedImmediateTrue(count)
                            enableShift = True
                            continueLoop = False
                        count += 1
                    # enableShift function turn on shift for all users and queue
                    if enableShift:
                        await self.enableQueueShift()
                        users = await self.getQueueNumQueued()
                        await self.decrementNumQueued()
                        count = 2
                        while count < users:
                            await self.setUserShiftTrue(count)
                            count += 1
                    else:
                        await self.send_json({"queue":"1"})
                elif await self.getQueueIsShift():
                    await self.incrementNumCount()
                    if await self.getQueueCount() == await self.getQueueNumQueued():
                        await self.resetCount()
                        await self.resetQueueShift()
                    
                    await self.resetChatUser(numUser)
                    await self.setChatUserTrue(numUser-1)

                    await self.send_json({"queue":str(numUser-1)})
                else:
                    await self.send_json({"queue":command})    
        else:
            # Catch any errors and send it back
            ready = content.get("ready", None)
            readyNum = int(ready)

            forceDisconnect = await self.getSupportRoomForceDisconnect(readyNum)
            if forceDisconnect:
                await self.setSupportRoomForceDisconnectFalse(readyNum)
                await self.send_json({"leave": ready})
            else:
                await self.send_json({"stay": ready})

    @database_sync_to_async
    def getQueueObj(self):
        return models.Queue.objects.get(pk=1)

    @database_sync_to_async
    def getQueueObjAgentsAvailable(self):
        return models.Queue.objects.get(pk=1).agentsAvailable

    @database_sync_to_async
    def getQueueObjAgentInfo(self, key):
        return models.Queue.objects.get(pk=1).agentInfo[key]

    @database_sync_to_async
    def setQueueObjAgentInfo(self, key, value):
        queue = models.Queue.objects.get(pk=1)
        queue.agentInfo[key] = value
        queue.save()

    @database_sync_to_async
    def getQueueCount(self):
        return models.Queue.objects.get(pk=1).count

    @database_sync_to_async
    def getQueueNumQueued(self):
        return models.Queue.objects.get(pk=1).numQueued

    @database_sync_to_async
    def getQueueIsOpen(self):
        return models.Queue.objects.get(pk=1).isOpen

    @database_sync_to_async
    def getQueueIsShift(self):
        return models.Queue.objects.get(pk=1).shift

    @database_sync_to_async
    def createQueueObj(self):
        queueObj = models.Queue(primaryKey=1)
        queueObj.save(self)

    @database_sync_to_async
    def openQueue(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.isOpen = True
        queueObj.save()
    
    @database_sync_to_async
    def setQueue(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.numQueued = 1
        queueObj.save()

    @database_sync_to_async
    def incrementNumCount(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.count += 1
        queueObj.save()

    @database_sync_to_async
    def incrementNumQueued(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.numQueued += 1
        queueObj.save()

    @database_sync_to_async
    def decrementNumQueued(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.numQueued -= 1
        queueObj.save()

    @database_sync_to_async
    def enableQueueShift(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.shift = True
        queueObj.save()

    @database_sync_to_async
    def resetQueueShift(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.shift = False
        queueObj.save()

    @database_sync_to_async
    def resetCount(self):
        queueObj = models.Queue.objects.get(pk=1)
        queueObj.count = 0
        queueObj.save()

    @database_sync_to_async
    def getChatUserObj(self, num):
        return models.ChatUser.objects.get(pk=num)

    @database_sync_to_async
    def getChatUserNewObj(self):
        queueObj = models.Queue.objects.get(pk=1)
        return models.ChatUser.objects.get(pk=queueObj.numQueued)

    @database_sync_to_async
    def createChatUserObj(self):
        queueObj = models.Queue.objects.get(pk=1)
        newObj = models.ChatUser(queueNum=queueObj.numQueued)
        newObj.save()

    @database_sync_to_async
    def setChatUserTrue(self, count):
        chatUserObj = models.ChatUser.objects.get(pk=count)
        chatUserObj.inUse = True
        chatUserObj.save()

    @database_sync_to_async
    def setNewChatUserTrue(self):
        queueObj = models.Queue.objects.get(pk=1)
        chatUserObj = models.ChatUser.objects.get(pk=queueObj.numQueued)
        chatUserObj.inUse = True
        chatUserObj.save()

    @database_sync_to_async
    def resetChatUser(self, count):
        chatUserObj = models.ChatUser.objects.get(pk=count)
        chatUserObj.inUse = False
        chatUserObj.shiftUser = False
        chatUserObj.save()

    @database_sync_to_async
    def setUserShiftTrue(self, count):
        chatUserObj = models.ChatUser.objects.get(pk=count)
        chatUserObj.shiftUser = True
        chatUserObj.save()

    @database_sync_to_async
    def getSupportRoomObj(self, roomID):
        return models.SupportRoom.objects.get(pk=roomID)

    @database_sync_to_async
    def getSupportRoomUserJoined(self, roomID):
        return models.SupportRoom.objects.get(pk=roomID).userJoined

    @database_sync_to_async
    def getSupportRoomForceDisconnect(self, roomID):
        return models.SupportRoom.objects.get(pk=roomID).forceDisconnect

    @database_sync_to_async
    def getSupportRoomObjRoomActive(self, roomID):
        return models.SupportRoom.objects.get(pk=roomID).roomActive

    @database_sync_to_async
    def setSupportRoomUserJoinedTrue(self, roomID):
        room = models.SupportRoom.objects.get(pk=roomID)
        room.userJoined = True
        room.save()

    @database_sync_to_async
    def setSupportRoomUserJoinedImmediateTrue(self, roomID):
        room = models.SupportRoom.objects.get(pk=roomID)
        room.userJoinedImmediate = True
        room.save()

    @database_sync_to_async
    def setSupportRoomForceDisconnectFalse(self, roomID):
        room = models.SupportRoom.objects.get(pk=roomID)
        room.forceDisconnect = False
        room.save()



class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Are they logged in?
        if self.scope["user"].is_anonymous:
            # Reject the connection
            await self.close()
        else:
            # Accept the connection
            await self.accept()
        # Store which rooms the user has joined on this connection
        self.rooms = set()

    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        command = content.get("command", None)
        try:
            if command == "join":
                # Make them join the room
                await self.join_room(content["room"])
            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room"])
            elif command == "send":
                await self.send_room(content["room"], content["message"])
        except ClientError as e:
            # Catch any errors and send it back
            await self.send_json({"error": e.code})

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        for room_id in list(self.rooms):
            try:
                await self.leave_room(room_id)
            except ClientError:
                pass

    ##### Command helper methods called by receive_json

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        room = await get_room_or_error(room_id, self.scope["user"])
        # Send a join message if it's turned on
        if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.join",
                    "room_id": room_id,
                    "username": self.scope["user"].username,
                }
            )
        # Store that we're in the room
        self.rooms.add(room_id)
        # Add them to the group so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish opening the room
        await self.send_json({
            "join": str(room.id),
            "title": room.title,
        })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        room = await get_room_or_error(room_id, self.scope["user"])
        # Send a leave message if it's turned on
        if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.leave",
                    "room_id": room_id,
                    "username": self.scope["user"].username,
                }
            )
        # Remove that we're in the room
        self.rooms.discard(room_id)
        # Remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish closing the room
        await self.send_json({
            "leave": str(room.id),
        })

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        # Check they are in this room
        if room_id not in self.rooms:
            raise ClientError("ROOM_ACCESS_DENIED")
        # Get the room and send to the group about it
        room = await get_room_or_error(room_id, self.scope["user"])
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "room_id": room_id,
                "username": self.scope["user"].username,
                "message": message,
            }
        )

    ##### Handlers for messages sent over the channel layer

    # These helper methods are named by the types we send - so chat.join becomes chat_join
    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_ENTER,
                "room": event["room_id"],
                "username": event["username"],
            },
        )

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_LEAVE,
                "room": event["room_id"],
                "username": event["username"],
            },
        )

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_MESSAGE,
                "room": event["room_id"],
                "username": event["username"],
                "message": event["message"],
            },
        )

class OpenChatConsumer(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        await self.accept()
        # Store which rooms the user has joined on this connection
        self.rooms = set()

    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        command = content.get("command", None)
        try:
            if command == "join":
                # Make them join the room
                await self.join_room(content["room"])
            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room"])
            elif command == "send":
                await self.send_room(content["room"], content["message"])
        except ClientError as e:
            # Catch any errors and send it back
            await self.send_json({"error": e.code})

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave all the rooms we are still in
        for room_id in list(self.rooms):
            try:
                await self.leave_room(room_id)
            except ClientError:
                pass

    ##### Command helper methods called by receive_json

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        room = await get_OpenRoom_or_error(room_id)
        await self.setUserJoinTrue(room_id)
        # Send a join message if it's turned on
        try:
            thisUsername = self.scope["user"].username
        except Exception:
            thisUsername = 'User'

        if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.join",
                    "room_id": room_id,
                    "username": thisUsername,
                }
            )
        # Store that we're in the room
        self.rooms.add(room_id)
        # Add them to the group so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish opening the room
        await self.send_json({
            "join": str(room.id),
            "title": room.title,
        })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        room = await get_OpenRoom_or_error(room_id)
        await self.setUserJoinFalse(room_id)
        # Send a leave message if it's turned on
        try:
            thisUsername = self.scope["user"].username
        except Exception:
            thisUsername = 'User'

        if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.leave",
                    "room_id": room_id,
                    "username": thisUsername,
                }
            )
        # Remove that we're in the room
        self.rooms.discard(room_id)
        # Remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish closing the room
        await self.send_json({
            "leave": str(room.id),
        })

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        # Check they are in this room
        if room_id not in self.rooms:
            raise ClientError("ROOM_ACCESS_DENIED")
        # Get the room and send to the group about it
        try:
            thisUsername = self.scope["user"].username
        except Exception:
            thisUsername = 'User'

        room = await get_OpenRoom_or_error(room_id)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "room_id": room_id,
                "username": thisUsername,
                "message": message,
            }
        )

    ##### Handlers for messages sent over the channel layer

    # These helper methods are named by the types we send - so chat.join becomes chat_join
    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        try:
            thisUsername = event["username"]
            searchAdmin = re.search(r'admin', thisUsername)
            searchSupportAgent = re.search(r'agent', thisUsername)
            if (searchAdmin is not None) or (searchSupportAgent is not None):
                thisUsername = 'Support'
            else:
                thisUsername = 'User'
        except Exception:
            thisUsername = 'User'

        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_ENTER,
                "room": event["room_id"],
                "username": thisUsername,
            },
        )

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        try:
            thisUsername = event["username"]
            searchAdmin = re.search(r'admin', thisUsername)
            searchSupportAgent = re.search(r'agent', thisUsername)
            if (searchAdmin is not None) or (searchSupportAgent is not None):
                thisUsername = 'Support'
            else:
                thisUsername = 'User'
        except Exception:
            thisUsername = 'User'

        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_LEAVE,
                "room": event["room_id"],
                "username": thisUsername,
            },
        )

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        try:
            thisUsername = event["username"]
            searchAdmin = re.search(r'admin', thisUsername)
            searchSupportAgent = re.search(r'agent', thisUsername)
            if (searchAdmin is not None) or (searchSupportAgent is not None):
                thisUsername = 'Support'
            else:
                thisUsername = 'User'
        except Exception:
            thisUsername = 'User'

        await self.send_json(
            {
                "msg_type": settings.MSG_TYPE_MESSAGE,
                "room": event["room_id"],
                "username": thisUsername,
                "message": event["message"],
            },
        )

    @database_sync_to_async
    def setUserJoinTrue(self, room_id):
        room = models.SupportRoom.objects.get(pk=room_id)
        room.userJoined = True
        room.userJoinedImmediate = True
        room.save()

    @database_sync_to_async
    def setUserJoinFalse(self, room_id):
        room = models.SupportRoom.objects.get(pk=room_id)
        room.userJoined = False
        room.userJoinedImmediate = False
        room.save()