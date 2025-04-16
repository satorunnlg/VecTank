# vectank/client.py

# multiprocessing.managers.BaseManager をインポートし、リモートのオブジェクトにアクセス可能なマネージャーを利用します。
from multiprocessing.managers import BaseManager
# VectorSimMethod は類似度計算方法の Enum で、タンク作成時に利用される可能性があります。
from .core import VectorSimMethod

# StoreManager クラスは BaseManager を継承し、リモートで管理される VectorStore オブジェクトへのアクセスを可能にします。
class StoreManager(BaseManager):
    pass  # 特にカスタムな処理は行わず、BaseManager の機能をそのまま利用します

# StoreManager に対して、リモートのサーバから取得できる 'get_store' 関数を登録します。
# これにより、クライアント側で get_store() を呼び出すと、サーバ側のストアオブジェクトが返されます。
StoreManager.register('get_store')

# TankClient クラスは、サーバ上の VecTank のストアに接続し、タンク操作を簡単に行えるクライアント機能を提供します。
class TankClient:
    def __init__(self, address=('localhost', 50000), authkey: bytes = b'secret'):
        """
        コンストラクタ

        引数:
          address (tuple): サーバのアドレスとポート番号のタプル (デフォルトは ('localhost', 50000))
          authkey (bytes): サーバとの認証に用いるキー (デフォルトは b'secret')
        """
        # 指定されたアドレスと認証キーを用いて StoreManager のインスタンスを作成します。
        self.manager = StoreManager(address=address, authkey=authkey)
        # サーバに接続します。
        self.manager.connect()
        # サーバ側から登録された 'get_store' を呼び出し、リモートのストアオブジェクトを取得します。
        self.store = self.manager.get_store()

    def get_tank(self, tank_name: str):
        """
        リモートストアから指定されたタンクを取得します。

        引数:
          tank_name (str): 取得したいタンク名

        戻り値:
          リモートタンクオブジェクト
        """
        return self.store.get_tank(tank_name)

    def create_tank(self, tank_name: str, dim: int, default_sim_method: VectorSimMethod, dtype, persist: bool = False):
        """
        リモートストアに新しいタンクを作成します。

        引数:
          tank_name (str): 作成するタンク名
          dim (int): タンク内のベクトルの次元数
          default_sim_method (VectorSimMethod): デフォルトの類似度計算方法
          dtype: 保存するベクトルのデータ型 (例: numpy.float32)
          persist (bool): タンクを永続化するかどうか (デフォルトは False)

        戻り値:
          作成されたタンクオブジェクトまたは作成結果
        """
        return self.store.create_tank(tank_name, dim, default_sim_method, dtype, persist)