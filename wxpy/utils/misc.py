# coding: utf-8
from __future__ import unicode_literals

import inspect
import logging
import re
import threading
import time

from requests.adapters import HTTPAdapter

from wxpy.compatible import PY2

if PY2:
    from future.builtins import str
    # noinspection PyUnresolvedReferences
    import HTMLParser
else:
    import html


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
        # noinspection PyTypeChecker
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

    for attr, value in attributes.items():
        if getattr(obj, attr, None) != value:
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
        for attr in 'remark_name', 'display_name', 'nickname', 'wxid':
            if kw in '{0}'.format(getattr(chat, attr, '')).lower():
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


def get_raw_dict(chat_or_chats):
    """
    确保将用户转化为带有 UserName 键的用户字典

    :param chat_or_chats: 单个用户，或列表形式的多个用户
    :return: 单个用户字典，或列表形式的多个用户字典
    """

    from wxpy.api.chats import Chat

    def wrap_one(x):
        if isinstance(x, dict):
            return x
        elif isinstance(x, Chat):
            return x.raw
        elif isinstance(x, str):
            return {'UserName': chat_or_chats}
        else:
            if PY2:
                # noinspection PyUnresolvedReferences
                if isinstance(x, unicode):
                    return {'UserName': chat_or_chats}
            raise TypeError('unsupported type: {}'.format(type(x)))

    return smart_map(wrap_one, chat_or_chats)


def get_username(chat_or_chats):
    """
    确保将用户转化为 username 字串

    :param chat_or_chats: 单个用户，或列表形式的多个用户
    :return: 返回单个 username 字串，或列表形式的多个 username 字串
    """

    from wxpy.api.chats import Chat
    from wxpy.api.bot import Bot
    from wxpy.api.core import Core

    def get_one(x):
        if isinstance(x, (Chat, Bot, Core)):
            return x.username
        elif isinstance(x, dict):
            return x['UserName']
        elif isinstance(x, str):
            return x
        else:
            if PY2:
                # noinspection PyUnresolvedReferences
                if isinstance(x, unicode):
                    return x
            raise TypeError('Unsupported type: {}'.format(type(x)))

    return smart_map(get_one, chat_or_chats)


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
                pool_block=False
            ))


def repr_message(msg):
    """
    用于 Message 和 SentMessage 对象的 __repr__ 和 __unicode__
    """

    from wxpy.api.chats import Group

    text = (str(msg.text or '')).replace('\n', ' ↩ ')
    text += ' ' if text else ''

    if msg.sender == msg.core.self:
        ret = '↪ {self.receiver.name}'
    elif isinstance(msg.chat, Group) and msg.member and msg.member != msg.receiver:
        ret = '{self.sender.name} >> {self.member.name}'
    else:
        ret = '{self.sender.name}'

    ret += ' : {text}({self.type})'

    return ret.format(self=msg, text=text)


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


def start_new_thread(target, args=(), kwargs=None, daemon=True, use_caller_name=False):
    """
    启动一个新的进程，需要时自动为进程命名，并返回这个线程
    
    :param target: 调用目标
    :param args: 调用位置参数
    :param kwargs: 调用命名参数
    :param daemon: 作为守护进程
    :param use_caller_name: 为 True 则以调用者为名称，否则以目标为名称

    :return: 新的进程
    :rtype: threading.Thread
    """

    if use_caller_name:
        # 使用调用者的名称
        name = inspect.stack()[1][3]
    else:
        name = target.__name__

    logging.getLogger(
        # 使用外层的 logger
        inspect.currentframe().f_back.f_globals.get('__name__')
    ).debug('new thread: {}'.format(name))
    if PY2:
        _thread = threading.Thread(
            target=target, args=args, kwargs=kwargs,
            name=name)
        _thread.setDaemon(daemon)
    else:
        _thread = threading.Thread(
            target=target, args=args, kwargs=kwargs,
            name=name, daemon=daemon
        )
    _thread.start()

    return _thread


rp_emoji_span = re.compile(r'<span class="emoji emoji([\da-fA-F]+)"></span>?')

# 参考: https://en.wikipedia.org/wiki/Emoji#Unicode_blocks
rp_emoji_code_point = re.compile(r'1f[\da-f]{3}|[2-3][\da-f]{3}|a9|ae')

# Web 微信中的 emoji 是通过预先准备好的图片来渲染的 (为了不同平台中的 emoji 风格统一)
# 然而在这个特殊的渲染方式中，有一部分 emoji 存在错误的匹配
# 所以当需要需要输出 emoji 字符 (而不是图片) 时，需要使用一个映射表来修正
# 这个映射表需要从上面说的 Web 微信预先准备好的图片中去提取，显然这不现实…
# 下面的映射表 `emoji_mismatch_map`，是从 itchat 的代码中复制的，感谢维护者们的付出! 我要羞羞的抄作业了...
# https://github.com/littlecodersh/ItChat/blob/86a3fefc257800092d040f2f7849e781785fafe1/itchat/utils.py#L47
emoji_mismatch_map = {
    '1f63c': '1f601', '1f639': '1f602', '1f63a': '1f603',
    '1f4ab': '1f616', '1f64d': '1f614', '1f63b': '1f60d',
    '1f63d': '1f618', '1f64e': '1f621', '1f63f': '1f622',
}


def emoji_replace_hook(match):
    code = match.group(1)
    if code in emoji_mismatch_map:
        code = emoji_mismatch_map[code]

    emoji = ''
    for cp in rp_emoji_code_point.findall(code):
        emoji += '\\U{:0>8}'.format(cp).encode('utf-8').decode('unicode-escape', 'replace')
    return emoji


def decode_webwx_emoji(text):
    """ 将文本中的 <span/> 标签还原为 emoji """
    return rp_emoji_span.sub(emoji_replace_hook, text)


def decode_webwx_json_values(dct):
    """ 解码 Web 微信返回的 JSON 中的 values """

    for k, v in dct.items():
        if isinstance(v, str):
            v = v.replace('<br/>', '\n')
            v = decode_webwx_emoji(v)
            if PY2:
                # 3.0 < version < 3.3 使用 html.parser.HTMLParser().unescape
                # https://stackoverflow.com/questions/2360598/how-do-i-unescape-html-entities-in-a-string-in-python-3-1
                v = HTMLParser.HTMLParser().unescape(v)
            else:
                v = html.unescape(v)
            dct[k] = v

    return dct


def get_chat_type(raw_dict):
    """ 区分原始聊天对象字典的所属类型，返回聊天对象类 """
    from wxpy.api.chats import Friend, Group, Member, Service, Subscription

    if raw_dict['UserName'].startswith('@@'):
        return Group
    elif raw_dict['VerifyFlag'] >= 24:
        return Service
    elif raw_dict['VerifyFlag'] >= 8:
        return Subscription
    elif raw_dict.get('EncryChatRoomId') or 'MemberStatus' in raw_dict:
        return Member
    else:
        return Friend


def diff_usernames(old_chats, new_chats):
    """
    比较两个聊天对象列表或字典中的 username 的差异

    :param old_chats: 原来的聊天对象列表或字典
    :param new_chats: 新的聊天对象列表或字典
    :return: 一个元组: (old 中特有的, new 中特有的)
    """

    old, new = list(map(
        lambda x: set(map(
            get_username,
            x.keys() if isinstance(x, dict) else x
        )),
        (old_chats, new_chats),
    ))

    return list(old - new), list(new - old)


def chunks(whole, chunk_size):
    lst = ensure_list(whole)
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def new_local_msg_id():
    return str(int(time.time() * 1e7))
