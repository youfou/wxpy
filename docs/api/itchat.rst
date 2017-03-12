itchat 与原始数据
==============================

..  module:: wxpy


正是得益于 |itchat| 的坚实基础，wxpy 才能够在短时间内快速实现这些新的接口和功能。

感谢 itchat 维护者们的辛勤付出。

以下为如何在 wxpy 中混合使用 itchat 的原接口和原始数据。


..  |itchat| raw:: html

    <a href="https://github.com/littlecodersh/itchat" target="_blank">itchat</a>


使用 itchat 的原接口
------------------------------

只需在 wxpy 的 :class:`Bot` 对象后紧跟 `.core.*` 即可调用 itchat 的原接口。

例如，使用 itchat 的 `search_friends` 接口::

    from wxpy import *
    bot = Bot()
    found = bot.core.search_friends('游否')

..  attention:: 通过 itchat 原接口所获取到的结果为原始数据，可能无法直接传递到 wxpy 的对应方法中。


使用原始数据
------------------------------

wxpy 的所有 **聊天对象** 和 **消息对象** 均基于从 itchat 获取到的数据进行封装。若需使用原始数据，只需在对象后紧跟 `.raw`。

例如，查看一个 :class:`好友 <Friend>` 对象的原始数据::

    from wxpy import *
    bot = Bot()
    a_friend = bot.friends()[0]
    print(a_friend.raw)

