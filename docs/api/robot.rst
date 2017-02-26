机器人对象
==============================

..  module:: wxpy

机器人(:class:`Robot`)对象可被理解为一个抽象的 Web 微信客户端。


..  note::

    | 关于发送消息，请参见 :doc:`chat`。
    | 关于消息对象和自动处理，请参见 :doc:`message`。


初始化
----------------

..  note::

    :class:`Robot` 在初始化时便会执行登陆操作，需要手机扫描登陆。

..  autoclass:: Robot


获取聊天对象
----------------

..  automethod:: Robot.chats

..  automethod:: Robot.friends

..  automethod:: Robot.groups

..  automethod:: Robot.mps


加好友和建群
----------------

..  automethod:: Robot.add_friend

..  automethod:: Robot.accept_friend

..  automethod:: Robot.create_group


获取用户详细信息
----------------

..  automethod:: Robot.user_details


登出
----------------

..  automethod:: Robot.logout
