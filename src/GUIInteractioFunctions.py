import os

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.filemanager import MDFileManager
from chat_screen import ChatScreen
from builder import Builder
from Exceptions import UserNotInFriend


class GUIInterfaceFunctions(Builder):
    ids = {}

    def connectionLossWarningDialog(self):
        self.dialog = MDDialog(
            title='Messenger', text=f'Потеряно соединение с сервером...',
            on_dismiss=lambda instance: self.isDialogOpen(),
            buttons=[MDFlatButton(
                text='Ок', on_release=self.dismissDialog)
            ]
        )
        self.dialog.open()

    def userExistsWarningDialog(self):
        self.dialog = MDDialog(
            title='Messenger',
            text=f'Вы хотите добавить пользователя {self.searchusername}?',
            buttons=[MDFlatButton(text='Да', on_release=(
                lambda instance: self.appendUserInFriend())),
                     MDFlatButton(text='Нет', on_release=(
                         lambda ins: self.dialog.dismiss()))]
        )
        self.dialog.open()

    def userNotExistsWarningDialog(self):
        self.dialog = MDDialog(
            title='Messenger',
            text=f'Пользователя {self.searchusername} не существует!',
            buttons=[MDFlatButton(
                text='Ок', on_release=lambda instance: self.dialog.dismiss())])
        self.dialog.open()

    def userAddedWarningDialog(self):
        self.dialog = MDDialog(
            title='Messenger',
            text=f'Пользователь {self.searchusername} уже добавлен!',
            buttons=[MDFlatButton(
                text='Ок', on_release=lambda ins: self.dialog.dismiss())])
        self.dialog.open()

    def userRemoveWarningDialog(self, userWidgetObject):
        self.dialog = MDDialog(
            title='Messenger',
            text=f'Вы действительно хотите удалть позльзователя {userWidgetObject.text}?',
            buttons=[
                MDFlatButton(
                    text='Да', on_release=lambda _instnace:
                    self.getRemoveUser(userWidgetObject.text, userWidgetObject)),

                MDFlatButton(
                    text='Нет', on_release=lambda instance:
                    self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def dismissDialog(self, instance):
        if self.dialogOpen:
            self.dialog.dismiss()
        self.dialogOpen = False

    def isDialogOpen(self): self.dialogOpen = False

    def get_singup_screen(self):
        self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = "singup_screen"

    def get_singin_screen(self):
        self.screen_manager.transition.direction = 'right'
        self.screen_manager.current = "singin_screen"

    def get_main_screen(self):
        self.screen_manager.transition.direction = 'right'
        self.screen_manager.current = "main_screen"

    def setAccountInformation(self, *accountInformation):
        image_path = accountInformation[2]
        self.addingFriends(accountInformation[1])
        self.screen_manager.get_screen(
            'main_screen').ids.usernamelabel.text = accountInformation[0]

        if image_path:
            self.screen_manager.get_screen(
                'main_screen').ids.avatarimage.source = image_path

    def addingFriends(self, userWidgetTextView):
        for widget, widgetObjectPointer, roundIcon in (
                self.friendAddHandler(userWidgetTextView)
        ):
            if widget.text not in self.ids:
                self.ids[widget.text] = (widgetObjectPointer, roundIcon)
                self.screen_manager.get_screen(
                    'main_screen').ids.listusers.add_widget(widget)

    def apppendMessageInMessageList(self, chatName, senderName , messageWidget):
        self.ids[chatName][0].text = f"{senderName}: {messageWidget.text}"

        self.screen_manager.get_screen(
            f"chat|{chatName}"
        ).ids.message_list.add_widget(messageWidget)

        self.screen_manager.get_screen(
            f"chat|{chatName}"
        ).ids.sendmessage_textfield.text = ''

    def appendChatScreen(self, username):
        if username not in self.loads:
            self.screen_manager.add_widget(
                ChatScreen(
                    username=username,
                    press_leftboldiconbutton=self.get_main_screen,
                    press_sendiconbutton=self.sendMessage
                )
            )
            self.loads.append(username)