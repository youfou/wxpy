from .user import User


class Member(User):
    """
    群聊成员对象
    """

    def __init__(self, raw, group):
        super().__init__(raw)
        self.group = group
