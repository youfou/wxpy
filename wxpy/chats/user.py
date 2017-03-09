from .chat import Chat

MALE = 1
FEMALE = 2


class User(Chat):
    """
    好友(:class:`Friend`)、群聊成员(:class:`Member`)，和公众号(:class:`MP`) 的基础类
    """

    def __init__(self, response):
        super(User, self).__init__(response)

        self.alias = response.get('Alias')
        self.display_name = response.get('DisplayName')
        self.remark_name = response.get('RemarkName')
        self.sex = response.get('Sex')
        self.province = response.get('Province')
        self.city = response.get('City')
        self.signature = response.get('Signature')

    def add(self, verify_content=''):
        """
        把当前用户加为好友

        :param verify_content: 验证信息(文本)
        """
        return self.bot.add_friend(user=self, verify_content=verify_content)

    def accept(self, verify_content=''):
        """
        接受当前用户为好友

        :param verify_content: 验证信息(文本)
        :return: 新的好友对象
        """
        return self.bot.accept_friend(user=self, verify_content=verify_content)

    @property
    def is_friend(self):
        """
        判断当前用户是否为好友关系

        :return: 若为好友关系则为 True，否则为 False
        """
        if self.bot:
            return self in self.bot.friends()
