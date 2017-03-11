from .user import User


class Member(User):
    """
    群聊成员对象
    """

    def __init__(self, raw, group):
        super().__init__(raw, group.bot)
        self.group = group

    @property
    def display_name(self):
        """
        在群聊中的显示昵称
        """
        return self.raw.get('DisplayName')

    # Todo: 如何在获取以下信息时自动更新所在的群的详细数据？(下面注释的实现有误)

    # def _auto_update_group_for_details(self, attr):
    #
    #     value = self.raw.get(attr)
    #     if value is None:
    #         self.group.update_group(members_details=True)
    #         value = self.raw.get(attr)
    #
    #     return value
    #
    # @property
    # def sex(self):
    #     return self._auto_update_group_for_details('Sex')
    #
    # @property
    # def province(self):
    #     return self._auto_update_group_for_details('Province')
    #
    # @property
    # def city(self):
    #     return self._auto_update_group_for_details('City')
    #
    # @property
    # def signature(self):
    #     return self._auto_update_group_for_details('Signature')
