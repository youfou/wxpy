#!/usr/bin/env python3
# coding: utf-8

import datetime
import inspect
import logging
import re
import time
import traceback
from collections import Counter
from functools import wraps
from pprint import pformat
from threading import Thread
from xml.etree import ElementTree as ETree

import itchat

logger = logging.getLogger('wxpy')

# ---- Constants ----

MALE = 1
FEMALE = 2

# 文本
TEXT = 'Text'
# 位置
MAP = 'Map'
# 名片
CARD = 'Card'
# 提示
NOTE = 'Note'
# 分享
SHARING = 'Sharing'
# 图片
PICTURE = 'Picture'
# 语音
RECORDING = 'Recording'
# 文件
ATTACHMENT = 'Attachment'
# 视频
VIDEO = 'Video'
# 好友请求
FRIENDS = 'Friends'
# 系统
SYSTEM = 'System'


# ---- Functions ----

def handle_response(to_class=None):
    """
    装饰器：检查从 itchat 返回的字典对象，并将其转化为指定类的实例
    若返回值不为0，会抛出 ResponseError 异常

    :param to_class: 需转化成的类，若为None则不转换
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            ret = func(*args, **kwargs)

            if not ret:
                return

            if args:
                self = args[0]
            else:
                self = inspect.currentframe().f_back.f_locals.get('self')

            if isinstance(self, Robot):
                robot = self
            else:
                robot = getattr(self, 'robot', None)
                if not robot:
                    raise ValueError('robot not found:m\nmethod: {}\nself: {}\nrobot: {}'.format(
                        func, self, robot
                    ))

            ret = list_or_single(Response, ret, robot)

            if to_class:
                ret = list_or_single(to_class, ret)

            if isinstance(ret, list):
                if to_class is Group:
                    ret = Groups(ret)
                elif to_class:
                    ret = Chats(ret)

            return ret

        return wrapped

    return decorator


def ensure_list(x, except_false=True):
    """
    若传入的对象不为列表，则转化为列表

    :param x:
    :param except_false: None, False 等例外，会直接返回原值
    :return: 列表，或 None, False 等
    """
    if x or not except_false:
        return x if isinstance(x, (list, tuple)) else [x]


def match_name(chat, keywords):
    """
    检查一个 Chat 对象是否匹配所有名称关键词 (若关键词为空则直接认为匹配)

    :param chat: Chat 对象
    :param keywords: 名称关键词，可用空格分割
    :return: 匹配则返回 True，否则 False
    """
    if keywords:
        if isinstance(keywords, str):
            keywords = re.split(r'\s+', keywords)
        keywords = list(map(lambda x: x.lower(), keywords))
        for kw in keywords:
            for attr in 'nick_name', 'alias', 'remark_name', 'display_name':
                if kw in str(getattr(chat, attr, '')).lower():
                    break
            else:
                return False
    return True


def list_or_single(func, i, *args, **kwargs):
    """
    将单个对象或列表中的每个项传入给定的函数，并返回单个结果或列表结果，类似于 map 函数

    :param func: 传入到的函数
    :param i: 列表或单个对象
    :param args: func 函数所需的 args
    :param kwargs: func 函数所需的 kwargs
    :return: 若传入的为列表，则以列表返回每个结果，反之为单个结果
    """
    if isinstance(i, list):
        return list(map(lambda x: func(x, *args, **kwargs), i))
    else:
        return func(i, *args, **kwargs)


def wrap_user_name(user_or_users):
    """
    确保将用户转化为带有 UserName 键的用户字典

    :param user_or_users: 单个用户，或列表形式的多个用户
    :return: 单个用户字典，或列表形式的多个用户字典
    """
    return list_or_single(
        lambda x: x if isinstance(x, dict) else {'UserName': user_or_users},
        user_or_users
    )


def get_user_name(user_or_users):
    """
    确保将用户转化为 user_name 字串

    :param user_or_users: 单个用户，或列表形式的多个用户
    :return: 返回单个 user_name 字串，或列表形式的多个 user_name 字串
    """
    return list_or_single(
        lambda x: x['UserName'] if isinstance(x, dict) else x,
        user_or_users
    )


# ---- Response ----

class Response(dict):
    """
    | 从 itchat 获得的网络请求返回结果，绑定所属的 Robot 属性。
    | ret_code 不为 0 时会抛出 :class:`ResponseError` 异常
    """

    def __init__(self, raw, robot):
        super(Response, self).__init__(raw)

        self.robot = robot

        self.base_response = self.get('BaseResponse', dict())
        self.ret_code = self.base_response.get('Ret')
        self.err_msg = self.base_response.get('ErrMsg')

        if self.ret_code:
            raise ResponseError('code: {0.ret_code}; msg: {0.err_msg}'.format(self))


class ResponseError(Exception):
    """
    当 :class:`Response` 的返回值不为 0 时抛出的异常
    """
    pass


# ---- Chats ----


class Chat(dict):
    """
    单个用户(:class:`User`)和群聊(:class:`Group`)的基础类
    """

    def __init__(self, response):
        super(Chat, self).__init__(response)

        self.robot = getattr(response, 'robot', None)
        self.user_name = self.get('UserName')
        self.nick_name = self.get('NickName')

    @property
    def raw(self):
        """
        原始数据
        """
        return dict(self)

    @handle_response()
    def send(self, msg, media_id=None):
        """
        动态发送不同类型的消息，具体类型取决于 `msg` 的前缀。

        :param msg:
            | 由 **前缀** 和 **内容** 两个部分组成，若 **省略前缀**，将作为纯文本消息发送
            | **前缀** 部分可为: '@fil@', '@img@', '@msg@', '@vid@' (不含引号)
            | 分别表示: 文件，图片，纯文本，视频
            | **内容** 部分可为: 文件、图片、视频的路径，或纯文本的内容
        :param media_id: 填写后可省略上传过程
        """
        return self.robot.core.send(msg=str(msg), toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_image(self, path, media_id=None):
        """
        发送图片

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        return self.robot.core.send_image(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_file(self, path, media_id=None):
        """
        发送文件

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        return self.robot.core.send_file(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_video(self, path=None, media_id=None):
        """
        发送视频

        :param path: 文件路径
        :param media_id: 设置后可省略上传
        """
        return self.robot.core.send_video(fileDir=path, toUserName=self.user_name, mediaId=media_id)

    @handle_response()
    def send_msg(self, msg='Hello WeChat! -- by wxpy'):
        """
        发送文本消息

        :param msg: 文本内容
        """
        return self.robot.core.send_msg(msg=str(msg), toUserName=self.user_name)

    @handle_response()
    def send_raw_msg(self, msg_type, content):
        """
        以原始格式发送其他类型的消息。例如，好友名片::

            import wxpy
            robot = wxpy.Robot()
            @robot.register(msg_types=wxpy.CARD)
            def reply_text(msg):
                msg.chat.send_raw_msg(msg['MsgType'], msg['Content'])

        """
        return self.robot.core.send_raw_msg(msgType=msg_type, content=content, toUserName=self.user_name)

    @handle_response()
    def pin(self):
        """
        将聊天对象置顶
        """
        return self.robot.core.set_pinned(userName=self.user_name, isPinned=True)

    @handle_response()
    def unpin(self):
        """
        取消聊天对象的置顶状态
        """
        return self.robot.core.set_pinned(userName=self.user_name, isPinned=False)

    @property
    def name(self):
        for attr in 'display_name', 'remark_name', 'nick_name', 'alias':
            _name = getattr(self, attr, None)
            if _name:
                return _name

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((Chat, self.user_name))


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
        return self.robot.add_friend(verify_content=verify_content)

    def accept(self, verify_content=''):
        return self.robot.accept_friend(verify_content=verify_content)

    @property
    def is_friend(self):
        """
        判断当前用户是否为好友关系

        :return: 若为好友关系则为 True，否则为 False
        """
        if self.robot:
            return self in self.robot.friends()


class Friend(User):
    """
    好友对象
    """

    pass


class Member(User):
    """
    群聊成员对象
    """

    def __init__(self, raw, group):
        super().__init__(raw)
        self.group = group


class MP(User):
    """
    公众号对象
    """
    pass


class Group(Chat):
    """
    群聊对象
    """

    def __init__(self, response):
        super(Group, self).__init__(response)

        self._members = Chats(source=self)
        for raw in self.get('MemberList', list()):
            member = Member(raw, self)
            member.robot = self.robot
            self._members.append(member)

    @property
    def members(self):
        """
        群聊的成员列表
        """
        if not self._members or not self._members[-1].nick_name:
            self.update_group()
        return self._members

    def __contains__(self, user):
        user = wrap_user_name(user)
        for member in self.members:
            if member == user:
                return member

    def __iter__(self):
        for member in self.members:
            yield member

    def __getitem__(self, x):
        if isinstance(x, (int, slice)):
            return self.members.__getitem__(x)
        else:
            return super(Group, self).__getitem__(x)

    def __len__(self):
        return len(self.members)

    def search(self, name=None, **attributes):
        """
        在群聊中搜索成员

        :param name: 成员名称关键词
        :param attributes: 属性键值对
        :return: 匹配的群聊成员
        """
        return self.members.search(name, **attributes)

    @property
    def owner(self):
        """
        返回群主对象
        """
        owner_user_name = self.get('ChatRoomOwner')
        if owner_user_name:
            for member in self:
                if member.user_name == owner_user_name:
                    return member
        elif self.members:
            return self[0]

    @property
    def is_owner(self):
        """
        判断所属 robot 是否为群管理员
        """
        return self.get('IsOwner') == 1 or self.owner == self.robot.self

    def update_group(self, members_details=False):
        """
        更新群聊的信息

        :param members_details: 是否包括群聊成员的详细信息 (地区、性别、签名等)
        """

        @handle_response()
        def do():
            return self.robot.core.update_chatroom(self.user_name, members_details)

        self.__init__(do())

    @handle_response()
    def add_members(self, users, use_invitation=False):
        """
        向群聊中加入用户

        :param users: 待加入的用户列表或单个用户
        :param use_invitation: 使用发送邀请的方式
        """

        return self.robot.core.add_member_into_chatroom(
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

        return self.robot.core.delete_member_from_chatroom(
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
                logging.info('renaming group: {} => {}'.format(self.name, name))
                return self.robot.core.set_chatroom_name(get_user_name(self), name)

        ret = do()
        self.update_group()
        return ret


class Chats(list):
    """
    多个聊天对象的合集，可用于搜索或统计
    """

    def __init__(self, chat_list=None, source=None):
        if chat_list:
            super(Chats, self).__init__(chat_list)
        self.source = source

    def __add__(self, other):
        return Chats(super(Chats, self).__add__(other or list()))

    def search(self, name=None, **attributes):
        """
        在合集中进行搜索

        :param name: 名称 (可以是昵称、备注等)
        :param attributes: 属性键值对，键可以是 sex(性别), province(省份), city(城市) 等。例如可指定 province='广东'
        :return: 匹配的聊天对象合集
        """

        def match(user):
            if not match_name(user, name):
                return
            for attr, value in attributes.items():
                if (getattr(user, attr, None) or user.get(attr)) != value:
                    return
            return True

        if name:
            name = name.lower()
        return Chats(filter(match, self), self.source)

    def stats(self, attribs=('sex', 'province', 'city')):
        """
        统计各属性的分布情况

        :param attribs: 需统计的属性列表或元组
        :return: 统计结果
        """

        def attr_stat(objects, attr_name):
            return Counter(list(map(lambda x: getattr(x, attr_name), objects)))

        attribs = ensure_list(attribs)
        ret = dict()
        for attr in attribs:
            ret[attr] = attr_stat(self, attr)
        return ret

    def stats_text(self, total=True, sex=True, top_provinces=10, top_cities=10):
        """
        简单的统计结果的文本

        :param total: 总体数量
        :param sex: 性别分布
        :param top_provinces: 省份分布
        :param top_cities: 城市分布
        :return: 统计结果文本
        """

        def top_n_text(attr, n):
            top_n = list(filter(lambda x: x[0], stats[attr].most_common()))[:n]
            top_n = ['{}: {} ({:.2%})'.format(k, v, v / len(self)) for k, v in top_n]
            return '\n'.join(top_n)

        stats = self.stats()

        text = str()

        if total:
            if self.source:
                if isinstance(self.source, Robot):
                    user_title = '微信好友'
                    nick_name = self.source.self.nick_name
                elif isinstance(self.source, Group):
                    user_title = '群成员'
                    nick_name = self.source.nick_name
                else:
                    raise TypeError('source should be Robot or Group')
                text += '{nick_name} 共有 {total} 位{user_title}\n\n'.format(
                    nick_name=nick_name,
                    total=len(self),
                    user_title=user_title
                )
            else:
                text += '共有 {} 位用户\n\n'.format(len(self))

        if sex and self:
            males = stats['sex'].get(MALE, 0)
            females = stats['sex'].get(FEMALE, 0)

            text += '男性: {males} ({male_rate:.1%})\n女性: {females} ({female_rate:.1%})\n\n'.format(
                males=males,
                male_rate=males / len(self),
                females=females,
                female_rate=females / len(self),
            )

        if top_provinces and self:
            text += 'TOP {} 省份\n{}\n\n'.format(
                top_provinces,
                top_n_text('province', top_provinces)
            )

        if top_cities and self:
            text += 'TOP {} 城市\n{}\n\n'.format(
                top_cities,
                top_n_text('city', top_cities)
            )

        return text

    def add_all(self, interval=1, verify_content='', auto_update=True):
        """
        将合集中的所有用户加为好友，请小心应对调用频率限制！

        :param interval: 间隔时间(秒)
        :param verify_content: 验证说明文本
        :param auto_update: 自动更新到好友中
        :return:
        """
        for user in self:
            logging.info('Adding {}'.format(user.name))
            ret = user.add(verify_content, auto_update)
            logging.info(ret)
            logging.info('Waiting for {} seconds'.format(interval))
            time.sleep(interval)


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
                if (getattr(group, attr, None) or group.get(attr)) != value:
                    return
            return True

        return Groups(filter(match, self))


# ---- Messages ----

class MessageConfig(object):
    """
    单个消息注册配置
    """

    def __init__(
            self, robot, func, chats, msg_types,
            except_self, run_async, enabled
    ):
        self.robot = robot
        self.func = func

        self.chats = ensure_list(chats)
        self.msg_types = ensure_list(msg_types)
        self.except_self = except_self
        self.run_async = run_async

        self._enabled = None
        self.enabled = enabled

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        logging.info(self.__repr__())

    def __repr__(self):
        return '<{}: {}: {} ({}{})>'.format(
            self.__class__.__name__,
            self.robot.self.name,
            self.func.__name__,
            'Async, ' if self.run_async else '',
            'Enabled' if self.enabled else 'Disabled',
        )


class MessageConfigs(list):
    """
    一个机器人(Robot)的所有消息注册配置
    """

    def __init__(self, robot):
        """
        初始化

        :param robot: 这些配置所属的机器人
        """
        super(MessageConfigs, self).__init__()
        self.robot = robot

    def get_func(self, msg):
        """
        获取给定消息的对应回复函数。每条消息仅匹配和执行一个回复函数，后注册的配置具有更高的匹配优先级。

        :param msg: 给定的消息
        :return: 回复函数 func，及是否异步执行 run_async
        """

        def ret(_conf=None):
            if _conf:
                return _conf.func, _conf.run_async
            else:
                return None, None

        for conf in self[::-1]:

            if not conf.enabled or (conf.except_self and msg.chat == self.robot.self):
                return ret()

            if conf.msg_types and msg.type not in conf.msg_types:
                continue
            elif not conf.msg_types and msg.type == SYSTEM:
                continue

            if not conf.chats:
                return ret(conf)

            for chat in conf.chats:
                if chat == msg.chat or (isinstance(chat, type) and isinstance(msg.chat, chat)):
                    return ret(conf)

        return ret()

    def get_config(self, func):
        """
        根据执行函数找到对应的配置

        :param func: 已注册的函数
        :return: 对应的配置
        """
        for conf in self:
            if conf.func is func:
                return conf

    def _change_status(self, func, enabled):
        if func:
            self.get_config(func).enabled = enabled
        else:
            for conf in self:
                conf.enabled = enabled

    def enable(self, func=None):
        """
        开启指定函数的对应配置。若不指定函数，则开启所有已注册配置。

        :param func: 指定的函数
        """
        self._change_status(func, True)

    def disable(self, func=None):
        """
        关闭指定函数的对应配置。若不指定函数，则关闭所有已注册配置。

        :param func: 指定的函数
        """
        self._change_status(func, False)

    def _check_status(self, enabled):
        ret = list()
        for conf in self:
            if conf.enabled == enabled:
                ret.append(conf)
        return ret

    @property
    def enabled(self):
        """
        检查处于开启状态的配置

        :return: 处于开启状态的配置
        """
        return self._check_status(True)

    @property
    def disabled(self):
        """
        检查处于关闭状态的配置

        :return: 处于关闭状态的配置
        """
        return self._check_status(False)


class Message(dict):
    """
    单条消息对象
    """

    def __init__(self, raw, robot):
        super(Message, self).__init__(raw)

        self.robot = robot
        self.type = self.get('Type')

        self.is_at = self.get('isAt')
        self.file_name = self.get('FileName')
        self.img_height = self.get('ImgHeight')
        self.img_width = self.get('ImgWidth')
        self.play_length = self.get('PlayLength')
        self.url = self.get('Url')
        self.voice_length = self.get('VoiceLength')
        self.id = self.get('NewMsgId')

        self.text = None
        self.get_file = None
        self.create_time = None
        self.location = None
        self.card = None

        text = self.get('Text')
        if callable(text):
            self.get_file = text
        else:
            self.text = text

        create_time = self.get('CreateTime')
        if isinstance(create_time, int):
            self.create_time = datetime.datetime.fromtimestamp(create_time)

        if self.type == MAP:
            try:
                self.location = ETree.fromstring(self['OriContent']).find('location').attrib
                try:
                    self.location['x'] = float(self.location['x'])
                    self.location['y'] = float(self.location['y'])
                    self.location['scale'] = int(self.location['scale'])
                    self.location['maptype'] = int(self.location['maptype'])
                except (KeyError, ValueError):
                    pass
                self.text = self.location.get('label')
            except (TypeError, KeyError, ValueError, ETree.ParseError):
                pass
        elif self.type in (CARD, FRIENDS):
            self.card = User(self.get('RecommendInfo'))
            self.text = self.card.get('Content')

        # 将 msg.chat.send* 方法绑定到 msg.reply*，例如 msg.chat.send_img => msg.reply_img
        for method in '', '_image', '_file', '_video', '_msg', '_raw_msg':
            setattr(self, 'reply' + method, getattr(self.chat, 'send' + method))

    def __hash__(self):
        return hash((Message, self.id))

    def __repr__(self):
        text = (str(self.text) or '').replace('\n', ' ')
        ret = '{0.chat.name}'
        if self.member:
            ret += ' -> {0.member.name}'
        ret += ': '
        if self.text:
            ret += '{1} '
        ret += '({0.type})'
        return ret.format(self, text)

    @property
    def raw(self):
        """原始数据"""
        return dict(self)

    @property
    def chat(self):
        """
        来自的聊天对象
        """
        user_name = self.get('FromUserName')
        if user_name:
            for _chat in self.robot.chats():
                if _chat.user_name == user_name:
                    return _chat
            _chat = Chat(wrap_user_name(user_name))
            _chat.robot = self.robot
            return _chat

    @property
    def member(self):
        """
        发送此消息的群聊成员 (若消息来自群聊)
        """
        if isinstance(self.chat, Group):
            actual_user_name = self.get('ActualUserName')
            for _member in self.chat:
                if _member.user_name == actual_user_name:
                    return _member
            return Member(dict(UserName=actual_user_name, NickName=self.get('ActualNickName')), self.chat)


class Messages(list):
    """
    多条消息的合集，可用于记录或搜索
    """

    def __init__(self, msg_list=None, robot=None, max_history=10000):
        if msg_list:
            super(Messages, self).__init__(msg_list)
        self.robot = robot
        self.max_history = max_history

    def __add__(self, other):
        return Chats(super(Messages, self).__add__(other))

    def append(self, msg):
        del self[:-self.max_history + 1]
        return super(Messages, self).append(msg)

    def search(self, text=None, **attributes):
        """
        搜索消息

        :param text:
        :param attributes:
        :return:
        """

        def match(msg):
            if not match_name(msg, text):
                return
            for attr, value in attributes.items():
                if (getattr(msg, attr, None) or msg.get(attr)) != value:
                    return
            return True

        if text:
            text = text.lower()
        return Chats(filter(match, self), self.robot)


# ---- Robot ----


class Robot(object):
    """
    机器人对象，用于登陆和操作微信账号，涵盖大部分 Web 微信的功能
    """

    def __init__(
            self, save_path=None, console_qr=False, qr_path=None,
            qr_callback=None, login_callback=None, logout_callback=None
    ):
        """
        :param save_path:
            | 用于保存或载入登陆状态的文件路径，例如: 'wxpy.pkl'，为空则不尝试载入。
            | 填写本参数后，可在短时间内重新载入登陆状态，避免重复扫码，失效时会重新要求登陆
        :param console_qr: 在终端中显示登陆二维码，需要安装 Pillow 模块
        :param qr_path: 保存二维码的路径
        :param qr_callback: 获得二维码时的回调，接收参数: uuid, status, qrcode
        :param login_callback: 登陆时的回调，接收参数同上
        :param logout_callback: 登出时的回调，接收参数同上
        """

        self.core = itchat.Core()
        itchat.instanceList.append(self)

        self.core.auto_login(
            hotReload=bool(save_path), statusStorageDir=save_path,
            enableCmdQR=console_qr, picDir=qr_path, qrCallback=qr_callback,
            loginCallback=login_callback, exitCallback=logout_callback
        )

        self.message_configs = MessageConfigs(self)
        self.messages = Messages(robot=self)

        self.file_helper = Chat(wrap_user_name('filehelper'))
        self.file_helper.robot = self
        self.file_helper.nick_name = '文件传输助手'

        self.self = Chat(self.core.loginInfo['User'])
        self.self.robot = self

        self.save_path = save_path

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.self.name)

    @handle_response()
    def logout(self):
        """
        登出当前账号
        """

        return self.core.logout()

    @property
    def alive(self):
        """
        当前的登陆状态

        :return: 若为登陆状态，则为 True，否则为 False
        """

        return self.core.alive

    @alive.setter
    def alive(self, value):
        self.core.alive = value

    def dump_login_status(self, save_path=None):
        return self.core.dump_login_status(save_path or self.save_path)

    # chats

    def except_self(self, chats_or_dicts):
        """
        从聊天对象合集或用户字典列表中排除自身

        :param chats_or_dicts: 聊天对象合集或用户字典列表
        :return: 排除自身后的列表
        """
        return list(filter(lambda x: get_user_name(x) != self.self.user_name, chats_or_dicts))

    def chats(self, update=False):
        """
        获取所有聊天对象

        :param update: 是否更新
        :return: 聊天对象合集
        """
        return Chats(self.friends(update) + self.groups(update) + self.mps(update), self)

    def friends(self, update=False):
        """
        获取所有好友

        :param update: 是否更新
        :return: 聊天对象合集
        """

        @handle_response(Friend)
        def do():
            return self.core.get_friends(update=update)

        ret = do()
        ret.source = self

        return ret

    @handle_response(Group)
    def groups(self, update=False, contact_only=False):
        """
        获取所有群聊

        :param update: 是否更新
        :param contact_only: 是否限于保存为联系人的群聊
        :return: 群聊合集
        """
        return self.core.get_chatrooms(update=update, contactOnly=contact_only)

    @handle_response(MP)
    def mps(self, update=False):
        """
        获取所有公众号

        :param update: 是否更新
        :return: 聊天对象合集
        """
        return self.core.get_mps(update=update)

    @handle_response(User)
    def user_details(self, user_or_users, chunk_size=50):
        """
        获取单个或批量获取多个用户的详细信息(地区、性别、签名等)，但不可用于群聊成员

        :param user_or_users: 单个或多个用户对象或 user_name
        :param chunk_size: 分配请求时的单批数量，目前为 50
        :return: 单个或多个用户用户的详细信息
        """

        def chunks():
            total = ensure_list(user_or_users)
            for i in range(0, len(total), chunk_size):
                yield total[i:i + chunk_size]

        @handle_response()
        def process_one_chunk(_chunk):
            return self.core.update_friend(userName=get_user_name(_chunk))

        if isinstance(user_or_users, (list, tuple)):
            ret = list()
            for chunk in chunks():
                chunk_ret = process_one_chunk(chunk)
                if isinstance(chunk_ret, list):
                    ret += chunk_ret
                else:
                    ret.append(chunk_ret)
            return ret
        else:
            return process_one_chunk(user_or_users)

    def search(self, name=None, **attributes):
        """
        在所有类型的聊天对象中进行搜索

        :param name: 名称 (可以是昵称、备注等)
        :param attributes: 属性键值对，键可以是 sex(性别), province(省份), city(城市) 等。例如可指定 province='广东'
        :return: 匹配的聊天对象合集
        """

        return self.chats().search(name, **attributes)

    # add / create

    @handle_response()
    def add_friend(self, user, verify_content=''):
        """
        添加用户为好友

        :param user: 用户对象或用户名
        :param verify_content: 验证说明信息
        """
        return self.core.add_friend(
            userName=get_user_name(user),
            status=2,
            verifyContent=verify_content,
            autoUpdate=True
        )

    @handle_response()
    def accept_friend(self, user, verify_content=''):
        """
        接受用户为好友

        :param user: 用户对象或用户名
        :param verify_content: 验证说明信息
        """

        # Todo: 验证好友接口可用性，并在接受好友时直接返回新好友

        return self.core.add_friend(
            userName=get_user_name(user),
            status=3,
            verifyContent=verify_content,
            autoUpdate=True
        )

    def create_group(self, users, topic=None):
        """
        创建一个新的群聊

        :param users: 用户列表
        :param topic: 群名称
        :return: 若建群成功，返回一个新的群聊对象
        """

        @handle_response()
        def request():
            return self.core.create_chatroom(
                memberList=wrap_user_name(users),
                topic=topic or ''
            )

        ret = request()
        user_name = ret.get('ChatRoomName')
        if user_name:
            return Group(self.core.update_chatroom(userName=user_name))
        else:
            raise ResponseError('Failed to create group:\n{}'.format(pformat(ret)))

    # messages

    def _process_message(self, msg):
        """
        处理接收到的消息
        """

        if not self.alive:
            return

        func, run_async = self.message_configs.get_func(msg)

        if not func:
            return

        def process():
            # noinspection PyBroadException
            try:
                ret = func(msg)
                if ret is not None:
                    if isinstance(ret, (tuple, list)):
                        self.core.send(
                            msg=str(ret[0]),
                            toUserName=msg.chat.user_name,
                            mediaId=ret[1]
                        )
                    else:
                        self.core.send(
                            msg=str(ret),
                            toUserName=msg.chat.user_name
                        )
            except:
                logger.warning(
                    'An error occurred in registered function, '
                    'use `Robot().start(debug=True)` to show detailed information')
                logger.debug(traceback.format_exc())

        if run_async:
            Thread(target=process).start()
        else:
            process()

    def register(
            self, chats=None, msg_types=None,
            except_self=True, run_async=True, enabled=True
    ):
        """
        装饰器：用于注册消息配置

        :param chats: 单个或列表形式的多个聊天对象或聊天类型，为空时匹配所有聊天对象
        :param msg_types: 单个或列表形式的多个消息类型，为空时匹配所有消息类型 (SYSTEM 类消息除外)
        :param except_self: 排除自己在手机上发送的消息
        :param run_async: 异步执行配置的函数，可提高响应速度
        :param enabled: 当前配置的默认开启状态，可事后动态开启或关闭
        """

        def register(func):
            self.message_configs.append(MessageConfig(
                robot=self, func=func, chats=chats, msg_types=msg_types,
                except_self=except_self, run_async=run_async, enabled=enabled
            ))

            return func

        return register

    def start(self, block=True):
        """
        开始监听和处理消息

        :param block: 是否堵塞线程，为 False 时将在新的线程中运行
        """

        def listen():

            logger.info('{} Auto-reply started.'.format(self))
            try:
                while self.alive:
                    msg = Message(self.core.msgList.get(), self)
                    if msg.type is not SYSTEM:
                        self.messages.append(msg)
                    self._process_message(msg)
            except KeyboardInterrupt:
                logger.info('KeyboardInterrupt received, ending...')
                self.alive = False
                if self.core.useHotReload:
                    self.dump_login_status()
                logger.info('Bye.')

        if block:
            listen()
        else:
            t = Thread(target=listen, daemon=True)
            t.start()
