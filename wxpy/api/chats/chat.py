# coding: utf-8
from __future__ import unicode_literals

import logging

from wxpy.compatible.utils import force_encoded_string_output
from wxpy.api.messages.message_types import *

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
            return self._chat.get('NickName') or None
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

    # Todo: 支持发送名片
    # Todo: 发送后返回 SentMessage
    def send(self, content, send_type=None, media_id=None):
        """
        发送消息。默认为发送文本消息，也可指定其他消息类型

        :param content: 消息类型为 TEXT 时为消息的文本内容，其他类型时为文件路径
        :param send_type: 消息类型，支持 TEXT, IMAGE, EMOTICON, VIDEO, FILE (默认为 TEXT)
        :param media_id: 文件在服务器中的唯一 ID，填写后可省略上传步骤
        :return: 已发送的消息
        :rtype: :class:`SentMessage`
        """

        return self.core.send(self, content, send_type, media_id)

    def send_image(self, path, media_id=None):
        """
        发送图片

        :param path: 图片的文件路径
        :param media_id: 文件在服务器中的唯一 ID，填写后可省略上传步骤
        :return: 已发送的消息
        :rtype: :class:`SentMessage`
        """

        return self.send(path, IMAGE, media_id)

    def send_sticker(self, path, media_id=None):
        """
        发送表情 (类似于手机端中发送收藏的表情)

        :param path: 表情图片的文件路径
        :param media_id: 文件在服务器中的唯一 ID，填写后可省略上传步骤
        :return: 已发送的消息
        :rtype: :class:`SentMessage`
        """

        return self.send(path, STICKER, media_id)

    def send_video(self, path, media_id=None):
        """
        发送视频

        :param path: 视频的文件路径 (通常为 mp4 格式)
        :param media_id: 文件在服务器中的唯一 ID，填写后可省略上传步骤
        :return: 已发送的消息
        :rtype: :class:`SentMessage`
        """

        return self.send(path, VIDEO, media_id)

    def send_file(self, path, media_id=None):
        """
        发送文件

        :param path: 文件路径
        :param media_id: 文件在服务器中的唯一 ID，填写后可省略上传步骤
        :return: 已发送的消息
        :rtype: :class:`SentMessage`
        """

        return self.send(path, FILE, media_id)

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
