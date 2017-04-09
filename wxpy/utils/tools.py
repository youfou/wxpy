import logging
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
