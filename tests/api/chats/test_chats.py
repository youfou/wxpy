from collections import Counter

from wxpy import *


class TestChats:
    def test_search(self, group, friend):
        found = group.search('wxpy 机器人')
        assert friend in found
        assert isinstance(found, Chats)

    def test_stats(self, group):
        stats = group.members.stats()
        assert isinstance(stats, dict)
        for attr in 'province', 'city', 'sex':
            assert attr in stats
            assert isinstance(stats[attr], Counter)

    def test_stats_text(self, group):
        text = group.members.stats_text()
        assert '位群成员' in text
