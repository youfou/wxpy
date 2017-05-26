# coding: utf-8
from __future__ import unicode_literals

import atexit
import os
import pickle

import threading
from wxpy.compatible import PY2
if PY2:
    from UserDict import UserDict
else:
    from collections import UserDict

"""

# puid

尝试用聊天对象已知的属性，来查找对应的持久固定并且唯一的 用户 id


## 数据结构

PuidMap 中包含 4 个 dict，分别为

1. user_name -> puid
2. wxid -> puid
3. remark_name -> puid
4. caption (昵称, 性别, 省份, 城市) -> puid


## 查询逻辑

当给定一个 Chat 对象，需要获取对应的 puid 时，将按顺序，使用自己的对应属性，轮询以上 4 个 dict

* 若匹配任何一个，则获取到 puid，并将其他属性更新到其他的 dict
* 如果没有一个匹配，则创建一个新的 puid，并加入到以上的 4 个 dict


"""


class PuidMap(object):
    def __init__(self, path):
        """
        用于获取聊天对象的 puid (持续有效，并且稳定唯一的用户ID)，和保存映射关系

        :param path: 映射数据的保存/载入路径
        """
        self.path = path

        self.user_names = TwoWayDict()
        self.wxids = TwoWayDict()
        self.remark_names = TwoWayDict()

        self.captions = TwoWayDict()

        self._thread_lock = threading.Lock()

        if os.path.exists(self.path):
            self.load()

        atexit.register(self.dump)

    @property
    def attr_dicts(self):
        return self.user_names, self.wxids, self.remark_names

    def __len__(self):
        return len(self.user_names)

    def __bool__(self):
        return bool(self.path)

    def __nonzero__(self):
        return bool(self.path)

    def get_puid(self, chat):
        """
        获取指定聊天对象的 puid

        :param chat: 指定的聊天对象
        :return: puid
        :rtype: str
        """

        with self._thread_lock:

            if not (chat.user_name and chat.nick_name):
                return

            chat_attrs = (
                chat.user_name,
                chat.wxid,
                getattr(chat, 'remark_name', None),
            )

            chat_caption = get_caption(chat)

            puid = None

            for i in range(3):
                puid = self.attr_dicts[i].get(chat_attrs[i])
                if puid:
                    break
            else:
                if PY2:
                    captions = self.captions.keys()
                else:
                    captions = self.captions
                for caption in captions:
                    if match_captions(caption, chat_caption):
                        puid = self.captions[caption]
                        break

            if puid:
                new_caption = merge_captions(self.captions.get_key(puid), chat_caption)
            else:
                puid = chat.user_name[-8:]
                new_caption = get_caption(chat)

            for i in range(3):
                chat_attr = chat_attrs[i]
                if chat_attr:
                    self.attr_dicts[i][chat_attr] = puid

            self.captions[new_caption] = puid

            return puid

    def dump(self):
        """
        保存映射数据
        """
        with open(self.path, 'wb') as fp:
            pickle.dump((self.user_names, self.wxids, self.remark_names, self.captions), fp)

    def load(self):
        """
        载入映射数据
        """
        with open(self.path, 'rb') as fp:
            self.user_names, self.wxids, self.remark_names, self.captions = pickle.load(fp)


class TwoWayDict(UserDict):
    """
    可双向查询，且 key, value 均为唯一的 dict
    限制: key, value 均须为不可变对象，且不支持 .update() 方法
    """

    def __init__(self):
        if PY2:
            UserDict.__init__(self)
        else:
            super(TwoWayDict, self).__init__()
        self._reversed = dict()

    def get_key(self, value):
        """
        通过 value 查找 key
        """
        return self._reversed.get(value)

    def del_value(self, value):
        """
        删除 value 及对应的 key
        """
        del self[self._reversed[value]]

    def __setitem__(self, key, value):
        if self.get(key) != value:
            if key in self:
                self.del_value(self[key])
            if value in self._reversed:
                del self[self.get_key(value)]
            self._reversed[value] = key
            if PY2:
                return UserDict.__setitem__(self, key, value)
            else:
                return super(TwoWayDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        del self._reversed[self[key]]
        if PY2:
            return UserDict.__delitem__(self, key)
        else:
            return super(TwoWayDict, self).__delitem__(key)

    def update(*args, **kwargs):
        raise NotImplementedError


def get_caption(chat):
    return (
        chat.nick_name,
        getattr(chat, 'sex', None),
        getattr(chat, 'province', None),
        getattr(chat, 'city', None),
    )


def match_captions(old, new):
    if new[0]:
        for i in range(4):
            if old[i] and new[i] and old[i] != new[i]:
                return False
        return True


def merge_captions(old, new):
    return tuple(new[i] or old[i] for i in range(4))
