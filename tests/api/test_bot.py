import logging
import os
import time

from wxpy import *


class TestBot:
    def test_self(self, bot):
        assert bot.self.name is not None
        assert bot.self.name == bot.core.loginInfo['User']['NickName']

    def test_repr(self, bot):
        assert repr(bot) == '<Bot: {}>'.format(bot.self.name)

    def test_alive(self, bot):
        assert bot.alive

    def test_dump_login_status(self, bot):
        bot.dump_login_status()
        updated_at = os.path.getmtime(bot.cache_path)
        assert time.time() - updated_at < 1

    def test_enable_puid(self, bot, base_dir):
        from wxpy.utils.puid_map import PuidMap
        puid_path = os.path.join(base_dir, 'wxpy_bot_puid.pkl')
        puid_map = bot.enable_puid(puid_path)
        assert isinstance(puid_map, PuidMap)

    def test_chats(self, bot):
        chats = bot.chats()
        assert isinstance(chats, Chats)
        assert set(chats) == set(bot.friends() + bot.groups() + bot.mps())

    def test_friends(self, bot):
        friends = bot.friends()
        assert isinstance(friends, Chats)
        assert bot.self in friends
        for friend in friends:
            assert isinstance(friend, Friend)

    def test_groups(self, bot):
        groups = bot.groups()
        assert isinstance(groups, Groups)
        for group in groups:
            assert isinstance(group, Group)
            assert bot.self in group

    def test_mps(self, bot):
        mps = bot.mps()
        assert isinstance(mps, Chats)
        for mp in mps:
            assert isinstance(mp, MP)

    def test_search(self, bot):
        found_1 = bot.search(bot.self.name, sex=bot.self.sex or None)
        assert bot.self in found_1
        found_2 = bot.search(nick_name='__!#@$#%$__')
        assert not found_2

        for found in found_1, found_2:
            assert isinstance(found, Chats)
            assert found.source == bot

    def test_create_group(self, bot):
        users = bot.friends()[:3]
        topic = 'test creating group'
        try:
            new_group = bot.create_group(users, topic)
        except ResponseError as e:
            logging.warning('Failed to create group: {}'.format(e))
        except Exception as e:
            if 'Failed to create group:' in str(e):
                logging.warning(e)
            else:
                raise e
        else:
            assert new_group.name == topic
            assert new_group in bot.groups()
            assert set(users) == set(new_group.members)

            new_name = 'testing'
            new_group.rename_group(new_name)
            assert new_group.name == new_name

    def test_upload_file(self, bot, file_path, friend):
        media_id = bot.upload_file(file_path)
        friend.send_file(file_path, media_id=media_id)
