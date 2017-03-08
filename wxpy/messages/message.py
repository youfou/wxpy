from datetime import datetime
from xml.etree import ElementTree as ETree

import wxpy
from ..utils import wrap_user_name

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


class Message(dict):
    """
    单条消息对象
    """

    def __init__(self, raw, bot):
        super(Message, self).__init__(raw)

        self.bot = bot
        self.type = self.get('Type')

        self.is_at = self.get('isAt')
        self.file_name = self.get('FileName')
        self.img_height = self.get('ImgHeight')
        self.img_width = self.get('ImgWidth')
        self.play_length = self.get('PlayLength')
        self.url = self.get('Url')
        self.voice_length = self.get('VoiceLength')
        self.id = self.get('NewMsgId')

        self.text = None
        self.get_file = None
        self.create_time = None
        self.location = None
        self.card = None

        text = self.get('Text')
        if callable(text):
            self.get_file = text
        else:
            self.text = text

        # noinspection PyBroadException
        try:
            self.create_time = datetime.fromtimestamp(self.get('CreateTime'))
        except:
            pass

        if self.type == MAP:
            try:
                self.location = ETree.fromstring(self['OriContent']).find('location').attrib
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
            self.card = wxpy.User(self.get('RecommendInfo'))
            self.card.bot = self.bot
            self.text = self.card.get('Content')

        # 将 msg.chat.send* 方法绑定到 msg.reply*，例如 msg.chat.send_img => msg.reply_img
        for method in '', '_image', '_file', '_video', '_msg', '_raw_msg':
            setattr(self, 'reply' + method, getattr(self.chat, 'send' + method))

    def __hash__(self):
        return hash((Message, self.id))

    def __repr__(self):
        text = (str(self.text) or '').replace('\n', ' ')
        ret = '{0.chat.name}'
        if self.member:
            ret += ' -> {0.member.name}'
        ret += ': '
        if self.text:
            ret += '{1} '
        ret += '({0.type})'
        return ret.format(self, text)

    @property
    def raw(self):
        """原始数据"""
        return dict(self)

    @property
    def chat(self):
        """
        来自的聊天对象
        """
        user_name = self.get('FromUserName')
        if user_name:
            for _chat in self.bot.chats():
                if _chat.user_name == user_name:
                    return _chat
            _chat = wxpy.Chat(wrap_user_name(user_name))
            _chat.bot = self.bot
            return _chat

    @property
    def member(self):
        """
        发送此消息的群聊成员 (若消息来自群聊)
        """
        if isinstance(self.chat, wxpy.Group):
            actual_user_name = self.get('ActualUserName')
            for _member in self.chat:
                if _member.user_name == actual_user_name:
                    return _member
            return wxpy.Member(dict(UserName=actual_user_name, NickName=self.get('ActualNickName')), self.chat)
