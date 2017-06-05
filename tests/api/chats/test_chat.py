class TestChat:
    def test_pin_unpin(self, friend):
        friend.pin()
        friend.unpin()
