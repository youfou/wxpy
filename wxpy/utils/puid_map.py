import atexit
import os
import pickle


def enable_puid(data_path='wxpy_puid.pkl'):
    """
    开启聊天对象的 puid 属性

    :param data_path: puid 映射数据的保存/载入路径
    """

    from wxpy import Chat
    puid_map = PuidMap(data_path)
    Chat._puid_map = puid_map
    return puid_map


def _update_fixed_len_list(self, other):
    for i, b in enumerate(other):
        if b and self[i] != b:
            self[i] = b


class PuidMap(object):
    def __init__(self, data_path):
        """
        用于获取聊天对象的 puid (持续有效，并且始终唯一的用户ID)，和保存映射关系
        
        :param data_path: 映射数据的保存/载入路径
        """
        self.data_path = data_path
        self._data = dict()

        if os.path.exists(self.data_path):
            self.load()

        atexit.register(self.dump)

    def get_puid(self, chat):
        """
        获取指定聊天对象的 puid

        :param chat: 指定的聊天对象
        :return: puid
        :rtype: str
        """

        chat_value = PuidValue(chat)

        if not (chat_value.wxid or chat_value.remark_name or any(chat_value.caption)):
            # 除了 user_name 其他所有属性均为空的聊天对象
            return

        for known_puid, known_value in self._data.items():
            if known_value == chat_value:
                self._data[known_puid].update(chat_value)
                return known_puid

        new_puid = chat.user_name[-8:]
        self._data[new_puid] = chat_value
        return new_puid

    def dump(self):
        """
        保存映射数据
        """
        with open(self.data_path, 'wb') as fp:
            pickle.dump(self._data, fp)

    def load(self):
        """
        载入映射数据
        """
        with open(self.data_path, 'rb') as fp:
            self._data = pickle.load(fp)

    def _new_map(self, chat):
        """
        puid: user_name, wxid, remark_name, mutable
        """
        puid = chat.user_name[-32:]
        self._data[puid] = PuidValue(chat)
        return puid


class PuidValue(list):
    def __init__(self, chat):
        """
        PuidMap._data {key: value} 中的 value 部分
        
        包括:
        * user_name
        * wxid
        * remark_name
        * caption (昵称、性别、省份、城市)
        
        :param chat: 用于初始化的聊天对象
        """

        super(PuidValue, self).__init__([
            chat.user_name,
            chat.wxid or None,
            getattr(chat, 'remark_name', None) or None,
            ChatCaption(chat),
        ])

    @property
    def user_name(self):
        return self[0]

    @property
    def wxid(self):
        return self[1]

    @property
    def remark_name(self):
        return self[2]

    @property
    def caption(self):
        return self[3]

    def __setitem__(self, key, value):
        if key == 3 and self[3] == value:
            # caption 只有当匹配时才进行补全，否则整个替换
            self[3].update(value)
        else:
            super(PuidValue, self).__setitem__(key, value)

    def __eq__(self, other):
        for i, a in enumerate(self):
            # 按优先顺序遍历各属性，有匹配则为相等 (其中 caption 的匹配比较特殊)
            b = other[i]
            if a and b and a == b:
                return True

        return False

    update = _update_fixed_len_list


class ChatCaption(list):
    def __init__(self, chat):
        """
        聊天对象的 昵称、性别、省份、城市
        """
        super(ChatCaption, self).__init__([
            getattr(chat, attr, None) or None for attr in (
                'nick_name', 'sex', 'province', 'city')
        ])

    def __eq__(self, other):
        # 这些属性的匹配原则是：可以有属性缺失，但不可有任何冲突，否则为无效
        if self[0]:
            match = 0
            for i, a in enumerate(self):
                b = other[i]
                if a and b:
                    if a == b:
                        match += 1
                    else:
                        return False
            return match

    update = _update_fixed_len_list
