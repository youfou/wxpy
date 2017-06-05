# coding: utf-8
from __future__ import unicode_literals
import logging
import pprint

import requests

from wxpy.ext.talk_bot_utils import get_context_user_id, next_topic
from wxpy.utils.misc import get_text_without_at_bot
from wxpy.utils import enhance_connection
from wxpy.compatible import *

logger = logging.getLogger(__name__)


class Tuling(object):
    """
    与 wxpy 深度整合的图灵机器人
    """

    'API 文档: http://tuling123.com/help/h_cent_webapi.jhtml'

    # 考虑升级 API 版本: http://doc.tuling123.com/openapi2/263611

    url = 'http://www.tuling123.com/openapi/api'

    def __init__(self, api_key=None):
        """
        | 内置的 api key 存在调用限制，建议自行申请。
        | 免费申请: http://www.tuling123.com/

        :param api_key: 你申请的 api key
        """

        self.session = requests.Session()
        enhance_connection(self.session)

        # noinspection SpellCheckingInspection
        self.api_key = api_key or '7c8cdb56b0dc4450a8deef30a496bd4c'
        self.last_member = dict()

    def is_last_member(self, msg):
        if msg.member == self.last_member.get(msg.chat):
            return True
        else:
            self.last_member[msg.chat] = msg.member

    def do_reply(self, msg, at_member=True):
        """
        回复消息，并返回答复文本

        :param msg: Message 对象
        :param at_member: 若消息来自群聊，回复时 @发消息的群成员
        :return: 答复文本
        :rtype: str
        """
        ret = self.reply_text(msg, at_member)
        msg.reply(ret)
        return ret

    def reply_text(self, msg, at_member=True):
        """
        仅返回消息的答复文本

        :param msg: Message 对象
        :param at_member: 若消息来自群聊，回复时 @发消息的群成员
        :return: 答复文本
        :rtype: str
        """

        def process_answer():

            logger.debug('Tuling answer:\n' + pprint.pformat(answer))

            ret = str()
            if at_member:
                if len(msg.chat) > 2 and msg.member.name and not self.is_last_member(msg):
                    ret += '@{} '.format(msg.member.name)

            code = -1
            if answer:
                code = answer.get('code', -1)

            if code >= 100000:
                text = answer.get('text')
                if not text or (text == msg.text and len(text) > 3):
                    text = next_topic()
                url = answer.get('url')
                items = answer.get('list', list())

                ret += str(text)
                if url:
                    ret += '\n{}'.format(url)
                for item in items:
                    ret += '\n\n{}\n{}'.format(
                        item.get('article') or item.get('name'),
                        item.get('detailurl')
                    )

            else:
                ret += next_topic()

            return ret

        def get_location(_chat):

            province = getattr(_chat, 'province', None) or ''
            city = getattr(_chat, 'city', None) or ''

            if province in ('北京', '上海', '天津', '重庆'):
                return '{}市{}区'.format(province, city)
            elif province and city:
                return '{}省{}市'.format(province, city)

        if not msg.bot:
            raise ValueError('bot not found: {}'.format(msg))

        if not msg.text:
            return

        from wxpy.api.chats import Group
        if at_member and isinstance(msg.chat, Group) and msg.member:
            location = get_location(msg.member)
        else:
            # 使该选项失效，防止错误 @ 人
            at_member = False
            location = get_location(msg.chat)

        user_id = get_context_user_id(msg)

        if location:
            location = location[:30]

        info = str(get_text_without_at_bot(msg))[-30:]

        payload = dict(
            key=self.api_key,
            info=info,
            userid=user_id,
            loc=location
        )

        logger.debug('Tuling payload:\n' + pprint.pformat(payload))

        # noinspection PyBroadException
        try:
            r = self.session.post(self.url, json=payload)
            answer = r.json()
        except:
            answer = None
        finally:
            return process_answer()
