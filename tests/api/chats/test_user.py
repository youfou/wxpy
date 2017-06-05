import re

from wxpy import *


class TestUser:
    def test_friend_attributes(self, friend):
        assert isinstance(friend, Friend)
        assert friend.nick_name == 'wxpy 机器人'
        assert friend.wxid in ('wxpy_bot', None)
        assert friend.province == '广东'
        assert friend.city == '深圳'
        assert friend.sex == MALE
        assert friend.signature == '如果没有正确响应，可能正在调试中…'
        assert re.match(r'@[\da-f]{32,}', friend.user_name)
        assert friend.is_friend

    # def test_add(self, member):
    #     member.add('wxpy tests: test_add')

    def test_accept(self, member):
        # 似乎只要曾经是好友，就可以调用这个方法，达到"找回已删除的好友"的效果
        member.accept()

    def test_remark_name(self, friend, member):
        new_remark_name = '__test__123__'

        for user in friend, member:
            current_remark_name = user.remark_name or ''
            for remark_name in new_remark_name, current_remark_name:
                user.set_remark_name(remark_name)
