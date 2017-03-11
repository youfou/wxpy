from wxpy.api.chats import Chats


class Messages(list):
    """
    多条消息的合集，可用于记录或搜索
    """

    def __init__(self, msg_list=None, bot=None, max_history=10000):
        if msg_list:
            super(Messages, self).__init__(msg_list)
        self.bot = bot
        self.max_history = max_history

    def __add__(self, other):
        return Chats(super(Messages, self).__add__(other))

    def append(self, msg):
        del self[:-self.max_history + 1]
        return super(Messages, self).append(msg)

    # TODO: 搜索消息功能 (keywords, **attributes) (先前的实现有误…)
