# vectank/cli.py
import argparse
from vectank.server import VectorDBServer
from vectank.core import VectorSimMethod
import numpy as np

def main():
    parser = argparse.ArgumentParser(
        description="VecTank サーバを起動します。"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=50000,
        help="サーバのポート番号 (デフォルト: 50000)"
    )
    parser.add_argument(
        "--authkey",
        type=str,
        default="secret",
        help="サーバの認証キー (デフォルト: 'secret')"
    )
    parser.add_argument(
        "--save-file",
        type=str,
        default="vectank_data",
        help="保存用ファイル名のプレフィックス (デフォルト: 'vectank_data')"
    )
    args = parser.parse_args()

    # サーバインスタンスの作成
    server = VectorDBServer(
        port=args.port, 
        authkey=args.authkey.encode(), 
        save_file=args.save_file
    )
    # サーバ起動時にデフォルトテーブルを作成（必要に応じて）
    server.db.create_table(
        "default", 
        dim=1200, 
        default_sim_method=VectorSimMethod.COSINE, 
        dtype=np.float32
    )
    # サーバの起動
    server.run()

if __name__ == '__main__':
    main()
