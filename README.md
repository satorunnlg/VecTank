# VecTank

[![Build Status](https://github.com/satorunnlg/VecTank/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/satorunnlg/VecTank/actions)
[![Coverage Status](https://coveralls.io/repos/github/satorunnlg/VecTank/badge.svg?branch=main)](https://coveralls.io/github/satorunnlg/VecTank?branch=main)
[![PyPI version](https://badge.fury.io/py/VecTank.svg)](https://badge.fury.io/py/VecTank)

VecTank は、軽量で高速なベクトル検索を実現するライブラリです。  
内部実装は NumPy を活用しており、大量のベクトルデータの追加、検索、更新、削除、永続化を効率的に行うことができます。また、複数のタンク（コレクション）を管理でき、用途に合わせた設定が可能です。

---

## 特徴

- **高速ベクトル検索**  
  - NumPy の一括演算による計算で、リアルタイム検索を実現。
  - 内積、コサイン類似度、ユークリッド距離など複数の類似度計算方式に対応。

- **柔軟なタンク管理**  
  - `VecTank` クラスにより、各タンクごとに次元数、データ型、デフォルトの計算方式を個別に設定可能。
  - `TankStore` クラスで複数のタンクを一元管理できます。

- **データ永続化機能**  
  - ベクトルデータは `.npz` 形式、メタデータは `pickle` 形式で保存。
  - サーバ停止前に自動保存する仕組みを備えています。

- **サーバ／クライアント通信**  
  - シンプルな API で、CLI 経由のサーバ起動やクライアントからの接続をサポート。
  - サーバ（`vectank-run` コマンド経由で起動）と、クライアント（`TankClient`）を利用し簡単な操作が可能です。

- **一括登録機能**  
  - 単一および複数のベクトルとメタデータを一度に登録可能な API を提供し、バッチ処理にも対応。

---

## インストール

VecTank は Python 3.7 以上で動作します。  
以下の手順に従ってインストールしてください。

1. **GitHub からリポジトリをクローン**

   ```bash
   git clone https://github.com/yourusername/VecTank.git
   cd VecTank
   ```

2. **パッケージのインストール**

   ```bash
   pip install .
   ```

また、開発中の場合は以下のコマンドでインストール（編集可能なモード）してください。

   ```bash
   pip install -e .
   ```

---

## 使い方

### 1. サーバの起動 (CLI)

VecTank は CLI 経由でサーバを簡単に起動する機能を提供します。  
インストール後、以下のコマンドでサーバを起動できます。

```bash
vectank-run --port 50000 --authkey secret
```

コマンドラインオプション:

- `--port`: サーバのポート番号 (デフォルト: 50000)
- `--authkey`: 認証キー (デフォルト: "secret")

サーバ起動時には、必要に応じてタンクの作成を行ってください。

### 2. クライアントからの利用

クライアント側では、`TankClient` クラスを利用してサーバに接続できます。たとえば、以下のコード例をご参照ください。

```python
from vectank.client import TankClient
from vectank.core import VectorSimMethod
import numpy as np

# サーバに接続
client = TankClient()

# "default" タンクを取得
tank = client.get_tank("default")

# 1200 次元の乱数ベクトルを生成して追加
vector = np.random.rand(1200).astype(np.float32)
metadata = {"name": "サンプルベクトル"}
key = tank.add_vector(vector, metadata)
print(f"追加したベクトルのキー: {key}")

# クエリベクトルによる検索（上位 5件を取得）
results = tank.search(vector, top_k=5)
for res in results:
    print(res)
```

### 3. ベンチマーク

大量のベクトルを登録および検索するパフォーマンスを評価するため、`examples/sample_benchmark.py` を利用できます。  
このスクリプトは、1200 次元の乱数ベクトル 20,000 個を登録し、上位 100 件の検索時間をミリ秒単位で表示します。

実行例:

```bash
python examples/sample_benchmark.py
```

### 4. テストの実行

VecTank のテストを実行する前に、サーバの起動が必要なテストも含まれるため、場合によっては事前にサーバを起動してください。

#### unittest を利用する場合

以下のコマンドで、全テストケースを詳細表示（verbose モード）で実行できます。

```bash
python -m unittest discover -v
```

テスト結果は標準出力に表示され、必要に応じて出力をファイルにリダイレクトすることも可能です。

例:

```bash
python -m unittest discover -v > test_results.txt 2>&1
```

#### pytest を利用する場合

以下のコマンドで、全テストケースを実行できます。

```bash
pytest --maxfail=1 --disable-warnings -q
```

JUnit 形式の XML レポートを生成する場合は、次のように実行します。

```bash
pytest --junitxml=report.xml
```

※ サーバ起動が不要な単体テストの場合は、サーバプロセスを起動せずにテストを実行することも可能です。

---

## ディレクトリ構成

VecTank リポジトリは以下のようなディレクトリ構成になっています。

```
VecTank/
├── vectank/           # ライブラリ本体
│   ├── __init__.py    # パッケージエントリポイント（公開 API の定義）
│   ├── core.py        # 類似度計算方式（Enum、計算関数など）
│   ├── tank.py        # VecTank クラス（ベクトルの追加、検索、更新、削除、永続化）
│   ├── store.py       # TankStore クラス（複数タンク管理）
│   ├── server.py      # サーバ起動用スクリプト（vectank-run のエントリポイント）
│   └── client.py      # TankClient クラス（クライアント用 API）
├── vectank/cli.py     # コマンドライン起動用のスクリプト（entry_point: vectank-run）
├── examples/          # 利用例・サンプルスクリプト
│   ├── run_server.py  # サーバ起動用スクリプト
│   └── sample_benchmark.py # 登録・検索パフォーマンス計測用スクリプト
├── tests/             # テストコード（unittest/pytest）
│   ├── test_tank.py
│   ├── test_store.py
│   ├── test_server.py
│   └── test_client.py
├── README.md          # このファイル
├── setup.py           # パッケージのセットアップスクリプト
└── LICENSE            # ライセンス情報 (MIT License 等)
```

---

## ライセンス

VecTank は MIT License の下で公開されています。  
詳細は [LICENSE](./LICENSE) をご覧ください。

---

## コンタクト / 貢献

ご意見・ご質問、バグ報告、または機能改善の提案などは、GitHub の [Issue](https://github.com/yourusername/VecTank/issues) をご利用ください。  
プルリクエストも歓迎します。  
VecTank を通じて、より効率的なベクトル管理と検索が実現できることを願っています！

---

VecTank をぜひお試しください！
