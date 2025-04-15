# vectank/cli.py
import argparse      # コマンドライン引数解析用
import os            # ファイル存在チェック用
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

    # データ永続化に利用するファイル名のプレフィックスを指定する引数を追加
    parser.add_argument(
        "--save-file",
        type=str,
        default="vectank_data",
        help="保存用ファイル名のプレフィックス (デフォルト: 'vectank_data')"
    )

    # コマンドライン引数の解析を実行し、結果を args に格納
    args = parser.parse_args()

    logging.info("コマンドライン引数の解析が完了しました。")

    # コマンドライン引数の値を利用して TankServer のインスタンスを作成
    # authkey はバイト型が必要なため、文字列からエンコードして変換しています
    server = TankServer(
        port=args.port, 
        authkey=args.authkey.encode(), 
        save_file=args.save_file
    )
    logging.info("TankServer のインスタンスが作成されました。")

    # サーバ起動時にデフォルトタンク "default" を作成
    # タンク名は "default"、ベクトルの次元数は 1200、
    # 類似度計算にはコサイン類似度 (COSINE) を使用し、
    # データ型は numpy の float32 を指定しています
    default_tank = server.store.create_tank(
        "default", 
        dim=1200, 
        default_sim_method=VectorSimMethod.COSINE, 
        dtype=np.float32
    )
    logging.info("デフォルトタンク 'default' を作成しました。")

    # 永続化ファイルが存在する場合、デフォルトタンクのデータを読み込みます。
    # ファイル名は "{save_file}_default_meta.pkl" および "{save_file}_default_vectors.npz" の規則でチェック
    default_meta_file = f"{args.save_file}_default_meta.pkl"
    default_vectors_file = f"{args.save_file}_default_vectors.npz"
    if os.path.exists(default_meta_file) and os.path.exists(default_vectors_file):
        logging.info("永続化ファイルが見つかりました。データを読み込みます...")
        default_tank.load_from_file()
    else:
        logging.info("永続化ファイルが見つかりません。新規作成します。")

    # サーバ起動開始
    logging.info("サーバを起動します。")
    server.run()

if __name__ == '__main__':
    main()
