# coding: utf-8
from __future__ import unicode_literals

import datetime
import hashlib
import json
import logging
import mimetypes
import os
import pickle
import platform
import random
import re
import subprocess
import time
from multiprocessing.pool import ThreadPool
from pprint import pformat
from xml.etree import ElementTree as ETree

import pyqrcode
import requests

from wxpy import __version__
from wxpy.api.chats import Chats, Friend, Group, MP, Member
from wxpy.api.data import Data
from wxpy.api.messages.message_types import *
from wxpy.api.messages.sent_message import SentMessage
from wxpy.api.uris import URIS
from wxpy.compatible.utils import force_encoded_string_output
from wxpy.exceptions import ResponseError
from wxpy.utils.misc import chunks, decode_webwx_json_values, diff_usernames, enhance_connection, ensure_list, \
    get_chat_type, get_username, new_local_msg_id, smart_map, start_new_thread

try:
    import queue
except ImportError:
    # noinspection PyUnresolvedReferences,PyPep8Naming
    import Queue as queue

try:
    import html
except ImportError:
    # Python 2.6-2.7
    # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyCompatibility
    from HTMLParser import HTMLParser

    html = HTMLParser()

logger = logging.getLogger(__name__)


class Core(object):
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) ' \
                 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'

    def __init__(
            self, bot=None, cache_path=None,
            console_qr=None, qr_path=None, proxies=None, hooks=None
    ):
        """
        :class:`Bot` 的内核，负责

        1. 完成初始化和登陆过程
        2. 同步检查和数据同步
        3. 包装 self.urls 中的各原始接口，供 :class:`Bot` 调用
        """

        self.bot = bot

        self.cache_path = 'wxpy.pkl' if cache_path is True else cache_path
        self.console_qr = console_qr

        if qr_path:
            self.qr_path = qr_path
        elif self.cache_path:
            # 根据 cache_path 生成相对应的 qr_path, 避免多开时重复
            self.qr_path = '{}_qrcode.png'.format(re.sub(r'\.\w+$', '', self.cache_path))
        else:
            self.qr_path = 'qrcode.png'

        self._proxies = proxies

        self.session = None
        self.uris = None
        self.data = Data()

        self.uuid = None
        self.qrcode = None

        self.message_queue = queue.Queue(0)
        self.alive = None

        if isinstance(hooks, dict):
            for ori_method_name, new_func in hooks.items():
                setattr(self, ori_method_name, new_func)

        self.load()

    @force_encoded_string_output
    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    @property
    def name(self):
        if self.data.raw_self:
            return self.data.raw_self.get('NickName')

    @property
    def username(self):
        return self.data.raw_self['UserName']

    # [requests]

    def new_session(self, cookies=None):

        # noinspection PyUnusedLocal
        def session_response_hook(resp, *args, **kwargs):
            resp.raise_for_status()

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        self.session.hooks.update(response=session_response_hook)
        enhance_connection(self.session)

        if self._proxies:
            self.session.proxies = self._proxies

        if cookies:
            self.session.cookies = self.data.cookies
        else:
            self.uris = URIS(self.session.get(URIS.START_PAGE).url)
            self.uuid = None

        return self.session

    def get(self, url, load_resp=True, **kwargs):
        """
        经过封装的 GET 请求，会自动进行返回值检查等操作

        :param url: 请求的 URL
        :param load_resp: 是否解析 Response 中的 JSON 内容，并返回解析后的 dict
        :param kwargs: 发起请求时的其他参数
        """
        resp = self.session.get(url, **kwargs)
        if load_resp:
            resp = self.load_response_as_json(resp)
        return resp

    def post(self, url, ext_data=None, load_resp=True, **kwargs):
        """
        经过封装的 POST 请求，会自动进行返回值检查等操作

        :param url: 请求的 URL
        :param ext_data: payload 中除了 BaseRequest 字段以外的部分
        :param load_resp: 是否解析 Response 中的 JSON 内容，并返回解析后的 dict
        :param kwargs: 发起请求时的其他参数
        """

        if 'files' not in kwargs:
            data = {'BaseRequest': self.base_request}
            if ext_data:
                data.update(ext_data)
            data = json.dumps(data, ensure_ascii=False).encode('utf-8', errors='replace')
            kwargs['data'] = data
            kwargs['headers'] = {'Content-Type': 'application/json;charset=UTF-8'}

        resp = self.session.post(url, **kwargs)
        if load_resp:
            resp = self.load_response_as_json(resp)
        return resp

    def download(self, url, save_path=None):
        """
        下载文件

        :param url: 需要下载的 URL 地址
        :param save_path: 保存路径。为空时不保存到磁盘，直接返回内容数据
        """

        resp = self.session.get(url, stream=True)
        resp.raise_for_status()

        if save_path:
            with open(save_path, 'wb') as fp:
                for chunk in resp.iter_content(chunk_size=128):
                    fp.write(chunk)
                return resp
        else:
            return resp.content

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

        if self.session:
            try:
                self.sync(retries=1)
            except ResponseError:
                logger.info('failed to continue last data sync loop')
            else:
                return self._logged_in()

        while True:

            if self.data.uin:
                self.uuid = self.get_push_login_uuid()
                self.data = Data()

            if not self.uuid:
                self.new_session()
                prompt('Getting uuid for QR Code')
                self.uuid = self.get_qrcode_uuid()
                # pyqrcode.QRCode 对象
                self.qrcode = pyqrcode.create(self.uris.QR_LOGIN + self.uuid)

                prompt('Downloading QR Code')
                if self.qr_path.lower().endswith('.png'):
                    qr_save_path = None
                    self.qrcode.png(self.qr_path, scale=10)
                else:
                    qr_save_path = self.qr_path
                self.download(self.uris.QR_DOWNLOAD + self.uuid, qr_save_path)

                self.show_qrcode()
                prompt('Scan the QR Code to log in')

            while True:

                # 查询 uuid 状态
                resp = self.get(
                    self.uris.login,
                    params=dict(
                        loginicon=True,
                        uuid=self.uuid,
                        tip=self.uris.tip,
                        r=self.uris.ts_invert,
                        _=self.uris.ts_add_up
                    ),
                    load_resp=False,
                )

                code = from_js(resp.text, 'window.code')
                logging.debug('got uuid status code: {}'.format(code))

                if code == 200:
                    # 验证通过

                    redirect = from_js(resp.text, 'window.redirect_uri')
                    resp = self.get(redirect, load_resp=False)

                    # 中转的 xml
                    xml_resp = resp.history[0] if resp.history else resp

                    tree = ETree.fromstring(xml_resp.text)
                    ret_code = int(tree.findtext('ret'))

                    if ret_code:
                        # 登录失败
                        logger.error('unexpected login xml content:\n{}'.format(xml_resp.text))
                        self._logged_out(ResponseError(self, ret_code, tree.findtext('message')))

                    self.data.skey = tree.findtext('skey')
                    self.data.uin = int(tree.findtext('wxuin'))
                    self.data.pass_ticket = tree.findtext('pass_ticket')
                    self.data.gray_scale = int(tree.findtext('isgrayscale'))

                    # 登陆成功
                    self.uris = URIS(resp.url)

                    prompt('Initializing')
                    self.init()

                    prompt('Loading chats data')
                    self.get_contact()
                    self.batch_get_contact(self.get_chats(Group))

                    return self._logged_in()

                elif code == 201:
                    # 需要在手机上确认登陆
                    prompt('Confirm login on your phone')
                    self.remove_qrcode()
                    self.confirm_login()
                elif code == 400:
                    # uuid 超时
                    self.uuid = None
                    prompt('UUID expired\n')
                    self.uuid_expired()
                    break
                elif code == 408:
                    # 继续等待
                    continue
                else:
                    logger.warning('unexpected uuid status:\n{}'.format(resp.text))
                    self._logged_out(ResponseError(self, code, resp.text))

    def get_push_login_uuid(self):
        """ 获取 push login 的 uuid """
        resp_json = self.get(self.uris.push_login_url, params=dict(uin=self.data.uin))
        if resp_json.get('uuid'):
            return resp_json['uuid']
        else:
            logger.warning('uuid not found while trying to push login:\n{}'.format(resp_json))

    def get_qrcode_uuid(self):
        """ 获取二维码的 uuid """
        resp = self.get(self.uris.js_login, load_resp=False)
        code, uuid = from_js(resp.text, 'window.QRLogin.code', 'window.QRLogin.uuid')
        if code == 200 and uuid:
            return uuid
        else:
            raise ResponseError(self, code, 'failed to get qrcode uuid:\n{}'.format(resp.text))

    def init(self):

        json_resp = self.post(self.uris.init)
        self.data.raw_self = json_resp['User']
        self.process_chat_list(json_resp['ContactList'])
        self.status_notify(self.data.raw_self, self.data.raw_self, 3)

    def status_notify(self, sender, receiver, code):
        return self.post(
            self.uris.status_notify,
            params=dict(lang=self.uris.language, pass_ticket=self.data.pass_ticket),
            ext_data={
                'Code': code,
                'FromUserName': get_username(sender),
                'ToUserName': get_username(receiver),
                'ClientMsgId': self.uris.ts_now,
            })

    def op_log(self, chat, cmd_id, op=None, remark_name=None):

        ext_data = {
            'CmdId': cmd_id,
            'RemarkName': remark_name or '',
            'UserName': get_username(chat),
        }

        if op:
            ext_data['OP'] = op

        return self.post(self.uris.op_log, ext_data=ext_data)

    def verify_user(self, user, op_code, verify_content=None):
        return self.post(
            self.uris.verify_user,
            params=dict(r=self.uris.ts_now),
            ext_data={
                # 添加好友: 2; 通过验证: 3
                'Opcode': op_code,
                'SceneList': [33],
                'SceneListCount': 1,
                'VerifyContent': verify_content or '',
                'VerifyUserList': [get_username(user)],
                'VerifyUserListSize': 1,
                'skey': self.data.skey,
            })

    def create_chatroom(self, users, topic=None):
        """
        创建新的群聊

        :param users: 用户列表 (自己除外，至少需要两位好友)
        :param topic: 群名称
        :return: 若创建成功，返回新群的 username
        :rtype: str
        """

        usernames = list(filter(
            lambda x: x != self.username,
            map(get_username, users)
        ))

        if len(usernames) < 2:
            raise ValueError('too few users to create group')

        resp_json = self.post(
            self.uris.create_chatroom,
            params=dict(r=self.uris.ts_now),
            ext_data={
                'MemberCount': len(usernames),
                'MemberList': [{'UserName': username} for username in usernames],
                'Topic': topic or '',
            })

        if 'ChatRoomName' not in resp_json:
            raise ValueError(
                'failed to create group, '
                'missing username in the response:'
                '\n{}'.format(pformat(resp_json)))

        self.batch_get_contact(resp_json['ChatRoomName'])

        return resp_json['ChatRoomName']

    def update_chatroom(self, group, func_name, info_dict):

        """
        更新群所需的接口，例如 邀请入群、移出群员、修改群名
        """

        ext_data = {'ChatRoomName': get_username(group)}
        ext_data.update(info_dict)

        return self.post(self.uris.update_chatroom, params=dict(fun=func_name), ext_data=ext_data)

    def revoke_msg(self, receiver, server_id, local_id):
        """ 撤回消息 """
        return self.post(
            self.uris.revoke_msg,
            ext_data={
                'SvrMsgId': str(server_id),
                'ToUserName': get_username(receiver),
                'ClientMsgId': str(local_id),
            })

    def data_sync_loop(self):
        """ 主循环: 数据同步 """

        try:
            while True:
                ret_code = None
                selector = None
                for _ in range(3):
                    ret_code, selector = self.sync_check()
                    if ret_code == 0:
                        break
                    elif 1100 <= ret_code <= 1102:
                        return self._logged_out(ret_code)
                    else:
                        logger.error('sync error: ret_code={}; selector={}'.format(ret_code, selector))
                else:
                    self._logged_out(ResponseError(self, ret_code, 'failed to sync'))

                if selector:
                    self.sync()
        finally:
            self.dump()

    def sync_check(self, retries=3):
        """ 检查同步状态 """
        final_error = None
        for _ in range(retries):
            resp = self.get(
                self.uris.sync_check,
                params=dict(
                    r=self.uris.ts_now,
                    skey=self.data.skey,
                    sid=self.sid,
                    uin=self.data.uin,
                    deviceid=self.device_id,
                    synckey='|'.join(['{0[Key]}_{0[Val]}'.format(d) for d in (
                        self.data.sync_check_key or self.data.sync_key)['List']]),
                    _=self.uris.ts_add_up
                ),
                timeout=(10, 30),
                load_resp=False,
            )

            logger.debug('"synccheck" resp: {}'.format(resp.text))

            try:
                found = re.search(
                    r'window\.synccheck={retcode:"(\d+)",selector:"(\d+)"}',
                    resp.text.replace(' ', '')
                )
                ret_code = int(found.group(1))
                selector = int(found.group(2))
            except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
                logger.error('unexpected "synccheck" result:\n{}'.format(resp.text))
                final_error = e
            else:
                return ret_code, selector
        self._logged_out(final_error)

    def sync(self, retries=3):
        """
        同步数据

        聊天对象更新:
            新增/减少群成员: ModContactList (该群新消息时触发)
            新增/更新聊天对象: ModContactList
            减少聊天对象: DelContactList
        """

        final_error = None
        for _ in range(retries):
            try:
                resp_json = self.post(
                    self.uris.sync,
                    params=dict(
                        sid=self.sid,
                        skey=self.data.skey,
                        pass_ticket=self.data.pass_ticket
                    ),
                    ext_data={'SyncKey': self.data.sync_key, 'rr': self.uris.ts_invert},
                    timeout=(10, 30),
                )
            except ResponseError as e:
                # 在 push login 中会经历这一步，所以改用 INFO 等级
                logging.info('failed to sync: {}'.format(str(e)))
                final_error = e
            else:
                merge_chat_dict(self.data.raw_self, resp_json.get('Profile'))
                self.process_chat_list(resp_json['ModContactList'])
                self.put_new_messages(resp_json['AddMsgList'])
                self.process_chat_list(resp_json['DelContactList'], delete=True)
                # ModChatRoomMemberList 在 Web 微信中未被实现
                return resp_json
        else:
            self._logged_out(final_error)

    def get_contact(self):
        """ 更新通讯录列表 """
        seq = 0
        while True:
            resp_json = self.get(
                self.uris.get_contact,
                params=dict(
                    lang=self.uris.language,
                    pass_ticket=self.data.pass_ticket,
                    r=self.uris.ts_now,
                    seq=seq,
                    skey=self.data.skey,
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

            if isinstance(chat, Member):
                group_username = chat.group_username
            elif isinstance(chat, dict):
                group_username = chat.get('ChatRoomId') or chat.get('EncryChatRoomId') or ''
            else:
                group_username = ''

            req_list.append({
                'UserName': get_username(chat),
                'EncryChatRoomId': group_username
            })

        def process(_chunk):
            resp_json = self.post(
                self.uris.batch_get_contact,
                params=dict(type='ex', r=self.uris.ts_now, lang=self.uris.language),
                ext_data={'Count': len(_chunk), 'List': _chunk}
            )
            self.process_chat_list(resp_json['ContactList'])

        with ThreadPool(workers) as pool:
            pool.map(process, chunks(req_list, chunk_size))

    def send(self, receiver, content, send_type=None, media_id=None):
        """
        内部使用的消息发送方法

        :param receiver: 消息的接收者
        :param content: 发送的内容。消息类型为 TEXT 时为文本，其他类型时为文件路径
        :param media_id: 文件在服务器中的唯一 ID，填写后可省略上传步骤
        :param send_type: 消息类型，支持 TEXT, IMAGE, EMOTICON, VIDEO, FILE (默认为 TEXT)
        :return: :class:`SentMessage`
        """

        send_type = send_type or TEXT

        # url

        url = {
            TEXT: self.uris.send_msg,
            IMAGE: self.uris.send_msg_img,
            STICKER: self.uris.send_emoticon,
            VIDEO: self.uris.send_video_msg,
            FILE: self.uris.send_app_msg,
        }[send_type]

        # params

        params = {'pass_ticket': self.data.pass_ticket}

        if send_type in (IMAGE, VIDEO, FILE):
            params['fun'] = 'async'
            params['f'] = 'json'
        elif send_type == STICKER:
            params['fun'] = 'sys'

        # msg_dict

        local_id = new_local_msg_id()
        receiver_username = get_username(receiver)
        msg_dict = {
            'ClientMsgId': local_id,
            'FromUserName': self.username,
            'LocalID': local_id,
            'ToUserName': receiver_username,
            'Type': send_type.app or send_type.main,
        }

        if send_type == TEXT:
            msg_dict['Content'] = str(content)
        elif send_type != STICKER:
            msg_dict['Content'] = ''

        if send_type == STICKER:
            msg_dict['EmojiFlag'] = 2

        create_time = datetime.datetime.now()

        if send_type in (IMAGE, STICKER, VIDEO, FILE):
            if not media_id:
                media_id = self.upload_media(content, send_type, receiver)

            if send_type == FILE:
                # noinspection SpellCheckingInspection
                msg_dict['Content'] = \
                    '<appmsg appid="wxeb7ec651dd0aefa9" sdkver=""><title>{file_name}' \
                    '</title><des/><action/><type>6</type><content/><url/><lowurl/><appattach>' \
                    '<totallen>{file_size}</totallen><attachid>{media_id}</attachid>' \
                    '<fileext>{file_ext}</fileext></appattach><extinfo/></appmsg>'.format(
                        file_name=os.path.basename(content),
                        file_size=os.path.getsize(content),
                        media_id=media_id,
                        file_ext=os.path.splitext(content)[1][1:]
                    )
            else:
                msg_dict['MediaId'] = media_id

        # request

        resp_json = self.post(url, params=params, ext_data={'Msg': msg_dict, 'Scene': 0})

        return SentMessage(
            core=self,
            type=send_type,
            id=resp_json.get('MsgID'),
            local_id=resp_json.get('LocalID'),
            text=content if send_type == TEXT else None,
            path=content if send_type != TEXT else None,
            media_id=media_id,
            create_time=create_time,
            receiver=self.get_chat_obj(receiver_username),
        )

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
    def base_request(self):
        return {
            "Uin": self.data.uin, "Sid": self.sid,
            "Skey": self.data.skey, "DeviceID": self.device_id
        }

    @property
    def sid(self):
        return self.from_cookies('wxsid')

    @property
    def device_id(self):
        return 'e{}'.format(str(random.random())[2:17])

    def upload_media(self, path, msg_type, receiver=None):

        """
        上传文件，获取 media_id，可用于发送需要上传文件的消息

        *限制: 上传文件的路径中含有汉字时会导致失败*

        :param path: 文件路径
        :param msg_type: 准备用于发送的消息类型
        :param receiver: 接收者，默认为文件传输助手 (似乎并不严格)
        :return: media_id
        :rtype: str
        """

        logger.info('uploading file: {}'.format(path))

        media_type = {
            IMAGE: (1, 'pic'), STICKER: (4, 'doc'),
            VIDEO: (2, 'video'), FILE: (4, 'doc')
        }[msg_type]

        base_name = os.path.basename(path)
        file_size = os.path.getsize(path)
        file_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'

        with open(path, 'rb') as fp:
            file_md5 = hashlib.md5(fp.read()).hexdigest()

        with open(path, 'rb') as fp:
            resp_json = self.post(
                self.uris.upload_media,
                params=dict(f='json'),
                files=dict(
                    id=(None, 'WU_FILE_{}'.format(self.uris.upload_media_count)),
                    name=(None, base_name),
                    type=(None, file_type),
                    lastModifiedDate=(None, time.strftime(
                        '%a %b %d %Y %H:%M:%S GMT%z (%Z)',
                        time.localtime(os.path.getmtime(path))
                    )),
                    size=(None, str(file_size)),
                    mediatype=(None, media_type[1]),
                    uploadmediarequest=(None, json.dumps({
                        'UploadType': 2,
                        'BaseRequest': self.base_request,
                        'ClientMediaId': self.uris.ts_now,
                        'TotalLen': file_size,
                        'StartPos': 0,
                        'DataLen': file_size,
                        'MediaType': media_type[0],
                        'FromUserName': self.username,
                        'ToUserName': get_username(receiver) if receiver else 'filehelper',
                        'FileMd5': file_md5,
                    })),
                    webwx_data_ticket=(None, self.from_cookies('webwx_data_ticket')),
                    pass_ticket=(None, self.data.pass_ticket),
                    filename=(base_name, fp, file_type)
                )
            )

        self.uris.upload_media_count += 1
        return resp_json['MediaId']

    # [data]

    def dump(self):
        if self.cache_path:
            self.data.cookies = self.session.cookies
            self.data.uris = self.uris

            with open(self.cache_path, 'wb') as fp:
                pickle.dump(self.data, fp)

    def load(self):
        if self.cache_path and os.path.isfile(self.cache_path):
            with open(self.cache_path, 'rb') as fp:
                data = pickle.load(fp)

            if getattr(data, 'version', None) == __version__:
                self.data = data
                self.uris = self.data.uris
                self.new_session(self.data.cookies)

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
        """ 以命令行方式展示二维码 """
        # 第一种注释掉的方式在 PyCharm 的 console 中无法显示，但在其他平台中色彩更分明
        # print(qrcode.terminal(module_color=232, background=255, quiet_zone=1))
        print(self.qrcode.terminal(module_color='dark gray', background='light gray', quiet_zone=1))

    # noinspection PyMethodMayBeStatic
    def confirm_login(self):
        """ 需要在手机端确认登陆时 """
        pass

    def remove_qrcode(self):
        """ 删除已扫描的二维码 """
        if os.path.isfile(self.qr_path):
            os.remove(self.qr_path)

    # noinspection PyMethodMayBeStatic
    def uuid_expired(self):
        """ 二维码 / uuid 过期时 """
        pass

    # noinspection PyMethodMayBeStatic
    def logged_in(self):
        """ 登录成功时 """
        pass

    # noinspection PyMethodMayBeStatic
    def logged_out(self, reason):
        """
        登出，或登录失败时

        :param reason:

            登出原因
            * 当自己主动登出或被服务端踢下线时为错误码 (int)
            * 当出现其他异常时，为 Exception 对象
        """
        pass

    # noinspection PyMethodMayBeStatic
    def new_friend(self, friend):
        """
        有新的好友时

        :param friend: 新的好友
        """
        pass

    # noinspection PyMethodMayBeStatic
    def new_group(self, group):
        """
        加入了新的群聊时

        :param group: 新的群聊对象
        """
        pass

    # noinspection PyMethodMayBeStatic
    def new_member(self, member):
        """
        有新的群成员加入时 (似乎仅在有新消息时触发)

        :param member: 新的群成员对象
        """
        pass

    # noinspection PyMethodMayBeStatic
    def deleting_friend(self, friend):
        """
        即将从本地数据中删除好友时

        :param friend: 即将被删除的好友对象
        """
        pass

    # noinspection PyMethodMayBeStatic
    def deleting_group(self, group):
        """
        即将从本地数据中删除群聊时 (似乎仅在有新消息时触发)

        :param group: 即将被删除的群聊对象
        """
        pass

    # noinspection PyMethodMayBeStatic
    def deleting_member(self, member):
        """
        即将从本地数据中删除群聊成员时

        :param member: 即将被删除的群成员对象
        """
        pass

    # [processors]

    def _logged_in(self):
        """ 这个方法仅在内部使用，请勿 hook """

        self.alive = True

        prompt('Logged in as {}'.format(self.name))

        # 下面这个方法可以用来 hook
        self.logged_in()
        self.dump()

        # 开始并返回数据同步线程
        return start_new_thread(self.data_sync_loop)

    def _logged_out(self, reason):
        """
        这个方法仅在内部使用，请勿 hook

        :param reason: 登出原因: 可以是 错误号(int), 文字说明(str), 或异常(Exception)
        """

        self.alive = False

        # 下面这个方法可以用来 hook
        self.logged_out(reason)

        if isinstance(reason, int):
            prompt('Logged out ({})'.format(reason))
        elif isinstance(reason, str):
            prompt(reason)
        elif isinstance(reason, BaseException):
            raise reason

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
                if username in self.data.raw_chats:

                    if self.alive:
                        # 只提示登陆完成后的聊天对象变化
                        chat_obj = self.get_chat_obj(username)
                        if isinstance(chat_obj, Friend):
                            self.deleting_friend(chat_obj)
                        elif isinstance(chat_obj, Group):
                            self.deleting_group(chat_obj)

                        del self.data.raw_chats[username]

                else:
                    logger.warning('unknown chat to delete:\n{}'.format(raw_dict))

            else:
                chat_type = get_chat_type(raw_dict)
                if issubclass(chat_type, Member):
                    # 更新群成员的详细信息
                    self.data.raw_members[username] = raw_dict
                else:
                    # 新增好友、群聊，或更新群成员列表时

                    if issubclass(chat_type, Group) and self.username not in list(map(
                            lambda x: x['UserName'], raw_dict['MemberList'])):
                        # 跳过 shadow group
                        continue

                    if self.alive:
                        # 同样的，只提示登陆完成后的聊天对象变化
                        if issubclass(chat_type, Group):

                            if username in self.data.raw_chats:
                                # 群成员列表更新
                                before = self.data.raw_chats[username]['MemberList']
                                after = raw_dict['MemberList']

                                old, new = diff_usernames(before, after)
                                group_username = raw_dict['UserName']

                                list(map(lambda x: self.deleting_member(Member(self, x, group_username)),
                                         filter(lambda x: x['UserName'] in old, before)))

                                list(map(lambda x: self.new_member(Member(self, x, group_username)),
                                         filter(lambda x: x['UserName'] in new, after)))
                            else:
                                # 新增群聊
                                self.new_group(chat_type(self, raw_dict))

                        elif issubclass(chat_type, Friend) and username not in self.data.raw_chats:
                            # 新增好友
                            self.new_friend(chat_type(self, raw_dict))

                    self.data.raw_chats[username] = raw_dict

    def put_new_messages(self, raw_msg_list):
        for raw_msg in raw_msg_list:
            self.message_queue.put(raw_msg)

    # [utils]

    def load_response_as_json(self, resp):

        """
        解析 Response 中的 JSON 数据，并同步各

        :param resp: :class:`requests.Response` 对象
        """

        resp.encoding = 'utf-8'
        json_dict = resp.json(object_hook=decode_webwx_json_values)

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

    def get_chats(self, chat_type=None, convert=False):
        """
        从 Core.data.raw_chats 中过滤出指定类型的聊天对象列表

        :param chat_type: 传入基于 :class:`Chat` 的 class，来指定聊天对象类型
        :param convert: 将获得的 dict 转换为指定的类
        """

        chat_list = list(self.data.raw_chats.values())

        if chat_type:
            chat_list = list(filter(
                lambda x: issubclass(get_chat_type(x), chat_type),
                chat_list
            ))

        if convert:

            for i, raw_chat in enumerate(chat_list):
                to_class = get_chat_type(raw_chat) if chat_type in (None, MP) else chat_type
                username = raw_chat['UserName']
                chat_list[i] = to_class(self, username)

            chat_list = Chats(chat_list, self)

        return chat_list

    def get_chat_obj(self, username, group_username=None):
        """
        | 将 username 转化为聊天对象
        | 若为群成员，则需填 group_username
        """

        def fetch_contact(_username):
            if _username not in self.data.raw_chats:
                self.batch_get_contact(_username)
            if _username in self.data.raw_chats:
                raw_chat = self.data.raw_chats[_username]
                return get_chat_type(raw_chat)(self, raw_chat)

        if group_username:
            group = fetch_contact(group_username)
            member = group.find(username=username)
            if not member:
                group.update()
                member = group.find(username=username)
            return member
        else:
            return fetch_contact(username)

    def from_cookies(self, name):
        """ 从 cookies 中获取值 """
        return self.session.cookies.get(name)


def from_js(js, *names):
    """ 从 js 请求中获取指定的一个或多个变量名对应的值，需要时会自动转换为数字 """

    if names:
        def get_value(name):
            found = re.search(r'\b' + re.escape(name) + r'\s*=\s*(.+?)\s*;', js)
            if found:
                v = found.group(1)
                found = re.search(r'^(["\'])(.*?)\1$', v)
                if found:
                    return found.group(2)
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
            if isinstance(v, dict):
                if 'Buff' in v:
                    old[k] = v['Buff']
                    continue
            old[k] = v


def prompt(content):
    print('* {}'.format(content))
