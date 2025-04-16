# vectank/store.py

import os
from .tank import VectorTank  # VectorTank クラスをインポートし、タンク管理機能を利用します。
from .core import VectorSimMethod  # 類似度計算方法の Enum をインポートします。
import numpy as np  # 数値計算ライブラリ NumPy をインポート

class VectorStore:
    def __init__(self, store_dir: str = None):
        """
        コンストラクタ

        引数:
          store_dir (str): オプション。データ永続化に使用するディレクトリ。
                           指定がなければカレントディレクトリを利用します。
        内部状態:
          tanks (dict): 各タンク名と対応する VectorTank オブジェクトを管理する辞書。
          store_dir (str): 永続化に利用するディレクトリ。
        """
        self.tanks = {}
        self.store_dir = store_dir if store_dir is not None else os.getcwd()

    def create_tank(self, tank_name: str, dim: int,
                    default_sim_method: VectorSimMethod,
                    dtype: np.dtype,
                    persist: bool = False):
        """
        新しいタンクを作成し、ストアに登録します。

        引数:
          tank_name (str): 作成するタンクの名前
          dim (int): タンク内の各ベクトルの次元数
          default_sim_method (VectorSimMethod): デフォルトの類似度計算方法
          dtype (np.dtype): 保存するベクトルのデータ型 (例: numpy.float32)
          persist (bool, オプション): 永続化を有効にするかどうか (デフォルト: False)

        戻り値:
          作成された VectorTank オブジェクト

        例外:
          タンク名が既に存在する場合、ValueError を送出します。
        """
        # 同名のタンクが既に存在するかチェック
        if tank_name in self.tanks:
            raise ValueError(f"タンク {tank_name} は既に存在します。")
        # persist が True の場合、store_dir の下にタンク名でファイル出力するパスを指定
        if persist:
            if not os.path.exists(self.store_dir):
                os.makedirs(self.store_dir)
            persistence_path = os.path.join(self.store_dir, tank_name)
        else:
            persistence_path = None
        # 新しい VectorTank オブジェクトを作成
        tank = VectorTank(tank_name, dim, default_sim_method, dtype, persist, persistence_path)
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
        if tank_name not in self.tanks:
            return None
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
            del self.tanks[tank_name]

    def list_tanks(self):
        """
        登録されている全てのタンク名の一覧を返します。

        戻り値:
          タンク名のリスト
        """
        return list(self.tanks.keys())
