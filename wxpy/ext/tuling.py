import logging
import pprint
import random
import re

import requests

logger = logging.getLogger(__name__)


class Tuling(object):
    """
    | 与 wxpy 深度整合的图灵机器人
    | 内置 API KEY 可能存在调用限制，建议自行申请一枚新的。
    | 获取 API KEY: http://www.tuling123.com/
    """

    'API 文档: http://tuling123.com/help/h_cent_webapi.jhtml'

    # 考虑升级 API 版本: http://doc.tuling123.com/openapi2/263611

    url = 'http://www.tuling123.com/openapi/api'

    def __init__(self, api_key=None):
        """
        :param api_key: 图灵机器人服务所需的 API KEY (详见: http://www.tuling123.com/)
        """
        self.session = requests.Session()

        # noinspection SpellCheckingInspection
        self.api_key = api_key or '7c8cdb56b0dc4450a8deef30a496bd4c'
        self.last_member = dict()

    @property
    def _change_words(self):
        return random.choice((
            '换个话题吧',
            '聊点别的吧',
            '下一个话题吧',
            '无言以对呢',
            '这话我接不了呢'
        ))

    def is_last_member(self, msg):
        if msg.member == self.last_member.get(msg.sender):
            return True
        else:
            self.last_member[msg.sender] = msg.member

    def do_reply(self, msg, to_member=True):
        """
        回复消息，并返回答复文本

        :param msg: Message 对象
        :param to_member: 若消息来自群聊，回复 @发消息的群成员
        :return: 答复文本
        """
        ret = self.reply_text(msg, to_member)
        msg.reply(ret)
        return ret

    def reply_text(self, msg, to_member=True):
        """
        返回消息的答复文本

        :param msg: Message 对象
        :param to_member: 若消息来自群聊，回复 @发消息的群成员
        :return: 答复文本
        """

        def process_answer():

            logger.debug('Tuling answer:\n' + pprint.pformat(answer))

            ret = str()
            if to_member:
                if len(msg.sender) > 2 and msg.member.name and not self.is_last_member(msg):
                    ret += '@{} '.format(msg.member.name)

            code = -1
            if answer:
                code = answer.get('code', -1)

            if code >= 100000:
                text = answer.get('text')
                if not text or (text == msg.text and len(text) > 3):
                    text = self._change_words
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
                ret += self._change_words

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
        if to_member and isinstance(msg.sender, Group) and msg.member:
            user_id = msg.member.user_name
            location = get_location(msg.member)
        else:
            to_member = False
            user_id = msg.sender.user_name
            location = get_location(msg.sender)

        user_id = re.sub(r'[^a-zA-Z\d]', '', user_id)
        user_id = user_id[-32:]
        if location:
            location = location[:30]
        info = str(msg.text)[-30:]

        payload = dict(
            key=self.api_key,
            info=info,
            user_id=user_id,
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
