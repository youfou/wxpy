import logging
from pprint import pformat
from threading import Thread

import itchat

from wxpy.api.chats import Chat, Chats, Friend, Group, MP, User
from wxpy.api.messages import Message, MessageConfig, MessageConfigs, Messages
from wxpy.api.messages import SYSTEM
from wxpy.exceptions import ResponseError
from wxpy.utils import ensure_list, get_user_name, handle_response, wrap_user_name

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
            | 当前会话缓存的保存路径，不指定则不使用缓存功能。
            | 缓存后，可避免重复扫码，缓存失效时会重新要求登陆。
            | 缓存有效时间非常短暂，适用于修改代码后的重新运行。
        :param console_qr:
            | 在终端中显示登陆二维码。该功能需要安装 pillow 模块 (`pip3 install pillow`)。
            | 该参数可为整数(int)，表示二维码单元格的宽度，通常为 2。当该参数被设为 `True` 时，也将在内部当作 2。
            | 该参数也可为负数，表示以反色显示二维码，适用于浅底深字的命令行界面。
            | 例如: 在大部分 Linux 系统中可设为 `True` 或 2，而在 macOS Terminal 的默认白底配色中，应设为 -2。
        :param qr_path: 保存二维码的路径
        :param qr_callback: 获得二维码后的回调，接收参数: uuid, status, qrcode
        :param login_callback: 登陆成功后的回调，接收参数同上
        :param logout_callback: 登出时的回调，接收参数同上
        """

        self.core = itchat.Core()
        itchat.instanceList.append(self)

        if console_qr is True:
            console_qr = 2

        self.core.auto_login(
            hotReload=bool(cache_path), statusStorageDir=cache_path,
            enableCmdQR=console_qr, picDir=qr_path, qrCallback=qr_callback,
            loginCallback=login_callback, exitCallback=logout_callback
        )

        self.message_configs = MessageConfigs(self)
        self.messages = Messages(bot=self)

        self.file_helper = Chat(wrap_user_name('filehelper'), self)

        self.self = Chat(self.core.loginInfo['User'], self)
        self.self.bot = self

        self.cache_path = cache_path

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

    def dump_login_status(self, cache_path=None):
        return self.core.dump_login_status(cache_path or self.cache_path)

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

    def _retrieve_itchat_storage(self, attr):
        with self.core.storageClass.updateLock:
            return getattr(self.core.storageClass, attr)

    @handle_response(Friend)
    def friends(self, update=False):
        """
        获取所有好友

        :param update: 是否更新
        :return: 聊天对象合集
        """

        if update:
            return self.core.get_friends(update=update)
        else:
            return self._retrieve_itchat_storage('memberList')

    @handle_response(Group)
    def groups(self, update=False, contact_only=False):
        """
        获取所有群聊

        :param update: 是否更新
        :param contact_only: 是否限于保存为联系人的群聊
        :return: 群聊合集
        """

        # itchat 原代码有些难懂，似乎 itchat 中的 get_contact() 所获取的内容视其 update 参数而变化
        # 如果 update=False 获取所有类型的本地聊天对象
        # 反之如果 update=True，变为获取收藏的聊天室

        if update or contact_only:
            return self.core.get_chatrooms(update=update, contactOnly=contact_only)
        else:
            return self._retrieve_itchat_storage('chatroomList')

    @handle_response(MP)
    def mps(self, update=False):
        """
        获取所有公众号

        :param update: 是否更新
        :return: 聊天对象合集
        """

        if update:
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
        """

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
            return Group(self.core.update_chatroom(userName=user_name), self)
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
                            toUserName=msg.sender.user_name,
                            mediaId=ret[1]
                        )
                    else:
                        self.core.send(
                            msg=str(ret),
                            toUserName=msg.sender.user_name
                        )
            except:
                logger.exception('\nAn error occurred in {}.'.format(func))

        if run_async:
            Thread(target=process).start()
        else:
            process()

    def register(
            self, senders=None, msg_types=None,
            except_self=True, run_async=True, enabled=True
    ):
        """
        装饰器：用于注册消息配置

        :param senders: 单个或列表形式的多个聊天对象或聊天类型，为空时匹配所有聊天对象
        :param msg_types: 单个或列表形式的多个消息类型，为空时匹配所有消息类型 (SYSTEM 类消息除外)
        :param except_self: 排除自己在手机上发送的消息
        :param run_async: 异步执行配置的函数，可提高响应速度
        :param enabled: 当前配置的默认开启状态，可事后动态开启或关闭
        """

        def register(func):
            self.message_configs.append(MessageConfig(
                bot=self, func=func, senders=senders, msg_types=msg_types,
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
