# coding: utf-8
from __future__ import unicode_literals

from .user import User


# Todo: 若尝试获取群成员信息时为空，自动更新成员信息 (并要照顾到遍历所有群成员的场景)


class Member(User):
    """
    群聊成员对象
    """

    def __init__(self, raw, group):
        super(Member, self).__init__(raw, group.bot)
        self._group_user_name = group.user_name

    @property
    def group(self):
        for _group in self.bot.groups():
            if _group.user_name == self._group_user_name:
                return _group
        raise Exception('failed to find the group belong to')

    @property
    def display_name(self):
        """
        在群聊中的显示昵称
        """
        return self.raw.get('DisplayName')

    def remove(self):
        """
        从群聊中移除该成员
        """
        return self.group.remove_members(self)

    @property
    def name(self):
        """
        | 该群成员的友好名称
        | 具体为: 从 群聊显示名称、昵称(或群名称)，或微信号中，按序选取第一个可用的
        """
        for attr in 'display_name', 'nick_name', 'wxid':
            _name = getattr(self, attr, None)
            if _name:
                return _name
