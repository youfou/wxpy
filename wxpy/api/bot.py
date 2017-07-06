# coding: utf-8
from __future__ import unicode_literals

import atexit
import logging
import tempfile
import weakref
from pprint import pformat
from threading import Thread
from types import MethodType

from wxpy.api.chats import Friend, Group, MP
from wxpy.api.core import Core
from wxpy.api.messages import MessageConfig, Messages, Registered
from wxpy.api.messages.message_types import *
from wxpy.compatible import PY2
from wxpy.compatible.utils import force_encoded_string_output
from wxpy.utils import PuidMap, get_raw_dict, get_username, start_new_thread

try:
    import queue
except ImportError:
    # noinspection PyUnresolvedReferences,PyPep8Naming
    import Queue as queue

logger = logging.getLogger(__name__)


class Bot(object):
    """
    机器人对象，用于登陆和操作微信账号，涵盖大部分 Web 微信的功能::
    
        from wxpy import *
        bot = Bot()
        
        # 机器人账号自身
        myself = bot.self
        
        # 向文件传输助手发送消息
        bot.file_helper.send('Hello from wxpy!')
    """

    def __init__(self, cache_path=None, console_qr=None, qr_path=None, proxies=None, hooks=None):
        """
        :param cache_path:
            * 设置当前会话的缓存路径，并开启缓存功能；为 `None` (默认) 则不开启缓存功能。
            * 开启缓存后可在短时间内避免重复扫码，缓存失效时会重新要求登陆。
            * 设为 `True` 时，使用默认的缓存路径 'wxpy.pkl'。
        :param console_qr:
            * 在终端中显示登陆二维码，需要安装 pillow 模块 (`pip3 install pillow`)。
            * 可为整数(int)，表示二维码单元格的宽度，通常为 2 (当被设为 `True` 时，也将在内部当作 2)。
            * 也可为负数，表示以反色显示二维码，适用于浅底深字的命令行界面。
            * 例如: 在大部分 Linux 系统中可设为 `True` 或 2，而在 macOS Terminal 的默认白底配色中，应设为 -2。
        :param qr_path: 保存二维码的路径
        :param proxies: `requests 代理，形式为
            <http://docs.python-requests.org/en/master/user/advanced/#proxies>`_
        :param hooks: 用于快速重载 :class:`Core` 中的各种方法，形式为 `{'原方法名': 新函数, ...}`
        """

        self.core = Core(
            bot=weakref.proxy(self), cache_path=cache_path,
            console_qr=console_qr, qr_path=qr_path, proxies=proxies
        )

        if isinstance(hooks, dict):
            for ori_method_name, replace_func in hooks.items():
                # noinspection PyArgumentList
                setattr(self.core, ori_method_name, MethodType(replace_func, self.core))

        self.core_thread = self.core.login()

        self.self = self.core.self
        self.username = self.core.username

        self.messages = Messages()
        self.registered = Registered(self)

        # Todo: 重新实现 puid，以及 puid 的版本迁移
        self.puid_map = None
        # Todo: 自动标为已读: 改为以秒数间隔的操作，避免操作过于频繁
        self.auto_mark_as_read = False

        self.is_listening = False
        self.listening_thread = None

        if PY2:
            from wxpy.compatible.utils import TemporaryDirectory
            # noinspection PyArgumentList
            self.temp_dir = TemporaryDirectory(prefix='wxpy_')
        else:
            self.temp_dir = tempfile.TemporaryDirectory(prefix='wxpy_')

        self.start()

        atexit.register(self._cleanup)

    @force_encoded_string_output
    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.core.name)

    def __unicode__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.core.name)

    @property
    def name(self):
        """
        机器人的微信昵称
        """

        return self.core.name

    @property
    def alive(self):
        """
        若为登陆状态，则为 True，否则为 False
        """

        return self.core_thread.is_alive()

    # chats

    def enable_puid(self, path='wxpy_puid.pkl'):
        """
        **可选操作:** 启用聊天对象的 :any:`puid <Chat.puid>` 属性::
            
            # 启用 puid 属性，并指定 puid 所需的映射数据保存/载入路径
            bot.enable_puid('wxpy_puid.pkl')
            
            # 指定一个好友
            my_friend = bot.friends().search('游否')[0]
            
            # 查看他的 puid
            print(my_friend.puid)
            # 'edfe8468'

        ..  tip::
        
            | :any:`puid <Chat.puid>` 是 **wxpy 特有的聊天对象/用户ID**
            | 不同于其他 ID 属性，**puid** 可始终被获取到，且具有稳定的唯一性

        :param path: puid 所需的映射数据保存/载入路径
        """

        self.puid_map = PuidMap(path)
        return self.puid_map

    @property
    def file_helper(self):
        """
        文件传输助手 (聊天对象)
        """
        return self.core.get_chat_obj('filehelper')

    @property
    def chats(self):
        """
        所有聊天对象

        :rtype: :class:`wxpy.Chats`
        """

        return self.core.get_chats(convert=True)

    @property
    def friends(self):
        """
        好友列表

        :rtype: :class:`wxpy.Chats`
        """

        return self.core.get_chats(Friend, convert=True)

    @property
    def groups(self):
        """
        群聊列表

        | 一些不活跃的群可能无法被获取到
        | 建议重要的群加入到通讯录中，以确保始终可见

        :rtype: :class:`wxpy.Chats`
        """

        return self.core.get_chats(Group, convert=True)

    @property
    def mps(self):
        """
        公众号列表

        :rtype: :class:`wxpy.Chats`
        """

        return self.core.get_chats(MP, convert=True)

    def get(self, keywords=None, **attributes):
        """
        查找聊天对象，等同于 :any:`Bot.chats.get(...) <Chats.get>`
        """
        return self.chats.get(keywords, **attributes)

    def find(self, keywords=None, **attributes):
        """
        查找聊天对象，等同于 :any:`Bot.chats.find(...) <Chats.find>`
        """
        return self.chats.find(keywords, **attributes)

    def search(self, keywords=None, **attributes):
        """
        查找聊天对象，等同于 :any:`Bot.chats.search(...) <Chats.search>`
        """
        return self.chats.search(keywords, **attributes)

    # add / create

    def add_friend(self, user, verify_content=''):
        """
        添加用户为好友 (注意有严格的调用频率限制!)

        :param user: 用户对象，或 username
        :param verify_content: 验证说明信息
        """

        logger.info('{}: adding {} (verify_content: {})'.format(self, user, verify_content))

        return self.core.verify_user(user, 2, verify_content)

    def add_mp(self, user):
        """
        添加/关注 公众号
        
        :param user: 公众号对象，或 username
        """

        logger.info('{}: adding {}'.format(self, user))

        return self.core.verify_user(user, 1)

    def accept_friend(self, user):
        """
        接受用户为好友

        :param user: 用户对象 (msg.card) 或 username
        :return: 新的好友对象
        :rtype: :class:`wxpy.Friend`
        """

        logger.info('{}: accepting new friend {}'.format(self, user))

        self.core.verify_user(user, 3)
        self.core.batch_get_contact(user)

        return self.friends.find(username=get_username(user)) or Friend(self.core, get_raw_dict(user))

    def create_group(self, users, topic=None):
        """
        创建一个新的群聊 (注意有严格的调用频率限制!)

        :param users: 用户列表 (不含自己，至少 2 位)
        :param topic: 群名称
        :return: 若建群成功，返回一个新的群聊对象
        :rtype: :class:`wxpy.Group`
        """

        logger.info('{}: creating group (topic: {}), with users:\n{}'.format(
            self, topic, pformat(users)))

        username = self.core.create_chatroom(users, topic)
        return self.groups.find(username=username)

    # upload

    def upload_file(self, path, msg_type):
        """
        | 上传文件，并获取 media_id
        | 可用于重复发送图片、表情、视频，和文件

        :param path: 文件路径
        :param msg_type: 发送时的消息类型，支持 IMAGE, STICKER, VIDEO, FILE
        :return: media_id
        :rtype: str
        """

        logger.info('{}: uploading file: {}'.format(self, path))

        return self.core.upload_media(path, msg_type)

    # messages / register

    def _process_message(self, msg):
        """
        处理接收到的消息
        """

        if not self.alive:
            return

        config = self.registered.get_config(msg)

        logger.debug('{}: new message (func: {}):\n{}'.format(
            self, config.func.__name__ if config else None, msg))

        if config:

            def process():
                # noinspection PyBroadException
                try:
                    ret = config.func(msg)
                    if ret is not None:
                        msg.reply(ret)
                except:
                    logger.exception('an error occurred in {}.'.format(config.func))

                if self.auto_mark_as_read and not msg.type == UNKNOWN and msg.sender != self.self:
                    from wxpy import ResponseError
                    try:
                        msg.chat.mark_as_read()
                    except ResponseError as e:
                        logger.warning('failed to mark as read: {}'.format(e))

            if config.run_async:
                start_new_thread(process, use_caller_name=True)
            else:
                process()

    def register(
            self, chats=None, msg_types=None,
            except_self=True, run_async=True, enabled=True
    ):
        """
        装饰器：用于注册消息配置

        :param chats: 消息所在的聊天对象：单个或列表形式的多个聊天对象或聊天类型，为空时匹配所有聊天对象
        :param msg_types: 消息的类型：单个或列表形式的多个消息类型，为空时匹配所有已知消息类型
        :param except_self: 排除由自己发送的消息
        :param run_async: 是否异步执行所配置的函数：可提高响应速度
        :param enabled: 当前配置的默认开启状态，可事后动态开启或关闭
        """

        def do_register(func):
            self.registered.append(MessageConfig(
                bot=self, func=func, chats=chats, msg_types=msg_types,
                except_self=except_self, run_async=run_async, enabled=enabled
            ))

            return func

        return do_register

    # noinspection PyBroadException
    def _listen(self):
        try:
            logger.info('{}: started'.format(self))
            self.is_listening = True

            while self.alive and self.is_listening:
                try:
                    msg = self.core.message_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if msg.type != UNKNOWN:
                    self.messages.append(msg)

                try:
                    self._process_message(msg)
                except:
                    logger.exception('an error occurred while processing msg:\n{}'.format(msg))
        finally:
            self.is_listening = False
            self._cleanup()
            logger.info('{}: stopped'.format(self))

    def start(self):
        """
        开始消息监听和处理 (登陆后会自动开始)
        """

        if not self.alive:
            logger.warning('{} has been logged out!'.format(self))
        elif self.is_listening:
            logger.warning('{} is already running, no need to start again.'.format(self))
        else:
            self.listening_thread = start_new_thread(self._listen)

    def stop(self):
        """
        停止消息监听和处理 (登出后会自动停止)
        """

        if self.is_listening:
            self.is_listening = False
            self.listening_thread.join()
        else:
            logger.warning('{} is not running.'.format(self))

    def join(self):
        """
        阻塞进程，直到结束消息监听 (例如，机器人被登出时)
        """

        if isinstance(self.listening_thread, Thread):
            try:
                logger.info('{}: joined'.format(self))
                self.listening_thread.join()
            except KeyboardInterrupt:
                pass

    def logout(self):
        """
        登出当前账号
        """

        return self.core.logout()

    def _cleanup(self):
        if self.is_listening:
            self.stop()
        self.temp_dir.cleanup()
