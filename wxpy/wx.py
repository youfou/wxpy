import datetime
import inspect
import logging
import queue
import time
import traceback
from collections import Counter
from functools import wraps
from threading import Thread
from xml.etree import ElementTree as ETree

import itchat

MALE = 1
FEMALE = 2

# ---- Message Types ----

TEXT = 'Text'
MAP = 'Map'
CARD = 'Card'
NOTE = 'Note'
SHARING = 'Sharing'
PICTURE = 'Picture'
RECORDING = 'Recording'
ATTACHMENT = 'Attachment'
VIDEO = 'Video'
FRIENDS = 'Friends'
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


def ensure_only_one(found):
    """
    确保列表中仅有一个项，并返回这个项
    :param found: 列表
    :return: 唯一项
    """
    if not isinstance(found, list):
        raise TypeError('expected list, {} found'.format(type(found)))
    elif not found:
        raise ValueError('not found')
    elif len(found) > 1:
        raise ValueError('more than one found')
    else:
        return found[0]


def ensure_list(x, except_false=True):
    """
    若传入的对象不为列表，则转化为列表
    :param x:
    :param except_false: None, False 等例外，会直接返回原值
    :return: 列表，或 None, False 等
    """
    if x or not except_false:
        return x if isinstance(x, (list, tuple)) else [x]


def match_name(chat, name):
    """
    检查一个 Chat 对象是否匹配给定的名称，若名称为空则直接认为匹配
    :param chat: Chat 对象
    :param name: 名称
    :return: 返回匹配的属性，或 False 表示不匹配
    """
    if name:
        name = name.lower()
        for attr in 'nick_name', 'alias', 'remark_name', 'display_name':
            if name in str(getattr(chat, attr, '')).lower():
                return attr
    else:
        return True

    return False


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
    从 itchat 获得的返回结果，绑定所属的 Robot 属性。
    返回值不为 0 时抛出 ResponseError 异常
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
    返回值不为 0 时抛出的 ResponseError 异常
    """
    pass


# ---- Chats ----


class Chat(dict):
    """
    一个基本的聊天对象类，可被继承为 单个用户(User) 或群聊(Group)
    """

    def __init__(self, response):
        super(Chat, self).__init__(response)

        self.robot = getattr(response, 'robot', None)
        self.user_name = self.get('UserName')
        self.nick_name = self.get('NickName')

    @property
    def raw(self):
        return dict(self)

    @handle_response()
    def send(self, msg, media_id=None):
        return self.robot.send(str(msg), self.user_name, media_id)

    @handle_response()
    def send_file(self, path, media_id=None):
        return self.robot.send_file(path, self.user_name, media_id)

    @handle_response()
    def send_image(self, path, media_id=None):
        return self.robot.send_image(path, self.user_name, media_id)

    @handle_response()
    def send_msg(self, msg='Test Message'):
        return self.robot.send_msg(msg, self.user_name)

    @handle_response()
    def send_raw_msg(self, msg_type, content):
        return self.robot.send_raw_msg(msg_type, content, self.user_name)

    @handle_response()
    def send_video(self, path=None, media_id=None):
        return self.robot.send_video(path, self.user_name, media_id)

    @handle_response()
    def pin(self):
        """
        置顶
        """
        return self.robot.set_pinned(self.user_name, isPinned=True)

    @handle_response()
    def unpin(self):
        """
        取消置顶
        """
        return self.robot.set_pinned(self.user_name, isPinned=False)

    @property
    def name(self):
        return self.nick_name or self.user_name

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((Chat, self.user_name))


class User(Chat):
    """
    单个用户，可被继承为 好友(Friend)、群聊成员(Member)、公众号(MP) 等
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

    def add(self, verify_content='', auto_update=True):
        return self.robot.add_friend(self, 2, verify_content, auto_update)

    def accept(self, verify_content='', auto_update=True):
        return self.robot.add_friend(self, 3, verify_content, auto_update)

    @property
    def name(self):
        """
        用户的昵称，以及好友备注或群昵称
        """
        modified = self.display_name or self.remark_name
        if modified:
            return '{} ({})'.format(modified, self.nick_name)
        elif self.nick_name:
            return self.nick_name
        else:
            return self.user_name

    @property
    def is_friend(self):
        """
        判断是否为好友
        :return:
        """
        if self.robot:
            return self in self.robot.friends


class Friend(User):
    """
    好友
    """

    pass


class Member(User):
    """
    群成员
    """

    def __init__(self, raw, group):
        super().__init__(raw)
        self.group = group


class MP(User):
    """
    公众号
    """
    pass


class Group(Chat):
    """
    群聊
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

    def search(self, name=None, **conditions):
        return self.members.search(name, **conditions)

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
        return self['IsOwner'] == 1

    def update_group(self, members_details=False):
        """
        更新群聊的信息
        :param members_details: 包括群聊成员的详细信息 (地区、性别、签名等)
        """

        @handle_response()
        def do():
            return self.robot.update_chatroom(self.user_name, members_details)

        self.__init__(do())

    @handle_response()
    def add_members(self, users, use_invitation=False):
        """
        向群聊中加入用户
        :param users: 待加入的用户列表或单个用户
        :param use_invitation: 使用发送邀请的方式
        """

        return self.robot.add_member_into_chatroom(
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

        return self.robot.delete_member_from_chatroom(
            self.user_name,
            ensure_list(wrap_user_name(members))
        )

    @handle_response()
    def set_alias(self, name):
        """
        设置群备注，似乎仅在 Web 版微信中有效
        :param name: 备注名称
        :return:
        """
        return self.robot.set_alias(get_user_name(self), name)

    def rename_group(self, name):
        """
        修改群名称
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
                return self.robot.set_chatroom_name(get_user_name(self), name)

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
        return Chats(super(Chats, self).__add__(other))

    def search(self, name=None, **conditions):
        """
        在合集中进行搜索
        :param name: 名称 (可以是昵称、备注等)
        :param conditions: 条件键值对，键可以是 sex(性别), province(省份), city(城市) 等。例如可指定 province='广东'
        """

        def match(user):
            if not match_name(user, name):
                return
            for attr, value in conditions.items():
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

    def stats_text(self, total=True, sex=True, top_provinces=10, top_cities=10, print_out=True):
        """
        简单的统计结果的文本
        :param total: 总体数量
        :param sex: 性别分布
        :param top_provinces: 省份分布
        :param top_cities: 城市分布
        :param print_out: 是否打印出来
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
                elif isinstance(self.source, Group):
                    user_title = '群成员'
                else:
                    raise TypeError('source should be Robot or Group')
                text += '{nick_name} 共有 {total} 位{user_title}\n\n'.format(
                    nick_name=self.source.nick_name,
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

        if print_out:
            print(text)
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

    def search(self, name=None, users=None):
        """
        根据给定的条件搜索合集中的群聊
        :param name: 群聊名称
        :param users: 需包含的用户
        :return: 匹配条件的群聊列表
        """

        def match(group):
            if not match_name(group, name):
                return
            if users:
                for user in users:
                    if user not in group:
                        return
            return True

        return Groups(filter(match, self))


# ---- Messages ----

class MsgFuncConfig(object):
    """
    单个消息注册配置
    """

    def __init__(
            self, robot, func, chats, msg_types,
            friendly_only, run_async, enabled
    ):
        self.robot = robot
        self.func = func

        self.chats = chats
        self.msg_types = msg_types
        self.friendly_only = friendly_only
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

    @property
    def _status_str(self):
        return 'Enabled' if self.enabled else 'Disabled'

    def __repr__(self):
        return '<{}: {} -> {} ({})>'.format(
            self.__class__.__name__,
            self.robot.name,
            self.func.__name__,
            self._status_str,
        )


class MsgFuncConfigs(object):
    """
    一个机器人(Robot)的所有消息注册配置
    """

    def __init__(self, robot):
        self.robot = robot
        self.configs = list()

    def __iter__(self):
        for conf in self.configs:
            yield conf

    def __getitem__(self, x):
        if isinstance(x, (int, slice)):
            return self.configs.__getitem__(x)
        else:
            for conf in self:
                if conf.func is x:
                    return conf
            else:
                raise KeyError

    def __repr__(self):
        return repr(self.configs)

    def register(
            self, func, chats, msg_types,
            friendly_only, run_async=True, enabled=True
    ):
        """
        注册新的消息配置
        :param func: 所需执行的回复函数
        :param chats: 单个或列表形式的多个聊天对象或聊天类型，为空时表示不限制
        :param msg_types: 单个或列表形式的多个消息类型，为空时表示不限制
        :param friendly_only: 仅限于好友，或已加入的群聊，可用于过滤不可回复的系统类消息
        :param run_async: 异步执行配置的函数，以提高响应速度
        :param enabled: 配置的默认开启状态，可事后动态开启或关闭
        """
        chats, msg_types = map(ensure_list, (chats, msg_types))
        self.configs.append(MsgFuncConfig(
            self.robot, func, chats, msg_types,
            friendly_only, run_async, enabled
        ))

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

        for conf in self.configs[::-1]:

            if not conf.enabled or (conf.friendly_only and msg.chat not in self.robot.chats):
                return ret()

            if conf.msg_types and msg.type not in conf.msg_types:
                continue

            if not conf.chats:
                return ret(conf)

            for chat in conf.chats:
                if chat == msg.chat or (isinstance(chat, type) and isinstance(msg.chat, chat)):
                    return ret(conf)

        return ret()

    def get_config(self, func):
        """
        根据执行函数找到对应的配置，可用于调试
        :param func:
        :return:
        """
        return self[func]

    def _change_status(self, func, enabled):
        if func:
            self[func].enabled = enabled
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
                ret.append(conf.func)
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
    单条消息
    """

    def __init__(self, raw, robot):
        super(Message, self).__init__(raw)

        self.robot = robot

        self.is_at = self.get('isAt')
        self.type = self.get('Type')
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
        elif self.type == CARD:
            self.card = User(self.get('Text'))
            self.text = self.card.nick_name

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
        return dict(self)

    @property
    def chat(self):
        """
        来自的聊天对象
        """
        user_name = self.get('FromUserName')
        if user_name:
            for _chat in self.robot.chats:
                if _chat.user_name == user_name:
                    return _chat
            return Chat(wrap_user_name(user_name))

    @property
    def member(self):
        """
        来自的群聊成员
        """
        user_name = self.get('ActualUserName')
        if user_name:
            for _member in self.chat:
                if _member.user_name == user_name:
                    return _member
            return User(dict(UserName=user_name, NickName=self.get('ActualNickName')))


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

    def search(self, text=None, **conditions):
        def match(msg):
            if not match_name(msg, text):
                return
            for attr, value in conditions.items():
                if (getattr(msg, attr, None) or msg.get(attr)) != value:
                    return
            return True

        if text:
            text = text.lower()
        return Chats(filter(match, self), self.robot)


# ---- Robot ----

# noinspection PyAbstractClass
class Robot(itchat.Core, Chat):
    """
    微信机器人
    """

    def __init__(
            self, save_path='wxpy.pkl',
            console_qr=False, qr_path=None, qr_callback=None,
            login_callback=None, logout_callback=None
    ):
        """
        初始化微信机器人
        :param save_path: 用于保存/载入的登陆状态文件路径，可在短时间内重新载入登陆状态，失效时会重新要求登陆，若为空则不尝试载入
        :param console_qr: 在终端中显示登陆二维码，需要安装 Pillow 模块
        :param qr_path: 保存二维码的路径
        :param qr_callback: 获得二维码时的回调，接收参数: uuid, status, qrcode
        :param login_callback: 登陆时的回调
        :param logout_callback: 登出时的回调
        """
        super(Robot, self).__init__()
        itchat.instanceList.append(self)

        self.auto_login(
            bool(save_path), save_path,
            console_qr, qr_path, qr_callback,
            login_callback, logout_callback
        )

        self.file_helper = Chat(wrap_user_name('filehelper'))
        self.file_helper.robot = self

        Chat.__init__(self, self.loginInfo['User'])

        self.msg_func_configs = MsgFuncConfigs(self)

        self.messages = Messages(robot=self)

    @property
    def self(self):
        """
        返回自身用户对象
        :return:
        """
        for user in self.get_friends(False, False):
            if user == self:
                return user

    # get

    def except_self(self, dicts):
        return list(filter(lambda x: get_user_name(x) != self.user_name, dicts))

    def get_chats(self, update=True):
        """
        获得所有类型的聊天对象合集
        :param update: 是否请求更新
        :return: 所有类型的聊天对的象合集
        """
        return Chats(self.get_friends(update) + self.get_groups(update) + self.get_mps(update), self)

    @property
    def chats(self):
        """
        获得本地的所有类型聊天对象合集
        """
        return self.get_chats(False)

    @handle_response(Friend)
    def get_friends(self, update=True, except_self=True):
        """
        获得好友对象合集
        :param update: 是否请求更新
        :param except_self: 是否排除自身
        :return: 好友对象合集
        """
        ret = super(Robot, self).get_friends(update=update)
        return self.except_self(ret) if except_self else ret

    @property
    def friends(self):
        """
        获得本地的好友对象合集
        """
        return self.get_friends(False)

    @handle_response(Group)
    def get_groups(self, update=True, contact_only=False):
        """
        获得群聊对象合集
        :param update: 是否请求更新
        :param contact_only: 仅获取存为联系人的群聊
        :return: 群聊对象合集
        """
        return super(Robot, self).get_chatrooms(update, contact_only)

    @property
    def groups(self):
        """
        获得本地的群聊对象合集，不限是否保存为联系人
        """
        return self.get_groups(False)

    @handle_response(MP)
    def get_mps(self, update=True):
        """
        获得公众号对象合集
        :param update: 是否请求更新
        :return: 公众号对象合集
        """
        return super(Robot, self).get_mps(update)

    @property
    def mps(self):
        """
        获取本地的公众号对象合集
        """
        return self.get_mps(False)

    @handle_response(User)
    def get_user_details(self, users, chunk_size=50):
        """
        获得单个或批量获得多个用户的详细信息(地区、性别、签名等)，但不可用于群聊成员
        :param users: 单个或多个用户对象或 user_name
        :param chunk_size: 分配请求时的单批数量，目前为50
        :return: 单个或多个用户用户的详细信息
        """

        def chunks():
            total = ensure_list(users)
            for i in range(0, len(total), chunk_size):
                yield total[i:i + chunk_size]

        @handle_response()
        def do(chunk):
            return self.update_friend(get_user_name(chunk))

        if isinstance(users, (list, tuple)):
            ret = list()
            for c in chunks():
                r = do(c)
                if isinstance(r, list):
                    ret += r
                else:
                    ret.append(r)
            return ret

        else:
            return do(users)

    # add / create

    @handle_response()
    def add_friend(self, user, status=2, verify_content='', auto_update=True):
        """
        添加用户为好友
        :param user: 用户对象或用户名
        :param status: 2 表示发出好友请求，3 表示接受好友请求
        :param verify_content: 验证说明信息
        :param auto_update: 自动更新好友信息
        :return:
        """
        return super(Robot, self).add_friend(get_user_name(user), status, verify_content, auto_update)

    def create_group(self, users, topic=None):
        """
        创建一个新的群聊
        :param users: 用户列表
        :param topic: 群名称
        :return: 若建群成功，返回一个新的群聊对象
        """

        @handle_response()
        def do():
            return super(Robot, self).create_chatroom(wrap_user_name(users), topic or '')

        ret = do()
        user_name = ret.get('ChatRoomName')
        if user_name:
            return Group(self.update_chatroom(user_name))
        else:
            raise ResponseError('建群失败:\n{}'.format(ret))

    # messages

    def configured_reply(self):
        """
        已注册的消息配置
        """
        try:
            msg = Message(self.msgList.get(timeout=1), self)
        except queue.Empty:
            return

        self.messages.append(msg)
        func, run_async = self.msg_func_configs.get_func(msg)

        if not func:
            return

        def do():
            # noinspection PyBroadException
            try:
                func_ret = func(msg)
                if func_ret is not None and msg.chat:
                    self.send(str(func_ret), msg.chat.user_name)
            except:
                logger = logging.getLogger('itchat')
                logger.warning(
                    'An error occurred in registered function, '
                    'use `Robot().run(debug=True)` to show detailed information')
                logger.debug(traceback.format_exc())

        if run_async:
            t = Thread(target=do)
            t.start()
        else:
            do()

    # noinspection PyMethodOverriding
    def msg_register(
            self, chats=None, msg_types=None,
            friendly_only=True, run_async=True, enabled=True
    ):
        """
        装饰器：用于注册消息配置
        :param chats: 单个或列表形式的多个聊天对象或聊天类型，为空时表示不限制
        :param msg_types: 单个或列表形式的多个消息类型，为空时表示不限制
        :param friendly_only: 仅限于好友，或已加入的群聊，可用于过滤不可回复的系统类消息
        :param run_async: 异步执行配置的函数，以提高响应速度
        :param enabled: 当前配置的默认开启状态，可事后动态开启或关闭
        """

        def register(func):
            self.msg_func_configs.register(
                func, chats, msg_types,
                friendly_only, run_async, enabled
            )
            return func

        return register

    def run(self, block=True, debug=False):
        """
        开始监听和处理消息
        :param block: 是否堵塞进程
        :param debug: 是否开启调试信息
        """
        return super(Robot, self).run(debug, block)
