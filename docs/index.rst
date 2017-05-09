.. wxpy documentation master file, created by
   sphinx-quickstart on Sat Feb 25 23:57:26 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


wxpy: 用 Python 玩微信
==============================

微信机器人 / 优雅而强大的微信个人号 API
    wxpy 在 itchat 的基础上，通过大量接口优化提升了模块的易用性，并进行丰富的功能扩展


项目主页
----------------

https://github.com/youfou/wxpy


用来干啥
----------------

一些常见的场景

* 控制路由器、智能家居等具有开放接口的玩意儿
* 运行脚本时自动把日志发送到你的微信
* 加群主为好友，自动拉进群中
* 跨号或跨群转发消息
* 自动陪人聊天
* 逗人玩
* ...

总而言之，可用来实现各种微信个人号的自动化操作

体验一下
----------------

**这有一个现成的微信机器人，想不想调戏一下？**

记得填写入群口令 👉 [ **wxpy** ]，与群里的大神们谈笑风生 😏

..  image:: wechat-group.png


轻松安装
----------------

**Python 3.x** 版本，安装方法:

    1. 从 PYPI 官方源下载安装 (在国内使用可能比较慢或不稳定):

    ..  code:: shell

        pip3 install -U wxpy

    2. 从豆瓣 PYPI 镜像源下载安装 (**建议国内用户使用**):

    ..  code:: shell

        pip3 install -U wxpy -i "https://pypi.doubanio.com/simple/"

Python 2.x 版本处于 **测试阶段** (感谢 `@RaPoSpectre`_ 的贡献)

    安装方法 (可与 Python 3 版本共存)

    ..  code:: shell

        pip2 install -U "git+https://github.com/bluedazzle/wxpy.git@py2"

    欢迎测试，请在 `这里提交问题`_

    ..  _@RaPoSpectre: https://github.com/bluedazzle
    ..  _这里提交问题: https://github.com/bluedazzle/wxpy/issues


简单上手
----------------

..  automodule:: wxpy


模块特色
----------------

* 全面对象化接口，调用更优雅
* 默认多线程响应消息，回复更快
* 包含 聊天机器人、共同好友 等 :doc:`实用组件 <utils>`
* 只需两行代码，在其他项目中 :doc:`用微信接收警告 <logging_with_wechat>`
* :doc:`愉快的探索和调试 <console>`，无需涂涂改改
* 可混合使用 itchat 的原接口
* 当然，还覆盖了各类常见基本功能:

    * 发送文本、图片、视频、文件
    * 通过关键词或用户属性搜索 好友、群聊、群成员等
    * 获取好友/群成员的昵称、备注、性别、地区等信息
    * 加好友，建群，邀请入群，移出群


文档目录
----------------

..  toctree::
    :maxdepth: 2

    bot
    chats
    messages
    logging_with_wechat
    console
    utils
    itchat
    faq

