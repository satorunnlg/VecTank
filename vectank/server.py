# vectank/server.py
from .db import VectorDB
from .core import VectorSimMethod
from multiprocessing.managers import BaseManager

class DBManager(BaseManager):
    pass

class VectorDBServer:
    def __init__(self, port: int = 50000, authkey: bytes = b'secret', save_file: str = None):
        self.db = VectorDB(save_file=save_file)
        self.port = port
        self.authkey = authkey

    def run(self):
        DBManager.register('get_db', callable=lambda: self.db)
        manager = DBManager(address=('', self.port), authkey=self.authkey)
        server = manager.get_server()
        print(f"VecTank サーバがポート {self.port} で起動中です。")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("サーバ停止前に各テーブルを保存中...")
            for table in self.db.tables.values():
                table.save_to_file()
            print("データ保存完了。")
