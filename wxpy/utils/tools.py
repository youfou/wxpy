# coding: utf-8
from __future__ import unicode_literals

import logging
import time
from functools import wraps

from wxpy.exceptions import ResponseError

logger = logging.getLogger(__name__)


def dont_raise_response_error(func):
    """
    装饰器：用于避免被装饰的函数在运行过程中抛出 ResponseError 错误
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResponseError as e:
            logger.warning('{0.__class__.__name__}: {0}'.format(e))

    return wrapped


def ensure_one(found):
    """
    确保列表中仅有一个项，并返回这个项，否则抛出 `ValueError` 异常

    通常可用在查找聊天对象时，确保查找结果的唯一性，并直接获取唯一项

    :param found: 列表
    :return: 唯一项
    """
    if not isinstance(found, list):
        raise TypeError('expected list, {} found'.format(type(found)))
    elif not found:
        raise ValueError('not found')
    elif len(found) > 1:
        raise ValueError('more than one found')
    else:
        return found[0]


def mutual_friends(*args):
    """
    找到多个微信用户的共同好友

    :param args: 每个参数为一个微信用户的机器人(Bot)，或是聊天对象合集(Chats)
    :return: 共同好友列表
    :rtype: :class:`wxpy.Chats`
    """

    from wxpy.api.bot import Bot
    from wxpy.api.chats import Chats, User

    class FuzzyUser(User):
        def __init__(self, user):
            super(FuzzyUser, self).__init__(user.raw, user.bot)

        def __hash__(self):
            return hash((self.nick_name, self.sex, self.province, self.city, self.raw['AttrStatus']))

    mutual = set()

    for arg in args:
        if isinstance(arg, Bot):
            friends = map(FuzzyUser, arg.friends())
        elif isinstance(arg, Chats):
            friends = map(FuzzyUser, arg)
        else:
            raise TypeError

        if mutual:
            mutual &= set(friends)
        else:
            mutual.update(friends)

    return Chats(mutual)


def detect_freq_limit(func, *args, **kwargs):
    """
    检测各类 Web 微信操作的频率限制，获得限制次数和周期
    
    :param func: 需要执行的操作函数
    :param args: 操作函数的位置参数
    :param kwargs: 操作函数的命名参数
    :return: 限制次数, 限制周期(秒数)
    """

    start = time.time()
    count = 0

    while True:
        try:
            func(*args, **kwargs)
        except ResponseError as e:
            logger.info('freq limit reached: {} requests passed, error_info: {}'.format(count, e))
            break
        else:
            count += 1
            logger.debug('{} passed'.format(count))

    while True:
        period = time.time() - start
        try:
            func(*args, **kwargs)
        except ResponseError:
            logger.debug('blocking: {:.0f} secs'.format(period))
            time.sleep(1)
        else:
            logger.info('freq limit detected: {} requests / {:.0f} secs'.format(count, period))
            return count, period
