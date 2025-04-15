# vectank/server.py

from .store import VectorStore  # VectorStore クラスをインポートし、ストア（タンク管理機能）の操作を実現
from .core import VectorSimMethod  # 類似度計算方法の Enum をインポート
from multiprocessing.managers import BaseManager  # リモートオブジェクトへのアクセスを可能とする BaseManager をインポート

# StoreManager クラスは BaseManager を継承し、リモートアクセス用の管理クラスとして定義します。
class StoreManager(BaseManager):
    pass  # カスタムな振る舞いは特になく、基本機能のみ利用

# TankServer クラスは、VecTank サーバーを起動してリモートからのストア操作を提供します。
class TankServer:
    def __init__(self, port: int = 50000, authkey: bytes = b'secret', save_file: str = None):
        """
        コンストラクタ

        引数:
          port (int): サーバがリッスンするポート番号 (デフォルト: 50000)
          authkey (bytes): サーバとの通信を認証するためのキー (デフォルト: b'secret')
          save_file (str): オプション。データ永続化に使用するファイル名またはパス

        内部状態:
          store (VectorStore): VectorStore のインスタンス、タンクの管理を行います。
          port (int): 指定されたポート番号
          authkey (bytes): 指定された認証キー
        """
        # VectorStore のインスタンスを生成。save_file が指定されていれば永続化用に利用
        self.store = VectorStore(save_file=save_file)
        # ポート番号を設定
        self.port = port
        # 認証用のバイト型キーを設定
        self.authkey = authkey

    def run(self):
        """
        サーバーを起動し、リモートクライアントからの接続を待ち受けます。
        
        処理内容:
          - StoreManager に get_store 関数を登録して、リモート側からストアオブジェクトを取得可能にします。
          - 指定されたポートと認証キーでサーバーを開始し、永久に接続を待ち受けます。
          - KeyboardInterrupt が発生した場合、各タンクのデータを保存して終了します。
        """
        # StoreManager に 'get_store' 名で、現在の VectorStore インスタンスを返す関数を登録
        StoreManager.register('get_store', callable=lambda: self.store)
        # 指定されたアドレス（空文字は全てのインターフェースでのバインドを意味する）とポート番号、
        # 認証キーを用いて StoreManager のインスタンスを生成
        manager = StoreManager(address=('', self.port), authkey=self.authkey)
        # サーバーオブジェクトを生成（serve_forever メソッドで接続待ち状態に入る）
        server = manager.get_server()
        # サーバー起動のメッセージを表示
        print(f"VecTank サーバがポート {self.port} で起動中です。")
        try:
            # サーバーを永久に起動。クライアントからの接続要求を処理します。
            server.serve_forever()
        except KeyboardInterrupt:
            # ユーザーによる割り込み（Ctrl+C 等）でサーバー停止した場合の処理
            print("サーバ停止前に各タンクを保存中...")
            # データ永続化のため、全タンクの save_to_file メソッドを呼び出し、ファイルに保存する
            for tank in self.store.tanks.values():
                tank.save_to_file()
            print("データ保存完了。")
