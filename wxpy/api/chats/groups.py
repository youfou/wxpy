# coding: utf-8
from __future__ import unicode_literals

from wxpy.utils import ensure_list, match_attributes, match_name
from .user import User
from .chats import Chats


class Groups(Chats):
    """
    群聊的合集，可用于按条件搜索
    """

    def search(self, keywords=None, members=None, **attributes):
        """
        在群聊合集中，根据给定的条件进行搜索

        :param keywords: 群聊名称关键词
        :param members: 需包含的群员 (比如需要包含几个特定的好友)
        :param attributes: 属性键值对，键可以是 owner(群主对象), is_owner(自身是否为群主), nickname(昵称) 等。
        :return: 匹配条件的群聊列表
        :rtype: :class:`wxpy.Groups`
        """

        members = ensure_list(members)
        if members:
            for user in members:
                if not isinstance(user, User):
                    raise TypeError('expected `User`, got {} (type: {})'.format(user, type(user)))

        def match(group):
            if not match_name(group, keywords):
                return
            if members:
                for _user in members:
                    if _user not in group:
                        return
            if not match_attributes(group, **attributes):
                return
            return True

        return Groups(filter(match, self))
