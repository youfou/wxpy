# coding: utf-8
from __future__ import unicode_literals

import logging
import os
import re
from collections import namedtuple
from contextlib import closing
from datetime import datetime
from xml.etree import ElementTree as ETree

from wxpy.api.messages.message_types import *
from wxpy.compatible import PY2
from wxpy.compatible.utils import force_encoded_string_output
from wxpy.utils import repr_message

if PY2:
    # noinspection PyUnresolvedReferences
    from urllib import urlencode
else:
    from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# 公众号推送中的单篇文章内容 (一次可推送多篇)
# 属性: 标题, 摘要, 文章 URL, 封面图片 URL
Article = namedtuple('Article', ['title', 'summary', 'url', 'cover'])

# 转账信息: 金额, 描述, 交易单号 (转账消息可被重复发送，所以要注意核对单号)
Cash = namedtuple('Cash', ['amount', 'description', 'id'])


class Message(object):
    """
    单条消息对象，包括:
    
    * 来自好友、群聊、好友请求等聊天对象的消息
    * 使用机器人账号在手机微信中发送的消息
    
    | 但 **不包括** 代码中通过 .send/reply() 系列方法发出的消息
    | 此类消息请参见 :class:`SentMessage`
    """

    def __init__(self, core, raw):
        self.core = core
        self.bot = self.core.bot

        self.raw = raw

        self._receive_time = datetime.now()

        self._file_ext = None

        # 将 msg.chat.send* 方法绑定到 msg.reply*，例如 msg.chat.send_img => msg.reply_img
        for method in '', '_image', '_sticker', '_file', '_video':
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
            TEXT = 'TEXT'
            # 位置
            LOCATION = 'LOCATION'
            # 图片
            IMAGE = 'IMAGE'
            # 语音
            VOICE = 'VOICE'
            # 好友验证
            NEW_FRIEND = 'NEW_FRIEND'
            # 名片
            CARD = 'CARD'
            # 视频
            VIDEO = 'VIDEO'
            # 表情 (不支持商店表情，下载前请先检查 file_size 属性)
            EMOTICON = 'EMOTICON'
            # URL
            URL = 'SHARE_URL'
            # 文件
            FILE = 'FILE'
            # 转账
            CASH = 'CASH'
            # 系统提示
            NOTICE = 'NOTICE'
            # 撤回提示
            RECALLED = 'RECALLED'
            # 未知
            UNKNOWN = 'UNKNOWN'
        
        :rtype: MessageType
        """

        _type = MessageType(
            main=self.raw.get('MsgType'),
            app=self.raw.get('AppMsgType'),
            sub=self.raw.get('SubMsgType'),
        )

        for t in KNOWN_MSG_TYPES:
            if _type == t:
                _type.name = t.name
                break

        return _type

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

        if self.type in (TEXT, NOTICE):
            return self._content
        elif self.type == LOCATION:
            found = re.search(r'^.+(?=:\n)', self._content)
            if found:
                return found.group()
        elif self.type in (URL, CASH):
            return self._content_xml.findtext('.//title')
        elif self.type == NEW_FRIEND:
            return self._content_xml.get('content')
        elif self.type == RECALLED:
            return self._content_xml.findtext('.//replacemsg')
        elif self.type == FILE:
            return self.file_name
        elif self.type == CARD:
            return self.card.name

    @property
    def _file_url(self):

        """
        | 消息中文件的下载地址 (内部使用)
        | 注意: 该 URL 会验证 cookies, 只能使用登陆所在的 session 进行下载
        | 若需下载，请使用 `get_file()` 方法
        """

        uris = self.core.uris
        tree = self._content_xml

        upper_params = {'MsgID': self.id, 'skey': self.core.data.skey, 'type': 'big'}
        lower_params = {'msgid': self.id, 'skey': self.core.data.skey}

        match = {
            IMAGE: (uris.get_msg_img, upper_params),
            STICKER: (uris.get_msg_img, upper_params),
            VOICE: (uris.get_voice, lower_params),
            VIDEO: (uris.get_video, lower_params),
        }.get(self.type)

        if tree and match:
            return '{}?{}'.format(match[0], urlencode(match[1]))
        elif self.type == FILE:
            return '{}?{}'.format(uris.get_media, urlencode(dict(
                sender=self.raw['FromUserName'],
                mediaid=self.media_id,
                filename=self._content_xml.findtext('.//title'),
                fromuser=self.core.data.raw_self['Uin'],
                pass_ticket=self.core.data.pass_ticket,
                webwx_data_ticket=self.core.from_cookies('webwx_data_ticket')
            )))

    @property
    def file_name(self):
        """
        消息中文件的文件名 (含后缀名)
        """
        if self._content_xml and self.type in (IMAGE, STICKER, VOICE, VIDEO):
            return '{}{}'.format(self.id, self.file_ext)
        elif self.type == FILE:
            return self._content_xml.findtext('.//title')

    @property
    def file_ext(self):
        """ 消息中文件的后缀名，例如 .jpeg, .png, .mp3 """

        if self._content_xml and self.type in (IMAGE, STICKER, VOICE, VIDEO):
            if not self._file_ext:
                with closing(self.core.session.get(self._file_url, stream=True)) as resp:
                    if resp.headers.get('Content-Type'):
                        self._file_ext = '.{}'.format(re.findall(r'\w+', resp.headers['Content-Type'])[-1])
            return self._file_ext
        elif self.type == FILE:
            return os.path.splitext(self.file_name)[1]

    def get_file(self, save_path=None):
        """
        下载图片、视频、语音、附件消息中的文件内容。

        可与 :any:`Message.file_name`, :any:`Message.file_ext` 配合使用。

        :param save_path: 文件的保存路径。若为 None，将直接返回字节数据
        """

        if self._file_url:
            return self.core.download(self._file_url, save_path)

    @property
    def file_size(self):
        """
        消息中文件的体积大小
        """
        match = {
            IMAGE: ('img', 'hdlength'),
            STICKER: ('img', 'hdlength'),
            VOICE: ('voicemsg', 'length'),
            VIDEO: ('videomsg', 'length'),
        }.get(self.type)

        if self._content_xml and match:
            return int(self._content_xml.find(match[0]).get(match[1]))
        elif self.type == FILE:
            return int(self._content_xml.findtext('.//totallen'))

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

        from wxpy.api.chats import Group

        if self.type == TEXT and isinstance(self.chat, Group):
            return bool(re.search(r'@' + re.escape(self.chat.self.name) + r'(?:\u2005|\s|$)', self.text))

    # misc

    @property
    def url(self):
        """
        分享类消息中的网页 URL
        """
        return self.raw.get('Url')

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
        if self.type == URL and isinstance(self.sender, MP):
            tree = ETree.fromstring(self.raw['Content'])
            # noinspection SpellCheckingInspection
            items = tree.findall('.//mmreader/category/item')

            article_list = list()

            for item in items:
                article = Article(
                    title=item.findtext('title'),
                    summary=item.findtext('digest'),
                    url=item.findtext('url'),
                    cover=item.findtext('cover'),
                )
                article_list.append(article)

            return article_list

    @property
    def card(self):
        """
        * 好友请求中的请求用户
        * 名片消息中的推荐用户
        """
        from wxpy.api.chats import User

        if self.type in (CARD, NEW_FRIEND):
            return User(self.core, self.raw.get('RecommendInfo'))

    @property
    def recalled_id(self):
        """
        被撤回消息的消息 ID
        """
        if self.type == RECALLED:
            return int(self._content_xml.findtext('.//msgid'))

    @property
    def cash(self):
        if self.type == CASH:
            tree = self._content_xml.find('.//wcpayinfo')
            return Cash(
                amount=float(re.search(r'\d+\.\d+', tree.findtext('feedesc')).group()),
                description=tree.findtext('pay_memo'),
                id=tree.findtext('transcationid'),
            )

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

        if self.raw.get('FromUserName') == self.core.username:
            return self.receiver
        else:
            return self.sender

    @property
    def sender(self):
        """
        消息的发送者
        
        :rtype: :class:`wxpy.User`, :class:`wxpy.Group`
        """

        return self.core.get_chat_obj(self.raw.get('FromUserName'))

    @property
    def receiver(self):
        """
        消息的接收者
        
        :rtype: :class:`wxpy.User`, :class:`wxpy.Group`
        """

        return self.core.get_chat_obj(self.raw.get('ToUserName'))

    @property
    def member(self):
        """
        * 若消息来自群聊，则此属性为消息的实际发送人(具体的群成员)
        * 若消息来自其他聊天对象(非群聊)，则此属性为 None
        
        :rtype: NoneType, :class:`wxpy.Member`
        """

        from wxpy.api.chats import Group

        if isinstance(self.chat, Group):
            found = re.search(r'^(@[\da-f]+):\n', self.raw['Content'])
            if found:
                return self.core.get_chat_obj(found.group(1), self.chat.username)
            elif self.type != NOTICE:
                return self.chat.self

    @property
    def _content(self):
        """ Content 字段中去除群员 username 后剩余的部分 """

        from wxpy.api.chats import Group

        if isinstance(self.sender, Group):
            content = re.sub(r'^@[\da-f]+:\n', '', self.raw['Content'])
            if self.type == VIDEO:
                # 发现当有人在群里发视频时，有时 Content 顶部会多 'xxx:\n' 在第二行 (xxx 是该群员的微信 ID)
                content = re.sub(r'^[\da-zA-Z\-_]+:\n', '', content)
            return content
        else:
            return self.raw['Content']

    @property
    def _content_xml(self):
        """ Content 字段中的 xml 对象 """
        try:
            return ETree.fromstring(self._content)
        except ETree.ParseError:
            pass

    def forward(self, chat, prefix=None, suffix=None):
        """
        将本消息转发给其他聊天对象

        支持以下消息类型
            * 文本 (`TEXT`)
            * 图片 (`IMAGE`)
            * 自定义表情 (`STICKER`)
                * 注: 不支持表情商店中的表情
            * 视频（`VIDEO`)
            * 文件 (`FILE`)
            * 名片 (`CARD`)
            * 语音 (`VOICE`)
                * 注: 会以文件方式发送
            * 分享链接 (`URL`)
                * 注: 会转化为 `标题 + 链接` 形式的文本消息
            * 地图 (`LOCATION`)
                * 注: 会转化为 `位置名称 + 地图链接` 形式的文本消息

        :param Chat chat: 接收转发消息的聊天对象
        :param str prefix: 转发时增加的 **前缀** 文本，原消息为文本时会自动换行
        :param str suffix: 转发时增加的 **后缀** 文本，原消息为文本时会自动换行

        :return: 若该消息支持转发，返回转发后的 :class:`SentMessage` 对象；反之返回 `NotImplemented`

        例如，将公司群中的老板消息转发出来::

            from wxpy import *

            bot = Bot()

            # 定位公司群
            company_group = bot.groups.get('公司微信群')

            # 定位老板
            boss = company_group.get('老板大名')

            # 将老板的消息转发到文件传输助手
            @bot.register(company_group)
            def forward_boss_message(msg):
                if msg.member == boss:
                    msg.forward(bot.file_helper, prefix='老板发言')

            # 阻塞线程
            embed()

        """

        logger.info('{}: forwarding to {}: {}'.format(self.bot, chat, self))

        if self.type in (TEXT, NOTICE):
            return chat.send('{}{}{}'.format(
                '{}\n'.format(prefix) if prefix else '',
                self.text,
                '{}\n'.format(suffix) if suffix else '',
            ))

        elif self.type in (IMAGE, STICKER, VIDEO, FILE):
            pass
