import logging

from wxpy.utils import ensure_list, get_user_name, handle_response, wrap_user_name
from .chat import Chat
from .chats import Chats
from .member import Member

logger = logging.getLogger(__name__)


class Group(Chat):
    """
    群聊对象
    """

    def __init__(self, raw, bot):
        super(Group, self).__init__(raw, bot)

    @property
    def members(self):
        """
        群聊的成员列表
        """

        def raw_member_list(update=False):
            if update:
                self.update_group()
            return self.raw.get('MemberList', list())

        ret = Chats(source=self)
        ret.extend(map(
            lambda x: Member(x, self),
            raw_member_list() or raw_member_list(True)
        ))
        return ret

    def __contains__(self, user):
        user_name = get_user_name(user)
        for member in self.members:
            if member.user_name == user_name:
                return member

    def __iter__(self):
        for member in self.members:
            yield member

    def __len__(self):
        return len(self.members)

    def search(self, name=None, **attributes):
        """
        在群聊中搜索成员

        :param name: 成员名称关键词
        :param attributes: 属性键值对
        :return: 匹配的群聊成员
        :rtype: :class:`wxpy.Chats`
        """
        return self.members.search(name, **attributes)

    @property
    def owner(self):
        """
        返回群主对象
        """
        owner_user_name = self.raw.get('ChatRoomOwner')
        if owner_user_name:
            for member in self:
                if member.user_name == owner_user_name:
                    return member
        elif self.members:
            return self.members[0]

    @property
    def is_owner(self):
        """
        判断所属 bot 是否为群管理员
        """
        return self.raw.get('IsOwner') == 1 or self.owner == self.bot.self

    @property
    def self(self):
        """
        机器人自身 (作为群成员)
        """
        for member in self:
            if member == self.bot.self:
                return member

    def update_group(self, members_details=False):
        """
        更新群聊的信息

        :param members_details: 是否包括群聊成员的详细信息 (地区、性别、签名等)
        """

        logger.info('updating {} (members_details={})'.format(self, members_details))

        @handle_response()
        def do():
            return self.bot.core.update_chatroom(self.user_name, members_details)

        super(Group, self).__init__(do(), self.bot)

    @handle_response()
    def add_members(self, users, use_invitation=False):
        """
        向群聊中加入用户

        :param users: 待加入的用户列表或单个用户
        :param use_invitation: 使用发送邀请的方式
        """

        logger.info('adding {} into {} (use_invitation={}))'.format(users, self, use_invitation))

        return self.bot.core.add_member_into_chatroom(
            self.user_name,
            ensure_list(wrap_user_name(users)),
            use_invitation
        )

    @handle_response()
    def remove_members(self, members):
        """
        从群聊中移除用户

        :param members: 待移除的用户列表或单个用户
        """

        logger.info('removing {} from {}'.format(members, self))

        return self.bot.core.delete_member_from_chatroom(
            self.user_name,
            ensure_list(wrap_user_name(members))
        )

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
                    name = bytes(name.encode(ecd))[:length].decode(ecd)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                else:
                    trimmed = True
                    break
            if trimmed:
                break

        @handle_response()
        def do():
            if self.name != name:
                logger.info('renaming group: {} => {}'.format(self.name, name))
                return self.bot.core.set_chatroom_name(get_user_name(self), name)

        ret = do()
        self.update_group()
        return ret
