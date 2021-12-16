from bson import ObjectId

from app.utils.datetime import get_utc_now
from tests.test_helper import get_random_str

order_in_db_data = {
    "_id": ObjectId(),
    "symbol": "601328",
    "exchange": "1",
    "symbol_name": "交通银行",
    "order_id": "60137436d77141c19bd22587",
    "fund_id": "6013726ed77141c19bd22586",
    "status": "4",
    "finished_quantity": 1000,
    "average_price": 4.48,
    "quantity": 1000,
    "operator": "buy",
    "price": 4.48,
    "created_at": "2021-01-29T02:34:30.091+0000",
    "updated_at": "2021-01-29T02:34:30.091+0000",
    "username": "18706738141",
    "task": None,
    "portfolio": ObjectId(),
    "create_datetime": get_utc_now(),
    "end_datetime": "2021-01-29T10:34:30.000+0000",
    "id": ObjectId(),
}

order_base_data = {
    "symbol": "601328",
    "exchange": "1",
    "order_id": str(ObjectId()),
    "fund_id": str(ObjectId()),
    "status": "0",
    "finished_quantity": 1000,
    "average_price": 10,
    "quantity": 1000,
    "operator": "buy",
    "price": 10,
}

order_in_create_data = {
    "symbol": "601328",
    "exchange": "1",
    "order_id": str(ObjectId()),
    "fund_id": str(ObjectId()),
    "status": "0",
    "finished_quantity": 1000,
    "average_price": 10,
    "quantity": 1000,
    "operator": "buy",
    "price": 10,
    "username": get_random_str(),
    "task": get_random_str(),
    "portfolio": str(ObjectId()),
}
