# coding: utf-8
from __future__ import unicode_literals

import logging

from wxpy.compatible.utils import force_encoded_string_output
from wxpy.utils import repr_message

logger = logging.getLogger(__name__)


class SentMessage(object):
    """
    程序中通过 .send/reply() 系列方法发出的消息
    
    *使用程序发送的消息也将被记录到历史消息 bot.messages 中*
    """

    def __init__(self, attributes):

        # 消息的类型 (仅可为 'Text', 'Picture', 'Video', 'Attachment')
        self.type = None

        # 消息的服务端 ID
        self.id = None

        # 消息的本地 ID (撤回时需要用到)
        self.local_id = None

        # 消息的文本内容
        self.text = None

        # 消息附件的本地路径
        self.path = None

        # 消息的附件 media_id
        self.media_id = None

        # 本地发送时间
        self.create_time = None

        # 接收服务端响应时间
        self.receive_time = None

        self.receiver = None

        # send_raw_msg 的各属性
        self.raw_type = None
        self.raw_content = None
        self.uri = None
        self.msg_ext = None

        for k, v in attributes.items():
            setattr(self, k, v)

    def __hash__(self):
        return hash((SentMessage, self.id))

    @force_encoded_string_output
    def __repr__(self):
        return repr_message(self)

    def __unicode__(self):
        return repr_message(self)

    @property
    def latency(self):
        """
        消息的延迟秒数 (发送时间和响应时间的差值)
        """
        if self.create_time and self.receive_time:
            return (self.receive_time - self.create_time).total_seconds()

    @property
    def chat(self):
        """
        消息所在的聊天会话 (始终为消息的接受者)
        """
        return self.receiver

    @property
    def member(self):
        """
        若在群聊中发送消息，则为群员
        """
        from wxpy import Group

        if isinstance(Group, self.receiver):
            return self.receiver.self

    @property
    def bot(self):
        """
        消息所属的机器人
        """
        return self.receiver.bot

    @property
    def sender(self):
        """
        消息的发送者
        """
        return self.receiver.bot.self

    def recall(self):
        """
        撤回本条消息 (应为 2 分钟内发出的消息)
        """

        logger.info('recalling msg:\n{}'.format(self))

        from wxpy.utils import BaseRequest
        req = BaseRequest(self.bot, '/webwxrevokemsg')
        req.data.update({
            "ClientMsgId": self.local_id,
            "SvrMsgId": str(self.id),
            "ToUserName": self.receiver.user_name,
        })

        # noinspection PyUnresolvedReferences
        return req.post()
