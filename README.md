# wxpy

微信个人号 API，基于 itchat，告别满屏 dict，更有 Python 范儿

> wxpy 通过继承和重载来实现改进，因此并不修改 itchat 本身，更不会有共存问题


## 安装

    pip3 install -U wxpy



> 需要使用 Python 3.x



## 使用

示例代码

```python
# 导入所需的组件，也可直接 from wxpy import *
from wxpy import Robot, Friend, Group, MALE, TEXT

# 初始化机器人，并登陆
robot = Robot()

# 搜索名称含有 "游否" 的男性深圳好友
my_friend = robot.friends.search('游否', sex=MALE, city="深圳")[0]

# 打印其他好友或群聊的文本消息 (装饰器语法，放在函数 def 的前一行即可)
@robot.msg_register([Friend, Group], TEXT)
def reply_others(msg):
    print(msg)

# 回复 my_friend 的所有消息 (后注册的匹配优先级更高)
@robot.msg_register(my_friend)
def reply_my_friend(msg):
    return 'received: {} ({})'.format(msg.text, msg.type)

# 开始监听和处理消息
robot.run()
```


> 目前暂无正式说明文档，更多的 API 使用说明请查看源码中的各 docstring。



## 关于

[ItChat](https://github.com/littlecodersh/ItChat) 是目前 GitHub 上唯一功能完善，且支持 Python 3.x 的微信个人号 API 模块，不过其大量使用 dict 进行数据传递，多少有些不方便。因此心血来潮通过继承重载的方式将 itchat 的接口层进行了全面的优化，相信通过本次优化，在调用接口的使用体验上会有一定的提升。

wxpy 仅仅是基于 itchat 的接口优化，网络数据等相对底层的工作仍然由 itchat 完成。
