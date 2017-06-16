# coding: utf-8
from __future__ import unicode_literals

import datetime
import logging
import re
import time
from functools import partial, wraps

from wxpy.api.consts import ATTACHMENT, PICTURE, TEXT, VIDEO
from wxpy.compatible import *
from wxpy.compatible.utils import force_encoded_string_output
from wxpy.utils import handle_response

logger = logging.getLogger(__name__)


def wrapped_send(msg_type):
    """
    send() 系列方法较为雷同，因此采用装饰器方式完成发送，并返回 SentMessage 对象
    """

    def decorator(func):
        @wraps(func)
        def wrapped(self, *args, **kwargs):

            # 用于初始化 SentMessage 的属性
            sent_attrs = dict(
                type=msg_type, receiver=self,
                create_time=datetime.datetime.now()
            )

            # 被装饰函数需要返回两个部分:
            # itchat_call_or_ret: 请求 itchat 原函数的参数字典 (或返回值字典)
            # sent_attrs_from_method: 方法中需要添加到 SentMessage 的属性字典
            itchat_call_or_ret, sent_attrs_from_method = func(self, *args, **kwargs)

            if msg_type:
                # 找到原 itchat 中的同名函数，并转化为指定了 `toUserName` 的偏函数
                itchat_partial_func = partial(
                    getattr(self.bot.core, func.__name__),
                    toUserName=self.user_name
                )

                logger.info('sending {} to {}:\n{}'.format(
                    func.__name__[5:], self,
                    sent_attrs_from_method.get('text') or sent_attrs_from_method.get('path')
                ))

                @handle_response()
                def do_send():
                    return itchat_partial_func(**itchat_call_or_ret)

                ret = do_send()
            else:
                # send_raw_msg 会直接返回结果
                ret = itchat_call_or_ret

            sent_attrs['receive_time'] = datetime.datetime.now()

            try:
                sent_attrs['id'] = int(ret.get('MsgID'))
            except (ValueError, TypeError):
                pass

            sent_attrs['local_id'] = ret.get('LocalID')

            # 加入被装饰函数返回值中的属性字典
            sent_attrs.update(sent_attrs_from_method)

            from wxpy import SentMessage
            sent = SentMessage(attributes=sent_attrs)
            self.bot.messages.append(sent)

            return sent

        return wrapped

    return decorator


class Chat(object):
    """
    单个用户 (:class:`User`) 和群聊 (:class:`Group`) 的基础类
    """

    def __init__(self, raw, bot):

        self.raw = raw
        self.bot = bot

    @property
    def puid(self):
        """
        持续有效，且稳定唯一的聊天对象/用户ID，适用于持久保存
        
        请使用 :any:`Bot.enable_puid()` 来启用 puid 属性
        
        ..  tip::
        
            | :any:`puid <Chat.puid>` 是 **wxpy 特有的聊天对象/用户ID**
            | 不同于其他 ID 属性，**puid** 可始终被获取到，且具有稳定的唯一性

        ..  attention::
        
            puid 映射数据 **不可跨机器人使用**

        """

        if self.bot.puid_map:
            return self.bot.puid_map.get_puid(self)
        else:
            raise TypeError('puid is not enabled, you can enable it by `bot.enable_puid()`')

    @property
    def nick_name(self):
        """
        该聊天对象的昵称 (好友、群员的昵称，或群名称)
        """
        if self.user_name == 'filehelper':
            return '文件传输助手'
        elif self.user_name == 'fmessage':
            return '好友请求'
        else:
            return self.raw.get('NickName')

    @property
    def name(self):
        """
        | 该聊天对象的友好名称
        | 具体为: 从 备注名称、群聊显示名称、昵称(或群名称)，或微信号中
        | 按序选取第一个可用的
        """
        for attr in 'remark_name', 'display_name', 'nick_name', 'wxid':
            _name = getattr(self, attr, None)
            if _name:
                return _name

    def send(self, content=None, media_id=None):
        """
        动态发送不同类型的消息，具体类型取决于 `msg` 的前缀。

        :param content:
            * 由 **前缀** 和 **内容** 两个部分组成，若 **省略前缀**，将作为纯文本消息发送
            * **前缀** 部分可为: '@fil@', '@img@', '@msg@', '@vid@' (不含引号)
            * 分别表示: 文件，图片，纯文本，视频
            * **内容** 部分可为: 文件、图片、视频的路径，或纯文本的内容
        :param media_id: 填写后可省略上传过程
        :rtype: :class:`wxpy.SentMessage`
        """

        method_map = dict(fil=self.send_file, img=self.send_image, vid=self.send_video)
        content = str('' if content is None else content)

        try:
            method, content = re.match(r'@(\w{3})@(.+)', content).groups()
        except AttributeError:
            method = None

        if method:
            return method_map[method](path=content, media_id=media_id)
        else:
            return self.send_msg(msg=content)

    @wrapped_send(TEXT)
    def send_msg(self, msg=None):
        """
        发送文本消息

        :param msg: 文本内容
        :rtype: :class:`wxpy.SentMessage`
        """

        if msg is None:
            msg = 'Hello from wxpy!'
        else:
            msg = str(msg)

        return dict(msg=msg), dict(text=msg)

    # Todo: 发送后可获取到 media_id

    @wrapped_send(PICTURE)
    def send_image(self, path, media_id=None):
        """
        发送图片

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        :rtype: :class:`wxpy.SentMessage`
        """

        return dict(fileDir=path, mediaId=media_id), locals()

    @wrapped_send(ATTACHMENT)
    def send_file(self, path, media_id=None):
        """
        发送文件

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        :rtype: :class:`wxpy.SentMessage`
        """

        return dict(fileDir=path, mediaId=media_id), locals()

    @wrapped_send(VIDEO)
    def send_video(self, path=None, media_id=None):
        """
        发送视频

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        :rtype: :class:`wxpy.SentMessage`
        """

        return dict(fileDir=path, mediaId=media_id), locals()

    @wrapped_send(None)
    def send_raw_msg(self, raw_type, raw_content, uri=None, msg_ext=None):
        """
        以原始格式发送其他类型的消息。

        :param int raw_type: 原始的整数消息类型
        :param str raw_content: 原始的消息内容
        :param str uri: 请求路径，默认为 '/webwxsendmsg'
        :param dict msg_ext: 消息的扩展属性 (会被更新到 `Msg` 键中)
        :rtype: :class:`wxpy.SentMessage`

        例如，发送好友或公众号的名片::

            my_friend.send_raw_msg(
                # 名片的原始消息类型
                raw_type=42,
                # 注意 `username` 在这里应为微信 ID，且被发送的名片必须为自己的好友
                raw_content='<msg username="wxpy_bot" nickname="wxpy 机器人"/>'
            )
        """

        logger.info('sending raw msg to {}'.format(self))

        uri = uri or '/webwxsendmsg'

        from wxpy.utils import BaseRequest
        req = BaseRequest(self.bot, uri=uri)

        msg = {
            'Type': raw_type,
            'Content': raw_content,
            'FromUserName': self.bot.self.user_name,
            'ToUserName': self.user_name,
            'LocalID': int(time.time() * 1e4),
            'ClientMsgId': int(time.time() * 1e4),
        }

        if msg_ext:
            msg.update(msg_ext)

        req.data.update({'Msg': msg, 'Scene': 0})

        # noinspection PyUnresolvedReferences
        return req.post(), {
            'raw_type': raw_type,
            'raw_content': raw_content,
            'uri': uri,
            'msg_ext': msg_ext,
        }

    @handle_response()
    def mark_as_read(self):
        """
        消除当前聊天对象的未读提示小红点
        """

        from wxpy.utils import BaseRequest
        req = BaseRequest(
            bot=self.bot,
            # itchat 中的 pass_ticket 已经预先编码了
            uri='/webwxstatusnotify?pass_ticket={}'.format(self.bot.core.loginInfo['pass_ticket'])
        )

        req.data.update({
            'ClientMsgId': int(time.time() * 1000),
            'Code': 1,
            'FromUserName': self.bot.self.user_name,
            'ToUserName': self.user_name,
        })

        logger.debug('marking {} as read'.format(self))

        return req.request('POST')

    @handle_response()
    def pin(self):
        """
        将聊天对象置顶
        """
        logger.info('pinning {}'.format(self))
        return self.bot.core.set_pinned(userName=self.user_name, isPinned=True)

    @handle_response()
    def unpin(self):
        """
        取消聊天对象的置顶状态
        """
        logger.info('unpinning {}'.format(self))
        return self.bot.core.set_pinned(userName=self.user_name, isPinned=False)

    @handle_response()
    def get_avatar(self, save_path=None):
        """
        获取头像

        :param save_path: 保存路径(后缀通常为.jpg)，若为 `None` 则返回字节数据
        """

        logger.info('getting avatar of {}'.format(self))

        from .group import Group
        from .member import Member
        from .friend import User

        if isinstance(self, Group):
            kwargs = dict(userName=None, chatroomUserName=self.user_name)
        elif isinstance(self, Member):
            kwargs = dict(userName=self.user_name, chatroomUserName=self.group.user_name)
        elif isinstance(self, User):
            kwargs = dict(userName=self.user_name, chatroomUserName=None)
        else:
            raise TypeError('expected `Chat`, got`{}`'.format(type(self)))

        kwargs.update(dict(picDir=save_path))

        return self.bot.core.get_head_img(**kwargs)

    @property
    def uin(self):
        """
        微信中的聊天对象ID，固定且唯一

        | 因微信的隐私策略，该属性有时无法被获取到
        | 建议使用 :any:`puid <Chat.puid>` 作为用户的唯一 ID
        """
        return self.raw.get('Uin')

    @property
    def alias(self):
        """
        若用户进行过一次性的 "设置微信号" 操作，则该值为用户设置的"微信号"，固定且唯一

        | 因微信的隐私策略，该属性有时无法被获取到
        | 建议使用 :any:`puid <Chat.puid>` 作为用户的唯一 ID
        """
        return self.raw.get('Alias')

    @property
    def wxid(self):
        """
        聊天对象的微信ID (实际为 .alias 或 .uin)

        | 因微信的隐私策略，该属性有时无法被获取到
        | 建议使用 :any:`puid <Chat.puid>` 作为用户的唯一 ID
        """

        return self.alias or self.uin or None

    @property
    def user_name(self):
        """
        该聊天对象的内部 ID，通常不需要用到

        ..  attention::

            同个聊天对象在不同用户中，此 ID **不一致** ，且可能在新会话中 **被改变**！
        """
        return self.raw.get('UserName')

    @force_encoded_string_output
    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __unicode__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __cmp__(self, other):
        if hash(self) == hash(other):
            return 0
        return 1

    def __hash__(self):
        return hash((Chat, self.user_name))
