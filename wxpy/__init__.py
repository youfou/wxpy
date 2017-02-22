#!/usr/bin/env python3
# coding: utf-8

"""

wxpy
~~~~
微信个人号 API，基于 itchat，告别满屏 dict，更有 Python 范儿


## 代码示例

>>> # 导入所需的组件，也可直接 from wxpy import *
>>> from wxpy import Robot, Friend, Group, MALE, TEXT
>>>
>>> # 初始化机器人，并登陆
>>> robot = Robot()
>>>
>>> # 搜索名称含有 "游否" 的男性深圳好友
>>> my_friend = robot.friends.search('游否', sex=MALE, city="深圳")[0]
>>>
>>> # 打印其他好友或群聊的文本消息 (装饰器语法，放在函数 def 的前一行即可)
>>> @robot.msg_register([Friend, Group], TEXT)
>>> def reply_others(msg):
>>>     print(msg)
>>>
>>> # 回复 my_friend 的所有消息 (后注册的匹配优先级更高)
>>> @robot.msg_register(my_friend)
>>> def reply_my_friend(msg):
>>>     return 'received: {} ({})'.format(msg.text, msg.type)
>>>
>>> # 开始监听和处理消息
>>> robot.run()


----

GitHub: https://github.com/youfou/wxpy

----

:copyright: (c) 2017 by Youfou.
:license: Apache 2.0, see LICENSE for more details.

"""


# 机器人
from .wx import Robot
# 聊天对象类
from .wx import Chat, Chats, Friend, Group, Groups, MP, Member, User
# 性别
from .wx import FEMALE, MALE
# 消息类型
from .wx import ATTACHMENT, CARD, FRIENDS, MAP, NOTE, PICTURE, RECORDING, SHARING, SYSTEM, TEXT, VIDEO
# 实用工具
from .utils import dont_raise_response_error, mutual_friends
# 图灵机器人
from .utils import Tuling


__title__ = 'wxpy'
__version__ = '0.0.5'
__author__ = 'Youfou'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2017 Youfou'
