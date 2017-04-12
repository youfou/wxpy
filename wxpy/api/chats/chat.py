import json
import logging
import time

import itchat.config
import itchat.returnvalues

from wxpy.utils import handle_response

logger = logging.getLogger(__name__)


class Chat(object):
    """
    单个用户(:class:`User`)和群聊(:class:`Group`)的基础类
    """

    def __init__(self, raw, bot):

        self.raw = raw
        self.bot = bot

        self.alias = self.raw.get('Alias')
        self.uin = self.raw.get('Uin')

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
        | 具体为: 从 备注名称、群聊显示名称、昵称(或群名称)，或微信号中，按序选取第一个可用的
        """
        for attr in 'remark_name', 'display_name', 'nick_name', 'wxid':
            _name = getattr(self, attr, None)
            if _name:
                return _name

    @property
    def wxid(self):
        """
        | 微信号
        | 有可能获取不到 (手机客户端也可能获取不到)
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

    @handle_response()
    def send(self, content='Hello, wxpy!', media_id=None):
        """
        动态发送不同类型的消息，具体类型取决于 `msg` 的前缀。

        :param content:
            * 由 **前缀** 和 **内容** 两个部分组成，若 **省略前缀**，将作为纯文本消息发送
            * **前缀** 部分可为: '@fil@', '@img@', '@msg@', '@vid@' (不含引号)
            * 分别表示: 文件，图片，纯文本，视频
            * **内容** 部分可为: 文件、图片、视频的路径，或纯文本的内容
        :param media_id: 填写后可省略上传过程
        """
        logger.info('sending to {}:\n{}'.format(self, content))
        return self.bot.core.send(msg=str(content), toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_image(self, path, media_id=None):
        """
        发送图片

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        logger.info('sending image to {}:\n{}'.format(self, path))
        return self.bot.core.send_image(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_file(self, path, media_id=None):
        """
        发送文件

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        logger.info('sending file to {}:\n{}'.format(self, path))
        return self.bot.core.send_file(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_video(self, path=None, media_id=None):
        """
        发送视频

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        logger.info('sending video to {}:\n{}'.format(self, path))
        return self.bot.core.send_video(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_msg(self, msg):
        """
        发送文本消息

        :param msg: 文本内容
        """
        logger.info('sending msg to {}:\n{}'.format(self, msg))
        return self.bot.core.send_msg(msg=str(msg), toUserName=self.user_name)

    @handle_response()
    def send_raw_msg(self, msg_type, content, uri=None, msg_ext=None):
        """
        以原始格式发送其他类型的消息。

        :param int msg_type: 原始的整数消息类型
        :param str content: 原始的消息内容
        :param str uri: 请求路径，默认为 '/webwxsendmsg'
        :param dict msg_ext: 消息的扩展属性 (会被更新到 `Msg` 键中)

        例如，好友名片::

            from wxpy import *
            bot = Bot()
            @bot.register(msg_types=CARD)
            def reply_text(msg):
                msg.chat.send_raw_msg(msg.raw['MsgType'], msg.raw['Content'])
        """

        core = self.bot.core
        url = core.loginInfo['url'] + (uri or '/webwxsendmsg')

        msg = {
            'Type': msg_type,
            'Content': content,
            'FromUserName': self.bot.self.user_name,
            'ToUserName': self.user_name,
            'LocalID': int(time.time() * 1e4),
            'ClientMsgId': int(time.time() * 1e4),
        }

        if msg_ext:
            msg.update(msg_ext)

        payload = {
            'BaseRequest': core.loginInfo['BaseRequest'],
            'Msg': msg,
            'Scene': 0,
        }

        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent': itchat.config.USER_AGENT
        }

        r = core.s.post(
            url, headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
        )

        logger.info('sent raw msg to {}'.format(self))
        return itchat.returnvalues.ReturnValue(rawResponse=r)

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

        from .friend import Friend
        from .group import Group
        from .member import Member

        if isinstance(self, Friend):
            kwargs = dict(userName=self.user_name, chatroomUserName=None)
        elif isinstance(self, Group):
            kwargs = dict(userName=None, chatroomUserName=self.user_name)
        elif isinstance(self, Member):
            kwargs = dict(userName=self.user_name, chatroomUserName=self.group.user_name)
        else:
            raise TypeError('expected `Friend`, `Group` or `Member`, got`{}`'.format(type(self)))

        kwargs.update(dict(picDir=save_path))

        return self.bot.core.get_head_img(**kwargs)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((Chat, self.user_name))
