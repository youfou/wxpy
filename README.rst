wxpy: 用 Python 玩微信
==============================

微信个人号 API，基于 itchat，全面优化接口，更有 Python 范儿

入门
--------


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

    # 回复 my_friend 的消息 (优先匹配后注册的函数!)
    @robot.register(my_friend)
    def reply_my_friend(msg):
       return 'received: {} ({})'.format(msg.text, msg.type)

    # 开始监听和自动处理消息
    robot.start()



安装
----------------

使用 Python 3.x ::

    pip3 install -U wxpy


讨论
----------------

* GitHub: https://github.com/youfou/wxpy
* 加入QQ群: `593325850 <http://shang.qq.com/wpa/qunwpa?idkey=9b370de567c3158b8103776543a4b2f752e9f52872c5da94d5a590b1f66a3233>`_
