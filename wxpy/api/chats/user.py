# coding: utf-8
from __future__ import unicode_literals

import logging

from .chat import Chat

logger = logging.getLogger(__name__)


class User(Chat):
    """
    好友(:class:`Friend`)、群聊成员(:class:`Member`)，和公众号(:class:`MP`) 的基础类
    """

    @property
    def remark_name(self):
        """
        备注名称
        """
        return self.raw.get('RemarkName') or None

    def set_remark_name(self, remark_name):
        """
        设置或修改好友的备注名称

        :param remark_name: 新的备注名称
        """

        logger.info('setting remark name for {}: {}'.format(self, remark_name))

        return self.core.op_log(self, 2, remark_name=remark_name or '')

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
        return self.raw.get('Sex') or None

    @property
    def province(self):
        """
        省份
        """
        return self.raw.get('Province') or None

    @property
    def city(self):
        """
        城市
        """
        return self.raw.get('City') or None

    @property
    def signature(self):
        """
        个性签名
        """
        return self.raw.get('Signature') or None

    @property
    def is_friend(self):
        """
        判断当前用户是否为好友关系

        :return: 若为好友关系，返回对应的好友，否则返回 False
        """

        if self.username in self.core.data.raw_chats:
            return self.core.get_chat_obj(self.username)
        return False

    def add(self, verify_content=None):
        """
        添加当前用户为好友

        :param verify_content: 验证信息(文本)
        """

        from .mp import MP

        if isinstance(self, MP):
            return self.bot.add_mp(self, verify_content)
        else:
            return self.bot.add_friend(self, verify_content)

    def accept(self):
        """
        接受当前用户为好友

        :return: 新的好友对象
        :rtype: :class:`wxpy.Friend`
        """
        return self.bot.accept_friend(self)
