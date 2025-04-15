# vectank/cli.py
import argparse  # コマンドライン引数の解析用ライブラリ
from vectank.server import VectorDBServer  # サーバ機能の実装クラスをインポート
from vectank.core import VectorSimMethod  # 類似度計算方法の Enum をインポート
import numpy as np  # 数値計算ライブラリ

def main():
    # argparse を利用してコマンドラインからの引数を解析するパーサーを作成
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

    # コマンドライン引数の値を利用して VecTank サーバのインスタンスを作成
    # authkey はバイト型が必要なため、文字列から変換しています
    server = VectorDBServer(
        port=args.port, 
        authkey=args.authkey.encode(), 
        save_file=args.save_file
    )

    # サーバ起動時にデフォルトテーブルを作成
    # テーブル名は "default"、ベクトルの次元数は 1200、
    # 類似度計算にはコサイン類似度 (COSINE) を使用し、
    # データ型は numpy の float32 を指定しています
    server.db.create_table(
        "default", 
        dim=1200, 
        default_sim_method=VectorSimMethod.COSINE, 
        dtype=np.float32
    )

    # サーバを起動する
    # このメソッドはブロッキング呼び出しとなり、サーバが停止するまで実行が継続します
    server.run()

if __name__ == '__main__':
    # このスクリプトが直接実行された場合、main() 関数を呼び出してサーバを起動します
    main()
