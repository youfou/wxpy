# coding: utf-8
from __future__ import unicode_literals

import logging
import os
import tempfile
import weakref
from datetime import datetime
from xml.etree import ElementTree as ETree

try:
    import html
except ImportError:
    # Python 2.6-2.7
    # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyCompatibility
    from HTMLParser import HTMLParser

    html = HTMLParser()

from wxpy.api.chats import Chat, Group, Member, User
from wxpy.compatible.utils import force_encoded_string_output
from wxpy.utils import wrap_user_name, repr_message
from .article import Article
from ..consts import ATTACHMENT, CARD, FRIENDS, MAP, PICTURE, RECORDING, SHARING, TEXT, VIDEO
from ...compatible import *

logger = logging.getLogger(__name__)


class Message(object):
    """
    单条消息对象，包括:
    
    * 来自好友、群聊、好友请求等聊天对象的消息
    * 使用机器人账号在手机微信中发送的消息
    
    | 但 **不包括** 代码中通过 .send/reply() 系列方法发出的消息
    | 此类消息请参见 :class:`SentMessage`
    """

    def __init__(self, raw, bot):
        self.raw = raw
        self.bot = weakref.proxy(bot)

        self._receive_time = datetime.now()

        # 将 msg.chat.send* 方法绑定到 msg.reply*，例如 msg.chat.send_img => msg.reply_img
        for method in '', '_image', '_file', '_video', '_msg', '_raw_msg':
            setattr(self, 'reply' + method, getattr(self.chat, 'send' + method))

    def __hash__(self):
        return hash((Message, self.id))

    @force_encoded_string_output
    def __repr__(self):
        return repr_message(self)

    def __unicode__(self):
        return repr_message(self)

    # basic

    @property
    def type(self):
        """
        消息的类型，目前可为以下值::
        
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
        
        :rtype: str
        """
        return self.raw.get('Type')

    @property
    def id(self):
        """
        消息的唯一 ID (通常为大于 0 的 64 位整型)
        """
        return self.raw.get('NewMsgId')

    # content
    @property
    def text(self):
        """
        消息的文本内容
        """
        _type = self.type
        _card = self.card

        if _type == MAP:
            location = self.location
            if location:
                return location.get('label')
        elif _card:
            if _type == CARD:
                return _card.name
            elif _type == FRIENDS:
                return _card.raw.get('Content')

        ret = self.raw.get('Text')
        if isinstance(ret, str):
            return ret

    def get_file(self, save_path=None):
        """
        下载图片、视频、语音、附件消息中的文件内容。
        
        可与 :any:`Message.file_name` 配合使用。

        :param save_path: 文件的保存路径。若为 None，将直接返回字节数据
        """

        _text = self.raw.get('Text')
        if callable(_text) and self.type in (PICTURE, RECORDING, ATTACHMENT, VIDEO):
            return _text(save_path)
        else:
            raise ValueError('download method not found, or invalid message type')

    @property
    def file_name(self):
        """
        消息中文件的文件名
        """
        return self.raw.get('FileName')

    @property
    def file_size(self):
        """
        消息中文件的体积大小
        """
        return self.raw.get('FileSize')

    @property
    def media_id(self):
        """
        文件类消息中的文件资源 ID (但图片视频语音等其他消息中为空)
        """
        return self.raw.get('MediaId')

    # group

    @property
    def is_at(self):
        """
        当消息来自群聊，且被 @ 时，为 True
        """
        return self.raw.get('IsAt') or self.raw.get('isAt')

    # misc

    @property
    def img_height(self):
        """
        图片高度
        """
        return self.raw.get('ImgHeight')

    @property
    def img_width(self):
        """
        图片宽度
        """
        return self.raw.get('ImgWidth')

    @property
    def play_length(self):
        """
        视频长度
        """
        return self.raw.get('PlayLength')

    @property
    def voice_length(self):
        """
        语音长度
        """
        return self.raw.get('VoiceLength')

    @property
    def url(self):
        """
        分享类消息中的网页 URL
        """
        _url = self.raw.get('Url')
        if isinstance(_url, str):
            _url = html.unescape(_url)

        return _url

    @property
    def articles(self):
        """
        公众号推送中的文章列表 (首篇的 标题/地址 与消息中的 text/url 相同)

        其中，每篇文章均有以下属性:

        * `title`: 标题
        * `summary`: 摘要
        * `url`: 文章 URL
        * `cover`: 封面或缩略图 URL
        """

        from wxpy import MP
        if self.type == SHARING and isinstance(self.sender, MP):
            tree = ETree.fromstring(self.raw['Content'])
            # noinspection SpellCheckingInspection
            items = tree.findall('.//mmreader/category/item')

            article_list = list()

            for item in items:
                def find_text(tag):
                    found = item.find(tag)
                    if found is not None:
                        return found.text

                article = Article()
                article.title = find_text('title')
                article.summary = find_text('digest')
                article.url = find_text('url')
                article.cover = find_text('cover')
                article_list.append(article)

            return article_list

    @property
    def card(self):
        """
        * 好友请求中的请求用户
        * 名片消息中的推荐用户
        """
        if self.type in (CARD, FRIENDS):
            return User(self.raw.get('RecommendInfo'), self.bot)

    # time

    @property
    def create_time(self):
        """
        服务端发送时间
        """
        # noinspection PyBroadException
        try:
            return datetime.fromtimestamp(self.raw.get('CreateTime'))
        except:
            pass

    @property
    def receive_time(self):
        """
        本地接收时间
        """
        return self._receive_time

    @property
    def latency(self):
        """
        消息的延迟秒数 (发送时间和接收时间的差值)
        """
        create_time = self.create_time
        if create_time:
            return (self.receive_time - create_time).total_seconds()

    @property
    def location(self):
        """
        位置消息中的地理位置信息
        """
        try:
            ret = ETree.fromstring(self.raw['OriContent']).find('location').attrib
            try:
                ret['x'] = float(ret['x'])
                ret['y'] = float(ret['y'])
                ret['scale'] = int(ret['scale'])
                ret['maptype'] = int(ret['maptype'])
            except (KeyError, ValueError):
                pass
            return ret
        except (TypeError, KeyError, ValueError, ETree.ParseError):
            pass

    # chats

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
            if not _chat:
                _chat = match_in_chats(self.bot.mps())

        if not _chat:
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

                * 仅支持公众号名片，以及自己发出的个人号名片

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
            fd, path = tempfile.mkstemp(
                suffix='_{}'.format(self.file_name),
                dir=self.bot.temp_dir.name
            )

            try:
                self.get_file(path)
                if self.type == PICTURE:
                    return wrapped_send('image', path)
                elif self.type == VIDEO:
                    return wrapped_send('video', path)
                else:
                    return wrapped_send('file', path)
            finally:
                os.close(fd)

        def raise_properly(text):
            logger.warning(text)
            if raise_for_unsupported:
                raise NotImplementedError(text)

        if self.type == TEXT:
            return wrapped_send('msg')

        elif self.type == SHARING:
            return wrapped_send('msg', '{}\n{}'.format(self.text, self.url))

        elif self.type == MAP:
            return wrapped_send('msg', '{}: {}\n{}'.format(
                self.location['poiname'], self.location['label'], self.url
            ))

        elif self.type == ATTACHMENT:

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
                raw_type=self.raw['MsgType'],
                raw_content=content,
                uri='/webwxsendappmsg?fun=async&f=json'
            )

        elif self.type == CARD:
            if self.card.raw.get('AttrStatus') and self.sender != self.bot.self:
                # 为个人名片，且不为自己所发出
                raise_properly('Personal cards sent from others are unsupported:\n{}'.format(self))
            else:
                return wrapped_send(
                    send_type='raw_msg',
                    raw_type=self.raw['MsgType'],
                    raw_content=self.raw['Content'],
                    uri='/webwxsendmsg'
                )

        elif self.type == PICTURE:
            if self.raw.get('HasProductId'):
                # 来自表情商店的表情
                raise_properly('Stickers from store are unsupported:\n{}'.format(self))
            else:
                return download_and_send()

        elif self.type == VIDEO:
            return download_and_send()

        elif self.type == RECORDING:
            return download_and_send()

        else:
            raise_properly('Unsupported message type:\n{}'.format(self))
