# vectank/client.py

# multiprocessing.managers.BaseManager をインポートし、リモートのオブジェクトにアクセス可能なマネージャーを利用します。
from multiprocessing.managers import BaseManager
# VectorSimMethod は類似度計算方法の Enum で、テーブル作成時に利用される可能性があります。
from .core import VectorSimMethod

# DBManager クラスは BaseManager を継承し、リモートで管理される VectorDB オブジェクトへのアクセスを可能にします。
class DBManager(BaseManager):
    pass  # 特にカスタムな処理は行わず、BaseManager の機能をそのまま利用します

# DBManager に対して、リモートのサーバから取得できる 'get_db' 関数を登録します。
# これにより、クライアント側で get_db() を呼び出すと、サーバ側のデータベースオブジェクトが返されます。
DBManager.register('get_db')

# VectorDBClient クラスは、サーバ上の VecTank のデータベースに接続し、テーブル操作を簡単に行えるクライアント機能を提供します。
class VectorDBClient:
    def __init__(self, address=('localhost', 50000), authkey: bytes = b'secret'):
        """
        コンストラクタ

        引数:
          address (tuple): サーバのアドレスとポート番号のタプル (デフォルトは ('localhost', 50000))
          authkey (bytes): サーバとの認証に用いるキー (デフォルトは b'secret')
        """
        # 指定されたアドレスと認証キーを用いて DBManager のインスタンスを作成します。
        self.manager = DBManager(address=address, authkey=authkey)
        # サーバに接続します。
        self.manager.connect()
        # サーバ側から登録された 'get_db' を呼び出し、リモートのデータベースオブジェクトを取得します。
        self.db = self.manager.get_db()

    def get_table(self, table_name: str):
        """
        リモートデータベースから指定されたテーブルを取得します。

        引数:
          table_name (str): 取得したいテーブル名

        戻り値:
          リモートテーブルオブジェクト
        """
        return self.db.get_table(table_name)

    def create_table(self, table_name: str, dim: int, default_sim_method: VectorSimMethod, dtype):
        """
        リモートデータベースに新しいテーブルを作成します。

        引数:
          table_name (str): 作成するテーブル名
          dim (int): テーブル内のベクトルの次元数
          default_sim_method (VectorSimMethod): デフォルトの類似度計算方法
          dtype: 保存するベクトルのデータ型 (例: numpy.float32)

        戻り値:
          作成されたテーブルオブジェクトまたは作成結果
        """
        return self.db.create_table(table_name, dim, default_sim_method, dtype)
