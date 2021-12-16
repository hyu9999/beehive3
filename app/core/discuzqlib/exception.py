class DiscuzqError(Exception):
    """
    Discuzq的自定义异常
    """
    def __init__(self, err):
        self.err = err
        self.message = str(err)

