wxpy: 用 Python 玩微信
==============================

优雅的微信个人号 机器人/API，基于 itchat，全面优化接口，更有 Python 范儿


用来干啥
----------------

一些常见的场景

* 控制路由器、智能家居等具有开放接口的玩意儿
* 跑脚本时自动把日志发送到你的微信
* 加群主为好友，自动拉进群中
* 充当各种信息查询
* 转发消息
* 逗人玩
* ... [1]_

总而言之，可用来实现各种微信个人号的自动化操作

..  [1] 脑洞太大的就不提了...


轻松安装
----------------

使用 Python 3.x ::

    pip3 install -U wxpy


简单上手
----------------


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
    my_friend.send('Hello WeChat!')
    # 发送图片
    my_friend.send_image('my_picture.jpg')

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


模块特色
----------------

* 全面对象化接口，调用更优雅
* 默认多线程响应消息，回复更快
* 附带 共同好友、图灵机器人 等实用组件
* 覆盖大部分常用功能:

    * 发送文本、图片、视频、文件
    * 通过关键词或用户属性搜索 好友、群聊、群成员 等
    * 获取好友/群成员昵称、备注、性别、地区
    * 加好友，建群，邀请进群，踢出群


了解更多
----------------

说明文档: http://wxpy.readthedocs.io

加入讨论
----------------

GitHub: https://github.com/youfou/wxpy

--------

加入微信交流群 (真的是群哦)

* 加以下微信，填写验证 [ **wxpy** ]，即可自动受邀入群

..  image:: docs/wechat-group.png
