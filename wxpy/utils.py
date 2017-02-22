import logging
import pprint
import re
from functools import wraps

import requests

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


class Tuling(object):
    """
    与 wxpy 深度整合的图灵机器人

    获取 api_key: http://www.tuling123.com/
    API 文档: http://tuling123.com/help/h_cent_webapi.jhtml
    """

    url = 'http://www.tuling123.com/openapi/api'

    def __init__(self, api_key):
        self.session = requests.Session()
        self.api_key = api_key

    def reply(self, msg, to_member=True):

        def process_answer():

            logging.debug('Tuling answer:\n' + pprint.pformat(answer))

            ret = str()
            if to_member and msg.member:
                name = member.display_name or member.nick_name
                if name:
                    ret += '@{} '.format(name)

            code = -1
            if answer:
                code = answer.get('code', -1)

            if code >= 100000:
                text = answer.get('text')
                url = answer.get('url')
                items = answer.get('list', list())

                if text:
                    ret += str(text)
                if url:
                    ret += '\n{}'.format(url)
                for item in items:
                    ret += '\n\n{}\n{}'.format(
                        item.get('article') or item.get('name'),
                        item.get('detailurl')
                    )

            else:
                ret += '这话我接不了…'

            msg.chat.send(ret)

        def get_location(_chat):

            province = getattr(_chat, 'province', None) or ''
            city = getattr(_chat, 'city', None) or ''

            if province in ('北京', '上海', '天津', '重庆'):
                return '{}市{}区'.format(province, city)
            elif province and city:
                return '{}省{}市'.format(province, city)

        if not msg.robot:
            raise ValueError('Robot not found: {}'.format(msg))

        chat = msg.chat
        member = msg.member

        if to_member and member:
            user_id = member.user_name
            location = get_location(member)
        else:
            user_id = chat.user_name
            location = get_location(chat)

        user_id = re.sub(r'[^a-zA-Z\d]', '', user_id)
        user_id = user_id[-32:]
        if location:
            location = location[:30]
        info = str(msg.text or '')[-30:]

        payload = dict(
            key=self.api_key,
            info=info,
            user_id=user_id,
            loc=location
        )

        logging.debug('Tuling payload:\n' + pprint.pformat(payload))

        # noinspection PyBroadException
        try:
            r = self.session.post(self.url, json=payload)
            answer = r.json()
        except:
            answer = None
        finally:
            process_answer()
