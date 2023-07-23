
from kivy.config import Config

Config.set('graphics', 'width', 600)
Config.set('graphics', 'height', 600)
Config.set("graphics", "resizable", '0')


from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.filemanager import MDFileManager
from kivymd.app import MDApp
from kivy.clock import Clock

from PIL import Image

import os, sys
import secrets
import base64
import time


from GUIInteractioFunctions import GUIInterfaceFunctions
from selectWidgetSize import selectWidgetSize
from singin_screen import SingInScreen
from singup_screen import SingUpScreen
from chat_screen import createMessageWidget
from main_screen import MainScreen
from event_loop import EventLoop, Event, events
from types_ import *


class MessengerApp(MDApp, EventLoop, GUIInterfaceFunctions):

    token = secrets.token_hex(64)
    dialogOpen, online = False, False
    accountData = ()
    messageNotSend = []

    image_baytes_base64 = ""
    lockRequest = False

    def build(self):
        Clock.schedule_interval(self.eventHandler, 1 / 30)
        self.createServerConnection()

        self.icon = "../assets/images/icon.png"
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(
            SingInScreen(
                press_button_login=self.getLogin,
                press_button_singup=self.get_singup_screen
            )
        )
        self.screen_manager.add_widget(
            SingUpScreen(
                press_select_photo=self.change_icon,
                press_leftboldiconbutton=self.get_singin_screen,
                press_regisrationbutton=self.getRegistration
            )
        )
        self.screen_manager.add_widget(
            MainScreen(
                press_search_button=self.searchUser,
                press_select_photo=self.change_icon
            )
        )
        return self.screen_manager

    def getLogin(self, usernamePassword=()):
        if not usernamePassword:
            self.username = self.screen_manager.get_screen(
                'singin_screen').ids.login_text_field.text
            self.password = self.screen_manager.get_screen(
                'singin_screen').ids.password_text_field.text
        else:
            self.username, self.password = usernamePassword
            self.login = False


        if (self.username and self.password and not self.lockRequest and
            isinstance(self.username, str) and isinstance(self.password, str)):

            self.lockRequest = True
            self.requestHandler(
                self.firstSocket, {
                    "type": singinData_t,
                    "content": {
                        "login": self.username,
                        "password": self.password,
                        "token": self.token
                    }
                }
            )

    def getRegistration(self, auto_login=False):
        self.username = self.screen_manager.get_screen(
            'singup_screen').ids.usernametextfield.text
        self.password = self.screen_manager.get_screen(
            'singup_screen').ids.passwrodtextfield.text
        surname = self.screen_manager.get_screen(
            'singup_screen').ids.surnametextfield.text

        if (3 <= len(self.username) <= 15 and len(surname) <= 25 and
            8 <= len(self.password) <= 30) and not self.lockRequest:

            self.lockRequest = True
            self.requestHandler(
                self.firstSocket, {
                    "type": singupData_t,
                    "content": {
                        "username": self.username,
                        "password": self.password,
                        "surname": surname,
                        "token": self.token
                    }
                }
            )
            if not self.image_baytes_base64:
                with open(self.createImagefile(
                        self.image_baytes_base64), "rb") as image_file:


                    self.image_baytes_base64 = base64.encodebytes(image_file.read()).decode()

            self.requestHandler(
                self.firstSocket, {
                    "type": newProfileImage_t,
                    "content": {
                        "username": self.username,
                        "image": self.image_baytes_base64,
                        "token": self.token
                    }
                }
            )

    def sendMessage(self, message, chatName):
        if message and len(message) <= 5000:
            messageRequest = {
                "type": requestSendMessage_t,
                "content": {
                    "username": self.username,
                    "message-text": message,
                    "Recipient": chatName,
                    "token": self.token
                }
            }
            self.requestHandler(self.firstSocket, messageRequest)
            messageWidget = createMessageWidget(radius=(23, 23, 0, 23))
            messageWidget.size_hint_x, messageWidget.halign = selectWidgetSize(message)
            messageWidget.pos_hint, messageWidget.text = {"right": .98}, message

            self.apppendMessageInMessageList(chatName, "Вы", messageWidget)
            if self.firstSocket.connectionRecoveryThread:
                self.messageNotSend.append(messageRequest)


    def receiveMessage(self, message, chatName):
        messageWidget = createMessageWidget(radius=(23, 23, 23, 0))
        messageWidget.size_hint_x, messageWidget.halign = selectWidgetSize(message)
        messageWidget.text, messageWidget.pos_hint = message, {"x": .02}

        self.apppendMessageInMessageList(
            chatName,
            chatName,
            messageWidget,
            recv=True
        )

    def searchUser(self, auto_login=False):
        self.searchusername = self.screen_manager.get_screen(
            'main_screen').ids.searchtextfieldr.text if self.screen_manager.get_screen(
            'main_screen').ids.searchtextfieldr.text else None

        if self.searchusername and not self.lockRequest:

            self.lockRequest = True
            self.requestHandler(
                self.firstSocket, {
                    "type": searchFriend_t,
                    "content": {
                        "username": self.username,
                        "search-username": self.searchusername,
                        "token": self.token
                    }
                }
            )

    def appendUserInFriend(self, appendedUser=None):
        if not appendedUser:
            self.dialog.dismiss()
            appendedUser = self.searchusername

        if not self.lockRequest:

            self.lockRequest = True
            self.requestHandler(
                self.firstSocket, {
                    "type": appendUser_t,
                    "content": {
                        "username": self.username,
                        "append-username": appendedUser,
                        "token": self.token
                    }
                }
            )

    def getRemoveUser(self, username, widgetPointer):
        requestRemoveUser = {
            "type": removeFriend_t,
            "content": {
                "username": self.username,
                "remove-username": username,
                "token": self.token
            }
        }
        self.dialog.dismiss()
        if not self.lockRequest:
            self.lockRequest = True
            self.requestHandler(self.firstSocket, requestRemoveUser)

        self.removed_user_widget = widgetPointer
        self.removed_username = username

    def change_icon(self, sendServer=False):
        self.filemanager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=lambda path: self.select_path(
                path=path, sendServer=sendServer
            )
        )
        self.filemanager.show('C:\\')

    def exit_manager(self, *args):
        self.filemanager.close()
        del self.filemanager

    def compressedimage(self, path):
        newpath = f"../compressed/{secrets.token_hex(12)}" \
                  f"{os.path.splitext(path)[-1]}"

        image = Image.open(path)
        image.thumbnail((600, 600))
        image.save(newpath)

        return newpath

    def select_path(self, path, sendServer=False):
        if not self.firstSocket.connectionRecoveryThread:
            if os.path.splitext(path)[-1].lower() in [".png", ".jpg", ".jpeg"]:
                with open(self.compressedimage(path), "rb") as image_file:
                    self.image_baytes_base64 = base64.encodebytes(image_file.read()).decode()
                    self.screen_manager.get_screen('main_screen').ids.avatarimage.source = path
                    self.exit_manager()
                    if sendServer:
                        if not self.lockRequest:
                            self.requestHandler(
                                self.firstSocket, {
                                    "type": newProfileImage_t,
                                    "content": {
                                        "username": self.username,
                                        "image": self.image_baytes_base64,
                                        "token": self.token
                                    }
                                }
                            )
                            if self.username in self.ids:
                                self.ids[self.username][1].source = path
                    else:
                        self.screen_manager.get_screen(
                            'singup_screen').ids.avatarimage.source = path
        else:
            events.append(Event(type=сonnectionError_t, content=None))

    def createImagefile(self, image_base64):
        if image_base64:
            image_path = f"../images/{secrets.token_hex(12)}"
            with open(image_path, "wb") as image_file:
                image_file.write(base64.decodebytes(image_base64.encode()))

            return image_path

        else:
            return "../assets/Images/user.png"

    def on_stop(self):
        closeDataJson = {
            "type": closeConnection_t,
            "content": {
                "close-connection": True
            }
        }
        if not self.lockRequest:
            self.lockRequest = True
            self.requestHandler(self.firstSocket, closeDataJson)

        for image in os.listdir("../images"):
            os.remove("../images/" + image)

        for compressedIamge in os.listdir("../compressed"):
            os.remove("../compressed/" + compressedIamge)


if __name__ == '__main__':
    MessengerApp().run()
