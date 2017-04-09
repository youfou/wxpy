.. wxpy documentation master file, created by
   sphinx-quickstart on Sat Feb 25 23:57:26 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


wxpy: 用 Python 玩微信
==============================

微信机器人 / 优雅的微信个人号API。

在 itchat 的基础上优化接口，扩展功能，提升了模块的易用性。


用来干啥
----------------

一些常见的场景

* 控制路由器、智能家居等具有开放接口的玩意儿
* 运行脚本时自动把日志发送到你的微信
* 加群主为好友，自动拉进群中
* 跨号或跨群转发消息
* 自动陪人聊天
* 逗人玩
* ... [1]_

总而言之，可用来实现各种微信个人号的自动化操作

..  [1] 脑洞太大的就不提了...


轻松安装
----------------

**wxpy 需要使用 Python 3.x**

可以通过以下方式安装

1. 从 PYPI 官方源下载安装 (在国内使用可能比较慢或不稳定)::

    pip3 install -U wxpy

2. 从豆瓣 PYPI 镜像源下载安装 (建议国内用户使用)::

    pip3 install -i https://pypi.doubanio.com/simple/ -U wxpy

..
    针对 **阿里云主机** 用户的特别说明

        阿里云主机默认使用自家的 PYPI 镜像，但截止目前 (2017-3-26) 已滞后长达 33 天！已有不少用户因此安装了滞后的版本，导致与项目文档产生偏差而无法使用。

        因此，强烈建议阿里云主机用户采用豆瓣 PYPI 镜像进行安装 (或替换为 PYPI 官方源)::

            pip3 install -i https://pypi.doubanio.com/simple/ -U wxpy

        *以上说明会在阿里云 PYPI 镜像同步问题修复后移除。*


简单上手
----------------

..  automodule:: wxpy


模块特色
----------------

* 全面对象化接口，调用更优雅
* 默认多线程响应消息，回复更快
* :doc:`愉快的探索和调试 <console>`，无需涂涂改改
* 包含 聊天机器人、共同好友 等 :doc:`实用组件 <utils>`
* 只需两行代码，在其他项目中 :doc:`用微信接收警告 <logging_with_wechat>`
* 可混合使用 itchat 的原接口
* 覆盖常见基本功能
    * 发送文本、图片、视频、文件
    * 通过关键词或用户属性搜索 好友、群聊、群成员 等
    * 获取好友/群成员昵称、备注、性别、地区
    * 加好友，建群，邀请进群，踢出群


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


项目主页
----------------

https://github.com/youfou/wxpy


--------

加入微信交流群 (真的是群哦)

* 扫描以下二维码，填写验证信息 [ **wxpy** ]，即可自动受邀入群

..  image:: wechat-group.png

