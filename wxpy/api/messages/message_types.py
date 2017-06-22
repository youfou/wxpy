# coding: utf-8
from __future__ import unicode_literals

from wxpy.compatible.utils import force_encoded_string_output


class MessageType(object):
    def __init__(self, name='unknown', l1=None, l2=None):

        """
        消息类型

        :param name: 友好类型名称
        :param l1: 原始 1 级类型
        :param l2: 原始 2 级类型
        """

        self.l1 = l1
        self.l2 = l2
        self.name = name

    @force_encoded_string_output
    def __repr__(self):
        return '<MsgType: {} ({}, {})>'.format(self.name, self.l1, self.l2)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    def __eq__(self, other):
        """
        | 对比两者的 l1 和 l2, 一方为 None 时不限制
        | 或直接字符串匹配名称
        """

        if isinstance(other, MessageType):
            for level in 'l1', 'l2':
                ls = getattr(self, level)
                lo = getattr(other, level)
                if None not in (ls, lo) and ls != lo:
                    return False
            return True
        else:
            return other == self.name

    def __cmp__(self, other):
        return 0 if self.__eq__(other) else 1

    def __hash__(self):
        return hash((self.name, self.l1, self.l2))


# 文本
TEXT = MessageType('text', 1, 0)
# 位置
LOCATION = MessageType('location', 1, 48)
# 图片
IMAGE = MessageType('image', 3, 0)
# 语音
VOICE = MessageType('voice', 34, 0)
# 好友验证
NEW_FRIEND = MessageType('new_friend', 37, 0)
# 名片
CARD = MessageType('card', 42, 0)
# 视频
VIDEO = MessageType('video', 43, 0)
# 表情
EMOTICON = MessageType('emotion', 47, 0)
# URL
URL = MessageType('url', 49, 5)
# 文件
FILE = MessageType('file', 49, 6)
# 转账
CASH_TRANSFER = MessageType('cash_transfer', 49, 2000)
# 系统提示
NOTICE = MessageType('notice', 10000, 0)
# 撤回提示
RECALLED = MessageType('recalled', 10002, 0)
# 未知的消息类型
UNKNOWN = MessageType()

ALL_MSG_TYPES = (
    TEXT, LOCATION, IMAGE, VOICE,
    NEW_FRIEND, CARD, VIDEO, EMOTICON,
    URL, FILE, CASH_TRANSFER, NOTICE,
    # UNKNOWN_MSG 必须排在最后 (轮询时最后匹配)
    RECALLED, UNKNOWN
)
