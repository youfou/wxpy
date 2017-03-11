from wxpy.utils import match_name


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
        """

        def match(group):
            if not match_name(group, name):
                return
            if users:
                for user in users:
                    if user not in group:
                        return
            for attr, value in attributes.items():
                if (getattr(group, attr, None) or group.raw.get(attr)) != value:
                    return
            return True

        return Groups(filter(match, self))
