from mywidget import MyWidget
from types_ import *


class Builder(MyWidget):
    def friendAddHandler(self, response):
        if not response: return
        commands = response.split('\n')

        for command in commands:
            data_widget = command.split(':')
            if data_widget[0] == "User_widget":
                username, secondary_text, image_path = data_widget[1:]
                yield self.UserAvatarListItem(
                    username, secondary_text, image_path)
