import logging

from wxpy.utils import ensure_list

logger = logging.getLogger(__name__)


class MessageConfig(object):
    """
    单个消息注册配置
    """

    def __init__(
            self, bot, func, senders, msg_types,
            except_self, run_async, enabled
    ):
        self.bot = bot
        self.func = func

        self.senders = ensure_list(senders)
        self.msg_types = ensure_list(msg_types)
        self.except_self = except_self
        self.run_async = run_async

        self._enabled = None
        self.enabled = enabled

    @property
    def enabled(self):
        """
        配置的开启状态
        """
        return self._enabled

    @enabled.setter
    def enabled(self, boolean):
        """
        设置配置的开启状态
        """
        self._enabled = boolean
        logger.info(self.__repr__())

    def __repr__(self):
        return '<{}: {}: {} ({}{})>'.format(
            self.__class__.__name__,
            self.bot.self.name,
            self.func.__name__,
            'Async, ' if self.run_async else '',
            'Enabled' if self.enabled else 'Disabled',
        )
