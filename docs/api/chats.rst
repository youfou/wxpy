聊天对象
==============================

..  module:: wxpy

通过机器人对象 :class:`Bot <Bot>` 的
:meth:`chats() <Bot.chats>`,
:meth:`friends() <Bot.friends>`，:meth:`groups() <Bot.groups>`,
:meth:`mps() <Bot.mps>` 方法,
可分别获取到当前机器人的 所有聊天对象、好友、群聊，以及公众号列表。

而获得到的聊天对象合集 :class:`Chats` 和 :class:`Groups` 具有一些合集方法，例如：:meth:`Chats.search` 可用于按条件搜索聊天对象::

    from wxpy import *
    bot = Bot()
    my_friend = bot.friends().search('游否', sex=MALE, city='深圳')[0]
    # <Friend: 游否>

在找到好友(或其他聊天对象)后，还可使用该聊天对象的 :meth:`send <Chat.send>` 系列方法，对其发送消息::

    # 发送文本
    my_friend.send('Hello, WeChat!')
    # 发送图片
    my_friend.send_image('my_picture.png')
    # 发送视频
    my_friend.send_video('my_video.mov')
    # 发送文件
    my_friend.send_file('my_file.zip')
    # 以动态的方式发送图片
    my_friend.send('@img@my_picture.png')


基本聊天对象
--------------------------------------

所有聊天对象都继承于以下两种基本聊天对象，并拥有相应的方法

..  autoclass:: Chat
    :members:

    ..  attribute:: bot

        所属的 :class:`机器人对象 <Bot>`

    ..  attribute:: user_name

        该聊天对象的内部 ID，通常不需要被用到

        ..  attention::

            同个聊天对象在不同用户中，此 ID **不一致** ，且可能在新会话中 **被改变**！

    ..  attribute:: nick_name

        该聊天对象的昵称 (好友、群员的昵称，或群名称)

    ..  attribute:: name

        | 该聊天对象的友好名称
        | 具体为: 从 备注名称、昵称(或群名称)，以及群聊显示名称 中按序选择第一个可用的

..  autoclass:: User
    :members:

    ..  attribute:: display_name

        群聊中的昵称

    ..  attribute:: remark_name

        备注名称

    ..  attribute:: sex

        性别

    ..  attribute:: province

        省份

    ..  attribute:: city

        城市

    ..  attribute:: signature

        个性签名

好友
-------------------

..  autoclass:: Friend
    :members:

群聊
-------------------

..  autoclass:: Group
    :members:


群聊成员
^^^^^^^^^^^^^^^^^^^^

..  autoclass:: Member
    :members:

公众号
-------------------

..  autoclass:: MP
    :members:

聊天对象合集
-------------------

好友、公众号、群聊成员的合集
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在 :class:`Chats` 对象中，除了最常用到的 :meth:`search() <Chats.search>` 外，还有两个特别的方法，:meth:`stats() <Chats.stats>` 与 :meth:`stats_text() <Chats.stats_text>`，可用来统计好友或群成员的性别和地区分布::

    bot.friends().stats_text()
    # 游否 共有 100 位微信好友\n\n男性: 67 (67.0%)\n女性: 23 (23.0%) ...

..  autoclass:: Chats
    :members:

群聊的合集
^^^^^^^^^^^^^^^^^^^^

..  autoclass:: Groups
    :members:

