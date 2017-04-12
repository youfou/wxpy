import inspect
import re
import weakref
from functools import wraps

from requests.adapters import HTTPAdapter

from wxpy.exceptions import ResponseError


def check_response_body(response_body):
    """
    检查 response body: ret_code 不为 0 时抛出 :class:`ResponseError` 异常

    :param response_body: response body
    """

    try:
        base_response = response_body['BaseResponse']
        ret = base_response['Ret']
        err_msg = base_response['ErrMsg']
    except KeyError:
        pass
    else:
        if ret != 0:
            raise ResponseError('ret: {}; err_msg: {}'.format(ret, err_msg))


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

            if ret is None:
                return

            if args:
                self = args[0]
            else:
                self = inspect.currentframe().f_back.f_locals.get('self')

            from wxpy.api.bot import Bot
            if isinstance(self, Bot):
                bot = weakref.proxy(self)
            else:
                bot = getattr(self, 'bot', None)
                if not bot:
                    raise ValueError('bot not found:m\nmethod: {}\nself: {}\nbot: {}'.format(
                        func, self, bot
                    ))

            smart_map(check_response_body, ret)

            if to_class:
                ret = smart_map(to_class, ret, bot)

            if isinstance(ret, list):
                from wxpy.api.chats import Group
                if to_class is Group:
                    from wxpy.api.chats import Groups
                    ret = Groups(ret)
                elif to_class:
                    from wxpy.api.chats import Chats
                    ret = Chats(ret, bot)

            return ret

        return wrapped

    return decorator


def ensure_list(x, except_false=True):
    """
    若传入的对象不为列表，则转化为列表

    :param x: 输入对象
    :param except_false: None, False 等例外，会直接返回原值
    :return: 列表，或 None, False 等
    :rtype: list
    """

    if isinstance(x, (list, tuple)) or (not x and except_false):
        return x
    return [x]


def prepare_keywords(keywords):
    """
    准备关键词
    """

    if not keywords:
        keywords = ''
    if isinstance(keywords, str):
        keywords = re.split(r'\s+', keywords)
    return map(lambda x: x.lower(), keywords)


def match_text(text, keywords):
    """
    判断文本内容中是否包含了所有的关键词 (不区分大小写)

    :param text: 文本内容
    :param keywords: 关键词，可以是空白分割的 str，或是多个精准关键词组成的 list
    :return: 若包含了所有的关键词则为 True，否则为 False
    """

    if not text:
        text = ''
    else:
        text = text.lower()

    keywords = prepare_keywords(keywords)

    for kw in keywords:
        if kw not in text:
            return False
    return True


def match_attributes(obj, **attributes):
    """
    判断对象是否匹配输入的属性条件

    :param obj: 对象
    :param attributes: 属性键值对
    :return: 若匹配则为 True，否则为 False
    """

    has_raw = hasattr(obj, 'raw')

    for attr, value in attributes.items():
        if (getattr(obj, attr, None) or (obj.raw.get(attr) if has_raw else None)) != value:
            return False
    return True


def match_name(chat, keywords):
    """
    判断一个 Chat 对象的名称是否包含了所有的关键词 (不区分大小写)

    :param chat: Chat 对象
    :param keywords: 关键词，可以是空白分割的 str，或是多个精准关键词组成的 list
    :return: 若包含了所有的关键词则为 True，否则为 False
    """

    keywords = prepare_keywords(keywords)

    for kw in keywords:
        for attr in 'remark_name', 'display_name', 'nick_name', 'wxid':
            if kw in str(getattr(chat, attr, '')).lower():
                break
        else:
            return False
    return True


def smart_map(func, i, *args, **kwargs):
    """
    将单个对象或列表中的每个项传入给定的函数，并返回单个结果或列表结果，类似于 map 函数

    :param func: 传入到的函数
    :param i: 列表或单个对象
    :param args: func 函数所需的 args
    :param kwargs: func 函数所需的 kwargs
    :return: 若传入的为列表，则以列表返回每个结果，反之为单个结果
    """
    if isinstance(i, (list, tuple, set)):
        return list(map(lambda x: func(x, *args, **kwargs), i))
    else:
        return func(i, *args, **kwargs)


def wrap_user_name(user_or_users):
    """
    确保将用户转化为带有 UserName 键的用户字典

    :param user_or_users: 单个用户，或列表形式的多个用户
    :return: 单个用户字典，或列表形式的多个用户字典
    """

    from wxpy.api.chats import Chat

    def wrap_one(x):
        if isinstance(x, dict):
            return x
        elif isinstance(x, Chat):
            return x.raw
        elif isinstance(x, str):
            return {'UserName': user_or_users}
        else:
            raise TypeError('Unsupported type: {}'.format(type(x)))

    return smart_map(wrap_one, user_or_users)


def get_user_name(user_or_users):
    """
    确保将用户转化为 user_name 字串

    :param user_or_users: 单个用户，或列表形式的多个用户
    :return: 返回单个 user_name 字串，或列表形式的多个 user_name 字串
    """

    from wxpy.api.chats import Chat

    def get_one(x):
        if isinstance(x, Chat):
            return x.user_name
        elif isinstance(x, dict):
            return x['UserName']
        elif isinstance(x, str):
            return x
        else:
            raise TypeError('Unsupported type: {}'.format(type(x)))

    return smart_map(get_one, user_or_users)


def get_receiver(receiver=None):
    """
    获得作为接收者的聊天对象

    :param receiver:
        * 当为 `None`, `True` 或字符串时，将以该值作为 `cache_path` 参数启动一个新的机器人，并返回该机器人的"文件传输助手"
        * 当为 :class:`机器人 <Bot>` 时，将返回该机器人的"文件传输助手"
        * 当为 :class:`聊天对象 <Chat>` 时，将返回该聊天对象
    :return: 作为接收者的聊天对象
    :rtype: :class:`wxpy.Chat`
    """

    from wxpy.api.chats import Chat
    from wxpy.api.bot import Bot

    if isinstance(receiver, Chat):
        return receiver
    elif isinstance(receiver, Bot):
        return receiver.file_helper
    elif receiver in (None, True) or isinstance(receiver, str):
        return Bot(cache_path=receiver).file_helper
    else:
        raise TypeError('expected Chat, Bot, str, True or None')


def enhance_connection(session, pool_connections=30, pool_maxsize=30, max_retries=30):
    """
    增强 requests.Session 对象的网络连接性能

    :param session: 需增强的 requests.Session 对象
    :param pool_connections: 最大的连接池缓存数量
    :param pool_maxsize: 连接池中的最大连接保存数量
    :param max_retries: 最大的连接重试次数 (仅处理 DNS 查询, socket 连接，以及连接超时)
    """

    for p in 'http', 'https':
        session.mount(
            '{}://'.format(p),
            HTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                max_retries=max_retries,
            ))


def get_text_without_at_bot(msg):
    """
    获得 Message 对象中的消息内容，并清理 @ 机器人的部分

    :param msg: Message 对象
    :return: 清理 @ 机器人部分后的文本内容
    :rtype: str
    """

    from wxpy.api.chats import Group

    text = msg.text

    if isinstance(msg.chat, Group):
        name = msg.chat.self.name
        text = re.sub(r'\s*@' + re.escape(name) + r'\u2005?\s*', '', text)

    return text
