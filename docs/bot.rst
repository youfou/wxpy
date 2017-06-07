机器人对象
==============================

..  module:: wxpy

机器人 :class:`Bot` 对象可被理解为一个 Web 微信客户端。


..  note::

    | 关于发送消息，请参见 :doc:`chats`。
    | 关于消息对象和自动处理，请参见 :doc:`messages`。


初始化/登陆
----------------

..  note::

    :class:`Bot` 在初始化时便会执行登陆操作，需要手机扫描登陆。

..  autoclass:: Bot

..  automethod:: Bot.enable_puid


..  attribute:: Bot.auto_mark_as_read

    为 True 时，将自动消除手机端的新消息小红点提醒 (默认为 False)


获取聊天对象
----------------

..  attribute:: Bot.self

    机器人自身 (作为一个聊天对象)

    若需要给自己发送消息，请先进行以下一次性操作::

        # 在 Web 微信中把自己加为好友
        bot.self.add()
        bot.self.accept()

        # 发送消息给自己
        bot.self.send('能收到吗？')


..  attribute:: Bot.file_helper

    文件传输助手

..  automethod:: Bot.friends

..  automethod:: Bot.groups

..  automethod:: Bot.mps

..  automethod:: Bot.chats


搜索聊天对象
----------------

..  note::

    * 通过 `.search()` 获得的搜索结果 **均为列表**
    * 若希望找到唯一结果，可使用 :any:`ensure_one()`

搜索好友::

    # 搜索名称包含 '游否' 的深圳男性好友
    found = bot.friends().search('游否', sex=MALE, city='深圳')
    # [<Friend: 游否>]
    # 确保搜索结果是唯一的，并取出唯一结果
    youfou = ensure_one(found)
    # <Friend: 游否>

搜索群聊::

    # 搜索名称包含 'wxpy'，且成员中包含 `游否` 的群聊对象
    wxpy_groups = bot.groups().search('wxpy', [youfou])
    # [<Group: wxpy 交流群 1>, <Group: wxpy 交流群 2>]

在群聊中搜素::

    # 在刚刚找到的第一个群中搜索
    group = wxpy_groups[0]
    # 搜索该群中所有浙江的群友
    found = group.search(province='浙江')
    # [<Member: 浙江群友 1>, <Group: 浙江群友 2>, <Group: 浙江群友 3> ...]

搜索任何类型的聊天对象 (但不包含群内成员) ::

    # 搜索名称含有 'wxpy' 的任何聊天对象
    found = bot.search('wxpy')
    # [<Friend: wxpy 机器人>, <Group: wxpy 交流群 1>, <Group: wxpy 交流群 2>]

加好友和建群
----------------

..  automethod:: Bot.add_friend

..  automethod:: Bot.add_mp

..  automethod:: Bot.accept_friend

自动接受好友请求::

    # 注册好友请求类消息
    @bot.register(msg_types=FRIENDS)
    # 自动接受验证信息中包含 'wxpy' 的好友请求
    def auto_accept_friends(msg):
        # 判断好友请求中的验证文本
        if 'wxpy' in msg.text.lower():
            # 接受好友 (msg.card 为该请求的用户对象)
            new_friend = bot.accept_friend(msg.card)
            # 或 new_friend = msg.card.accept()
            # 向新的好友发送消息
            new_friend.send('哈哈，我自动接受了你的好友请求')

..  automethod:: Bot.create_group


其他
----------------

..  automethod:: Bot.user_details

..  automethod:: Bot.upload_file

..  automethod:: Bot.join

..  automethod:: Bot.logout


控制多个微信 (多开)
--------------------------------

仅需初始化多个 :class:`Bot` 对象，即可同时控制多个微信::

    bot1 = Bot()
    bot2 = Bot()

