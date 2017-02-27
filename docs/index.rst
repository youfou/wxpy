.. wxpy documentation master file, created by
   sphinx-quickstart on Sat Feb 25 23:57:26 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


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

..  automodule:: wxpy


模块特色
----------------

* 全面对象化接口，调用更优雅
* 默认多线程响应消息，回复更快
* 附带 :any:`共同好友 <mutual_friends>`、:any:`图灵机器人 <Tuling>` 等实用组件
* 覆盖大部分常用功能:

    * 发送文本、图片、视频、语音、文件
    * 通过关键词或用户属性搜索 好友、群聊、群成员 等
    * 获取好友/群成员昵称、备注、性别、地区
    * 加好友，建群，邀请进群，踢出群


文档目录
----------------

..  toctree::
    :maxdepth: 2

    api/robot
    api/chat
    api/message
    api/utils


加入讨论
----------------

GitHub: https://github.com/youfou/wxpy

--------

加入微信交流群:

* 加以下微信，填写验证 [ **wxpy** ]，即可自动受邀

.. image:: wechat-group.png
