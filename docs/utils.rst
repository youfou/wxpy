实用组件
==============================

..  module:: wxpy

额外内置了一些实用的小组件，可按需使用。


确保查找结果的唯一性
------------------------------

..  autofunction:: ensure_one

代码示例::

    bot = Bot()
    # 确保只找到了一个叫"游否"的好友，并返回这个好友
    my_friend = ensure_one(bot.search('游否'))

图灵机器人
------------------------------

..  autoclass:: Tuling
    :members:

代码示例::

    bot = Bot()
    my_friend = ensure_one(bot.search('游否'))
    tuling = Tuling(api_key='你的 API KEY')

    # 使用图灵机器人自动回复指定好友
    @bot.register(my_friend)
    def reply_my_friend(msg):
        tuling.do_reply(msg)


查找共同好友
------------------------------

..  autofunction:: mutual_friends

代码示例::

    bot1 = Bot()
    bot2 = Bot()

    # 打印共同好友
    for mf in mutual_friends(bot, bot2):
        print(mf)


忽略 `ResponseError` 异常
------------------------------

..  autofunction:: dont_raise_response_error
