# coding: utf-8
from __future__ import unicode_literals

import json
import logging
import os
import platform
import random
import re
import subprocess
from multiprocessing.pool import ThreadPool
from xml.etree import ElementTree as ETree

import pyqrcode
import requests

from wxpy.api.chats import Friend, Group, Member
from wxpy.api.data import Data
from wxpy.api.uris import LANGUAGE, URIS
from wxpy.compatible.utils import force_encoded_string_output
from wxpy.exceptions import ResponseError
from wxpy.utils.misc import chunks, enhance_connection, ensure_list, get_username, smart_map, start_new_thread, \
    test_chat_type

try:
    import queue
except ImportError:
    # noinspection PyUnresolvedReferences,PyPep8Naming
    import Queue as queue

logger = logging.getLogger(__name__)


# external data: cookies, uris,


class Core(object):
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) ' \
                 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'

    def __init__(
            self, bot=None, cache_path=None,
            console_qr=None, qr_path=None, proxies=None, hooks=None
    ):
        """
        class:`Bot` 的内核，负责

        1. 完成初始化和登陆过程
        2. 同步检查和数据同步
        3. 包装 self.urls 中的各原始接口，供 class:`Bot` 调用
        """

        self.bot = bot

        self.cache_path = 'wxpy.pkl' if cache_path is True else cache_path
        self.console_qr = console_qr
        self.qr_path = qr_path or 'QR.jpg'

        self._proxies = proxies

        self.session = None
        self.uris = None
        self.uuid = None

        self.data = Data()

        self.msg_queue = queue.Queue()

        if isinstance(hooks, dict):
            # Todo: 在 hook 后的函数中传入原方法
            for method_name, new_func in hooks.items():
                setattr(self, method_name, new_func)

    @force_encoded_string_output
    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    @property
    def name(self):
        return self.data.self.name

    # [requests]

    def make_session(self, cookies=None):

        # noinspection PyUnusedLocal
        def session_response_hook(resp, *args, **kwargs):
            final_error = None
            for _ in range(3):
                try:
                    resp.raise_for_status()
                except requests.HTTPError as e:
                    logger.exception('retrying for http status code')
                    final_error = e
                    resp = session.send(resp.request)
                else:
                    return resp
            raise final_error

        session = requests.Session()
        session.headers.update({'User-Agent': self.USER_AGENT})
        session.hooks.update(response=session_response_hook)
        enhance_connection(session)

        if self._proxies:
            session.proxies = self._proxies

        if cookies:
            # Todo: load cookies
            pass
        else:
            self.uris = URIS(session.get(URIS.start).url)
            self.uuid = None

        return session

    def get(self, url, **kwargs):
        """ get 请求 """
        resp = self.session.get(url, **kwargs)
        return self.check_response_json(resp)

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
        return self.check_response_json(resp)

    def download(self, url, save_path):
        """ 下载文件 """
        resp = self.session.get(url, stream=True)
        with open(save_path, 'wb') as fp:
            for chunk in resp.iter_content(chunk_size=128):
                fp.write(chunk)

    @property
    def proxies(self):
        return self._proxies

    @proxies.setter
    def proxies(self, value):
        self.session.proxies = value
        self._proxies = value

    # [apis]

    def login(self):
        """ 登陆 """

        while True:

            self.session = self.make_session()

            prompt('Getting uuid for QR Code')
            self.uuid = self.get_qrcode_uuid()
            prompt('Downloading QR Code')
            self.download(self.uris.qr_download + self.uuid, self.qr_path)
            self.show_qrcode()
            prompt('Scan the QR Code to log in')

            while True:

                # 查询登陆状态
                resp = self.get(
                    self.uris.login,
                    params=dict(
                        loginicon=True,
                        uuid=self.uuid,
                        tip=self.uris.tip,
                        r=self.uris.ts_invert,
                        _=self.uris.ts_add_up
                    ),
                    timeout=(10, 30)
                )

                code = from_js(resp.text, 'window.code')
                logging.debug('got qr status code: {}'.format(code))

                if code == 200:
                    # 登陆成功
                    self.remove_qr_code()

                    redirect = from_js(resp.text, 'window.redirect_uri')
                    resp = self.get(redirect)
                    self.uris = URIS(resp.url)

                    tree = ETree.fromstring(resp.history[0].text)
                    self.data.skey = tree.findtext('skey')
                    self.data.uin = int(tree.findtext('wxuin'))
                    self.data.pass_ticket = tree.findtext('pass_ticket')
                    self.data.gray_scale = int(tree.findtext('isgrayscale'))

                    prompt('Initializing')
                    self.init()

                    prompt('Loading chats, this may take a while')
                    self.get_contact()
                    self.batch_get_contact(self.filter_chats_by_type(Group))

                    prompt('Logged in as {}'.format(self.name))
                    self.logged_in()

                    # 开始并返回数据同步线程
                    return start_new_thread(self.data_sync_loop)

                elif code == 201:
                    # 扫码成功
                    prompt('QR Code scanned')
                    prompt('Confirm login on your phone')
                    self.confirm_login()
                elif code == 400:
                    # 二维码超时
                    prompt('QR Code expired\n')
                    self.qr_expired()
                    break
                elif code == 408:
                    # 继续等待
                    continue
                else:
                    logger.warning('unexpected qr status:\n{}'.format(resp.text))

    def get_push_login_uuid(self):
        """ 获取 push login 的 uuid """
        if self.data.uin:
            return self.get(self.uris.push_login_url, params=dict(uin=self.data.uin)).json().get('uuid')

    def get_qrcode_uuid(self):
        """ 获取二维码的 uuid """
        resp = self.get(self.uris.js_login)
        code, uuid = from_js(resp.text, 'window.QRLogin.code', 'window.QRLogin.uuid')
        if code == 200 and uuid:
            return uuid
        else:
            raise ResponseError(self, code, 'failed to get qrcode uuid:\n{}'.format(resp.text))

    def init(self):

        json_resp = self.post(self.uris.init)
        self.data.self = Friend(self, json_resp['User'])
        self.process_chat_list(json_resp['ContactList'])
        self.status_notify(self.data.self, self.data.self, 3)

    def status_notify(self, sender, receiver, code):
        return self.post(
            self.uris.status_notify,
            params=dict(lang=LANGUAGE, pass_ticket=self.data.pass_ticket),
            data_ext={
                'Code': code,
                'FromUserName': get_username(sender),
                'ToUserName': get_username(receiver),
                'ClientMsgId': self.uris.ts_now,
            })

    def data_sync_loop(self):
        """ 主循环: 数据同步 """

        while True:
            ret_code = None
            selector = None
            for _ in range(3):
                ret_code, selector = self.sync_check()
                if ret_code == 0:
                    break
                elif 1100 <= ret_code <= 1102:
                    self.offline(ResponseError(self, ret_code, 'logged out by remote server'))
                else:
                    logger.error('sync error: ret_code={}; selector={}'.format(ret_code, selector))
            else:
                self.offline(ResponseError(self, ret_code, 'failed to sync'))

            if selector:
                self.sync()

    def sync_check(self):
        """ 检查同步状态 """
        final_error = None
        for _ in range(3):
            resp = self.get(
                self.uris.sync_check,
                params=dict(
                    r=self.uris.ts_now,
                    skey=self.data.skey,
                    sid=self.sid,
                    uin=self.data.uin,
                    deviceid=self.device_id,
                    synckey='|'.join(['{0[Key]}_{0[Val]}'.format(d) for d in self.data.sync_key['List']]),
                    _=self.uris.ts_add_up
                ),
                timeout=(10, 30),
            )

            logger.debug('"synccheck" resp: {}'.format(resp.text))

            try:
                m = re.search(r'window\.synccheck={retcode:"(\d+)",selector:"(\d+)"}', resp.text.replace(' ', ''))
                ret_code = int(m.group(1))
                selector = int(m.group(2))
            except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
                logger.error('unexpected "synccheck" result:\n{}'.format(resp.text))
                final_error = e
            else:
                return ret_code, selector
        self.offline(final_error)

    def sync(self):
        """
        同步数据

        聊天对象更新:
            新增/减少群成员: ModContactList (该群新消息时触发)
            新增/更新聊天对象: ModContactList
            减少聊天对象: DelContactList
        """

        final_error = None
        for _ in range(3):
            try:
                resp_json = self.post(
                    self.uris.sync,
                    params=dict(
                        sid=self.sid,
                        skey=self.data.skey,
                        lang=LANGUAGE,
                        pass_ticket=self.data.pass_ticket
                    ),
                    data_ext={'SyncKey': self.data.sync_key, 'rr': self.uris.ts_invert},
                    timeout=(10, 30),
                )
            except ResponseError as e:
                logging.exception('failed to get new content while syncing:')
                final_error = e
            else:
                merge_chat_dict(self.data.self.raw, resp_json.get('Profile'))
                self.process_chat_list(resp_json['ModContactList'])
                self.put_new_messages(resp_json['AddMsgList'])
                self.process_chat_list(resp_json['DelContactList'], delete=True)
                # ModChatRoomMemberList 在 Web 微信中未被实现
                return resp_json
        else:
            self.offline(final_error)

    def get_contact(self):
        """ 更新通讯录列表 """
        seq = 0
        while True:
            resp_json = self.get(
                self.uris.get_contact,
                params=dict(
                    r=self.uris.ts_now,
                    seq=seq,
                    pass_ticket=self.data.pass_ticket
                )
            )

            self.process_chat_list(resp_json['MemberList'])
            seq = resp_json.get('Seq')
            if not seq:
                break

    def batch_get_contact(self, chat_or_chats, workers=5, chunk_size=50):
        """
        批量更新聊天对象详情

        :param chat_or_chats: 需要更新的聊天对象 (单个或列表)
        :param workers: 并发线程数 (默认为 5)
        :param chunk_size: 每个请求中处理的聊天对象个数 (最高为 50)
        """

        chat_or_chats = ensure_list(chat_or_chats)

        req_list = list()
        for chat in chat_or_chats:
            req_list.append({
                'UserName': chat.username,
                'EncryChatRoomId': chat.group.username if isinstance(chat, Member) else '',
            })

        def process(_chunk):
            resp_json = self.post(
                self.uris.batch_get_contact,
                params=dict(type='ex', r=self.uris.ts_now, lang=LANGUAGE),
                data_ext={'Count': len(_chunk), 'List': _chunk}
            )
            self.process_chat_list(resp_json['ContactList'])

        # for chunk in chunks(req_list, chunk_size):
        #     process(chunk)

        with ThreadPool(workers) as pool:
            pool.map(process, chunks(req_list, chunk_size))

    def logout(self):
        """ 主动登出 """

        logger.info('logging out {}'.format(self.name))

        return self.session.post(
            self.uris.logout,
            params=dict(
                redirect=1,
                type=0,
                skey=self.data.skey
            ),
            data=dict(
                sid=self.sid,
                uin=self.data.uin
            )
        )

    @property
    def sid(self):
        return self.from_cookies('wxsid')

    @property
    def device_id(self):
        return 'e{}'.format(str(random.random())[2:17])

    # [events]

    def show_qrcode(self):
        """ 展示二维码 """

        if not self.console_qr:
            system = platform.system()
            # noinspection PyBroadException
            try:
                if system == 'Darwin':
                    subprocess.call(['open', self.qr_path])
                elif system == 'Linux':
                    subprocess.call(['xdg-open', self.qr_path])
                else:
                    # noinspection PyUnresolvedReferences
                    os.startfile(self.qr_path)
            except:
                logger.warning('failed to open qrcode, using console_qr instead')
            else:
                return

        self.show_console_qr()

    def show_console_qr(self):
        qrcode = pyqrcode.create(self.uris.qr_login + self.uuid)
        # print(qrcode.terminal(module_color=232, background=255, quiet_zone=1))
        print(qrcode.terminal(module_color='dark gray', background='light gray', quiet_zone=1))

    # noinspection PyMethodMayBeStatic
    def confirm_login(self):
        pass

    def remove_qr_code(self):
        if os.path.isfile(self.qr_path):
            os.remove(self.qr_path)

    # noinspection PyMethodMayBeStatic
    def qr_expired(self):
        pass

    # noinspection PyMethodMayBeStatic
    def logged_in(self):
        pass

    def new_friend(self, friend):
        pass

    def new_group(self, group):
        pass

    def new_member(self, group, member):
        pass

    def friend_deleted(self, friend):
        pass

    def group_deleted(self, group):
        pass

    def member_deleted(self, group, member):
        pass

    # noinspection PyMethodMayBeStatic
    def offline(self, exception):
        """ 被登出/掉线 """
        prompt('You\'ve been logged out by remote server')
        raise exception

    # [processors]

    def process_chat_list(self, raw_chat_list, delete=False):
        """
        处理返回数据中的聊天对象字典列表

        :param raw_chat_list: 聊天对象字典列表
        :param delete: 当为 True 时，删除聊天对象 (默认为 False)
        """

        for raw_dict in raw_chat_list:
            username = raw_dict['UserName']
            if delete:
                # 删除聊天对象
                if username in self.data.chats:
                    del self.data.chats[username]
                else:
                    logger.warning('unknown chat to delete:\n{}'.format(raw_dict))
            else:
                chat_type = test_chat_type(raw_dict)
                if issubclass(chat_type, Member):
                    # 更新群成员的详细信息
                    self.data.raw_members[username] = raw_dict
                else:
                    if username in self.data.chats:
                        # 更新聊天对象详情
                        self.data.chats[username].raw = raw_dict
                    else:
                        # 新增聊天对象
                        self.data.chats[username] = chat_type(self, raw_dict)

    def put_new_messages(self, raw_msg_list):
        for raw_msg in raw_msg_list:
            # self.msg_queue.put(Message(self, raw_msg))
            print(raw_msg['Content'])

    # [utils]

    def check_response_json(self, resp):

        """
        | 尝试从 requests.Response 对象中解析 JSON 数据
        | 若解析到 JSON 数据，则进行基本处理和检查，并返回 JSON 数据
        | 反之返回原来的 Response 对象

        :param resp: class:`requests.Response` 对象
        """

        try:
            json_dict = json.loads(resp.content.decode('utf-8', errors='replace'))
        except (json.JSONDecodeError, TypeError):
            return resp

        skey = json_dict.get('SKey')
        if skey:
            self.data.skey = skey
        sync_key = json_dict.get('SyncKey')
        if sync_key:
            self.data.sync_key = sync_key
        sync_check_key = json_dict.get('SyncCheckKey')
        if sync_check_key:
            self.data.sync_check_key = sync_check_key

        if 'BaseResponse' in json_dict:
            try:
                base_response = json_dict['BaseResponse']
                err_code = base_response['Ret']
                err_msg = base_response['ErrMsg']
            except (KeyError, TypeError):
                logger.error('failed to parse base_response:\n{}'.format(json_dict['BaseResponse']))
            else:
                if err_code != 0:
                    raise ResponseError(self, err_code, err_msg)

        return json_dict

    def filter_chats_by_type(self, chat_type):
        return list(filter(
            lambda x: isinstance(x, chat_type),
            self.data.chats.values()
        ))

    def from_cookies(self, name):
        """ 从 cookies 中获取值 """
        return self.session.cookies.get(name, domain='.' + self.uris.host)

    '''
    def get_group_by_member(self, raw_member):
        """ 找到群成员所属的群聊对象 """
        group_id = raw_member.get('EncryChatRoomId')
        if group_id:
            group_username = self.data.group_usernames.get(group_id)
            if not group_username:
                logger.warning('no group found by {}'.format(raw_member))
            else:
                return self.data.chats[group_username]
    '''


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


def prompt(content):
    print('* {}'.format(content))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    core = Core()
    core.login()
    gs = core.filter_chats_by_type(Group)
    gs[-1].update()
