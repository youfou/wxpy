import html
import logging
import os
import tempfile
import weakref
from datetime import datetime
from xml.etree import ElementTree as ETree

from wxpy.api.chats import Chat, Group, Member, User
from wxpy.utils import wrap_user_name

logger = logging.getLogger(__name__)

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

        self.bot = weakref.proxy(bot)
        self.type = self.raw.get('Type')

        self.is_at = self.raw.get('IsAt') or self.raw.get('isAt')

        self.file_name = self.raw.get('FileName')
        self.file_size = self.raw.get('FileSize')
        self.media_id = self.raw.get('MediaId')

        self.img_height = self.raw.get('ImgHeight')
        self.img_width = self.raw.get('ImgWidth')

        self.play_length = self.raw.get('PlayLength')
        self.voice_length = self.raw.get('VoiceLength')

        self.url = self.raw.get('Url')
        if isinstance(self.url, str):
            self.url = html.unescape(self.url)

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
            if self.type is CARD:
                self.text = self.card.name
            else:
                self.text = self.card.raw.get('Content')

        # 将 msg.chat.send* 方法绑定到 msg.reply*，例如 msg.chat.send_img => msg.reply_img
        for method in '', '_image', '_file', '_video', '_msg', '_raw_msg':
            setattr(self, 'reply' + method, getattr(self.chat, 'send' + method))

    def __hash__(self):
        return hash((Message, self.id))

    def __repr__(self):
        text = (str(self.text or '')).replace('\n', ' ↩ ')
        text += ' ' if text else ''

        if self.sender == self.bot.self:
            ret = '↪ {self.receiver.name}'
        elif isinstance(self.chat, Group) and self.member != self.receiver:
            ret = '{self.sender.name} › {self.member.name}'
        else:
            ret = '{self.sender.name}'

        ret += ' : {text}({self.type})'

        return ret.format(self=self, text=text)

    @property
    def chat(self):
        """
        消息所在的聊天会话，即:

        * 对于自己发送的消息，为消息的接收者
        * 对于别人发送的消息，为消息的发送者
        
        :rtype: :class:`wxpy.User`, :class:`wxpy.Group`
        """

        if self.raw.get('FromUserName') == self.bot.self.user_name:
            return self.receiver
        else:
            return self.sender

    @property
    def sender(self):
        """
        消息的发送者
        
        :rtype: :class:`wxpy.User`, :class:`wxpy.Group`
        """

        return self._get_chat_by_user_name(self.raw.get('FromUserName'))

    @property
    def receiver(self):
        """
        消息的接收者
        
        :rtype: :class:`wxpy.User`, :class:`wxpy.Group`
        """

        return self._get_chat_by_user_name(self.raw.get('ToUserName'))

    @property
    def member(self):
        """
        * 若消息来自群聊，则此属性为消息的实际发送人(具体的群成员)
        * 若消息来自其他聊天对象(非群聊)，则此属性为 None
        
        :rtype: NoneType, :class:`wxpy.Member`
        """

        if isinstance(self.chat, Group):
            if self.sender == self.bot.self:
                return self.chat.self
            else:
                actual_user_name = self.raw.get('ActualUserName')
                for _member in self.chat.members:
                    if _member.user_name == actual_user_name:
                        return _member
                return Member(dict(
                    UserName=actual_user_name,
                    NickName=self.raw.get('ActualNickName')
                ), self.chat)

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

    def forward(self, chat, prefix=None, suffix=None, raise_for_unsupported=False):
        """
        将本消息转发给其他聊天对象

        支持以下消息类型
            * 文本 (`TEXT`)
            * 视频（`VIDEO`)
            * 文件 (`ATTACHMENT`)
            * 图片/自定义表情 (`PICTURE`)

                * 但不支持表情商店中的表情

            * 名片 (`CARD`)

                * 仅支持公众号名片

            * 分享 (`SHARING`)

                * 会转化为 `标题 + 链接` 形式的文本消息

            * 语音 (`RECORDING`)

                * 会以文件方式发送
            
            * 地图 (`MAP`)
                
                * 会转化为 `位置名称 + 地图链接` 形式的文本消息

        :param Chat chat: 接收转发消息的聊天对象
        :param str prefix: 转发时增加的 **前缀** 文本，原消息为文本时会自动换行
        :param str suffix: 转发时增加的 **后缀** 文本，原消息为文本时会自动换行
        :param bool raise_for_unsupported:
            | 为 True 时，将为不支持的消息类型抛出 `NotImplementedError` 异常

        例如，将公司群中的老板消息转发出来::

            from wxpy import *

            bot = Bot()

            # 定位公司群
            company_group = ensure_one(bot.groups().search('公司微信群'))

            # 定位老板
            boss = ensure_one(company_group.search('老板大名'))

            # 将老板的消息转发到文件传输助手
            @bot.register(company_group)
            def forward_boss_message(msg):
                if msg.member == boss:
                    msg.forward(bot.file_helper, prefix='老板发言')

            # 堵塞线程
            embed()

        """

        logger.info('{}: forwarding to {}: {}'.format(self.bot, chat, self))

        def wrapped_send(send_type, *args, **kwargs):
            if send_type == 'msg':
                if args:
                    text = args[0]
                elif kwargs:
                    text = kwargs['msg']
                else:
                    text = self.text
                ret = chat.send_msg('{}{}{}'.format(
                    str(prefix) + '\n' if prefix else '',
                    text,
                    '\n' + str(suffix) if suffix else '',
                ))
            else:
                if prefix:
                    chat.send_msg(prefix)
                ret = getattr(chat, 'send_{}'.format(send_type))(*args, **kwargs)
                if suffix:
                    chat.send_msg(suffix)

            return ret

        def download_and_send():
            path = tempfile.mkstemp(
                suffix='_{}'.format(self.file_name),
                dir=self.bot.temp_dir.name
            )[1]
            self.get_file(path)
            if self.type is PICTURE:
                return wrapped_send('image', path)
            elif self.type is VIDEO:
                return wrapped_send('video', path)
            else:
                return wrapped_send('file', path)

        def raise_properly(text):
            logger.warning(text)
            if raise_for_unsupported:
                raise NotImplementedError(text)

        if self.type is TEXT:
            return wrapped_send('msg')

        elif self.type is SHARING:
            return wrapped_send('msg', '{}\n{}'.format(self.text, self.url))

        elif self.type is MAP:
            return wrapped_send('msg', '{}: {}\n{}'.format(
                self.location['poiname'], self.location['label'], self.url
            ))

        elif self.type is ATTACHMENT:

            # noinspection SpellCheckingInspection
            content = \
                "<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''>" \
                "<title>{file_name}</title><des></des><action></action>" \
                "<type>6</type><content></content><url></url><lowurl></lowurl>" \
                "<appattach><totallen>{file_size}</totallen><attachid>{media_id}</attachid>" \
                "<fileext>{file_ext}</fileext></appattach><extinfo></extinfo></appmsg>"

            content = content.format(
                file_name=self.file_name,
                file_size=self.file_size,
                media_id=self.media_id,
                file_ext=os.path.splitext(self.file_name)[1].replace('.', '')
            )

            return wrapped_send(
                send_type='raw_msg',
                msg_type=self.raw['MsgType'],
                content=content,
                uri='/webwxsendappmsg?fun=async&f=json'
            )

        elif self.type is CARD:
            if self.card.raw.get('AttrStatus'):
                # 为个人名片
                raise_properly('Personal cards are unsupported:\n{}'.format(self))
            else:
                return wrapped_send(
                    send_type='raw_msg',
                    msg_type=self.raw['MsgType'],
                    content=self.raw['Content'],
                    uri='/webwxsendmsg'
                )

        elif self.type is PICTURE:
            if self.raw.get('HasProductId'):
                # 来自表情商店的表情
                raise_properly('Stickers from store are unsupported:\n{}'.format(self))
            else:
                return download_and_send()

        elif self.type is VIDEO:
            return download_and_send()

        elif self.type is RECORDING:
            return download_and_send()

        else:
            raise_properly('Unsupported message type:\n{}'.format(self))
