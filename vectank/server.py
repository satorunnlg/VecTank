# vectank/server.py

from .db import VectorDB       # VectorDB クラスをインポートし、データベースの操作を実現
from .core import VectorSimMethod  # 類似度計算方法の Enum をインポート
from multiprocessing.managers import BaseManager  # リモートオブジェクトへのアクセスを可能とする BaseManager をインポート

# DBManager クラスは BaseManager を継承し、リモートアクセス用の管理クラスとして定義します。
class DBManager(BaseManager):
    pass  # カスタムな振る舞いは特になく、基本機能のみ利用

# VectorDBServer クラスは、VecTank サーバーを起動してリモートからのデータベース操作を提供します。
class VectorDBServer:
    def __init__(self, port: int = 50000, authkey: bytes = b'secret', save_file: str = None):
        """
        コンストラクタ

        引数:
          port (int): サーバがリッスンするポート番号 (デフォルト: 50000)
          authkey (bytes): サーバとの通信を認証するためのキー (デフォルト: b'secret')
          save_file (str): オプション。データ永続化に使用するファイル名またはパス

        内部状態:
          db (VectorDB): VectorDB のインスタンス、テーブルの管理を行います。
          port (int): 指定されたポート番号
          authkey (bytes): 指定された認証キー
        """
        # VectorDB のインスタンスを生成。save_file が指定されていれば永続化用に利用
        self.db = VectorDB(save_file=save_file)
        # ポート番号を設定
        self.port = port
        # 認証用のバイト型キーを設定
        self.authkey = authkey

    def run(self):
        """
        サーバーを起動し、リモートクライアントからの接続を待ち受けます。
        
        処理内容:
          - DBManager に get_db 関数を登録して、リモート側からデータベースオブジェクトを取得可能にします。
          - 指定されたポートと認証キーでサーバーを開始し、永久に接続を待ち受けます。
          - KeyboardInterrupt が発生した場合、各テーブルのデータを保存して終了します。
        """
        # DBManager に 'get_db' 名で、現在の VectorDB インスタンスを返す関数を登録
        DBManager.register('get_db', callable=lambda: self.db)
        # 指定されたアドレス（空文字は全てのインターフェースでのバインドを意味する）とポート番号、
        # 認証キーを用いて DBManager のインスタンスを生成
        manager = DBManager(address=('', self.port), authkey=self.authkey)
        # サーバーオブジェクトを生成（serve_forever メソッドで接続待ち状態に入る）
        server = manager.get_server()
        # サーバー起動のメッセージを表示
        print(f"VecTank サーバがポート {self.port} で起動中です。")
        try:
            # サーバーを永久に起動。クライアントからの接続要求を処理します。
            server.serve_forever()
        except KeyboardInterrupt:
            # ユーザーによる割り込み（Ctrl+C 等）でサーバー停止した場合の処理
            print("サーバ停止前に各テーブルを保存中...")
            # データ永続化のため、全テーブルの save_to_file メソッドを呼び出し、ファイルに保存する
            for table in self.db.tables.values():
                table.save_to_file()
            print("データ保存完了。")
