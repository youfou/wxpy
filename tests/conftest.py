# coding: utf-8

"""
部分用例需要与 "wxpy 机器人" 进行互动
"""

import os
import time
from functools import partial
from queue import Queue

import pytest

from wxpy import *

_base_dir = os.path.dirname(os.path.realpath(__file__))

print('logging in test bot...')
_bot = Bot(os.path.join(_base_dir, 'wxpy_bot.pkl'))
_friend = ensure_one(_bot.friends().search('wxpy 机器人'))
_group = ensure_one(_bot.groups().search('wxpy test'))
_member = ensure_one(_group.search('游否'))

_shared_dict = dict()

attachments_dir = os.path.join(_base_dir, 'attachments')
gen_attachment_path = partial(os.path.join, attachments_dir)

global_use = partial(pytest.fixture, scope='session', autouse=True)


@global_use()
def base_dir():
    return _base_dir


@global_use()
def bot():
    return _bot


@global_use()
def friend():
    yield _friend
    while True:
        try:
            _friend.set_remark_name('')
        except ResponseError as e:
            if e.err_code == 1205:
                time.sleep(10)
                continue
        else:
            break


@global_use()
def group():
    return _group


@global_use()
def shared_dict():
    return _shared_dict


@global_use()
def member():
    return _member


@global_use()
def image_path():
    return gen_attachment_path('image.png')


@global_use()
def file_path():
    return gen_attachment_path('file.txt')


@global_use()
def video_path():
    return gen_attachment_path('video.mp4')


def wait_for_message(chats=None, msg_types=None, except_self=True, timeout=30):
    """
    等待一条指定的消息，并返回这条消息

    :param chats: 所需等待消息所在的聊天会话
    :param msg_types: 所需等待的消息类型
    :param except_self: 是否排除自己发送的消息
    :param timeout: 等待的超时秒数，若为 None 则一直等待，直到收到所需的消息
    :return: 若在超时内等到了消息，则返回此消息，否则抛出 `queue.Empty` 异常
    """

    received = Queue()

    @_bot.register(chats=chats, msg_types=msg_types, except_self=except_self)
    def _func(msg):
        received.put(msg)

    _config = _bot.registered.get_config_by_func(_func)

    ret = received.get(timeout=timeout)

    _bot.registered.remove(_config)

    return ret
