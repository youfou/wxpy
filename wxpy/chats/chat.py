from ..utils import handle_response


class Chat(object):
    """
    单个用户(:class:`User`)和群聊(:class:`Group`)的基础类
    """

    def __init__(self, raw, bot):

        self.raw = raw
        self.bot = bot

        self.user_name = self.raw.get('UserName')
        self.nick_name = self.raw.get('NickName')

    @handle_response()
    def send(self, msg, media_id=None):
        """
        动态发送不同类型的消息，具体类型取决于 `msg` 的前缀。

        :param msg:
            | 由 **前缀** 和 **内容** 两个部分组成，若 **省略前缀**，将作为纯文本消息发送
            | **前缀** 部分可为: '@fil@', '@img@', '@msg@', '@vid@' (不含引号)
            | 分别表示: 文件，图片，纯文本，视频
            | **内容** 部分可为: 文件、图片、视频的路径，或纯文本的内容
        :param media_id: 填写后可省略上传过程
        """
        return self.bot.core.send(msg=str(msg), toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_image(self, path, media_id=None):
        """
        发送图片

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        return self.bot.core.send_image(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_file(self, path, media_id=None):
        """
        发送文件

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        return self.bot.core.send_file(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_video(self, path=None, media_id=None):
        """
        发送视频

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        return self.bot.core.send_video(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_msg(self, msg='Hello WeChat! -- by wxpy'):
        """
        发送文本消息

        :param msg: 文本内容
        """
        return self.bot.core.send_msg(msg=str(msg), toUserName=self.user_name)

    @handle_response()
    def send_raw_msg(self, msg_type, content):
        """
        以原始格式发送其他类型的消息。例如，好友名片::

            from wxpy import *
            bot = Bot()
            @bot.register(msg_types=CARD)
            def reply_text(msg):
                msg.chat.send_raw_msg(msg['MsgType'], msg['Content'])

        """
        return self.bot.core.send_raw_msg(msgType=msg_type, content=content, toUserName=self.user_name)

    @handle_response()
    def pin(self):
        """
        将聊天对象置顶
        """
        return self.bot.core.set_pinned(userName=self.user_name, isPinned=True)

    @handle_response()
    def unpin(self):
        """
        取消聊天对象的置顶状态
        """
        return self.bot.core.set_pinned(userName=self.user_name, isPinned=False)

    @property
    def name(self):
        """
        当前聊天对象的友好名称
        """
        for attr in 'remark_name', 'display_name', 'nick_name', 'alias':
            _name = getattr(self, attr, None)
            if _name:
                return _name

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((Chat, self.user_name))
