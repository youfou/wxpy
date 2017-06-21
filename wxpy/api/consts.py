# coding: utf-8
from __future__ import unicode_literals

# 以下常量采用了 Web 微信 JS 中的命名方式
# 部分消息类型际上不会在 Web 微信中被用到

SYSTEM = None

# 文本
TEXT = 'text', 1
# 图片
IMAGE = 'image', 3
# 语音
VOICE = 'voice', 34
# 视频
VIDEO = 'video', 43
# 小视频
MICRO_VIDEO = 'micro_video', 62
# 表情
EMOTICON = 'emotion', 47

# 分享链接
APP = 'app', 49


# VOIP 通话
VOIP = 'voip', 50
# VOIP 提醒
VOIP_NOTIFY = 'voip_notify', 52
# VOIP 邀请
VOIP_INVITE = 'voip_invite', 53
# 定位
LOCATION = 'location', 48
# 状态提醒 (例如 Web 微信登陆、消息已读)
STATUS_NOTIFY = 'status_notify', 51
# 系统提醒
SYS_NOTICE = 'sys_notice', 9999
# 可能的好友推荐
POSSIBLE_FRIEND = 'possible_friend', 40
# 好友验证
VERIFY = 'verify', 37
# 名片分享
SHARE_CARD = 'share_card', 42
# 系统消息
SYS = 'sys', 10000
# 消息撤回提醒
RECALLED = 'recalled', 10002

# 男性
MALE = 'male', 1
# 女性
FEMALE = 'female', 2
