import atexit
import functools
import logging
import os.path
import queue
import tempfile
from pprint import pformat
from threading import Thread

import itchat

from wxpy.api.chats import Chat, Chats, Friend, Group, MP, User
from wxpy.api.messages import Message, MessageConfig, Messages, Registered, SYSTEM
from wxpy.utils import enhance_connection, ensure_list, get_user_name, handle_response, wrap_user_name

logger = logging.getLogger(__name__)


class Bot(object):
    """
    机器人对象，用于登陆和操作微信账号，涵盖大部分 Web 微信的功能
    """

    def __init__(
            self, cache_path=None, console_qr=False, qr_path=None,
            qr_callback=None, login_callback=None, logout_callback=None
    ):
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
        :param qr_callback: 获得二维码后的回调，接收参数: uuid, status, qrcode
        :param login_callback: 登陆成功后的回调，接收参数同上
        :param logout_callback: 登出时的回调，接收参数同上
        """

        self.core = itchat.Core()
        itchat.instanceList.append(self)

        enhance_connection(self.core.s)

        if cache_path is True:
            cache_path = 'wxpy.pkl'

        self.cache_path = cache_path

        if console_qr is True:
            console_qr = 2

        self.core.auto_login(
            hotReload=bool(cache_path), statusStorageDir=cache_path,
            enableCmdQR=console_qr, picDir=qr_path, qrCallback=qr_callback,
            loginCallback=login_callback, exitCallback=logout_callback
        )

        self.self = Friend(self.core.loginInfo['User'], self)
        self.file_helper = Chat(wrap_user_name('filehelper'), self)

        self.messages = Messages()
        self.registered = Registered(self)

        self.is_listening = False
        self.listening_thread = None

        self.temp_dir = tempfile.TemporaryDirectory(prefix='wxpy_')
        self.start()

        atexit.register(self._cleanup)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.self.name)

    @handle_response()
    def logout(self):
        """
        登出当前账号
        """

        logger.info('{}: logging out'.format(self))

        return self.core.logout()

    @property
    def alive(self):
        """
        若为登陆状态，则为 True，否则为 False
        """

        return self.core.alive

    @alive.setter
    def alive(self, value):
        self.core.alive = value

    def dump_login_status(self, cache_path=None):
        logger.info('{}: dumping login status'.format(self))
        return self.core.dump_login_status(cache_path or self.cache_path)

    # chats

    def except_self(self, chats_or_dicts):
        """
        从聊天对象合集或用户字典列表中排除自身

        :param chats_or_dicts: 聊天对象合集或用户字典列表
        :return: 排除自身后的列表
        :rtype: :class:`wxpy.Chats`
        """
        return list(filter(lambda x: get_user_name(x) != self.self.user_name, chats_or_dicts))

    def chats(self, update=False):
        """
        获取所有聊天对象

        :param update: 是否更新
        :return: 聊天对象合集
        :rtype: :class:`wxpy.Chats`
        """
        return Chats(self.friends(update) + self.groups(update) + self.mps(update), self)

    def _retrieve_itchat_storage(self, attr):
        with self.core.storageClass.updateLock:
            return getattr(self.core.storageClass, attr)

    @handle_response(Friend)
    def friends(self, update=False):
        """
        获取所有好友

        :param update: 是否更新
        :return: 聊天对象合集
        :rtype: :class:`wxpy.Chats`
        """

        if update:
            logger.info('{}: updating friends'.format(self))
            return self.core.get_friends(update=update)
        else:
            return self._retrieve_itchat_storage('memberList')

    @handle_response(Group)
    def groups(self, update=False, contact_only=False):
        """
        获取所有群聊对象

        一些不活跃的群可能无法被获取到，可通过在群内发言，或修改群名称的方式来激活

        :param update: 是否更新
        :param contact_only: 是否限于保存为联系人的群聊
        :return: 群聊合集
        :rtype: :class:`wxpy.Groups`
        """

        # itchat 原代码有些难懂，似乎 itchat 中的 get_contact() 所获取的内容视其 update 参数而变化
        # 如果 update=False 获取所有类型的本地聊天对象
        # 反之如果 update=True，变为获取收藏的聊天室

        if update or contact_only:
            logger.info('{}: updating groups'.format(self))
            return self.core.get_chatrooms(update=update, contactOnly=contact_only)
        else:
            return self._retrieve_itchat_storage('chatroomList')

    @handle_response(MP)
    def mps(self, update=False):
        """
        获取所有公众号

        :param update: 是否更新
        :return: 聊天对象合集
        :rtype: :class:`wxpy.Chats`
        """

        if update:
            logger.info('{}: updating mps'.format(self))
            return self.core.get_mps(update=update)
        else:
            return self._retrieve_itchat_storage('mpList')

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
        :rtype: :class:`wxpy.Chats`
        """

        return self.chats().search(name, **attributes)

    # add / create

    @handle_response()
    def add_friend(self, user, verify_content=''):
        """
        添加用户为好友

        :param user: 用户对象或 user_name
        :param verify_content: 验证说明信息
        """

        logger.info('{}: adding {} (verify_content: {})'.format(self, user, verify_content))

        return self.core.add_friend(
            userName=get_user_name(user),
            status=2,
            verifyContent=verify_content,
            autoUpdate=True
        )

    def accept_friend(self, user, verify_content=''):
        """
        接受用户为好友

        :param user: 用户对象或 user_name
        :param verify_content: 验证说明信息
        :return: 新的好友对象
        :rtype: :class:`wxpy.Friend`
        """

        logger.info('{}: accepting {} (verify_content: {})'.format(self, user, verify_content))

        @handle_response()
        def do():
            return self.core.add_friend(
                userName=get_user_name(user),
                status=3,
                verifyContent=verify_content,
                autoUpdate=True
            )

        do()
        # 若上一步没有抛出异常，则返回该好友
        for friend in self.friends():
            if friend == user:
                return friend

    def create_group(self, users, topic=None):
        """
        创建一个新的群聊

        :param users: 用户列表
        :param topic: 群名称
        :return: 若建群成功，返回一个新的群聊对象
        :rtype: :class:`wxpy.Group`
        """

        logger.info('{}: creating group (topic: {}), with users:\n{}'.format(
            self, topic, pformat(users)))

        @handle_response()
        def request():
            return self.core.create_chatroom(
                memberList=dict_list,
                topic=topic or ''
            )

        dict_list = wrap_user_name(self.except_self(ensure_list(users)))
        ret = request()
        user_name = ret.get('ChatRoomName')
        if user_name:
            return Group(self.core.update_chatroom(userName=user_name), self)
        else:
            raise Exception('Failed to create group:\n{}'.format(pformat(ret)))

    # upload

    def upload_file(self, path):
        """
        | 上传文件，并获取 media_id
        | 可用于重复发送图片、表情、视频，和文件

        :param path: 文件路径
        :return: media_id
        :rtype: str
        """

        logger.info('{}: uploading file: {}'.format(self, path))

        @handle_response()
        def do():
            upload = functools.partial(self.core.upload_file, fileDir=path)
            ext = os.path.splitext(path)[1].lower()

            if ext in ('.bmp', '.png', '.jpeg', '.jpg', '.gif'):
                return upload(isPicture=True)
            elif ext == '.mp4':
                return upload(isVideo=True)
            else:
                return upload()

        return do().get('MediaId')

    # messages / register

    def _process_message(self, msg):
        """
        处理接收到的消息
        """

        if not self.alive:
            return

        config = self.registered.get_config(msg)

        logger.debug('{}: received message (func: {}):\n{}'.format(
            self, config.func.__name__ if config else None, msg))

        if not config:
            return

        def process():
            # noinspection PyBroadException
            try:
                ret = config.func(msg)
                if ret is not None:
                    msg.reply(ret)
            except:
                logger.exception('\nAn error occurred in {}.'.format(config.func))

        if config.run_async:
            Thread(target=process, daemon=True).start()
        else:
            process()

    def register(
            self, chats=None, msg_types=None,
            except_self=True, run_async=True, enabled=True
    ):
        """
        装饰器：用于注册消息配置

        :param chats: 消息所在的聊天对象：单个或列表形式的多个聊天对象或聊天类型，为空时匹配所有聊天对象
        :param msg_types: 消息的类型：单个或列表形式的多个消息类型，为空时匹配所有消息类型 (SYSTEM 类消息除外)
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

    def _listen(self):
        try:
            logger.info('{}: started'.format(self))
            self.is_listening = True
            while self.alive and self.is_listening:
                try:
                    msg = Message(self.core.msgList.get(timeout=0.5), self)
                except queue.Empty:
                    continue
                if msg.type is not SYSTEM:
                    self.messages.append(msg)
                self._process_message(msg)
        finally:
            self.is_listening = False
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
            self.listening_thread = Thread(target=self._listen, daemon=True)
            self.listening_thread.start()

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
        堵塞进程，直到结束消息监听 (例如，机器人被登出时)
        """

        if isinstance(self.listening_thread, Thread):
            try:
                logger.info('{}: joined'.format(self))
                self.listening_thread.join()
            except KeyboardInterrupt:
                pass

    def _cleanup(self):
        if self.is_listening:
            self.stop()
        if self.alive and self.core.useHotReload:
            self.dump_login_status()
        self.temp_dir.cleanup()
