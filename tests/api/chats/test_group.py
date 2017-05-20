import pytest

from wxpy import *


class TestGroup:
    def test_group_attributes(self, group, friend, member):
        isinstance(group.members, Chats)
        assert friend in group
        assert member in group
        assert group.self == group.bot.self
        assert group.self in group
        assert not group.is_owner
        assert group.owner == friend

    def test_update_group(self, group):
        group.update_group(members_details=True)
        assert group.members[-1].sex is not None

    def test_add_members(self, group, member):
        try:
            group.add_members(member)
        except ResponseError as e:
            if e.err_code != 1205:
                raise e

    def test_remove_members(self, member):
        with pytest.raises(ResponseError) as e:
            member.remove()
            assert e.err_code == -66

    def test_rename_group(self, group):
        current_name = group.name
        new_name = '__test_123_group__'

        for name in new_name, current_name:
            group.rename_group(name)
