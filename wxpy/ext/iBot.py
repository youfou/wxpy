# -*- coding:utf-8 -*-

import collections
import hashlib
import logging
import traceback
import requests

from wxpy.api.messages import Message
from wxpy.utils import enhance_connection, get_context_user_id

logger = logging.getLogger(__name__)


class IBot(object):
	"""
	* 与 wxpy 深度整合的小i机器人
	* 需获取 Key和Secret: http://cloud.xiaoi.com/
	"""

	def __init__(self, app_key, app_secret):
		"""
		在 http://cloud.xiaoi.com/ 注册后可获得账户的Key和Secret
		:param app_key: 必填, 你的 iBotCloud 的 Key
		:param app_secret: 必填, 你的 iBotCloud的 Secret
		"""
		self.app_key = app_key
		self.app_secret = app_secret
		self.realm = "xiaoi.com"
		self.http_method = "POST"
		self.uri = "/ask.do"
		self.url = "http://nlp.xiaoi.com/ask.do?platform=custom"

		self.session = requests.Session()
		xauth = self._make_http_header_xauth()
		headers = {
			"Content-type": "application/x-www-form-urlencoded",
			"Accept": "text/plain",
		}
		headers.update(xauth)
		self.session.headers.update(headers)
		enhance_connection(self.session)

	def _make_signature(self):
		"""
		生成请求签名
		:return:
		"""
		# nonce = "".join([str(randint(0, 9)) for _ in range(40)])
		# 40位随机字符
		nonce = "4103657107305326101203516108016101205331"
		sha1 = "{0}:{1}:{2}".format(self.app_key, self.realm, self.app_secret).encode("utf-8")
		sha1 = hashlib.sha1(sha1).hexdigest()
		sha2 = "{0}:{1}".format(self.http_method, self.uri).encode("utf-8")
		sha2 = hashlib.sha1(sha2).hexdigest()
		signature = "{0}:{1}:{2}".format(sha1, nonce, sha2).encode("utf-8")
		signature = hashlib.sha1(signature).hexdigest()
		logger.debug("signature:" + signature)
		logger.debug("nonce:" + nonce)

		ret = collections.namedtuple("signature_return", "signature nonce")
		ret.signature = signature
		ret.nonce = nonce
		return ret

	def _make_http_header_xauth(self):
		"""
		生成请求认证
		:return: ret
		"""
		sign = self._make_signature()
		ret = {
			"X-Auth": "app_key=\"{0}\",nonce=\"{1}\",signature=\"{2}\"".format(
				self.app_key, sign.nonce, sign.signature)
		}
		return ret

	def do_reply(self, msg):
		"""
		回答问题, 返回回复文本
		:param msg: Message 对象 or 纯文本
		:return: 回复文本
		"""
		if isinstance(msg, Message):
			user_id = get_context_user_id(msg)
			question = msg.text
		else:
			user_id = "abc"
			question = msg or ""
		params = {
			"question": question,
			"format": "json",
			"platform": "custom",
			"userId": user_id,
		}
		try:
			rep = self.session.post(self.url, data=params)
			content = rep.content.decode("utf-8")
			return content
		except Exception as e:
			traceback.print_exc()
			return ""
