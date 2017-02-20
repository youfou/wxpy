import logging
from functools import wraps

from .wx import Chats, ResponseError, Robot, User


def dont_raise_response_error(func):
    """
    装饰器：用于避免抛出 ResponseError 错误
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResponseError as e:
            logging.warning('{0.__class__.__name__}: {0}'.format(e))

    return wrapped


def mutual_friends(*args):
    """
    找到多个微信用户的共同好友
    :param args: 每个参数表示一个微信用户，可以是机器人(Robot)，或聊天对象合集(Chats)
    :return: 共同的好友
    """
    class FuzzyUser(User):
        def __init__(self, user):
            super(FuzzyUser, self).__init__(user)

        def __hash__(self):
            return hash((self.nick_name, self.province, self.city, self['AttrStatus']))

    mutual = set()

    for arg in args:
        if isinstance(arg, Robot):
            friends = map(FuzzyUser, arg.friends)
        elif isinstance(arg, Chats):
            friends = map(FuzzyUser, arg)
        else:
            raise TypeError

        if mutual:
            mutual &= set(friends)
        else:
            mutual.update(friends)

    return Chats(mutual)
