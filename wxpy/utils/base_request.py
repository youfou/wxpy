# coding: utf-8
from __future__ import unicode_literals

import functools
import json

import itchat.config
import itchat.returnvalues

from .misc import handle_response


class BaseRequest(object):
    def __init__(self, bot, uri, params=None):
        """
        基本的 Web 微信请求模板，可用于修改后发送请求
        
        可修改属性包括:
        
        * url (会通过 url 参数自动拼接好)
        * data (默认仅包含 BaseRequest 部分)
        * headers
        
        :param bot: 所使用的机器人对象
        :param uri: API 路径，将与基础 URL 进行拼接
        """
        self.bot = bot
        self.url = self.bot.core.loginInfo['url'] + uri
        self.params = params
        self.data = {'BaseRequest': self.bot.core.loginInfo['BaseRequest']}
        self.headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent': itchat.config.USER_AGENT
        }

        for method in 'get', 'post', 'put', 'delete':
            setattr(self, method, functools.partial(
                self.request, method=method.upper()
            ))

    def request(self, method, to_class=None):
        """
        (在完成修改后) 发送请求
        
        :param method: 请求方法: 'GET', 'POST'，'PUT', 'DELETE' 等
        :param to_class: 使用 `@handle_response(to_class)` 把结果转化为相应的类
        """

        if self.data:
            self.data = json.dumps(self.data, ensure_ascii=False).encode('utf-8')
        else:
            self.data = None

        @handle_response(to_class)
        def do():
            return itchat.returnvalues.ReturnValue(
                rawResponse=self.bot.core.s.request(
                    method=method,
                    url=self.url,
                    params=self.params,
                    data=self.data,
                    headers=self.headers
                ))

        return do()
