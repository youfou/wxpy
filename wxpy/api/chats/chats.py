import logging
import time
from collections import Counter

from wxpy.utils import match_attributes, match_name

logger = logging.getLogger(__name__)


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
        :rtype: :class:`wxpy.Chats`
        """

        def match(chat):

            if not match_name(chat, name):
                return
            if not match_attributes(chat, **attributes):
                return
            return True

        return Chats(filter(match, self), self.source)

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
        from .user import FEMALE, MALE
        from wxpy.api.bot import Bot

        def top_n_text(attr, n):
            top_n = list(filter(lambda x: x[0], stats[attr].most_common()))[:n]
            top_n = ['{}: {} ({:.2%})'.format(k, v, v / len(self)) for k, v in top_n]
            return '\n'.join(top_n)

        stats = self.stats()

        text = str()

        if total:
            if self.source:
                if isinstance(self.source, Bot):
                    user_title = '微信好友'
                    nick_name = self.source.self.nick_name
                elif isinstance(self.source, Group):
                    user_title = '群成员'
                    nick_name = self.source.nick_name
                else:
                    raise TypeError('source should be Bot or Group')
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

    def add_all(self, interval=3, verify_content=''):
        """
        将合集中的所有用户加为好友，请小心应对调用频率限制！

        :param interval: 间隔时间(秒)
        :param verify_content: 验证说明文本
        """
        to_add = self[:]

        while to_add:
            adding = to_add.pop(0)
            logger.info('Adding {}'.format(adding))
            ret = adding.add(verify_content=verify_content)
            logger.info(ret)
            logger.info('Waiting for {} seconds'.format(interval))
            if to_add:
                time.sleep(interval)
