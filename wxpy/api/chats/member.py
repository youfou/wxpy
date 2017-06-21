# coding: utf-8
from __future__ import unicode_literals

from .user import User


class Member(User):
    """
    群聊成员对象
    """

    # noinspection PyMissingConstructor
    def __init__(self, core, _raw, group_username):
        self.core = core
        self._raw = _raw
        self._group_username = group_username

    @property
    def group(self):
        return self.core.data.chats[self._group_username]

    @property
    def name(self):
        """
        | 该聊天对象的友好名称
        | 即: 从 群聊显示名称、昵称(或群名称)，username 中按序选取第一个可用的
        """
        for attr in 'display_name', 'nickname', 'username':
            _name = getattr(self, attr, None)
            if _name:
                return _name

    @property
    def nickname(self):
        """
        该聊天对象的昵称 (好友、群员的昵称，或群名称)
        """
        return self._raw.get('NickName') or None

    @property
    def display_name(self):
        """
        在群聊中的显示昵称
        """
        return self._raw.get('DisplayName') or None

    @property
    def username(self):
        return self._raw.get('NickName') or None

    def remove(self):
        """
        从群聊中移除该成员
        """
        return self.group.remove_members(self)

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

        if self.is_friend:
            return self.is_friend.raw
        else:
            return self.core.data.raw_members[self.username]
