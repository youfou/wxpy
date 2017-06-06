from datetime import datetime

from tests.conftest import wait_for_message
from wxpy import *


def sent_message(sent_msg, msg_type, receiver):
    assert isinstance(sent_msg, SentMessage)
    assert sent_msg.type == msg_type
    assert sent_msg.receiver == receiver
    assert sent_msg.bot == receiver.bot
    assert sent_msg.sender == receiver.bot.self
    assert isinstance(sent_msg.receive_time, datetime)
    assert isinstance(sent_msg.create_time, datetime)
    assert sent_msg.create_time < sent_msg.receive_time


class TestMessage:
    def test_text_message(self, group, friend):
        sent_message(group.send('text'), TEXT, group)
        msg = wait_for_message(group, TEXT)
        assert isinstance(msg, Message)
        assert msg.type == TEXT
        assert msg.text == 'Hello!'
        assert not msg.is_at
        assert msg.chat == group
        assert msg.sender == group
        assert msg.receiver == group.self
        assert msg.member == friend
        assert 0 < msg.latency < 30

        group.send('at')
        msg = wait_for_message(group, TEXT)
        assert msg.is_at

    def test_picture_message(self, group, image_path):
        sent = group.send_image(image_path)
        sent_message(sent, PICTURE, group)
        assert sent.path == image_path

    def test_video_message(self, group, video_path):
        sent = group.send_video(video_path)
        sent_message(sent, VIDEO, group)
        assert sent.path == video_path

    def test_raw_message(self, group):
        # 发送名片
        raw_type = 42
        raw_content = '<msg username="{}" nickname="{}"/>'.format('wxpy_bot', 'wxpy 机器人')
        sent_message(group.send_raw_msg(raw_type, raw_content), None, group)

    def test_send(self, friend, file_path, image_path, video_path):
        text_to_send = 'test sending text'
        sent = friend.send(text_to_send)
        sent_message(sent, TEXT, friend)
        assert sent.text == text_to_send

        sent = friend.send('@fil@{}'.format(file_path))
        sent_message(sent, ATTACHMENT, friend)
        assert sent.path == file_path

        sent = friend.send('@img@{}'.format(image_path))
        sent_message(sent, PICTURE, friend)
        assert sent.path == image_path

        sent = friend.send('@vid@{}'.format(video_path))
        sent_message(sent, VIDEO, friend)
        assert sent.path == video_path

        # 发送名片
        raw_type = 42
        raw_content = '<msg username="{}" nickname="{}"/>'.format('wxpy_bot', 'wxpy 机器人')
        uri = '/webwxsendmsg'
        sent = friend.send_raw_msg(raw_type, raw_content)
        sent_message(sent, None, friend)

        assert sent.type is None
        assert sent.raw_type == raw_type
        assert sent.raw_content == raw_content
        assert sent.uri == uri
