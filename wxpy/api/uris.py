# coding: utf-8
from __future__ import unicode_literals

import time
from ctypes import c_int32
from wxpy.compatible import PY2

if PY2:
    from urllib import quote
    from urlparse import urlparse, urljoin
else:
    from urllib.parse import quote, urljoin, urlparse

# 以下大部分值来自
# https://res.wx.qq.com/a/wx_fed/webwx/res/static/js/index_4a48aef.js


class URIS(object):
    HOST_CASES = (
        # 可以通过正则替换从 JS 中获取
        # 查找: .+?(?<=t\.indexOf\(")(.+?)(?=").+?(?<=a = ")(.+?)(?=").+?(?<=n = ")(.+?)(?=").+?(?<=i = ")(.+?)(?=").+?
        # 替换为: ('$1', '$2', '$3', '$4'),\n
        ('wx2.qq.com', 'login.wx2.qq.com', 'file.wx2.qq.com', 'webpush.wx2.qq.com'),
        ('wx8.qq.com', 'login.wx8.qq.com', 'file.wx8.qq.com', 'webpush.wx8.qq.com'),
        ('qq.com', 'login.wx.qq.com', 'file.wx.qq.com', 'webpush.wx.qq.com'),
        ('web2.wechat.com', 'login.web2.wechat.com', 'file.web2.wechat.com', 'webpush.web2.wechat.com'),
        ('wechat.com', 'login.web.wechat.com', 'file.web.wechat.com', 'webpush.web.wechat.com'),
    )

    START_PAGE = 'https://wx.qq.com/'
    QR_DOWNLOAD = 'https://login.weixin.qq.com/qrcode/'
    QR_LOGIN = 'https://login.weixin.qq.com/l/'

    # noinspection SpellCheckingInspection
    def __init__(self, current_page=START_PAGE, language='zh_CN'):
        """
        初始化和提供 Web 微信中各接口所需的 URI
        :param current_page: Web 微信当前所处的页面 URL
        """

        self.current_page = current_page
        self.language = language

        self.host = urlparse(self.current_page).netloc
        self.path_prefix = '/cgi-bin/mmwebwx-bin'
        self.base = urljoin(self.current_page, self.path_prefix)

        a = 'login.weixin.qq.com'
        n = 'file.wx.qq.com'
        i = 'webpush.weixin.qq.com'

        for case in self.HOST_CASES:
            if case[0] in self.current_page:
                a, n, i = case[1:]
                break

        protocol = 'https://'

        self.js_login = protocol + a + '/jslogin?appid=wx782c26e4c19acffb&redirect_uri=' + quote(
            self.base + '/webwxnewloginpage') + '&fun=new&lang=' + self.language
        self.login = protocol + a + self.path_prefix + '/login'
        self.sync_check = protocol + i + self.path_prefix + '/synccheck'
        self.download_media = protocol + n + self.path_prefix + '/webwxgetmedia'
        self.upload_media = protocol + n + self.path_prefix + '/webwxuploadmedia'

        self.preview = self.base + '/webwxpreview'
        self.init = self.base + '/webwxinit?r={}'.format(self.ts_invert)
        self.get_contact = self.base + '/webwxgetcontact'
        self.sync = self.base + '/webwxsync'
        self.batch_get_contact = self.base + '/webwxbatchgetcontact'
        self.get_icon = self.base + '/webwxgeticon'
        self.send_msg = self.base + '/webwxsendmsg'
        self.send_msg_img = self.base + '/webwxsendmsgimg'
        self.send_video_msg = self.base + '/webwxsendvideomsg'
        self.send_emoticon = self.base + '/webwxsendemoticon'
        self.send_app_msg = self.base + '/webwxsendappmsg'
        self.get_head_img = self.base + '/webwxgetheadimg'
        self.get_msg_img = self.base + '/webwxgetmsgimg'
        self.get_media = self.base + '/webwxgetmedia'
        self.get_video = self.base + '/webwxgetvideo'
        self.logout = self.base + '/webwxlogout'
        self.get_voice = self.base + '/webwxgetvoice'
        self.update_chatroom = self.base + '/webwxupdatechatroom'
        self.create_chatroom = self.base + '/webwxcreatechatroom'
        self.status_notify = self.base + '/webwxstatusnotify'
        self.check_url = self.base + '/webwxcheckurl'
        self.verify_user = self.base + '/webwxverifyuser'
        self.feedback = self.base + '/webwxsendfeedback'
        self.stat_report = self.base + '/webwxstatreport'
        self.search_contact = self.base + '/webwxsearchcontact'
        self.op_log = self.base + '/webwxoplog'
        self.check_upload = self.base + '/webwxcheckupload'
        self.revoke_msg = self.base + '/webwxrevokemsg'
        self.push_login_url = self.base + '/webwxpushloginurl'

        self._ts_add_up = int(time.time() * 1000)
        self._tip_called = False

        self.upload_media_count = 0

    @property
    def ts_now(self):
        return int(time.time() * 1000)

    @property
    def ts_invert(self):
        # 模拟 JavaScript 中的 `~new Date`
        return ~ c_int32(int(time.time() * 1000)).value

    @property
    def ts_add_up(self):
        self._ts_add_up += 1
        return self._ts_add_up

    @property
    def tip(self):
        if self._tip_called:
            return 0
        else:
            self._tip_called = True
            return 1


if __name__ == '__main__':
    uris = URIS()
    print(uris.ts_invert)
