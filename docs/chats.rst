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


各类型的继承关系
--------------------------------------

..  note:: 在继续了解各个聊天对象之前，我们必须先理解各种不同类型的聊天对象的继承关系。

基础类
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

所有聊天对象，均继承于以下两种基础类，并拥有相应的属性和方法。

基本聊天对象 :class:`Chat`
    * 所有的聊天对象均继承于此类型
    * 拥有 微信ID、昵称 等属性
    * 拥有 发送消息 :meth:`Chat.send`, 获取头像 :meth:`Chat.get_avatar` 等方法

单个聊天对象 :class:`User`
    * 继承于 :class:`Chat`，表示个体聊天对象 (而非群聊)。
    * 被以下聊天对象所继承
        * 好友对象 :class:`Friend`
        * 群成员对象 :class:`Member`
        * 公众号对象 :class:`MP`
    * 拥有 性别、省份、城市、是否为好友 等属性
    * 拥有 加为好友 :meth:`User.add`, 接受为好友 :meth:`User.accept` 等方法

实际类
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在实际使用过程中，我们会更多的用到以下实际聊天对象类型。

..  tip:: 请牢记，除了自身私有的属性和方法外，它们还拥有对应基础类的属性和方法 (未重复列出)。

* 好友 :class:`Friend`
* 群聊 :class:`Group`
* 群成员 :class:`Member`
* 公众号 :class:`MP`


基本聊天对象
--------------------------------------

所有聊天对象都继承于"基本聊天对象"

..  autoclass:: Chat
    :members:

    ..  attribute:: bot

        所属的 :class:`机器人对象 <Bot>`

    ..  attribute:: raw

        原始数据



单个聊天对象
--------------------------------------

..  autoclass:: User
    :members:

好友
-------------------

..  autoclass:: Friend
    :members:

群聊
-------------------

..  autoclass:: Group
    :members:


群成员
^^^^^^^^^^^^^^^^^^^^

..  autoclass:: Member
    :members:

实用技巧
^^^^^^^^^^^^^^^^^^^^

判断一位用户是否在群中只需用 `in` 语句::

    friend = bot.friends().search('游否')[0]
    group = bot.groups().search('wxpy 交流群')[0]

    if friend in group:
        print('是的，{} 在 {} 中！'.format(friend.name, group.name))
        # 是的，游否 在 wxpy 交流群 中！

若要遍历群成员，可直接对群对象使用 `for` 语句::

    # 打印所有群成员
    for member in group:
        print(member)

若需查看群成员数量，直接使用 `len()` 即可::

    len(group) # 这个群的成员数量

若需判断一位群成员是否就是某个好友，使用 `==` 即可::

    member = group.search('游否')[0]
    if member == friend:
        print('{} is {}'.format(member, friend))
        # <Member: 游否> is <Friend: 游否>


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
