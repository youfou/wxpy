# coding: utf-8
from __future__ import unicode_literals

import logging
import re
import time

from wxpy.compatible.utils import force_encoded_string_output

logger = logging.getLogger(__name__)


class Chat(object):
    def __init__(self, core, _chat):

        """
        基本聊天对象
            单个用户 (:class:`User`) 和群聊 (:class:`Group`) 的基础类

        :param core: 关联的内核对象
        :param _chat: username 或 原始数据 dict
        """

        self.core = core
        self.bot = self.core.bot

        self._chat = _chat

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

        if self.core.puid_map:
            return self.core.puid_map.get_puid(self)
        else:
            raise TypeError('puid is not enabled, you can enable it by `bot.enable_puid()`')

    @property
    def nickname(self):
        """
        该聊天对象的昵称 (好友、群员的昵称，或群名称)
        """

        from .member import Member

        if isinstance(self, Member):
            return self._raw.get('NickName') or None
        else:
            return self.raw.get('NickName') or None

    @property
    def name(self):
        """
        | 该聊天对象的友好名称
        | 即: 从 备注名称、群聊显示名称、昵称(或群名称)，username 中按序选取第一个可用的
        """
        for attr in 'remark_name', 'display_name', 'nickname', 'username':
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

        raise NotImplementedError

    # Todo: 发送后可获取到 media_id

    def send_image(self, path, media_id=None):
        """
        发送图片

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        :rtype: :class:`wxpy.SentMessage`
        """

        raise NotImplementedError

    def send_file(self, path, media_id=None):
        """
        发送文件

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        :rtype: :class:`wxpy.SentMessage`
        """

        raise NotImplementedError

    def send_video(self, path=None, media_id=None):
        """
        发送视频

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        :rtype: :class:`wxpy.SentMessage`
        """

        raise NotImplementedError

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

        msg = {
            'Type': raw_type,
            'Content': raw_content,
            'FromUserName': self.core.username,
            'ToUserName': self.username,
            'LocalID': int(time.time() * 1e4),
            'ClientMsgId': int(time.time() * 1e4),
        }

        if msg_ext:
            msg.update(msg_ext)

        raise NotImplementedError

    def mark_as_read(self):
        """
        消除当前聊天对象的未读提示小红点
        """

        logger.debug('marking {} as read'.format(self))

        raise NotImplementedError

    def pin(self):
        """
        将聊天对象置顶
        """
        logger.info('pinning {}'.format(self))
        raise NotImplementedError

    def unpin(self):
        """
        取消聊天对象的置顶状态
        """
        logger.info('unpinning {}'.format(self))
        raise NotImplementedError

    def get_avatar(self, save_path=None):
        """
        获取头像

        :param save_path: 保存路径(后缀通常为.jpg)，若为 `None` 则返回字节数据
        """

        logger.info('getting avatar of {}'.format(self))

        raise NotImplementedError

    @property
    def raw(self):
        """
        原始数据
        """

        if isinstance(self._chat, dict):
            return self._chat
        else:
            return self.core.data.raw_chats.get(self._chat, dict())

    @property
    def username(self):

        """
        该聊天对象的内部 ID，会随着登陆会话而改变，通常不需要用到

        ..  attention::
            此 ID 在机器人重新登录后 **会被改变** !
        """

        if isinstance(self._chat, str):
            return self._chat
        else:
            return self._chat['UserName']

    # @property
    # def uin(self):
    #     """
    #     微信中的聊天对象ID，固定唯一
    #
    #     | 该属性已被官方暂时屏蔽，通常无法被获取到
    #     | 建议使用 :any:`puid <Chat.puid>` 作为用户的唯一 ID
    #     """
    #     return self.raw.get('Uin') or None
    #
    # @property
    # def alias(self):
    #     """
    #     若用户进行过一次性的 "设置微信号" 操作，则该值为用户设置的"微信号"，固定唯一
    #
    #     | 该属性已被官方暂时屏蔽，通常无法被获取到
    #     | 建议使用 :any:`puid <Chat.puid>` 作为用户的唯一 ID
    #     """
    #     return self.raw.get('Alias') or None
    #
    # @property
    # def wxid(self):
    #     """
    #     聊天对象的微信ID (实际为 .alias 或 .uin)
    #
    #     | 该属性已被官方暂时屏蔽，通常无法被获取到
    #     | 建议使用 :any:`puid <Chat.puid>` 作为用户的唯一 ID
    #     """
    #
    #     return self.alias or self.uin

    def update(self):
        """
        更新聊天对象的详细信息

        ..  tip::

            | 对于群聊对象，`group.update()` 仅更新群本身，而不会更新群成员的详细信息
            | 若要更新群员信息，可使用 `group.members.update()`
        """

        self.core.batch_get_contact(self)

    @force_encoded_string_output
    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __cmp__(self, other):
        return 0 if self.__eq__(other) else 1

    def __hash__(self):
        return hash((Chat, self.username))
