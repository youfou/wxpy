# coding: utf-8
from __future__ import unicode_literals

import logging

from wxpy.utils import handle_response
from .chat import Chat

logger = logging.getLogger(__name__)


class User(Chat):
    """
    好友(:class:`Friend`)、群聊成员(:class:`Member`)，和公众号(:class:`MP`) 的基础类
    """

    def __init__(self, raw, bot):
        super(User, self).__init__(raw, bot)

    @property
    def remark_name(self):
        """
        备注名称
        """
        return self.raw.get('RemarkName')

    @handle_response()
    def set_remark_name(self, remark_name):
        """
        设置或修改好友的备注名称

        :param remark_name: 新的备注名称
        """

        logger.info('setting remark name for {}: {}'.format(self, remark_name))

        return self.bot.core.set_alias(userName=self.user_name, alias=remark_name)

    @property
    def sex(self):
        """
        性别，目前有::
        
            # 男性
            MALE = 1
            # 女性
            FEMALE = 2
        
        未设置时为 `None`
        """
        return self.raw.get('Sex')

    @property
    def province(self):
        """
        省份
        """
        return self.raw.get('Province')

    @property
    def city(self):
        """
        城市
        """
        return self.raw.get('City')

    @property
    def signature(self):
        """
        个性签名
        """
        return self.raw.get('Signature')

    @property
    def is_friend(self):
        """
        判断当前用户是否为好友关系

        :return: 若为好友关系，返回对应的好友，否则返回 False
        """
        if self.bot:
            try:
                friends = self.bot.friends()
                index = friends.index(self)
                return friends[index]
            except ValueError:
                return False

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
        :rtype: :class:`wxpy.Friend`
        """
        return self.bot.accept_friend(user=self, verify_content=verify_content)
