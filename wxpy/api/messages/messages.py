# coding: utf-8
from __future__ import unicode_literals
import threading

from wxpy.utils import match_attributes, match_text


class Messages(list):
    """
    多条消息的合集，可用于记录或搜索
    """

    def __init__(self, msg_list=None, max_history=200):
        if msg_list:
            super(Messages, self).__init__(msg_list)
        self.max_history = max_history
        self._thread_lock = threading.Lock()

    def append(self, msg):
        """
        仅当 self.max_history 为 int 类型，且大于 0 时才保存历史消息
        """
        with self._thread_lock:
            if isinstance(self.max_history, int) and self.max_history > 0:
                del self[:-self.max_history + 1]
                return super(Messages, self).append(msg)

    def search(self, keywords=None, **attributes):
        """
        搜索消息记录

        :param keywords: 文本关键词
        :param attributes: 属性键值对
        :return: 所有匹配的消息
        :rtype: :class:`wxpy.Messages`
        """

        def match(msg):
            if not match_text(msg.text, keywords):
                return
            if not match_attributes(msg, **attributes):
                return
            return True

        return Messages(filter(match, self), max_history=self.max_history)
