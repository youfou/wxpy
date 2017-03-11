消息处理
==============================

..  module:: wxpy

每当机器人接收到消息时，会自动执行以下两个步骤

1. 将消息保存到 `Bot.messages` 中
2. 查找消息预先注册的函数，并执行(若有注册)

消息对象
----------------

..  autoclass:: Message
    :members:

    ..  method:: reply(...)

        等同于 :meth:`Message.sender.send(...) <Chat.send>`

    ..  method:: reply_image(...)

        等同于 :meth:`Message.sender.send_image(...) <Chat.send_image>`

    ..  method:: reply_file(...)

        等同于 :meth:`Message.sender.send_file(...) <Chat.send_file>`

    ..  method:: reply_video(...)

        等同于 :meth:`Message.sender.send_video(...) <Chat.send_video>`

    ..  method:: reply_msg(...)

        等同于 :meth:`Message.sender.send_msg(...) <Chat.send_msg>`

    ..  method:: reply_raw_msg(...)

        等同于 :meth:`Message.sender.send_raw_msg(...) <Chat.send_raw_msg>`

    ..  method:: get_file(save_path=None)

        :param save_path: 文件的保存路径。若为 `None`，将直接返回字节数据

        下载文件(包括图片、视频等)。

    ..  attribute:: text

        消息的文本内容

    ..  attribute:: bot

        接收消息的 :class:`机器人对象 <Bot>`

    ..  attribute:: type

        消息的类型，目前可为以下值::

            # 文本
            TEXT = 'Text'
            # 位置
            MAP = 'Map'
            # 名片
            CARD = 'Card'
            # 提示
            NOTE = 'Note'
            # 分享
            SHARING = 'Sharing'
            # 图片
            PICTURE = 'Picture'
            # 语音
            RECORDING = 'Recording'
            # 文件
            ATTACHMENT = 'Attachment'
            # 视频
            VIDEO = 'Video'
            # 好友请求
            FRIENDS = 'Friends'
            # 系统
            SYSTEM = 'System'

    ..  attribute:: is_at

        当消息来自群聊，且被 @ 时，为 True

    ..  attribute:: file_name

        文件名 (图片、视频等带有文件的消息)

    ..  attribute:: img_height

        图片高度

    ..  attribute:: img_width

        图片宽度

    ..  attribute:: play_length

        视频长度

    ..  attribute:: url

        分享类消息的 URL (非文件类消息)

    ..  attribute:: voice_length

        语音长度

    ..  attribute:: id

        消息ID

    ..  attribute:: location

        地图消息的地理位置信息

    ..  attribute:: card

        名片消息或好友请求的用户对象

    ..  attribute:: create_time

        消息的发送时间戳


自动处理消息
---------------------

可通过 **预先注册** 的方式，实现消息的自动处理。

..  hint:: **预先注册**: 预先将来自特定聊天对象的特定类型的消息，注册到相应的处理函数。

消息注册
^^^^^^^^^^^^^^

将 :meth:`以下方法 <Bot.register>` 作为函数的装饰器，即可完成注册。

当接收到符合条件的消息时，会自动执行被注册的函数，并以参数的形式传入 :class:`消息对象 <Message>`。

..  automethod:: Bot.register

..  note:: 每条消息仅匹配一个预先注册函数，且优先匹配后注册的函数！

..  tip::

    1.  `chats` 和 `msg_types` 参数可以接收一个列表或干脆一个单项。按需使用，方便灵活。
    2.  `chats` 参数既可以是聊天对象实例，也可以是对象类。当为类时，表示匹配该类型的所有聊天对象。
    3. 在被注册函数中，可以直接通过 `return <回复内容>` 的方式来回复消息，等同于调用 `msg.reply(<回复内容>)`。

开始监听
^^^^^^^^^^^^^^

..  note:: 在完成消息注册后，务必通过以下方法开始监听和处理消息。

..  automethod:: Bot.start

示例代码
^^^^^^^^^^^^^

在以下例子中，机器人将

* 忽略 "一个无聊的群" 的所有消息
* 回复好友 "游否" 和其他群聊中被 @ 的 TEXT 类消息
* 打印所有其他消息

初始化机器人，并找到好友和群聊::

    from wxpy import *
    bot = Bot()
    my_friend = bot.friends().search('游否')[0]
    boring_group = bot.groups().search('一个无聊的群')[0]

打印所有其他消息::

    @bot.register()
    def just_print(msg):
        # 打印消息
        print(msg)

回复好友"游否"和其他群聊中被 @ 的 TEXT 类消息::

    @bot.register([my_friend, Group], TEXT)
    def auto_reply(msg):
        # 如果是群聊，但没有被 @，则不回复
        if not (isinstance(msg.sender, Group) and not msg.is_at):
            # 回复消息内容和类型
            return '收到消息: {} ({})'.format(msg.text, msg.type)

忽略"一个无聊的群"的所有消息::

    @bot.register(boring_group)
    def ignore(msg):
        # 啥也不做
        return


开始监听和自动处理::

    bot.start()


动态开关注册配置
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..  note:: 该操作需要在额外的线程中进行！


查看当前的注册配置情况::

    bot.message_configs
    # [<MessageConfig: just_print (Async, Enabled)>,
    #  <MessageConfig: auto_reply (Async, Enabled)>,
    #  <MessageConfig: ignore (Async, Enabled)>]

关闭所有注册配置::

    bot.message_configs.disable()

重新开启 `just_print` 函数::

    bot.message_configs.enable(just_print)

查看当前开启的注册配置::

    bot.message_configs.enabled
    # [<MessageConfig: just_print (Async, Enabled)>]

