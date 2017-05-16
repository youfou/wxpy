from datetime import datetime

from wxpy import *

text_to_send = 'testing'


class TestChat:
    def test_send(self, friend, file_path, image_path, video_path):
        sent_list = list()

        sent = friend.send(text_to_send)
        sent_list.append(sent)
        assert sent.type == TEXT
        assert sent.text == text_to_send

        sent = friend.send('@fil@{}'.format(file_path))
        sent_list.append(sent)
        assert sent.type == ATTACHMENT
        assert sent.path == file_path

        sent = friend.send('@img@{}'.format(image_path))
        sent_list.append(sent)
        assert sent.type == PICTURE
        assert sent.path == image_path

        sent = friend.send('@vid@{}'.format(video_path))
        sent_list.append(sent)
        assert sent.type == VIDEO
        assert sent.path == video_path

        # 发送名片
        raw_type = 42
        raw_content = '<msg username="{}" nickname="{}"/>'.format('wxpy_bot', 'wxpy 机器人')
        uri = '/webwxsendmsg'
        sent = friend.send_raw_msg(raw_type, raw_content)
        sent_list.append(sent)

        assert sent.type is None
        assert sent.raw_type == raw_type
        assert sent.raw_content == raw_content
        assert sent.uri == uri

        for sent in sent_list:
            assert isinstance(sent, SentMessage)
            assert sent.receiver == friend
            assert sent.chat == friend
            assert sent.bot == friend.bot
            assert sent.sender == friend.bot.self
            assert isinstance(sent.receive_time, datetime)
            assert isinstance(sent.create_time, datetime)
            assert sent.create_time < sent.receive_time

        sent_list[0].recall()

    def test_pin_unpin(self, friend):
        friend.pin()
        friend.unpin()
