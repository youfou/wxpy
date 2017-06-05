# coding: utf-8
from __future__ import unicode_literals

import logging

from wxpy.utils import get_receiver

logger = logging.getLogger(__name__)


class WeChatLoggingHandler(logging.Handler):
    def __init__(self, receiver=None):
        """
        可向指定微信聊天对象发送日志的 Logging Handler

        :param receiver:
            * 当为 `None`, `True` 或字符串时，将以该值作为 `cache_path` 参数启动一个新的机器人，并发送到该机器人的"文件传输助手"
            * 当为 :class:`机器人 <Bot>` 时，将发送到该机器人的"文件传输助手"
            * 当为 :class:`聊天对象 <Chat>` 时，将发送到该聊天对象
        """

        super(WeChatLoggingHandler, self).__init__()
        self.receiver = get_receiver(receiver)

    def emit(self, record):
        if record.name.startswith('wxpy.'):
            # 排除 wxpy 的日志
            return

        # noinspection PyBroadException
        try:
            self.receiver.send(self.format(record))
        except:
            # Todo: 将异常输出到屏幕
            pass


def get_wechat_logger(receiver=None, name=None, level=logging.WARNING):
    """
    获得一个可向指定微信聊天对象发送日志的 Logger

    :param receiver:
        * 当为 `None`, `True` 或字符串时，将以该值作为 `cache_path` 参数启动一个新的机器人，并发送到该机器人的"文件传输助手"
        * 当为 :class:`机器人 <Bot>` 时，将发送到该机器人的"文件传输助手"
        * 当为 :class:`聊天对象 <Chat>` 时，将发送到该聊天对象
    :param name: Logger 名称
    :param level: Logger 等级，默认为 `logging.WARNING`
    :return: Logger
    """

    _logger = logging.getLogger(name=name)
    _logger.setLevel(level=level)
    _logger.addHandler(WeChatLoggingHandler(receiver=receiver))

    return _logger
