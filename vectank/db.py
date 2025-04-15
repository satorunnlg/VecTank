# vectank/db.py

from .table import VectorTable  # VectorTable クラスをインポートし、テーブル管理機能を利用します。
from .core import VectorSimMethod  # 類似度計算方法の Enum をインポートします。
import numpy as np  # 数値計算ライブラリ NumPy をインポート

class VectorDB:
    def __init__(self, save_file: str = None):
        """
        コンストラクタ
        
        引数:
          save_file (str): オプション。データ永続化に使用するファイル名またはパス。
        
        内部状態:
          tables (dict): 各テーブル名と対応する VectorTable オブジェクトを管理する辞書。
          save_file (str): 引数で指定された永続化用ファイル名またはパス。
        """
        # テーブルを管理するための辞書。キー: テーブル名, 値: VectorTable オブジェクト
        self.tables = {}
        # 永続化に利用するファイル名またはパスを保持
        self.save_file = save_file

    def create_table(self, table_name: str, dim: int,
                     default_sim_method: VectorSimMethod,
                     dtype: np.dtype):
        """
        新しいテーブルを作成し、データベースに登録します。
        
        引数:
          table_name (str): 作成するテーブルの名前
          dim (int): テーブル内の各ベクトルの次元数
          default_sim_method (VectorSimMethod): デフォルトの類似度計算方法
          dtype (np.dtype): 保存するベクトルのデータ型 (例: numpy.float32)
        
        戻り値:
          作成された VectorTable オブジェクト
        
        例外:
          テーブル名が既に存在する場合、ValueError を送出します。
        """
        # 同名のテーブルが既に存在するかチェック
        if table_name in self.tables:
            raise ValueError(f"テーブル {table_name} は既に存在します。")
        # 新しい VectorTable オブジェクトを作成
        table = VectorTable(table_name, dim, default_sim_method, dtype, self.save_file)
        # 作成したテーブルを内部の辞書に登録
        self.tables[table_name] = table
        # 作成したテーブルオブジェクトを返す
        return table

    def get_table(self, table_name: str):
        """
        指定されたテーブル名に対応するテーブルを取得します。
        
        引数:
          table_name (str): 取得したいテーブルの名前
        
        戻り値:
          対応する VectorTable オブジェクト
        
        例外:
          テーブルが存在しない場合、KeyError を送出します。
        """
        # テーブルが存在するかチェック
        if table_name not in self.tables:
            raise KeyError(f"テーブル {table_name} は存在しません。")
        # 存在するテーブルを返す
        return self.tables[table_name]

    def drop_table(self, table_name: str):
        """
        指定されたテーブルをデータベースから削除します。
        
        引数:
          table_name (str): 削除するテーブルの名前
          
        処理:
          テーブルが存在する場合は、内部管理辞書から削除します。
        """
        if table_name in self.tables:
            # 辞書からテーブルを削除
            del self.tables[table_name]

    def list_tables(self):
        """
        登録されている全てのテーブル名の一覧を返します。
        
        戻り値:
          テーブル名のリスト
        """
        return list(self.tables.keys())
