用微信监控你的程序
==============================

..  module:: wxpy

通过利用微信强大的通知能力，我们可以把程序中的警告/日志发到自己的微信上。

wxpy 提供以下两种方式来实现这个需求。


获得专用 Logger
------------------------------

.. autofunction:: get_wechat_logger

::

    from wxpy import get_wechat_logger

    # 获得一个专用 Logger
    # 当不设置 `receiver` 时，会将日志发送到随后扫码登陆的微信的"文件传输助手"
    logger = get_wechat_logger()

    # 发送警告
    logger.warning('这是一条 WARNING 等级的日志，你收到了吗？')

    # 接收捕获的异常
    try:
        1 / 0
    except:
        logger.exception('现在你又收到了什么？')


加入到现有的 Logger
------------------------------

.. autoclass:: WeChatLoggingHandler

::

    import logging
    from wxpy import WeChatLoggingHandler

    # 这是你现有的 Logger
    logger = logging.getLogger(__name__)

    # 初始化一个微信 Handler
    wechat_handler = WeChatLoggingHandler()
    # 加到入现有的 Logger
    logger.addHandler(wechat_handler)

    logger.warning('你有一条新的告警，请查收。')


指定接收者
------------------------------

当然，我们也可以使用其他聊天对象来接收日志。

比如，先在微信中建立一个群聊，并在里面加入需要关注这些日志的人员。然后把这个群作为接收者。

::

    from wxpy import *

    # 初始化机器人
    bot = Bot()
    # 找到需要接收日志的群 -- `ensure_one()` 用于确保找到的结果是唯一的，避免发错地方
    group_receiver = ensure_one(bot.groups().search('XX业务-告警通知'))

    # 指定这个群为接收者
    logger = get_wechat_logger(group_receiver)

    logger.error('打扰大家了，但这是一条重要的错误日志...')

