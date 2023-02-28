import asyncio
import pickle
import base64
import json
import sys
import time

from db.jsondbms import DbmsJson

from src.config import types
from src.config.responses import *



class RequestHandler:
    async def handlerRequestReceivedClient(self,
                                           clientRequest,
                                           StreamReaderSocket, StreamWriterSocket):

        clientRequest = json.loads(clientRequest)
        match clientRequest.get("type"):
            case types.singinData_t if clientRequest.get("content"):
                _username = None
                clientRequestContent = clientRequest.get("content")
                clientResponse = unsuccessfulLogin
                clientData = self.getContentValue(
                    clientRequestContent, "login", "password", "token")

                if None not in clientData:
                    username, password, token = clientData
                    _db_response = self.db.checkForPresenceDatabase(username, password)
                    if not _db_response or username in self.online_users:
                        return None, (json.dumps(clientResponse) + "\0").encode()

                    _username = username
                    clientResponse = appendFieldResponse(
                        successfulLogin, {
                            "content": {
                                "username": username,
                                "image": self.db.getUserData(username)["image"],
                                "unsent-messages": self.unsent_messages.get(username),
                                "friends": [
                                    (friendname, self.db.getUserData(friendname)["image"])
                                    for friendname in self.db.getUserData(username)["friends"]
                                ]
                            }
                        }
                    )
                    self.online_users[username] =(StreamReaderSocket,
                                                  StreamWriterSocket, token)

                    try: self.unsent_messages.pop(username)
                    except KeyError: pass

                return _username, (json.dumps(clientResponse) + "\0").encode()

            case types.singupData_t if clientRequest.get("content"):
                clientResponse = badRequest
                clientRequestContent = clientRequest.get("content")
                clientData = self.getContentValue(
                    clientRequestContent, "username", "password", "surname", "token")

                _username = None
                if None not in clientData:
                    username, password, surname, token = clientData
                    _db_response = self.db.checkForPresenceDatabase(username)
                    if not _db_response:
                        _username = username
                        self.db.appendUserInDataBase(username, surname, password)
                        clientResponse = appendFieldResponse(
                            successfulRegistration, {"content": {"username": username}})

                        self.online_users[username] = (StreamReaderSocket,
                                                       StreamWriterSocket, token)


                return _username, (json.dumps(clientResponse) + "\0").encode()

            case types.searchFriend_t if clientRequest.get("content"):
                clientRequestContent = clientRequest.get("content")
                clientResponse = badRequest
                clientData = self.getContentValue(
                        clientRequestContent, "username", "search-username", "token")

                if None not in clientData:
                    username, searchusername, token, *_ = clientData
                    try:
                        if self.online_users[username][2] == token:
                            existuser, existsearchuser = (
                                self.db.checkForPresenceDatabase(username),
                                self.db.checkForPresenceDatabase(searchusername)
                            )
                            if not existuser:
                                clientResponse = badRequest
                            elif not existsearchuser:
                                clientResponse = userNotExists
                            else:
                                if searchusername in self.db.getUserData(username)["friends"]:
                                    clientResponse = userAdded

                                else: clientResponse = userExists

                    except KeyError: pass

                return None, (json.dumps(clientResponse) + "\0").encode()

            case types.appendUser_t if clientRequest.get("content"):
                clientResponse = badRequest
                clientRequestContent = clientRequest.get("content")
                clientData = self.getContentValue(
                    clientRequestContent, "username", "append-username", "token")

                if None not in clientData:
                    username, append_username, token, *_ = clientData
                    try:
                        if self.online_users[username][2] == token:
                            if (self.db.checkForPresenceDatabase(username) and
                                self.db.checkForPresenceDatabase(append_username)):

                                self.db.getUserData(username)["friends"].append(append_username)
                                self.db.updatedb()
                                clientResponse = appendFieldResponse(
                                    appendUser, {
                                        "content": {
                                            "username": append_username,
                                            "message-text": "Best Messanger",
                                            "image": self.db.getUserData(append_username)["image"]
                                        }
                                    }
                                )

                    except KeyError: pass

                return None, (json.dumps(clientResponse) + "\0").encode()

            case types.removeFriend_t if clientRequest.get("content"):
                clientResponse = badRequest
                clientRequestContent = clientRequest.get("content")
                clientData = self.getContentValue(
                    clientRequestContent, "username", "remove-username", "token")

                if None not in clientData:
                    username, remove_username, token, *_ = clientData
                    try:
                        if self.online_users[username][2] == token:
                            if (self.db.checkForPresenceDatabase(username) and
                                self.db.checkForPresenceDatabase(remove_username)):

                                try:
                                    self.db.getUserData(username)["friends"].remove(remove_username)
                                    self.db.updatedb()
                                    clientResponse = {
                                        "type": types.removeFriend_t, "code": 200,
                                        "content": {
                                            "remove-username": remove_username
                                        }
                                    }

                                except ValueError: pass

                    except KeyError: pass

                return None, (json.dumps(clientResponse) + "\0").encode()

            case types.newProfileImage_t if clientRequest.get("content"):
                clientRequestContent = clientRequest.get("content")
                clientData = self.getContentValue(clientRequestContent, "username", "image", "token")
                clientResponse = badRequest

                if None not in clientData:
                    username, image, token = clientData
                    try:
                        if self.online_users[username][2] == token:
                            if self.db.checkForPresenceDatabase(username):
                                self.db.getUserData(username)["image"] = image
                                self.db.updatedb()

                                for _username, userdata in self.db.db.items():
                                    if username != _username and username in userdata["friends"]:
                                        friendResponse = {
                                            "type": types.updateUserImage_t,
                                            "code": 200,
                                            "content": {
                                                "username": username,
                                                "image": image
                                            }
                                        }
                                        try:
                                            self.online_users[_username][1].write(
                                                (json.dumps(friendResponse) + '\0').encode())

                                            await self.online_users[_username][1].drain()

                                        except KeyError: pass

                                clientResponse = {
                                    "type": types.newProfileImage_t,
                                    "code": 200,
                                    "content": None
                                }

                    except KeyError: pass

                return None, (json.dumps(clientResponse) + "\0").encode()

            case types.requestSendMessage_t if clientRequest.get("content"):
                clientResponse = badRequest
                clientRequestContent = clientRequest.get("content")
                clientData = self.getContentValue(
                    clientRequestContent, "username", "message-text", "Recipient", "token")

                if None not in clientData:
                    sender_username, message_text, recipient, token, *_ = clientData
                    try:
                        if self.online_users[sender_username][2] == token:
                            if self.db.checkForPresenceDatabase(recipient):
                                sendingMessageRequest = {
                                    "type": types.requestSendMessage_t, "code": 200,
                                    "content": {
                                        "sender": sender_username,
                                        "message-text": message_text
                                    }
                                }
                                try:
                                    clientResponse = {
                                        "type": None, "code": 200,
                                        "content": None
                                    }
                                    if sender_username != recipient:
                                        self.online_users[recipient][1].write(
                                            (json.dumps(sendingMessageRequest) + "\0").encode()
                                        ); await self.online_users[recipient][1].drain()

                                except KeyError:
                                    clientResponse = badRequest
                                    if recipient not in self.unsent_messages:
                                        self.unsent_messages[recipient] = {}

                                    if sender_username not in self.unsent_messages[recipient]:
                                        self.unsent_messages[recipient][sender_username] = []

                                    self.unsent_messages[recipient][sender_username].append(message_text)

                    except KeyError: pass

                return None, (json.dumps(clientResponse) + '\0').encode()

    def getContentValue(self, content: dict, *values):
        return tuple(
            map(lambda value: content.get(value), values))

    def isRequestReceivedFull(self, request, eofSymbol):
        try: return eofSymbol in request # request[-1] == eofSymbol
        except IndexError: pass


class AcceptServerConnection:

    async def _runServer(self, host, port):
        createServerObject = await asyncio.start_server(
            self.connectionHandlerMethod, host, port)

        async with createServerObject as self.serverSocket:
            await self.serverSocket.serve_forever()

    async def connectionHandlerMethod(self,
                                      StreamReaderSocket: asyncio.StreamReader,
                                      StreamWriterSocket: asyncio.StreamWriter):

        username, isusername = None, False
        request_received_client = bytes()
        try:
            while not self._stop_server:
                try: request_received_client += await StreamReaderSocket.readuntil(b"\0")
                except asyncio.exceptions.LimitOverrunError:
                    request_received_client += await StreamReaderSocket.read(1024)

                requestReceivedClientDecode = request_received_client.decode()
                if self.isRequestReceivedFull(
                        requestReceivedClientDecode, types.EOF):

                    try:
                        _username, readyResponse = await self.handlerRequestReceivedClient(
                            requestReceivedClientDecode[:-1], StreamReaderSocket, StreamWriterSocket
                        )
                        request_received_client = bytes()

                        if not isusername: username = _username; isusername = True
                        if readyResponse:
                            StreamWriterSocket.write(readyResponse)
                            await StreamWriterSocket.drain()

                    except (TypeError, UnboundLocalError): pass

        except ConnectionResetError:
            try: self.online_users.pop(username)
            except KeyError: pass

class Server(AcceptServerConnection, RequestHandler):

    def __init__(self, host, port):
        self.host, self.port = host, port

        self._stop_server = False
        self._online_sockets = {}
        self.unsent_messages = {}
        self.online_users = {}
        self.socket_count = 0

        self.db = DbmsJson("database")

    def runServer(self):
        asyncio.run(self._runServer(self.host, self.port))

    def stopServer(self):
        self._stop_server = True

