# vectank/cli.py
import argparse      # コマンドライン引数解析用
import os            # ファイル存在チェック用
import logging       # ログ出力用
from vectank.server import TankServer  # サーバ機能の実装クラス
from vectank.core import VectorSimMethod # 類似度計算方式の Enum
import numpy as np   # 数値計算ライブラリ

def main():
    # ログ設定（INFO レベル以上、時刻情報付き）
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # argparse による引数解析の準備
    parser = argparse.ArgumentParser(
        description="VecTank サーバを起動します。"
    )
    
    # サーバのポート番号指定
    parser.add_argument(
        "--port",
        type=int,
        default=50000,
        help="サーバのポート番号 (デフォルト: 50000)"
    )
    
    # 認証キーの指定
    parser.add_argument(
        "--authkey",
        type=str,
        default="secret",
        help="サーバの認証キー (デフォルト: 'secret')"
    )
    
    # 永続化に使用するストアディレクトリの指定
    parser.add_argument(
        "--store_dir",
        type=str,
        default=None,
        help="データ永続化に使用するディレクトリ (指定しない場合はカレントディレクトリ)"
    )
    
    args = parser.parse_args()
    logging.info("コマンドライン引数の解析が完了しました。")
    
    # TankServer インスタンスの生成（store_dir を引数として渡す）
    server = TankServer(
        port=args.port, 
        authkey=args.authkey.encode(),
        store_dir=args.store_dir
    )
    logging.info("TankServer のインスタンスが作成されました。")
    
    # サーバ起動
    logging.info("サーバを起動します。")
    server.run()

if __name__ == '__main__':
    main()
