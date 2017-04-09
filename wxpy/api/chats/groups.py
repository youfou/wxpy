from wxpy.utils import ensure_list, match_attributes, match_name
from .user import User


class Groups(list):
    """
    群聊的合集，可用于按条件搜索
    """

    def __init__(self, group_list=None):
        if group_list:
            super(Groups, self).__init__(group_list)

    def search(self, name=None, users=None, **attributes):
        """
        根据给定的条件搜索合集中的群聊

        :param name: 群聊名称
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
            if not match_name(group, name):
                return
            if users:
                for _user in users:
                    if _user not in group:
                        return
            if not match_attributes(group, **attributes):
                return
            return True

        return Groups(filter(match, self))
