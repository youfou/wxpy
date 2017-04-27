class ResponseError(Exception):
    """
    当 BaseResponse 的返回值不为 0 时抛出的异常
    """

    @property
    def err_code(self):
        return self.args[0].get('err_code')

    @property
    def err_msg(self):
        return self.args[0].get('err_msg')
