"""Standard messanger module - print instead of senfing"""

from alphavar.io.messanger.message_class import AbstractMessanger


class StandardMessanger(AbstractMessanger):
    """Stdout messaging"""

    def send_message(self, text):
        print(text)
