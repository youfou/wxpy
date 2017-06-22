# coding: utf-8
from __future__ import unicode_literals

import logging
import threading

from wxpy.utils import get_username
from .chat import Chat
from .chats import Chats
from .member import Member

logger = logging.getLogger(__name__)


class Group(Chat):
    """
    群聊对象
    """

    def __init__(self, core, _chat):
        super(Group, self).__init__(core, _chat)
        self._complete_lock = threading.Lock()

    @property
    def members(self):
        """
        群聊的成员列表

        :rtype: class:Chats:
        """

        return Chats(map(lambda x: Member(self.core, x, self.username), self.raw['MemberList']), self)

    def __contains__(self, user):
        username = get_username(user)
        for raw_member in self.raw['MemberList']:
            if username == raw_member.get('UserName'):
                return Member(self.core, raw_member, self.username)

    def __iter__(self):
        for member in self.members:
            yield member

    def __len__(self):
        return len(self.members)

    def __getitem__(self, item):
        return self.members.__getitem__(item)

    def get(self, keywords=None, **attributes):
        """
        在群聊中查找群成员，等同于 :any:`Group.members.get(...) <Chats.get>`
        """
        return self.members.get(keywords, **attributes)

    def find(self, keywords=None, **attributes):
        """
        在群聊中查找群成员，等同于 :any:`Group.members.find(...) <Chats.find>`
        """
        return self.members.find(keywords, **attributes)

    def search(self, keywords=None, **attributes):
        """
        在群聊中查找群成员，等同于 :any:`Group.members.search(...) <Chats.search>`
        """
        return self.members.search(keywords, **attributes)

    @property
    def owner(self):
        """
        返回群主对象
        """
        owner_username = self.raw.get('ChatRoomOwner')
        if owner_username:
            for member in self:
                if member.username == owner_username:
                    return member
        elif self.members:
            return self.members[0]

    @property
    def is_owner(self):
        """
        判断所属 bot 是否为群管理员
        """
        return self.raw.get('IsOwner') or self.owner.username == self.core.username

    @property
    def self(self):
        """
        机器人自身 (作为群成员)
        """
        return self.__contains__(self.core.data.raw_self)

    def _complete_member_details(self):
        """
        补全群聊中不完整的群员详细信息
        """

        with self._complete_lock:
            to_complete = list()
            for mb in self.members:
                if not mb.is_friend and mb.username not in self.core.data.raw_members:
                    to_complete.append(mb)
            if to_complete:
                self.core.batch_get_contact(to_complete)

    def add_members(self, users, use_invitation=False):
        """
        向群聊中加入用户

        :param users: 待加入的用户列表或单个用户
        :param use_invitation: 使用发送邀请的方式
        """

        logger.info('adding {} into {} (use_invitation={}))'.format(users, self, use_invitation))

        raise NotImplementedError

    def remove_members(self, members):
        """
        从群聊中移除用户

        :param members: 待移除的用户列表或单个用户
        """

        raise NotImplementedError

    def rename_group(self, name):
        """
        修改群聊名称

        :param name: 新的名称，超长部分会被截断 (最长32字节)
        """

        encodings = ('gbk', 'utf-8')

        trimmed = False

        for ecd in encodings:
            for length in range(32, 24, -1):
                try:
                    # noinspection PyUnresolvedReferences
                    name = bytes(name.encode(ecd))[:length].decode(ecd)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                else:
                    trimmed = True
                    break
            if trimmed:
                break

        logger.info('renaming group: {} => {}'.format(self.name, name))

        raise NotImplementedError
