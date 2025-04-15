# vectank/cli.py
import argparse      # コマンドライン引数解析用
import os            # ファイル存在チェック用（※旧仕様向けのコメント）
import logging       # ログ出力用
from vectank.server import TankServer  # サーバ機能の実装クラス
from vectank.core import VectorSimMethod # 類似度計算方式の Enum
import numpy as np   # 数値計算ライブラリ

def main():
    # ログ設定。INFO レベル以上のメッセージを出力し、時刻情報を付加する
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # argparse を利用してコマンドライン引数を解析するパーサーを作成
    parser = argparse.ArgumentParser(
        description="VecTank サーバを起動します。"
    )

    # サーバがリッスンするポート番号を指定する引数を追加
    parser.add_argument(
        "--port",
        type=int,
        default=50000,
        help="サーバのポート番号 (デフォルト: 50000)"
    )

    # サーバとの通信で認証に用いる認証キーを指定する引数を追加
    parser.add_argument(
        "--authkey",
        type=str,
        default="secret",
        help="サーバの認証キー (デフォルト: 'secret')"
    )

    # 旧仕様ではデフォルトタンク "default" を生成していましたが、今回の仕様では生成しません。

    # コマンドライン引数の解析を実行し、結果を args に格納
    args = parser.parse_args()

    logging.info("コマンドライン引数の解析が完了しました。")

    # コマンドライン引数の値を利用して TankServer のインスタンスを作成
    # authkey はバイト型が必要なため、文字列からエンコードして変換しています
    server = TankServer(
        port=args.port, 
        authkey=args.authkey.encode()
    )
    logging.info("TankServer のインスタンスが作成されました。")

    # defaultタンクの生成は行わず、必要に応じたタンクはシステム起動後に作成してください。

    # サーバ起動開始
    logging.info("サーバを起動します。")
    server.run()

if __name__ == '__main__':
    main()
