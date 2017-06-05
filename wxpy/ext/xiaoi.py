# coding: utf-8
from __future__ import unicode_literals
# created by: Han Feng (https://github.com/hanx11)

import collections
import hashlib
import logging

import requests

from wxpy.api.messages import Message
from wxpy.ext.talk_bot_utils import get_context_user_id, next_topic
from wxpy.utils.misc import get_text_without_at_bot
from wxpy.utils import enhance_connection

logger = logging.getLogger(__name__)

from wxpy.compatible import *

class XiaoI(object):
    """
    与 wxpy 深度整合的小 i 机器人
    """

    # noinspection SpellCheckingInspection
    def __init__(self, key, secret):
        """
        | 需要通过注册获得 key 和 secret
        | 免费申请: http://cloud.xiaoi.com/

        :param key: 你申请的 key
        :param secret: 你申请的 secret
        """

        self.key = key
        self.secret = secret

        self.realm = "xiaoi.com"
        self.http_method = "POST"
        self.uri = "/ask.do"
        self.url = "http://nlp.xiaoi.com/ask.do?platform=custom"

        xauth = self._make_http_header_xauth()

        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain",
        }

        headers.update(xauth)

        self.session = requests.Session()
        self.session.headers.update(headers)
        enhance_connection(self.session)

    def _make_signature(self):
        """
        生成请求签名
        """

        # 40位随机字符
        # nonce = "".join([str(randint(0, 9)) for _ in range(40)])
        nonce = "4103657107305326101203516108016101205331"

        sha1 = "{0}:{1}:{2}".format(self.key, self.realm, self.secret).encode("utf-8")
        sha1 = hashlib.sha1(sha1).hexdigest()
        sha2 = "{0}:{1}".format(self.http_method, self.uri).encode("utf-8")
        sha2 = hashlib.sha1(sha2).hexdigest()

        signature = "{0}:{1}:{2}".format(sha1, nonce, sha2).encode("utf-8")
        signature = hashlib.sha1(signature).hexdigest()

        ret = collections.namedtuple("signature_return", "signature nonce")
        ret.signature = signature
        ret.nonce = nonce

        return ret

    def _make_http_header_xauth(self):
        """
        生成请求认证
        """

        sign = self._make_signature()

        ret = {
            "X-Auth": "app_key=\"{0}\",nonce=\"{1}\",signature=\"{2}\"".format(
                self.key, sign.nonce, sign.signature)
        }

        return ret

    def do_reply(self, msg):
        """
        回复消息，并返回答复文本

        :param msg: Message 对象
        :return: 答复文本
        """

        ret = self.reply_text(msg)
        msg.reply(ret)
        return ret

    def reply_text(self, msg):
        """
        仅返回答复文本

        :param msg: Message 对象，或消息文本
        :return: 答复文本
        """

        error_response = (
            "主人还没给我设置这类话题的回复",
        )

        if isinstance(msg, Message):
            user_id = get_context_user_id(msg)
            question = get_text_without_at_bot(msg)
        else:
            user_id = "abc"
            question = msg or ""

        params = {
            "question": question,
            "format": "json",
            "platform": "custom",
            "userId": user_id,
        }

        resp = self.session.post(self.url, data=params)
        text = resp.text

        for err in error_response:
            if err in text:
                return next_topic()

        return text
