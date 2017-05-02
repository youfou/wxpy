# coding: utf-8
# from __future__ import unicode_literals
from future.builtins import str
# 导入模块
from wxpy import *

# 初始化机器人，扫码登陆
bot = Bot('bot.pkl')
my_friend = bot.friends().search('rapospectre')[0]
my_friend.send('Hello WeChat!')

# a = str('abc')
#
# print type(a)