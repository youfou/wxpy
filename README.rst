
wxpy
==================================

微信个人号 API，基于 itchat，全面优化接口，更有 Python 范儿


用 Python 玩转微信
------------------------

登陆微信::

    # 导入机器人组件
    from wxpy import *
    # 初始化机器人，扫码登陆
    robot = Robot()

简单发送消息::

    # 给自己的 "文件传输助手" 发送消息
    robot.file_helper.send('Hello WeChat!')
    # 发送图片
    robot.file_helper.send_image('my_picture.jpg')

在微信中搜索::

    # 搜索名称含有 "游否" 的男性深圳好友
    my_friend = robot.friends().search('游否', sex=MALE, city="深圳")[0]

自动响应各类消息::

    # 打印来自好友或群聊的文本消息
    @robot.register([Friend, Group], TEXT)
    def reply_others(msg):
       print(msg)

    # 回复 my_friend 的所有消息 (优先匹配后注册的函数!)
    @robot.register(my_friend)
    def reply_my_friend(msg):
       return 'received: {} ({})'.format(msg.text, msg.type)

    # 开始监听和处理消息
    robot.start()


快速安装
------------------

使用 Python 3.x ::

    pip3 install -U wxpy

一起讨论吧
------------------

加入QQ群: `593325850 <http://shang.qq.com/wpa/qunwpa?idkey=9b370de567c3158b8103776543a4b2f752e9f52872c5da94d5a590b1f66a3233>`_
