class TestGroups:
    def test_search(self, bot, group, member, friend):
        found = bot.groups().search('wxpy test', users=[bot.self, member, friend])
        assert group in found
