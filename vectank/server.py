# vectank/server.py

import logging
import socketserver
from multiprocessing.managers import BaseManager
from .store import VectorStore  # タンク管理機能を提供する VectorStore クラスをインポート
from .core import VectorSimMethod  # 類似度計算方式 Enum をインポート

# カスタム TCP サーバクラス（アドレス再利用を許可）:
class LoggingTCPServer(socketserver.TCPServer):
    allow_reuse_address = True
    def verify_request(self, request, client_address):
        logging.info(f"Accepted connection from {client_address}")
        return super().verify_request(request, client_address)

# LoggingStoreManager は BaseManager を継承し、内部サーバクラスを LoggingTCPServer に置き換えます。
class LoggingStoreManager(BaseManager):
    pass

# BaseManager で使用される内部サーバを LoggingTCPServer に変更
LoggingStoreManager._Server = LoggingTCPServer

# get_store() の呼び出し時に操作ログを出力するためのラッパー関数
def get_store_wrapper(store):
    def wrapped_get_store():
        logging.info("Remote operation: get_store() が呼び出されました。")
        return store
    return wrapped_get_store

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
        # VectorStore のインスタンスを生成。save_file が指定されれば永続化に利用
        self.store = VectorStore(save_file=save_file)
        self.port = port
        self.authkey = authkey

    def run(self):
        """
        サーバーを起動し、リモートクライアントからの接続と操作要求を待ち受けます。
        
        処理内容:
          - LoggingStoreManager に、リモート呼び出し時に操作ログを出力する
            get_store() ラッパーを登録します。
          - 指定されたポートと認証キーでサーバーを起動し、
            永久に接続要求を待ち受けます。
          - KeyboardInterrupt 発生時、各タンクのデータを保存して終了します。
        """
        # get_store() 呼び出し時に操作ログを出力するラッパー関数で登録
        LoggingStoreManager.register('get_store', callable=get_store_wrapper(self.store))
        manager = LoggingStoreManager(address=('', self.port), authkey=self.authkey)
        server = manager.get_server()
        logging.info(f"VecTank サーバがポート {self.port} で起動中です。")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info("サーバ停止前に各タンクを保存中...")
            for tank in self.store.tanks.values():
                tank.save_to_file()
            logging.info("データ保存完了。")
