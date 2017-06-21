# coding: utf-8
from __future__ import unicode_literals

import wxpy


class Data(object):
    version = wxpy.__version__

    def __init__(self):
        """
        :class:`Core` 中的所有状态相关的数据内容，方便转存和载入
        """

        self.cookies = None
        self.uris = None

        self.skey = None
        self.sync_key = None
        self.sync_check_key = None

        self.uin = None
        self.pass_ticket = None
        self.gray_scale = None
        self.invite_start_count = None

        self.raw_self = None
        self.raw_chats = dict()
        self.raw_members = dict()
