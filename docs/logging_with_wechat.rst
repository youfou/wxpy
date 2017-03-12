程序员利器: 在微信上打日志
==============================

..  module:: wxpy

当我们编写程序时，经常通过"打日志"的方式来记录程序的运行情况，然后在程序运行过程中盯着屏幕，或者定期的去检查所产生的日志。

回想一下，你是否曾经守着电脑不肯走开，生怕错过一条重要日志？或者当你外出时，心里挂念着电脑上的程序运行得如何？

现在，我们可以通过利用微信强大的通知能力，帮我们实现"第一时间了解程序运行情况"的需求：把日志打到微信上去。

wxpy 提供以下两种方式来实现这个需求。


获得一个专用 Logger
------------------------------

.. autofunction:: get_wechat_logger

示例代码::

    import logging
    from wxpy import get_wechat_logger

    # 获得一个专用 Logger，并设置等级为 INFO
    # 当不设置 `receiver` 时，会将日志发送到随后扫码登陆的微信的"文件传输助手"
    logger = get_wechat_logger(level=logging.INFO)

    logger.info('这是一条 INFO 等级的日志，你收到了吗？')

    try:
        1 / 0
    except:
        logger.exception('现在你又收到了什么？')


加入到现有的 Logger
------------------------------

.. autoclass:: WeChatLoggingHandler

示例代码::

    import logging
    from wxpy import WeChatLoggingHandler

    # 这是你现有的 Logger
    logger = logging.getLogger(__name__)

    # 初始化一个微信 Handler
    wechat_handler = WeChatLoggingHandler()
    # 加到入现有的 Logger
    logger.addHandler(wechat_handler)

    logger.warning('你有一条新警告，请查收')


指定接收者
------------------------------

当然，我们也可以使用其他聊天对象来接收日志。

比如，先在微信中建立一个群聊，并在里面加入需要关注这些日志的人员。然后把这个群作为日志的接收者。

示例代码::

    from wxpy import *

    # 初始化机器人
    bot = Bot()
    # 找到需要接收日志的群 -- `ensure_one()` 用于确保找到的结果是唯一的，避免发错地方
    group_receiver = ensure_one(bot.groups().search('XX日志关注小组'))

    # 指定这个群为接收者
    logger = get_wechat_logger(group_receiver)

    logger.error('打扰大家了，但这是一条重要的错误日志...')

