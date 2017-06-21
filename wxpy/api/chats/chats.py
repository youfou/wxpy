# coding: utf-8
from __future__ import unicode_literals

import logging
from collections import Counter

from wxpy.compatible import *
from wxpy.utils import match_attributes, match_name, ensure_one

logger = logging.getLogger(__name__)


class Chats(list):
    """
    多个聊天对象的列表，可用于搜索、更新、统计等功能
    """

    def __init__(self, chat_list=None, source=None):
        if chat_list:
            super(Chats, self).__init__(chat_list)
        self.source = source

    def __add__(self, other):
        return Chats(
            super(Chats, self).__add__(other or list()),
            self.source if self.source == getattr(other, 'source', None) else None
        )

    def _iter_match(self, keywords=None, **attributes):
        def match(_chat):

            if not match_name(_chat, keywords):
                return
            if not match_attributes(_chat, **attributes):
                return
            return True

        for chat in self:
            if match(chat):
                yield chat

    def get(self, keywords=None, **attributes):

        """
        | 找到匹配所设条件的唯一聊天对象
        | 若结果不唯一，或没有找到，会抛出 `ValueError` 异常

        :param keywords:

            | 聊天对象的名称关键词 (空格分隔, 不区分大小写)
            | 用于在 remark_name, display_name, nickname, wxid 中进行搜索

        :param attributes:

            属性键值对，键可以是 sex(性别), province(省份), city(城市) 等，例如::

                bot.chats.get(nickname='游否', city='深圳', sex=MALE)

        :rtype: :class:`Chat`
        """

        found = list(self._iter_match(keywords, **attributes))
        return ensure_one(found)

    def find(self, keywords=None, **attributes):
        """
        | 类似于 any:`Chats.get`，不同之处在于仅返回 **首个匹配的** 聊天对象
        | 也就是说: 即便列表内有多个匹配，也不会抛出异常; 若没有匹配的，则返回 None

        :rtype: :class:`Chat`
        """

        for chat in self._iter_match(keywords, **attributes):
            return chat

    def search(self, keywords=None, **attributes):
        """
        类似于 any:`Chats.get`，不同之处在于会返回 **所有匹配的** 聊天对象

        :rtype: :class:`Chats`
        """

        return Chats(self._iter_match(keywords, **attributes), self.source)

    def update(self):
        """
        更新列表中的所有聊天对象
        """

        cores = dict()
        for chat in self:
            cores.setdefault(chat.core, list()).append(chat)
        for core in cores:
            core.batch_get_contact(cores[core])

    def stats(self, attribs=('sex', 'province', 'city')):
        """
        统计各属性的分布情况

        :param attribs: 需统计的属性列表或元组
        :return: 统计结果
        """

        def attr_stat(objects, attr_name):
            return Counter(list(map(lambda x: getattr(x, attr_name), objects)))

        from wxpy.utils import ensure_list
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

        from .group import Group
        from wxpy.api.consts import FEMALE
        from wxpy.api.consts import MALE
        from wxpy.api.core import Core

        def top_n_text(attr, n):
            top_n = list(filter(lambda x: x[0], stats[attr].most_common()))[:n]
            top_n = ['{}: {} ({:.2%})'.format(k, v, v / len(self)) for k, v in top_n]
            return '\n'.join(top_n)

        stats = self.stats()

        text = str()

        if total:
            if self.source:
                if isinstance(self.source, Core):
                    user_title = '微信好友'
                    nickname = self.source.name
                elif isinstance(self.source, Group):
                    user_title = '群成员'
                    nickname = self.source.nickname
                else:
                    raise TypeError('source should be Bot or Group')
                text += '{nickname} 共有 {total} 位{user_title}\n\n'.format(
                    nickname=nickname,
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
