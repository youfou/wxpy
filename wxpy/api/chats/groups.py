from wxpy.utils import ensure_list, match_attributes, match_name
from .user import User


class Groups(list):
    """
    群聊的合集，可用于按条件搜索
    """

    def __init__(self, group_list=None):
        if group_list:
            # Web 微信服务端似乎有个 BUG，会返回不存在的群
            # 具体表现为: 名称为先前退出的群，但成员列表却完全陌生
            # 因此加一个保护逻辑: 只返回"包含自己的群"

            super(Groups, self).__init__(
                list(filter(lambda x: x.bot.self in x, group_list))
            )

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
