# vectank/client.py
from multiprocessing.managers import BaseManager
from .core import VectorSimMethod

class DBManager(BaseManager):
    pass

DBManager.register('get_db')

class VectorDBClient:
    def __init__(self, address=('localhost', 50000), authkey: bytes = b'secret'):
        self.manager = DBManager(address=address, authkey=authkey)
        self.manager.connect()
        self.db = self.manager.get_db()

    def get_table(self, table_name: str):
        return self.db.get_table(table_name)

    def create_table(self, table_name: str, dim: int, default_sim_method: VectorSimMethod, dtype):
        return self.db.create_table(table_name, dim, default_sim_method, dtype)
