# vectank/db.py
from .table import VectorTable
from .core import VectorSimMethod
import numpy as np

class VectorDB:
    def __init__(self, save_file: str = None):
        self.tables = {}
        self.save_file = save_file

    def create_table(self, table_name: str, dim: int,
                     default_sim_method: VectorSimMethod,
                     dtype: np.dtype):
        if table_name in self.tables:
            raise ValueError(f"テーブル {table_name} は既に存在します。")
        table = VectorTable(table_name, dim, default_sim_method, dtype, self.save_file)
        self.tables[table_name] = table
        return table

    def get_table(self, table_name: str):
        if table_name not in self.tables:
            raise KeyError(f"テーブル {table_name} は存在しません。")
        return self.tables[table_name]

    def drop_table(self, table_name: str):
        if table_name in self.tables:
            del self.tables[table_name]

    def list_tables(self):
        return list(self.tables.keys())
