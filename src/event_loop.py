
from socket import socket, AF_INET, SOCK_STREAM
from Exceptions import UserNotInFriend
from kivy.uix.screenmanager import ScreenManagerException

import threading, time
import json, types_

events = []


class Event(object):
    __slots__ = ("type", "content")

    def __init__(self, type, content):
        self.type = type
        self.content = content

    def getEventContent(self): return self.content


class ClientSocketHandler(socket):
    __slots__ = ("_connection", "hp", "connectionRecoveryThread")

    def __init__(self, host: str, port: int):
        self.hp = (host, port)
        self._connection = False
        self.connectionRecoveryThread = False

        socket.__init__(self, AF_INET, SOCK_STREAM)

    def connection(self, instance: object):
        self.connectionRecoveryThread = True
        self._connection = False
        while not self._connection:
            try:
                self.connect(self.hp)
                self._connection = True; instance.break_loop = False
            except (ConnectionRefusedError, OSError) as exception: pass

        self.connectionRecoveryThread = False


def errorСhecking(method):
    def _errorChecking(*arguments, **kwargs):
        instance, socketInstance, *args = arguments
        try:
            method(*arguments, **kwargs)

        except (ConnectionAbortedError, ConnectionResetError, OSError):
            connectionErrorEvent = Event(type=types_.сonnectionError_t, content=None)
            if connectionErrorEvent not in events:
                events.append(connectionErrorEvent)

            if not socketInstance.connectionRecoveryThread:
                instance._startServerEventLoop(*socketInstance.hp)

    return _errorChecking


class EventLoop(object):
    @errorСhecking
    def connectionResponsHandler(self, firstSocket, json_loads=True):
        responseContent = "\r"
        while responseContent[-1] != "\0":
            response = firstSocket.recv(1024).decode()
            responseContent += response
            time.sleep(0.0001)

        if json_loads:
            response = (
                json.loads(responseContent[1:-1])
                if json_loads else responseContent[1:-1]
            )
            if response.get('code') > 200:
                responseContent, response = "", ""
                self.lockRequest = False
                return

        events.append(Event(type=response["type"],
                            content=response["content"]))

        responseContent, response = "", ""

    @errorСhecking
    def requestHandler(self, socket, request):
        if not request: return
        socket.send((json.dumps(request) + '\0').encode())


    def eventHandler(self, instance):
        for event in events:
            match event.type:
                case types_.сonnectionError_t:
                    self.lockRequest = False
                    events.remove(event)
                    if not self.dialogOpen:
                        self.connectionLossWarningDialog()
                        self.dialogOpen = True
                        self.online = False

                case types_.singinData_t:
                    self.lockRequest = False
                    events.remove(event)
                    content = event.getEventContent()
                    if content is not None and content.get('singin'):
                        username, friends, image, unsent_messages = (
                            content.get("username"), content.get("friends"),
                            content.get("image"), content.get("unsent-messages"))

                        self.accountData = (self.username, self.password)
                        _friends = ""
                        for friendname, friendimage in friends:
                            _friends += f"User_widget:{friendname}:Best Messenger:" \
                                        f"{self.createImagefile(friendimage)}\n"

                        self.setAccountInformation(username, _friends, self.createImagefile(image))
                        if unsent_messages:
                            for sender_name, messages in unsent_messages.items():
                                for message in messages:
                                    try: self.receiveMessage(message, sender_name)
                                    except ScreenManagerException:
                                        self.appendChatScreen(sender_name)
                                        self.receiveMessage(message, sender_name)

                        self.get_main_screen()
                        self.login = True

                case types_.singupData_t:
                    self.lockRequest = False
                    events.remove(event)
                    content = event.getEventContent()
                    if content is not None and content.get('singup'):
                        self.accountData = (self.username, self.password)
                        self.setAccountInformation(
                            self.username, None,
                            self.createImagefile(self.image_baytes_base64)
                        )
                        self.get_main_screen()

                case types_.appendUser_t:
                    self.lockRequest = False
                    events.remove(event)
                    content = event.getEventContent()
                    username, messageText, image = (
                        content.get("username"),
                        content.get("message-text"), content.get("image")
                    )
                    self.addingFriends(f"User_widget:{username}:{messageText}:"
                                       f"{self.createImagefile(image)}\n")

                    for action in self.beforeIterate:
                        if action.get("type") == "receiveMessage":
                            content = action.get("content")
                            messageText = content.get("message")
                            chatName = content.get("chatName")

                            self.receiveMessage(messageText, chatName)
                            self.beforeIterate.remove(action)

                        elif action.get("type") == "appendListMessageAndChat":
                            content = action.get("content")
                            chatName = content.get("chatName")
                            messages = content.get("messages")
                            for message in messages:
                                self.receiveMessage(message, chatName)

                            self.beforeIterate.remove(action)

                case types_.removeFriend_t:
                    self.lockRequest = False
                    events.remove(event)
                    content = event.getEventContent()
                    if content and content.get("remove-username"):
                        self.screen_manager.get_screen(
                            "main_screen").ids.listusers.remove_widget(self.removed_user_widget)

                        try:
                            self.screen_manager.remove_widget(
                                self.screen_manager.get_screen(
                                    f"chat|{content.get('remove-username')}"
                                )
                            )
                        except ScreenManagerException: pass

                        if content.get("remove-username") in self.ids:
                            self.ids.pop(content.get("remove-username"))

                        if content.get("remove-username") in self.loads:
                            self.loads.remove(content.get("remove-username"))

                case types_.requestSendMessage_t:
                    self.lockRequest = False
                    events.remove(event)
                    content = event.getEventContent()
                    if content:
                        sender_name, message_text = (
                            content.get("sender"), content.get("message-text"))

                        try:
                            if sender_name in self.ids:
                                self.receiveMessage(message_text, sender_name)
                            else:
                                raise UserNotInFriend

                        except (ScreenManagerException, UserNotInFriend):
                            self.beforeIterate.append(
                                {
                                    "type": "receiveMessage",
                                    "content": {
                                        "message": message_text,
                                        "chatName": sender_name
                                    }
                                }
                            )
                            self.appendChatScreen(sender_name)
                            if sender_name not in self.ids:
                                self.appendUserInFriend(sender_name)

                case types_.listMessageData_t:
                    self.lockRequest = False
                    events.remove(event)
                    for messageData in event.getEventContent():
                        if types_.messageData_t in messageData:
                            messages = messageData[types_.messageData_t]["Message"]
                            chatName = messageData[types_.messageData_t]["Chat"]
                            try:
                                if chatName in self.ids:
                                    for message in messages:
                                        self.receiveMessage(message, chatName)
                                else: raise UserNotInFriend

                            except ScreenManagerException:
                                self.appendChatScreen(chatName)
                                if chatName not in self.ids:
                                    self.appendUserInFriend(chatName)

                                for message in messages:
                                    self.receiveMessage(message, chatName)

                            except UserNotInFriend:
                                self.beforeIterate.append(
                                    {
                                        "type": "appendListMessageAndChat",
                                        "content": {
                                            "messages": messages,
                                            "chatName": chatName
                                        }
                                    }
                                )
                                self.appendChatScreen(chatName)
                                if chatName not in self.ids:
                                    self.appendUserInFriend(chatName)

                case types_.messageNotSend_t:
                    self.lockRequest = False
                    if self.login:
                        for messageRequest in self.messageNotSend:
                            self.requestHandler(self.secondSocket, messageRequest)
                            time.sleep(0.01)

                        self.messageNotSend.clear()
                        events.remove(event)

                    self.login = False

                case types_.updateUserImage_t:
                    self.lockRequest = False
                    events.remove(event)
                    content = event.getEventContent()
                    if content:
                        username, image = content.get("username"), content.get("image")
                        if username in self.ids:
                            self.ids[username][1].source = self.createImagefile(image)


                case types_.userExists_t:
                    self.lockRequest = False
                    self.userExistsWarningDialog()
                    events.remove(event)

                case types_.userNotExists_t:
                    self.lockRequest = False
                    self.userNotExistsWarningDialog()
                    events.remove(event)

                case types_.userAdded_t:
                    self.lockRequest = False
                    self.userAddedWarningDialog()
                    events.remove(event)

                case None: events.remove(event)

    def _startServerEventLoop(self, host, port):
        self.break_loop = False
        self.login = False
        self.beforeIterate = []

        self.firstSocket = ClientSocketHandler(host, port)
        self._threadListenSocket(self.firstSocket)

    def _threadListenSocket(self, socket):
        if not socket.connectionRecoveryThread:
            socket.connection(self)
            if not self.online and self.accountData:
                self.online = True
                self.getLogin(usernamePassword=self.accountData)
                events.append(Event(type=types_.messageNotSend_t,
                                    content=None))

            while not self.break_loop:
                self.connectionResponsHandler(socket)

    def startServerEventLoop(self):
        threading.Thread(target=self._startServerEventLoop,
            args=("localhost", 5000), daemon=True).start()
