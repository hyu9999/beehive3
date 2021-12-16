class StockBasic:
    symbol_name = "测试股票"
    precision = 2
    min_unit = 100


class MockRedisOperatorStock:

    @staticmethod
    async def get_stock_price(*args, **kwargs):
        """
        app.crud.stock.get_stock_basic
        """
        return [{"current": "10"}]

    @staticmethod
    async def get_stock_basic(*args, **kwargs):
        """
        app.crud.stock.get_stock_basic
        """
        return StockBasic
