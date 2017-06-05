# coding: utf-8
from __future__ import unicode_literals

from wxpy.utils import ensure_list, match_attributes, match_name
from .user import User


class Groups(list):
    """
    群聊的合集，可用于按条件搜索
    """

    # 记录已知的 shadow group 和 valid group
    # shadow group 直接抛弃
    # valid group 直接通过
    # 其他的需要确认是否包含机器人自身，并再分类到上面两种群中

    shadow_group_user_names = list()
    valid_group_user_names = list()

    def __init__(self, group_list=None):
        if group_list:
            # Web 微信服务端似乎有个 BUG，会返回不存在的群
            # 具体表现为: 名称为先前退出的群，但成员列表却完全陌生
            # 因此加一个保护逻辑: 只返回"包含自己的群"

            groups_to_init = list()

            for group in group_list:
                if group.user_name in Groups.shadow_group_user_names:
                    continue
                elif group.user_name in Groups.valid_group_user_names:
                    groups_to_init.append(group)
                else:
                    if group.bot.self in group:
                        Groups.valid_group_user_names.append(group.user_name)
                        groups_to_init.append(group)
                    else:
                        Groups.shadow_group_user_names.append(group.user_name)

            super(Groups, self).__init__(groups_to_init)

    def search(self, keywords=None, users=None, **attributes):
        """
        在群聊合集中，根据给定的条件进行搜索

        :param keywords: 群聊名称关键词
        :param users: 需包含的用户
        :param attributes: 属性键值对，键可以是 owner(群主对象), is_owner(自身是否为群主), nick_name(精准名称) 等。
        :return: 匹配条件的群聊列表
        :rtype: :class:`wxpy.Groups`
        """

        users = ensure_list(users)
        if users:
            for user in users:
                if not isinstance(user, User):
                    raise TypeError('expected `User`, got {} (type: {})'.format(user, type(user)))

        def match(group):
            if not match_name(group, keywords):
                return
            if users:
                for _user in users:
                    if _user not in group:
                        return
            if not match_attributes(group, **attributes):
                return
            return True

        return Groups(filter(match, self))
