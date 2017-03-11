from .message import SYSTEM


class MessageConfigs(list):
    """
    一个机器人(Bot)的所有消息注册配置
    """

    def __init__(self, bot):
        """
        初始化

        :param bot: 这些配置所属的机器人
        """
        super(MessageConfigs, self).__init__()
        self.bot = bot

    def get_func(self, msg):
        """
        获取给定消息的对应回复函数。每条消息仅匹配和执行一个回复函数，后注册的配置具有更高的匹配优先级。

        :param msg: 给定的消息
        :return: 回复函数 func，及是否异步执行 run_async
        """

        def ret(_conf=None):
            if _conf:
                return _conf.func, _conf.run_async
            else:
                return None, None

        for conf in self[::-1]:

            if not conf.enabled or (conf.except_self and msg.sender == self.bot.self):
                return ret()

            if conf.msg_types and msg.type not in conf.msg_types:
                continue
            elif not conf.msg_types and msg.type == SYSTEM:
                continue

            if not conf.senders:
                return ret(conf)

            for sender in conf.senders:
                if sender == msg.sender or (isinstance(sender, type) and isinstance(msg.sender, sender)):
                    return ret(conf)

        return ret()

    def get_config(self, func):
        """
        根据执行函数找到对应的配置

        :param func: 已注册的函数
        :return: 对应的配置
        """
        for conf in self:
            if conf.func is func:
                return conf

    def _change_status(self, func, enabled):
        if func:
            self.get_config(func).enabled = enabled
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
