#!/usr/bin/env python3
# coding: utf-8

"""


登陆微信::

    # 导入模块
    from wxpy import *
    # 初始化机器人，扫码登陆
    robot = Robot()

找到好友::

    # 搜索名称含有 "游否" 的男性深圳好友
    my_friend = robot.friends().search('游否', sex=MALE, city="深圳")[0]

发送消息::

    # 发送文本给好友
    robot.my_friend.send('Hello WeChat!')
    # 发送图片
    robot.my_friend.send_image('my_picture.jpg')

自动响应各类消息::

    # 打印来自其他好友、群聊和公众号的消息
    @robot.register()
    def print_others(msg):
       print(msg)

    # 回复 `my_friend` 的消息 (优先匹配后注册的函数!)
    @robot.register(my_friend)
    def reply_my_friend(msg):
       return 'received: {} ({})'.format(msg.text, msg.type)

    # 开始监听和自动处理消息
    robot.start()


"""

from .utils import Tuling, dont_raise_response_error, ensure_one, mutual_friends
from .wx import ATTACHMENT, CARD, FEMALE, FRIENDS, MALE, MAP, NOTE, PICTURE, RECORDING, SHARING, SYSTEM, TEXT, VIDEO
from .wx import Chat, Chats, Friend, Group, Groups, MP, Member, Message, Messages, Robot, User

__title__ = 'wxpy'
__version__ = '0.0.8'
__author__ = 'Youfou'
__license__ = 'MIT'
__copyright__ = '2017, Youfou'
