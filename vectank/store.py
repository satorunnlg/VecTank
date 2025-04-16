# vectank/store.py

from .tank import VectorTank  # VectorTank クラスをインポートし、タンク管理機能を利用します。
from .core import VectorSimMethod  # 類似度計算方法の Enum をインポートします。
import numpy as np  # 数値計算ライブラリ NumPy をインポート

class VectorStore:
    def __init__(self, save_file: str = None):
        """
        コンストラクタ

        引数:
          save_file (str): オプション。データ永続化に使用するファイル名またはパス。

        内部状態:
          tanks (dict): 各タンク名と対応する VectorTank オブジェクトを管理する辞書。
          save_file (str): 引数で指定された永続化用ファイル名またはパス。
        """
        # タンクを管理するための辞書。キー: タンク名, 値: VectorTank オブジェクト
        self.tanks = {}
        # 永続化に利用するファイル名またはパスを保持
        self.save_file = save_file

    def create_tank(self, tank_name: str, dim: int,
                    default_sim_method: VectorSimMethod,
                    dtype: np.dtype):
        """
        新しいタンクを作成し、ストアに登録します。

        引数:
          tank_name (str): 作成するタンクの名前
          dim (int): タンク内の各ベクトルの次元数
          default_sim_method (VectorSimMethod): デフォルトの類似度計算方法
          dtype (np.dtype): 保存するベクトルのデータ型 (例: numpy.float32)

        戻り値:
          作成された VectorTank オブジェクト

        例外:
          タンク名が既に存在する場合、ValueError を送出します。
        """
        # 同名のタンクが既に存在するかチェック
        if tank_name in self.tanks:
            raise ValueError(f"タンク {tank_name} は既に存在します。")
        # 新しい VectorTank オブジェクトを作成
        tank = VectorTank(tank_name, dim, default_sim_method, dtype, self.save_file)
        # 作成したタンクを内部の辞書に登録
        self.tanks[tank_name] = tank
        # 作成したタンクオブジェクトを返す
        return tank

    def get_tank(self, tank_name: str):
        """
        指定されたタンク名に対応するタンクを取得します。

        引数:
          tank_name (str): 取得したいタンクの名前

        戻り値:
          対応する VectorTank オブジェクト。存在しない場合は None を返します。
        """
        # タンクが存在するかチェック
        if tank_name not in self.tanks:
            return None
        # 存在するタンクを返す
        return self.tanks[tank_name]

    def drop_tank(self, tank_name: str):
        """
        指定されたタンクをストアから削除します。

        引数:
          tank_name (str): 削除するタンクの名前

        処理:
          タンクが存在する場合は、内部管理辞書から削除します。
        """
        if tank_name in self.tanks:
            # 辞書からタンクを削除
            del self.tanks[tank_name]

    def list_tanks(self):
        """
        登録されている全てのタンク名の一覧を返します。

        戻り値:
          タンク名のリスト
        """
        return list(self.tanks.keys())
