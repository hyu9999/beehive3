from pymongo import MongoClient

from app import settings


class MongoUtils:
    def __init__(self):
        db_param = {
            "host": settings.db.MONGO_HOST,
            "port": settings.db.MONGO_PORT,
            "username": settings.db.MONGO_USER,
            "password": settings.db.MONGO_PASS,
            "connect": False,
        }
        self.client = MongoClient(**db_param)

        self.db = self.client[settings.db.DB_NAME]

    def query(self, table_name, filters=None):
        filters = filters or {}
        collection = self.db[table_name]
        data = collection.find(filters)
        return data

    def get(self, table_name, filters=None):
        filters = filters or {}
        collection = self.db[table_name]
        ret_data = collection.find_one(filters)
        return ret_data

    def create(self, table_name, filters):
        collection = self.db[table_name]
        ret_data = collection.insert_one(filters)
        return ret_data

    def update(self, table_name, filters, params):
        collection = self.db[table_name]
        ret_data = collection.update_one(filters, params)
        return ret_data

    def batch_update(self, table_name, batch_list, order=True):
        collection = self.db[table_name]
        ret_data = collection.bulk_write(batch_list, ordered=order)
        return ret_data

    def batch_create(self, table_name, batch_list):
        collection = self.db[table_name]
        ret_data = collection.insert_many(batch_list)
        return ret_data

    def count(self, table_name, filters, **kwargs):
        collection = self.db[table_name]
        ret_data = collection.count_documents(filters, **kwargs)
        return ret_data

    def close(self):
        self.client.close()


mongo_util = MongoUtils()
