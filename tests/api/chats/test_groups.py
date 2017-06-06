class TestGroups:
    def test_search(self, bot, group, member, friend):
        found = bot.groups().search(group.name, users=[bot.self, member, friend])
        assert group in found
