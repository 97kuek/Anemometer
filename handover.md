# Anemometer 引継ぎ資料

## 1. はじめに

本ドキュメントは、Anemometer プロジェクトの引継ぎ資料です。  
本プロジェクトは、風向・風速計からネットワーク経由で送信される風速データを収集・保存し、リアルタイムで可視化するシステムです。

基本的なセットアップ手順・起動方法・アクセス先 URL などの **運用手順は [README.md](README.md) を参照してください**。  
本資料では、システムの技術的な背景・設計判断・コンポーネント詳細・引継ぎ上の注意事項を解説します。

---

## 2. システム全体のアーキテクチャ

### 2.1 コンポーネント構成

```
[センサー / シミュレータ]
        │ HTTP POST（HMAC署名付き）
        ▼
[Nginx] ← ポート8000でリクエストを受け付け
  │  /grafana/ → [Grafana:3000]（ダッシュボード）
  │  その他   → [Django:8001]（API サーバー）
        │
        ├── メモリキャッシュ（LatestData）
        │       └── リアルタイム配信用
        └── [MySQL]（永続化ストレージ）
                └── 過去データの保存・検索
```

### 2.2 データフロー

1. センサー（またはシミュレータ）が 1 秒ごとに `POST /data/create/` へ送信
2. Django が HMAC-SHA256 署名を検証
3. 検証成功後、サーバー時刻で Time を上書きしてデータを保存
   - MySQL DB（`data_data` テーブル）に永続化
   - メモリキャッシュ（`LatestData.LHWD`）に追加
4. Grafana が `GET /data/LD/` を 1 秒間隔でポーリング
5. Django がメモリキャッシュから最新データを返却（DB アクセスなし）

---

## 3. インフラ技術：Docker の基礎

本プロジェクトを理解する上で最も重要な前提知識が **Docker** です。

### 3.1 主要概念

| 概念 | 説明 |
|---|---|
| **Image** | コンテナを作成するための設計図。`Dockerfile` から生成される |
| **Container** | Image をもとに起動される独立した実行環境 |
| **Volume** | コンテナは使い捨てが前提なので、データを永続化するためにホストのストレージ領域をマウントする仕組み |
| **Docker Compose** | 複数コンテナを連携して管理するツール。`docker-compose.yaml` に構成を定義する |

### 3.2 ネットワークとポートフォワーディング

- **内部 DNS**: Docker ネットワーク内では `django`、`mysql` などのコンテナ名でホスト名として相互通信できる
- **ポートフォワーディング**: ホストのポートをコンテナ内ポートへ転送する（例：`8000:80` は PC の 8000 番を Nginx の 80 番へ転送）

---

## 4. 各コンテナの役割と設定ファイル

### 4.1 Nginx（`nginx:1.25`）

外部からの HTTP リクエストをパスに応じて各コンテナへ振り分けます。

**`nginx/nginx.conf` の主要設定:**

| パス | 転送先 | 説明 |
|---|---|---|
| `/static` | `/static`（ファイル直接配信） | CSS・JS 等の静的ファイル |
| `/grafana/` | `grafana:3000/grafana/` | Grafana ダッシュボード |
| `/grafana/api/` | `grafana:3000/grafana/api/` | Grafana API（WebSocket 対応） |
| その他 | `django:8001`（uWSGI 経由） | Django API |

**重要な注意点:** Grafana は `localhost:8000/grafana/` 経由でのみ正常動作します。`localhost:3000` への直接アクセスはリダイレクトエラーになります（`GF_SERVER_ROOT_URL` の設定による）。

### 4.2 Django（Python 3.11 / Django 4.1）

システムのメインロジックです。uWSGI サーバーとして動作しポート 8001 で待機します。

**ディレクトリ構成:**
```
anemometer_server/
├── anemometer_server/    # プロジェクト設定
│   ├── settings.py       # DB・ミドルウェア・セキュリティ設定
│   └── urls.py           # ルートルーティング
├── data/                 # 風速データの受信・保存・配信
│   ├── models.py         # DB テーブル定義
│   ├── views.py          # API ロジック
│   ├── serializers.py    # データ変換・バリデーション
│   └── urls.py           # /data/ 以下のルーティング
└── flightdata/           # フライトデータ（Firebase 連携）
    ├── views.py          # Firebase 取得・キャッシュ・API
    └── urls.py           # /flightdata/ 以下のルーティング
```

### 4.3 MySQL（`mysql:8.0`）

風速データを長期保存します。  
コンテナ起動時に `mysql/.env` の環境変数からデータベース・ユーザーを自動作成します。

**テーブル構成（Django マイグレーションで自動作成）:**

| テーブル名 | 内容 |
|---|---|
| `data_data` | 風速データ（Time・AID・data の JSON） |
| `data_secretkey` | HMAC 認証用の共有鍵 |

### 4.4 Grafana

`grafana/provisioning/` 配下の設定ファイルをコンテナ起動時に自動読み込みします。

| ファイル | 内容 |
|---|---|
| `provisioning/datasources/django_restapi.yaml` | Infinity プラグインのデータソース設定 |
| `provisioning/dashboards/anemometer.yaml` | ダッシュボード定義ファイルの読み込み設定 |
| `provisioning/json/anemometer-*.json` | ダッシュボードの実際の定義 |

Grafana は MySQL を直接参照せず、**Django の REST API（`/data/LD/` 等）から JSON を取得して描画**する設計になっています。

---

## 5. 環境変数の管理

本システムの設定値は `.env` ファイルで管理しています。**これらのファイルは `.gitignore` により Git 管理対象外**です。

| ファイル | 主な設定内容 |
|---|---|
| `mysql/.env` | MySQL の root パスワード・DB 名・ユーザー・パスワード |
| `django/.env` | Django から MySQL への接続情報（ユーザー・パスワード・DB 名） |
| `grafana/.env` | Grafana の管理者パスワード・公開 URL・インストールプラグイン |

### settings.py の主要設定

| 設定 | 値 | 説明 |
|---|---|---|
| `SECRET_KEY` | 環境変数 `DJANGO_SECRET_KEY` から読込（フォールバックあり） | セッション・CSRF トークンの暗号化 |
| `DEBUG` | 環境変数 `DJANGO_DEBUG=True` の場合のみ有効 | 本番では必ず `False` |
| `ALLOWED_HOSTS` | `localhost`, `127.0.0.1`, `django`, `anemometer.tyama.mydns.jp` | アクセスを許可するホスト名 |

---

## 6. コアロジック解説：`data/views.py`

### 6.1 LatestData クラス（メモリキャッシュ）

`LatestData` はサーバー起動時に 1 インスタンスだけ生成され、全リクエストで共有されます。

```python
latestdata = LatestData()  # モジュールロード時に 1 度だけ生成
```

| 属性 | 型 | 役割 |
|---|---|---|
| `LHWD` | `deque(maxlen=1000)` | 直近データのキャッシュ（最大 1000 件・1 時間以内） |
| `Anemometer` | `deque(maxlen=256)` | センサーごとの死活状態（Working / Unstable） |
| `_lock` | `threading.Lock` | 複数リクエストからの同時アクセスを保護 |

**設計上の注意点:**  
- `deque(maxlen=...)` により、上限を超えると古いデータが自動的に削除されます（メモリリーク防止）
- `threading.Lock` で全ての読み書きを保護しています（スレッド競合防止）

### 6.2 センサー状態管理（Anemometer）

センサーは AID（Anemometer ID）で識別されます。

| 状態 | 条件 |
|---|---|
| `Working` | 最終受信から 15 秒以内 |
| `Unstable` | 最終受信から 15〜60 秒 |
| 削除（リストから消える） | 最終受信から 60 秒以上 |

### 6.3 DHCP 機能

センサーが AID 未設定の場合に `/data/DHCP/` へリクエストすると、未使用の AID（1〜100 の整数）を自動割り当てします。

---

## 7. セキュリティ：HMAC-SHA256 認証の仕組み

未認証デバイスからの不正データ送信を防ぐために実装しています。

### 認証フロー

```
[送信側]
送信データ（JSON）+ SecretKey
       ↓ HMAC-SHA256
    署名値（Base64）
       ↓ Authorization ヘッダに付与して送信

[受信側 Django]
受信データ + DB の SecretKey
       ↓ HMAC-SHA256
    署名値（Base64）
       ↓ ヘッダの値と比較
    一致 → 201 Created
    不一致 → 401 Unauthorized
```

### 実装詳細

```python
# 送信側（cli/server.py）
psk = hashlib.sha256(secret_key.encode()).digest()
signature = hmac.new(key=psk, msg=payload, digestmod=hashlib.sha256).digest()
auth_header = base64.b64encode(signature).decode()

# 受信側（data/views.py）
key_obj = SecretKey.objects.first()   # DB から取得（0 件なら False を返す）
secret = hashlib.sha256(key_obj.Key.encode()).digest()
signature = hmac.new(key=secret, msg=payload, digestmod=hashlib.sha256).digest()
```

### SecretKey の変更方法

```bash
# Django 管理画面（/admin/）から GUI で変更するか、シェルで直接操作
docker compose exec django ./manage.py shell -c \
  "from data.models import SecretKey; SecretKey.objects.all().delete(); SecretKey.objects.create(Key='新しいキー')"
```

変更後は、シミュレータ側の環境変数も合わせて変更してください：

```bash
ANEMOMETER_SECRET_KEY=新しいキー python3 cli.py
```

---

## 8. フライトデータ機能（flightdata アプリ）

Firebase Realtime Database から 2 秒ごとにフライトデータ（グライダーの飛行情報）を取得して配信する機能です。

### 動作の仕組み

```
[Firebase Realtime Database]
        │ 2秒ごとに fetch（バックグラウンドスケジューラ）
        ▼
[getdata.json]（一時ファイル）
        │ GETリクエスト時に読み込み＆クリア
        ▼
[LatestData.LHWD]（メモリキャッシュ）
        │
        ▼
[GET /flightdata/LD/ または /flightdata/LHWD/]
```

### Firebase URL の設定

デフォルトの Firebase URL は `flightdata/views.py` の環境変数で上書きできます：

```bash
# django/.env に追記
FIREBASE_URL=https://your-database.firebaseio.com/.json
```

### API エンドポイント

| パス | 説明 |
|---|---|
| `/flightdata/LD/` | 直近 2 分以内の最新フライトデータ（1 件） |
| `/flightdata/LHWD/` | 直近 1 時間以内のフライトデータ一覧 |

---

## 9. API エンドポイント一覧

### 風速データ（`/data/`）

| メソッド | パス | 説明 | 認証 |
|---|---|---|---|
| `POST` | `/data/create/` | センサーデータの受信 | HMAC 必須 |
| `GET` | `/data/LD/` | 各センサーの最新値（1 件/センサー） | なし |
| `GET` | `/data/LHWD/` | 直近 1 時間分の全データ | なし |
| `GET` | `/data/Anemometer/` | 全センサーの死活状態 | なし |
| `GET` | `/data/filter/?datetime_range=開始,終了` | 期間指定検索（最大 1000 件） | なし |
| `GET` | `/data/DHCP/` | 未使用 AID の自動割り当て | なし |

**`/data/create/` のリクエスト形式:**

```json
{
  "AID": 1,
  "Time": "2024-01-01 12:00:00.000000",
  "WindSpeed": 3.5,
  "WindDirection": 180.0,
  "Latitude": 35.11972,
  "Longitude": 138.63194,
  "data": {
    "WindSpeed": 3.5,
    "WindDirection": 180.0,
    "Latitude": 35.11972,
    "Longitude": 138.63194,
    "LHWD": true,
    "LD": true
  }
}
```

**`datetime_range` の書式:**  
`?datetime_range=2024-01-01T00:00:00,2024-01-01T23:59:59`

---

## 10. マイグレーション運用手順

`data/models.py` などのモデルを変更した場合、必ず以下の手順で DB へ反映してください。

```bash
# 1. 変更差分からマイグレーションファイルを生成
docker compose exec django ./manage.py makemigrations

# 2. DB へ適用
docker compose exec django ./manage.py migrate
```

生成されたマイグレーションファイル（`data/migrations/` 以下）は **必ず Git にコミット**してください。これにより他者が `init.sh` を実行した際にも同じスキーマが自動適用されます。

---

## 11. Grafana ダッシュボードの永続化手順

Grafana の変更はデフォルトでコンテナ内に保存されるため、コンテナを再作成すると消えます。以下の手順でファイルとして永続化してください。

1. `http://localhost:8000/grafana/` でダッシュボードを編集・保存
2. 画面上部の「Dashboard settings（歯車）」→「JSON Model」を開く
3. 表示された JSON を全コピーする
4. `grafana/provisioning/json/anemometer-*.json` の中身を上書き保存
5. Git にコミットする

---

## 12. CI/CD パイプライン

`.gitlab-ci.yml` に定義されており、特定ブランチへのプッシュで本番サーバーへ自動デプロイされます。

```yaml
# ブランチ名が "anemometer.tyama.mydns.jp" の場合に自動実行
rules:
  - if: '$CI_COMMIT_BRANCH == "anemometer.tyama.mydns.jp"'
```

**デプロイの流れ:**
1. 対象ブランチへプッシュ
2. GitLab Runner が起動
3. `docker compose down` → `./init.sh` を実行
4. 新しいコードでコンテナが再ビルド・起動

---

## 13. シミュレータの仕様

### cli/cli.py

`curses` ライブラリによるターミナル UI を描画しながら、1 秒ごとに 3 台のセンサー分のデータを送信します。

**シミュレート対象（富士川滑空場）:**

| AID | ラベル | 緯度 | 経度 |
|---|---|---|---|
| 1 | 南端 | 35.11972 | 138.63194 |
| 2 | 中央 | 35.12062 | 138.63169 |
| 3 | 北端 | 35.12152 | 138.63144 |

**送信データ:** 平均 1.5 m/s、標準偏差 0.5 m/s のガウス分布で風速をランダム生成。風向は 180°（南風）を中心に ±10° のばらつきを加えています。

### cli/server.py

HMAC 署名付きの HTTP POST を担当するモジュールです。SecretKey は環境変数 `ANEMOMETER_SECRET_KEY` から取得します（未設定時のデフォルトは `secret`）。

### cli/jsontest.py

動作確認用のテストスクリプトです。`cli.py` と同じ HMAC 認証・データ形式でリクエストを送信します。環境変数 `ANEMOMETER_SECRET_KEY` でキーを指定できます。

---

## 14. 既知の制限・将来の改善候補

| 項目 | 内容 |
|---|---|
| HTTPS 非対応 | 現状は HTTP のみ。本番では Nginx に SSL 証明書を設定することを推奨 |
| レートリミットなし | `/data/create/` に大量リクエストを投げると DB が溢れる可能性がある |
| テストコードなし | `data/tests.py` が空。今後は送受信・認証のテストを追加推奨 |
| MySQL 権限が広い | `anemometer` ユーザーが DB 全体に `ALL PRIVILEGES` を持つ。本番では SELECT/INSERT に絞るべき |
| Grafana ダッシュボードが手動管理 | 編集のたびに JSON エクスポートが必要 |

---

## 15. トラブルシューティング

### ログの確認

```bash
docker compose logs django      # Python エラー・リクエストログ
docker compose logs mysql       # DB 接続エラー
docker compose logs nginx       # プロキシエラー・アクセスログ
docker compose logs -f django   # リアルタイムで追う
```

### Django コンテナ内で直接操作

```bash
# コンテナ内シェルに入る
docker compose exec django /bin/bash

# Django 対話型シェル（ORM でDB確認）
docker compose exec django ./manage.py shell
```

```python
# 例: 直近のデータを確認
from data.models import Data
Data.objects.order_by('-Time')[:5].values()

# 例: SecretKey の確認
from data.models import SecretKey
list(SecretKey.objects.all())
```

### よくあるエラー

| エラー | 原因 | 対処 |
|---|---|---|
| `Connection Error` | サーバーが起動していない | `docker compose up -d` で起動 |
| `Authentication Error (401)` | SecretKey が未登録 or 不一致 | DB への登録を確認、シミュレータのキーと一致させる |
| `Grafana: Bad Gateway` | Django コンテナが起動していない | `docker compose ps` でコンテナ確認 |
| `Table doesn't exist` | マイグレーション未実行 | `makemigrations` → `migrate` を実行 |
| `ALLOWED_HOSTS` エラー | アクセス元ホストが許可リストにない | `settings.py` の `ALLOWED_HOSTS` に追加 |
