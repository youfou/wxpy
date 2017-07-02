# coding: utf-8
from __future__ import unicode_literals

from .user import User


class Member(User):
    """
    群聊成员对象
    """

    def __init__(self, core, _raw, group_username):
        super(Member, self).__init__(core, _raw)
        self.group_username = group_username

    @property
    def group(self):
        from .group import Group
        return Group(self.core, self.group_username)

    @property
    def display_name(self):
        """
        在群聊中的显示昵称
        """
        return self._chat.get('DisplayName') or None

    @property
    def name(self):
        return self._chat.get('DisplayName') or self._chat.get('NickName') or None

    def remove(self):
        """
        从群聊中移除该成员
        """
        return self.group.remove(self)

    @property
    def raw(self):

        # 群成员的属性获取来源优先级:
        # 1. Member.raw # display_name, nickname, username 会在这层获取到
        # 2. Data.raw_chats # 如果已经是好友，性别地区签名等其他扩展属性会在这层获取到
        # 3. Data.raw_members # 如果不是好友，其他信息会在这层获取到，并可跨群共享

        # 如此可以:
        # 1. 避免合并属性字典(合并会带来内容准确度问题，例如当群员删除群内显示名称时)
        # 2. 共享已获取到的属性 (适用于当群员为好友，或一人多群)

        # noinspection PyProtectedMember
        self.group._complete_member_details()

        return self.core.data.raw_chats.get(self.username) or self.core.data.raw_members[self.username]
