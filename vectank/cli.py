# vectank/cli.py
import argparse  # コマンドライン引数の解析用ライブラリ
import os          # ファイル存在チェック用のライブラリ
from vectank.server import TankServer  # サーバ機能の実装クラス (旧 VectorDBServer) をインポート
from vectank.core import VectorSimMethod  # 類似度計算方法の Enum をインポート
import numpy as np  # 数値計算ライブラリ

def main():
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

    # データの永続化に利用するファイル名のプレフィックスを指定する引数を追加
    parser.add_argument(
        "--save-file",
        type=str,
        default="vectank_data",
        help="保存用ファイル名のプレフィックス (デフォルト: 'vectank_data')"
    )

    # コマンドライン引数の解析を実行し、結果を args に格納
    args = parser.parse_args()

    # コマンドライン引数の値を利用して TankServer のインスタンスを作成
    # authkey はバイト型が必要なため、文字列から変換しています
    server = TankServer(
        port=args.port, 
        authkey=args.authkey.encode(), 
        save_file=args.save_file
    )

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

    # 永続化ファイルが存在する場合、デフォルトタンクのデータを読み込みます。
    # ここでは、ファイル名の規則として、"{save_file}_default_meta.pkl" と "{save_file}_default_vectors.npz" を用いています。
    default_meta_file = f"{args.save_file}_default_meta.pkl"
    default_vectors_file = f"{args.save_file}_default_vectors.npz"
    if os.path.exists(default_meta_file) and os.path.exists(default_vectors_file):
        print("永続化ファイルが見つかりました。データを読み込みます...")
        default_tank.load_from_file()
    else:
        print("永続化ファイルが見つかりません。新規作成します。")

    # サーバを起動する
    # このメソッドはブロッキング呼び出しとなり、サーバが停止するまで実行が継続します
    server.run()

if __name__ == '__main__':
    # このスクリプトが直接実行された場合、main() 関数を呼び出してサーバを起動します
    main()
