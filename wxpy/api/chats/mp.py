# coding: utf-8

from .user import User


class MP(User):
    """
    公众号对象
    """
    pass


class Service(MP):
    """
    服务号对象
    """
    pass


class Subscription(MP):
    """
    订阅号对象
    """
    pass
