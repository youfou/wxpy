# coding: utf-8
from __future__ import unicode_literals
import random
import re


def get_context_user_id(msg, max_len=32, re_sub=r'[^a-zA-Z\d]'):
    """
    | 通过消息对象获取 Tuling, XiaoI 等聊天机器人的上下文用户 ID
    | 上下文用户 ID: 为群聊时，取群员的 user_name；非群聊时，取聊天对象的 user_name

    :param msg: 消息对象
    :param max_len: 最大长度 (从末尾截取)
    :param re_sub: 需要移除的字符的正则表达式 (为符合聊天机器人的 API 规范)
    :return: 上下文用户 ID
    """

    from wxpy.api.messages import Message
    from wxpy.api.chats import Group

    # 当 msg 不为消息对象时，返回 None
    if not isinstance(msg, Message):
        return

    if isinstance(msg.sender, Group):
        user = msg.member
    else:
        user = msg.sender

    user_id = re.sub(re_sub, '', user.user_name)

    return user_id[-max_len:]


def next_topic():
    """
    聊天机器人无法获取回复时的备用回复
    """

    return random.choice((
        '换个话题吧',
        '聊点别的吧',
        '下一个话题吧',
        '无言以对呢',
        '这话我接不了呢'
    ))
