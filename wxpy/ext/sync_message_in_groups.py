from threading import Thread
from wxpy.api.chats import MALE, FEMALE


def sync_message_in_groups(
        msg, groups, prefix=None, suffix=None,
        raise_for_unsupported=False, run_async=True
):
    """
    将消息同步到多个微信群中

    支持以下消息类型
        * 文本 (`TEXT`)
        * 视频（`VIDEO`)
        * 文件 (`ATTACHMENT`)
        * 图片/自定义表情 (`PICTURE`)

            * 但不支持表情商店中的表情

        * 名片 (`CARD`)

            * 仅支持公众号名片

        * 分享 (`SHARING`)

            * 会被转化为 `标题 + 链接` 形式的纯文本

        * 语音 (`RECORDING`)

            * 会以文件方式发送

    :param Message msg: 需同步的消息对象
    :param Group groups: 需同步的群列表
    :param str prefix:
        * 转发时的 **前缀** 文本，原消息为文本时会自动换行
        * 若不设定，则使用默认前缀作为提示
    :param str suffix:
        * 转发时的 **后缀** 文本，原消息为文本时会自动换行
        * 默认为空
    :param bool raise_for_unsupported:
        | 为 True 时，将为不支持的消息类型抛出 `NotImplementedError` 异常
    :param bool run_async: 是否异步执行，为 True 时不堵塞线程


    ::

        my_groups = [group1, group2, group3 ...]

        @bot.register(my_groups, except_self=False)
        def sync_my_groups(msg):
            sync_message_in_groups(msg, my_groups)

    """

    def process():
        for group in groups:
            if group == msg.chat:
                continue

            msg.forward(
                chat=group, prefix=prefix, suffix=suffix,
                raise_for_unsupported=raise_for_unsupported
            )

    if prefix is None:
        if msg.sender == msg.bot.self:
            member = msg.chat.self
        else:
            member = msg.member

        if member.sex is MALE:
            member_prefix = '\U0001f454'
        elif member.sex is FEMALE:
            member_prefix = '\U0001f380'
        else:
            member_prefix = '\U0001f60e'

        prefix = '\U0001f504 · {}\n{} · {}\n'.format(
            msg.chat.name, member_prefix, member.name
        ) + '¯' * 20

    if run_async:
        Thread(target=process, daemon=True).start()
    else:
        process()
