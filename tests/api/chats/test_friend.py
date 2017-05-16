import re

from wxpy import *


class TestFriend:
    def test_friend_attributes(self, friend):
        assert isinstance(friend, Friend)
        assert friend.name == 'wxpy 机器人 123'
        assert friend.nick_name == 'wxpy 机器人'
        assert friend.remark_name == friend.name
        assert friend.wxid in ('wxpy_bot', None)
        assert friend.province == '广东'
        assert friend.city == '深圳'
        assert friend.sex == MALE
        assert friend.signature == '如果没有正确响应，可能正在调试中…'
        assert re.match(r'@[\da-f]{32,}', friend.user_name)
        assert friend.is_friend
