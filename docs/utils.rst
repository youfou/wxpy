实用组件
==============================

..  module:: wxpy

额外内置了一些实用的小组件，可按需使用。


聊天机器人
------------------------------

目前提供了以下两种自动聊天机器人接口。


图灵
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..  autoclass:: Tuling
    :members:

    ::

        bot = Bot()
        my_friend = ensure_one(bot.search('游否'))
        tuling = Tuling(api_key='你申请的 API KEY')

        # 使用图灵机器人自动与指定好友聊天
        @bot.register(my_friend)
        def reply_my_friend(msg):
            tuling.do_reply(msg)


小 i
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..  autoclass:: XiaoI
    :members:

    ::

        bot = Bot()
        my_friend = ensure_one(bot.search('寒风'))
        xiaoi = XiaoI('你申请的 Key', '你申请的 Secret')

        # 使用小 i 机器人自动与指定好友聊天
        @bot.register(my_friend)
        def reply_my_friend(msg):
            xiaoi.do_reply(msg)


查找共同好友
------------------------------

..  autofunction:: mutual_friends

    ::

        bot1 = Bot()
        bot2 = Bot()

        # 打印共同好友
        for mf in mutual_friends(bot, bot2):
            print(mf)


确保查找结果的唯一性
------------------------------

..  autofunction:: ensure_one

    ::

        bot = Bot()
        # 确保只找到了一个叫"游否"的好友，并返回这个好友
        my_friend = ensure_one(bot.search('游否'))
        # <Friend: 游否>


在多个群中同步消息
------------------------------

..  autofunction:: sync_message_in_groups


检测频率限制
------------------------------

..  autofunction:: detect_freq_limit

    例如，测试发送文本消息的频率限制::

        bot = Bot('test.pkl')

        # 定义需要检测的操作
        def action():
            bot.file_helper.send()

        # 执行检测
        result = detect_freq_limit(action)
        # 查看结果
        print(result)
        # (120, 120.111222333)


忽略 `ResponseError` 异常
------------------------------

..  autofunction:: dont_raise_response_error

