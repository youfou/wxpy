import weakref

from .message import SYSTEM


class Registered(list):
    def __init__(self, bot):
        """
        保存当前机器人所有已注册的消息配置

        :param bot: 所属的机器人
        """
        super(Registered, self).__init__()
        self.bot = weakref.proxy(bot)

    def get_config(self, msg):
        """
        获取给定消息的注册配置。每条消息仅匹配一个注册配置，后注册的配置具有更高的匹配优先级。

        :param msg: 给定的消息
        :return: 匹配的回复配置
        """

        for conf in self[::-1]:

            if not conf.enabled or (conf.except_self and msg.sender == self.bot.self):
                continue

            if conf.msg_types and msg.type not in conf.msg_types:
                continue
            elif conf.msg_types is None and msg.type == SYSTEM:
                continue

            if conf.chats is None:
                return conf

            for chat in conf.chats:
                if (isinstance(chat, type) and isinstance(msg.chat, chat)) or chat == msg.chat:
                    return conf

    def get_config_by_func(self, func):
        """
        通过给定的函数找到对应的注册配置

        :param func: 给定的函数
        :return: 对应的注册配置
        """

        for conf in self:
            if conf.func is func:
                return conf

    def _change_status(self, func, enabled):
        if func:
            self.get_config_by_func(func).enabled = enabled
        else:
            for conf in self:
                conf.enabled = enabled

    def enable(self, func=None):
        """
        开启指定函数的对应配置。若不指定函数，则开启所有已注册配置。

        :param func: 指定的函数
        """
        self._change_status(func, True)

    def disable(self, func=None):
        """
        关闭指定函数的对应配置。若不指定函数，则关闭所有已注册配置。

        :param func: 指定的函数
        """
        self._change_status(func, False)

    def _check_status(self, enabled):
        ret = list()
        for conf in self:
            if conf.enabled == enabled:
                ret.append(conf)
        return ret

    @property
    def enabled(self):
        """
        检查处于开启状态的配置

        :return: 处于开启状态的配置
        """
        return self._check_status(True)

    @property
    def disabled(self):
        """
        检查处于关闭状态的配置

        :return: 处于关闭状态的配置
        """
        return self._check_status(False)
