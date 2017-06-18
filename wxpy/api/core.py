# coding: utf-8
from __future__ import unicode_literals

import json
import logging
import os
import platform
import random
import re
import subprocess
from xml.etree import ElementTree as ETree

import pyqrcode
import requests

from wxpy import ResponseError
from wxpy.api.chats import Friend, Group
from wxpy.api.data import Data
from wxpy.api.uris import LANGUAGE, URIS
from wxpy.utils.misc import enhance_connection, get_user_name, smart_map, start_new_thread, test_chat_type

try:
    import queue
except ImportError:
    # noinspection PyUnresolvedReferences,PyPep8Naming
    import Queue as queue

logger = logging.getLogger(__name__)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'


# external data: cookies, uris,


class Core(object):
    def __init__(
            self, bot=None, cache_path=None, console_qr=None, qr_path=None, proxies=None, hooks=None):
        """
        class:`Bot` 的内核，负责

        1. 完成初始化和登陆过程
        2. 同步检查和数据同步
        3. 包装 self.urls 中的各原始接口，供 class:`Bot` 调用

        :param bot: 所属机器人的 `weakref.proxy`
        :param proxies: `requests 代理
            <http://docs.python-requests.org/en/master/user/advanced/#proxies>`_
        """

        self.bot = bot

        if cache_path is True:
            self.cache_path = 'wxpy.pkl'
        else:
            self.cache_path = cache_path

        self.console_qr = console_qr
        self.qr_path = qr_path or 'QR.jpg'

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.proxies = proxies or dict()
        self.session.hooks.update(response=self.session_response_hook)
        enhance_connection(self.session)

        self.msg_queue = queue.Queue()
        self.uris = URIS(self.get(URIS.start).url)

        self.alive = False
        self.uuid = None

        self.data = Data()

        if isinstance(hooks, dict):
            # 若要在新的函数中调用原方法，调用 class:`Core` 中的对应方法即可!
            # Todo: 考虑让 key 支持 [new_func, -1 | 0 | 1] 的形式，以便自动在前|NA|后调用原方法
            for method_name, new_func in hooks.items():
                setattr(self, method_name, new_func)

        self.login()

    def get(self, url, **kwargs):
        """ get 请求 """
        resp = self.session.get(url, **kwargs)
        return self.check_json_response(resp)

    def post(self, url, data_ext=None, **kwargs):
        """ post 请求 """
        data = {'BaseRequest': {
            "Uin": self.data.uin,
            "Sid": self.sid,
            "Skey": self.data.skey,
            "DeviceID": self.device_id,
        }}

        if data_ext:
            data.update(data_ext)

        resp = self.session.post(url, json=data, **kwargs)
        return self.check_json_response(resp)

    def download(self, url, save_path):
        """ 下载文件 """
        resp = self.session.get(url, stream=True)
        with open(save_path, 'wb') as fp:
            for chunk in resp.iter_content(chunk_size=128):
                fp.write(chunk)

    def check_json_response(self, resp):

        """
        | 尝试从 requests.Response 对象中解析 JSON 数据
        | 若解析到 JSON 数据，则进行基本处理和检查，并返回 JSON 数据
        | 反之返回原来的 Response 对象

        :param resp: class:`requests.Response` 对象
        """

        try:
            data = json.loads(resp.content.decode('utf-8', errors='replace'))
        except (json.JSONDecodeError, TypeError):
            return resp

        skey = data.get('SKey')
        if skey:
            self.data.skey = skey
        sync_key = data.get('SyncKey')
        if sync_key:
            self.data.sync_key = sync_key
        sync_check_key = data.get('SyncCheckKey')
        if sync_check_key:
            self.data.sync_check_key = sync_check_key

        if 'BaseResponse' in data:
            try:
                base_response = data['BaseResponse']
                err_code = base_response['Ret']
                err_msg = base_response['ErrMsg']
            except (KeyError, TypeError):
                pass
            else:
                if err_code != 0:
                    raise ResponseError(bot=self.bot, err_code=err_code, err_msg=err_msg)

        return data

    def from_cookies(self, name):
        """ 从 cookies 中获取值 """
        return self.session.cookies.get(name, domain='.' + self.uris.host)

    def get_push_login_uuid(self):
        """ 获取 push login 的 uuid """
        if self.data.uin:
            print('attempting to push login')
            return self.get(self.uris.push_login_url, params=dict(uin=self.data.uin)).json().get('uuid')

    def get_qrcode_uuid(self):
        """ 获取二维码的 uuid """
        print('getting uuid of qrcode')
        resp = self.get(self.uris.js_login)
        code, uuid = from_js(resp.text, 'window.QRLogin.code', 'window.QRLogin.uuid')
        if code == 200:
            return uuid

    def show_console_qr(self):
        qrcode = pyqrcode.create(self.uris.qr_login + self.uuid)
        if self.console_qr:
            print(qrcode.terminal(module_color='black', background='white', quiet_zone=1))
        else:
            print(qrcode.terminal(module_color='white', background='black', quiet_zone=1))

    def show_qrcode(self):
        """ 展示二维码 """

        print('scan qrcode to login')

        if self.console_qr is None:
            os_ = platform.system()
            # noinspection PyBroadException
            try:
                if os_ == 'Darwin':
                    subprocess.call(['open', self.qr_path])
                elif os_ == 'Linux':
                    subprocess.call(['xdg-open', self.qr_path])
                else:
                    # noinspection PyUnresolvedReferences
                    os.startfile(self.qr_path)
            except:
                logger.warning('failed to open qrcode, use console_qr instead')
            else:
                return

        self.show_console_qr()

    # noinspection PyMethodMayBeStatic
    def confirm_login(self):
        print('please confirm login on your phone')

    # noinspection PyMethodMayBeStatic
    def login_timeout(self):
        print('login timeout, reloading qrcode')

    def login(self):
        """ 登陆 """

        self.uuid = self.get_push_login_uuid()

        while True:
            if not self.uuid:
                self.uuid = self.get_qrcode_uuid()
                if not self.uuid:
                    raise ValueError('failed to get uuid')
                self.download(self.uris.qr_download + self.uuid, self.qr_path)
                self.show_qrcode()

            resp = self.get(self.uris.login, params=dict(
                loginicon=True, uuid=self.uuid, tip=0, r=self.uris.ts_invert, _=self.uris.ts_add_up))
            code = from_js(resp.text, 'window.code')

            if code == 200:
                redirect = from_js(resp.text, 'window.redirect_uri')
                resp = self.get(redirect)
                self.uris = URIS(resp.url)

                if os.path.isfile(self.qr_path):
                    os.remove(self.qr_path)

                tree = ETree.fromstring(resp.history[0].text)
                self.data.skey = tree.findtext('skey')
                self.data.uin = int(tree.findtext('wxuin'))
                self.data.pass_ticket = tree.findtext('pass_ticket')
                self.data.gray_scale = int(tree.findtext('isgrayscale'))

                self.init()
                print('logged in successfully')
                start_new_thread(self.sync_loop).join()
                break

            elif code == 201:
                self.confirm_login()
            elif code == 408:
                self.uuid = None
                self.login_timeout()

    def init(self):
        print('initializing')
        json_resp = self.post(self.uris.init)
        self.data.self = Friend(self.bot, json_resp['User'])
        self.process_chat_list(json_resp['ContactList'], 'add')
        self.status_notify(self.data.self, self.data.self, 3)
        self.get_contact()

    def get_contact(self):
        print('updating chats')
        seq = 0
        while True:
            resp_json = self.get(self.uris.get_contact, params=dict(
                r=self.uris.ts_now, seq=seq, pass_ticket=self.data.pass_ticket))
            self.process_chat_list(resp_json['MemberList'], 'add')
            seq = resp_json.get('Seq')
            if not seq:
                break

    def status_notify(self, sender, receiver, code):
        return self.post(
            self.uris.status_notify,
            params=dict(lang=LANGUAGE, pass_ticket=self.data.pass_ticket),
            data_ext={
                'Code': code,
                'FromUserName': get_user_name(sender),
                'ToUserName': get_user_name(receiver),
                'ClientMsgId': self.uris.ts_now,
            })

    def process_chat_list(self, raw_chat_list, action):
        """
        处理返回数据中的联系人字典列表

        :param raw_chat_list: 聊天对象字典列表
        :param action:
            指定当聊天对象已存在时的操作
                * 支持 'add', 'update', 'delete'
                * 分布表示 覆盖, 合并, 删除 三种操作
        """

        for raw_dict in raw_chat_list:
            chat_class = test_chat_type(raw_dict)

            if issubclass(chat_class, Friend):
                parent = self.data.friends
            elif issubclass(chat_class, Group):
                parent = self.data.groups
            else:
                parent = self.data.mps

            user_name = raw_dict['UserName']

            if user_name in parent:
                if action == 'add':
                    parent[user_name].raw = raw_dict
                elif action == 'update':
                    merge_chat_dict(parent[user_name].raw, raw_dict)
                elif action == 'delete':
                    del parent[user_name]
                else:
                    raise ValueError('invalid action: {}'.format(action))
            elif action != 'delete':
                parent[user_name] = chat_class(self.bot, raw_dict)

    def add_new_messages(self, raw_msg):
        print(raw_msg)

    def sync_loop(self):
        """ 保持登陆状态并同步数据 """

        while True:
            ret_code = None
            selector = None
            for _ in range(3):
                ret_code, selector = self.sync_check()
                if ret_code == 0:
                    break
                elif 1100 < ret_code < 1102:
                    self.offline(ResponseError(self.bot, ret_code, 'logged out by remote'))
                else:
                    logger.error('sync error: ret_code={}; selector={}'.format(ret_code, selector))
            else:
                self.offline(ResponseError(self.bot, ret_code, 'failed to sync'))

            if selector:
                self.sync()

    def sync_check(self):
        """ 检查同步状态 """
        err = None
        for _ in range(3):
            resp = self.get(self.uris.sync_check, params=dict(
                r=self.uris.ts_now, skey=self.data.skey, sid=self.sid, uin=self.data.uin, deviceid=self.device_id,
                synckey='|'.join(['{0[Key]}_{0[Val]}'.format(d) for d in self.data.sync_key['List']]),
                _=self.uris.ts_add_up))
            try:

                m = re.search(r'window\.synccheck={retcode:"(\d+)",selector:"(\d+)"}', resp.text.replace(' ', ''))
                ret_code = int(m.group(1))
                selector = int(m.group(2))
            except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
                logger.error('got invalid "synccheck" result:\n{}'.format(resp.text))
                err = e
            else:
                return ret_code, selector
        self.offline(err)

    def sync(self):
        """ 同步数据 """
        resp_json = self.post(self.uris.sync, params=dict(
            sid=self.sid, skey=self.data.skey, lang=LANGUAGE, pass_ticket=self.data.pass_ticket
        ), data_ext={'SyncKey': self.data.sync_key, 'rr': self.uris.ts_invert})

        # 处理顺序：更新自己、更新聊天对象、新增消息、删除聊天对象
        # ModChatRoomMemberList 在 Web 微信中未被实现

        merge_chat_dict(self.data.self.raw, resp_json.get('Profile'))
        self.process_chat_list(resp_json['ModContactList'], 'update')
        self.add_new_messages(resp_json['AddMsgList'])
        self.process_chat_list(resp_json['DelContactList'], 'delete')

    # noinspection PyMethodMayBeStatic
    def offline(self, exception):
        """ 被迫登出/掉线 """
        raise exception

    def logout(self):
        """ 主动登出 """
        return self.session.post(
            self.uris.logout,
            params=dict(redirect=1, type=0, skey=self.data.skey),
            data=dict(sid=self.sid, uin=self.data.uin))

    # noinspection PyUnusedLocal
    def session_response_hook(self, resp, *args, **kwargs):
        err = None
        for _ in range(3):
            try:
                resp.raise_for_status()
            except requests.HTTPError as e:
                logger.exception('retrying for http status code')
                err = e
                resp = self.session.send(resp.request)
            else:
                return resp
        self.offline(err)

    @property
    def sid(self):
        return self.from_cookies('wxsid')

    @property
    def device_id(self):
        return 'e{}'.format(str(random.random())[2:17])


def from_js(js, *names):
    """ 从 js 请求中获取指定的一个或多个变量名对应的值，需要时会自动转换为数字 """

    if names:
        def get_value(name):
            m = re.search(r'\b' + re.escape(name) + r'\s*=\s*(.+?)\s*;', js)
            if m:
                v = m.group(1)
                m = re.search(r'^(["\'])(.*?)\1$', v)
                if m:
                    return m.group(2)
                elif '.' in v:
                    return float(v)
                else:
                    return int(v)

        try:
            ret = smart_map(get_value, names)
        except ValueError:
            raise ValueError('invalid js:\n{}'.format(js))
        if len(ret) == 1:
            return ret[0]
        return ret


def merge_chat_dict(old, new):
    for k, v in new.items():
        if v and v not in (old.get(k), {'Buff': ''}):
            old[k] = v


if __name__ == '__main__':
    core = Core()
    pass
