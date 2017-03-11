from datetime import datetime
from xml.etree import ElementTree as ETree

from wxpy.api.chats import Chat, Group, Member, User
from wxpy.utils import wrap_user_name

# 文本
TEXT = 'Text'
# 位置
MAP = 'Map'
# 名片
CARD = 'Card'
# 提示
NOTE = 'Note'
# 分享
SHARING = 'Sharing'
# 图片
PICTURE = 'Picture'
# 语音
RECORDING = 'Recording'
# 文件
ATTACHMENT = 'Attachment'
# 视频
VIDEO = 'Video'
# 好友请求
FRIENDS = 'Friends'
# 系统
SYSTEM = 'System'


class Message(object):
    """
    单条消息对象
    """

    def __init__(self, raw, bot):
        self.raw = raw

        self.bot = bot
        self.type = self.raw.get('Type')

        self.is_at = self.raw.get('isAt')
        self.file_name = self.raw.get('FileName')
        self.img_height = self.raw.get('ImgHeight')
        self.img_width = self.raw.get('ImgWidth')
        self.play_length = self.raw.get('PlayLength')
        self.url = self.raw.get('Url')
        self.voice_length = self.raw.get('VoiceLength')
        self.id = self.raw.get('NewMsgId')

        self.text = None
        self.get_file = None
        self.create_time = None
        self.location = None
        self.card = None

        text = self.raw.get('Text')
        if callable(text):
            self.get_file = text
        else:
            self.text = text

        # noinspection PyBroadException
        try:
            self.create_time = datetime.fromtimestamp(self.raw.get('CreateTime'))
        except:
            pass

        if self.type == MAP:
            try:
                self.location = ETree.fromstring(self.raw['OriContent']).find('location').attrib
                try:
                    self.location['x'] = float(self.location['x'])
                    self.location['y'] = float(self.location['y'])
                    self.location['scale'] = int(self.location['scale'])
                    self.location['maptype'] = int(self.location['maptype'])
                except (KeyError, ValueError):
                    pass
                self.text = self.location.get('label')
            except (TypeError, KeyError, ValueError, ETree.ParseError):
                pass
        elif self.type in (CARD, FRIENDS):
            self.card = User(self.raw.get('RecommendInfo'), self.bot)
            self.text = self.card.raw.get('Content')

        # 将 msg.sender.send* 方法绑定到 msg.reply*，例如 msg.sender.send_img => msg.reply_img
        for method in '', '_image', '_file', '_video', '_msg', '_raw_msg':
            setattr(self, 'reply' + method, getattr(self.sender, 'send' + method))

    def __hash__(self):
        return hash((Message, self.id))

    def __repr__(self):
        text = (str(self.text) or '').replace('\n', ' ')
        ret = '{0.sender.name}'
        if self.member:
            ret += ' -> {0.member.name}'
        ret += ': '
        if self.text:
            ret += '{1} '
        ret += '({0.type})'
        return ret.format(self, text)

    def _get_chat_by_user_name(self, user_name):
        """
        通过 user_name 找到对应的聊天对象

        :param user_name: user_name
        :return: 找到的对应聊天对象
        """
        def match_in_chats(_chats):
            for c in _chats:
                if c.user_name == user_name:
                    return c

        _chat = None

        if user_name.startswith('@@'):
            _chat = match_in_chats(self.bot.groups())
        elif user_name:
            _chat = match_in_chats(self.bot.friends())
            if _chat is None:
                _chat = match_in_chats(self.bot.mps())

        if _chat is None:
            _chat = Chat(wrap_user_name(user_name), self.bot)

        return _chat

    @property
    def sender(self):
        """
        消息的发送者
        """

        return self._get_chat_by_user_name(self.raw.get('FromUserName'))

    @property
    def receiver(self):
        """
        消息的接收者
        """

        return self._get_chat_by_user_name(self.raw.get('ToUserName'))

    @property
    def member(self):
        """
        若消息来自群聊，则此属性为实际发送消息的群成员
        """

        if isinstance(self.sender, Group):
            actual_user_name = self.raw.get('ActualUserName')
            for _member in self.sender:
                if _member.user_name == actual_user_name:
                    return _member
            return Member(dict(UserName=actual_user_name, NickName=self.raw.get('ActualNickName')), self.sender)
