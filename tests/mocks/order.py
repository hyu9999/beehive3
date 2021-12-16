class MockPutOrder:
    """
    app.service.orders.order_trade_put.PutOrder
    """
    @staticmethod
    def is_trade_time():
        return True

    @staticmethod
    async def check_trade_time():
        pass

    @staticmethod
    async def put_order():
        pass
