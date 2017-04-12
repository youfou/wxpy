import logging

from wxpy.utils import handle_response
from .user import User

logger = logging.getLogger(__name__)


class Friend(User):
    """
    好友对象
    """

    @handle_response()
    def set_remark_name(self, remark_name):
        """
        设置或修改好友的备注名称

        :param remark_name: 新的备注名称
        """

        logger.info('setting remark name for {}: {}'.format(self, remark_name))

        return self.bot.core.set_alias(userName=self.user_name, alias=str(remark_name))
