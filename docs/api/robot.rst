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

代码示例: 自动接受好友请求::

    # 注册好友请求类消息
    @robot.register(FRIENDS)
    # 自动接受验证信息中包含 'wxpy' 的好友请求
    def auto_accept_friends(msg):
        # 判断好友请求中的验证文本
        if 'wxpy' in msg.text.lower():
            # 接受好友 (msg.card 为该请求的用户对象)
            new_friend = msg.card.accept()
            # 向新的好友发送消息
            new_friend.send('哈哈，我自动接受了你的好友请求')

..  automethod:: Robot.create_group


获取用户详细信息
----------------

..  automethod:: Robot.user_details


登出
----------------

..  automethod:: Robot.logout
