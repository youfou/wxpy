# coding: utf-8
from __future__ import unicode_literals

from wxpy.compatible.utils import force_encoded_string_output


class MessageType(object):
    def __init__(self, name='UNKNOWN', main=None, app=None, sub=None):

        """
        消息类型

        :param name: 友好类型名称
        :param main: 主要类型
        :param app: 应用类型
        :param sub: 子类型
        """

        self.name = name

        self.main = main
        self.app = app
        self.sub = sub

    @force_encoded_string_output
    def __repr__(self):
        return '<MsgType: {} ({}, {}, {})>'.format(
            self.name, self.main, self.app, self.sub)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    def __eq__(self, other):
        """
        | 对比两者的各类型 ID, 一方为 None 时不限制
        | 或直接字符串匹配名称
        """

        if isinstance(other, MessageType):
            match = 0
            for type_name in 'main', 'app', 'sub':
                a = getattr(self, type_name)
                b = getattr(other, type_name)
                if None in (a, b):
                    continue
                if a != b:
                    return False
                match += 1
            return match
        else:
            return other == self.name

    def __cmp__(self, other):
        return 0 if self.__eq__(other) else 1

    def __hash__(self):
        return hash((self.name, self.main, self.app))


# 文本
TEXT = MessageType('TEXT', 1, 0, 0)
# 位置
LOCATION = MessageType('LOCATION', 1, 0, 48)
# 图片
IMAGE = MessageType('IMAGE', 3, 0, 0)
# 语音
VOICE = MessageType('VOICE', 34, 0, 0)
# 好友验证
NEW_FRIEND = MessageType('NEW_FRIEND', 37, 0, 0)
# 名片
CARD = MessageType('CARD', 42, 0, 0)
# 视频
VIDEO = MessageType('VIDEO', 43, 0, 0)
# 表情 (不支持商店表情，下载前请先检查 file_size 属性)
STICKER = MessageType('STICKER', 47, 0, 0)
# URL
URL = MessageType('URL', 49, 5, 0)
# 文件
FILE = MessageType('FILE', 49, 6, 0)
# 转账
CASH = MessageType('CASH', 49, 2000, 0)
# 系统提示
NOTICE = MessageType('NOTICE', 10000, 0, 0)
# 撤回提示
RECALLED = MessageType('RECALLED', 10002, 0, 0)

KNOWN_MSG_TYPES = (
    TEXT, LOCATION, IMAGE, VOICE,
    NEW_FRIEND, CARD, VIDEO, STICKER,
    URL, FILE, CASH, NOTICE, RECALLED
)

# 未知
UNKNOWN = MessageType()
