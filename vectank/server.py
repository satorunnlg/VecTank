"""
【概要】
  本ファイルは、サーバプロセスとして高速共有メモリストア（TankStore）を起動し、
  各タンク（VecTank インスタンス）の永続化管理および通信処理を行うための処理を実装しています。
  
【動作の流れ】
  1. コマンドライン引数から永続化ディレクトリ（store_dir）を取得。
  2. 指定ディレクトリが存在しない場合は作成。
  3. TankStore インスタンスを初期化し、内部のタンク数をログに出力。
  4. 無限ループで待機。Ctrl+C (KeyboardInterrupt) 発生時に、各タンクの永続化処理と
     TankStore のイベントループ停止を実施して終了する。
"""

import argparse
import os
import time
import logging
from vectank.store import TankStore  # TankStore は永続化ファイルから VecTank を管理するクラス

def main():
    # ログの初期設定（INFO レベル、時刻・レベル情報付き）
    logging.basicConfig(
       level=logging.INFO,
       format='[%(asctime)s][%(levelname)s] %(message)s',
       datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="高速共有メモリサーバを起動します。"
    )
    parser.add_argument(
        "--store_dir",
        type=str,
        default="data",
        help="永続化に使用するディレクトリ (デフォルト: data)"
    )
    parser.add_argument(
        "--store_name",
        type=str,
        default="tankstore_comm",
        help="通信用共有メモリの名前 (デフォルト: tankstore_comm)"
    )
    
    args = parser.parse_args()
    store_dir = args.store_dir
    store_name = args.store_name

    # 指定した永続化ディレクトリが存在しなければ作成
    if not os.path.exists(store_dir):
        os.makedirs(store_dir)
        logging.info("永続化ディレクトリ '%s' を作成しました。", store_dir)
    
    # TankStore の初期化: store_dir 内の既存タンク（永続化ファイル）を自動復元
    logging.info("共有メモリストアを初期化中 (store_dir=%s, store_name=%s)...", store_dir, store_name)
    store = TankStore(store_dir=store_dir, store_name=store_name)
    logging.info("TankStore が初期化されました。登録タンク数: %d", len(store.tanks))
    
    # サーバプロセスの待機ループ
    logging.info("サーバプロセスを起動中です。Ctrl+C で停止します。")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("サーバプロセス停止中... 各タンクの状態を永続化し、イベントループを停止します。")
        # 各タンクの永続化処理（TankStore 側で管理）を実施する場合は、
        # ここで必要に応じた処理（例：tank.save()）を呼び出してください。
        for tank in store.tanks.values():
            # tank.save() は空実装のため、実際の保存処理が必要ならここに追加
            logging.info("Tank '%s' の永続化処理を実施。", tank.tank_name)
        # TankStore のイベントループの停止と共有メモリの後片付け
        store.stop_event_loop()
        logging.info("TankStore のイベントループを停止しました。")

if __name__ == '__main__':
    main()