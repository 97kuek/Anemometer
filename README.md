# Anemometer — 風速計データ収集・可視化システム

IoT センサー（風速計）から送信される風速・風向データをリアルタイムで収集・保存・可視化するシステムです。

> 技術的な背景・アーキテクチャの詳細・CI/CD の構成などは [引き継ぎ資料 (handover.md)](handover.md) も合わせて参照してください。

---

## 目次

1. [システム構成](#1-システム構成)
2. [前提条件](#2-前提条件)
3. [初回セットアップ](#3-初回セットアップ)
4. [サーバーの起動・停止](#4-サーバーの起動停止)
5. [シミュレータの使い方](#5-シミュレータの使い方)
6. [各種アクセス先一覧](#6-各種アクセス先一覧)
7. [ディレクトリ構成](#7-ディレクトリ構成)
8. [API エンドポイント一覧](#8-api-エンドポイント一覧)
9. [モデル変更時のマイグレーション手順](#9-モデル変更時のマイグレーション手順)
10. [トラブルシューティング](#10-トラブルシューティング)

---

## 1. システム構成

| コンポーネント | 役割 |
|---|---|
| **Nginx** | リバースプロキシ。外部からのリクエストを Django / Grafana へ振り分ける |
| **Django** | REST API サーバー。データ受信・認証・DB 保存・配信を担当 |
| **MySQL** | 風速データの永続化ストレージ |
| **Grafana** | リアルタイムダッシュボードの描画・可視化 |

これら 4 つのコンテナが Docker Compose によって連携して動作します。

---

## 2. 前提条件

**Windows 環境では、ファイルシステムの権限問題を避けるため WSL2 上での作業を強く推奨します。**

### 必要なソフトウェア

- **Docker Desktop**（WSL2 ベースエンジンが有効になっていること）
- **WSL2**（Ubuntu 推奨）

### WSL2 + Docker Desktop のセットアップ（未導入の場合）

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) をインストールします。
2. Docker Desktop の設定画面で `Settings > General > Use the WSL 2 based engine` が ON になっていることを確認します。
3. PowerShell を管理者権限で開き、以下を実行して Ubuntu をインストールします。
   ```powershell
   wsl --install
   ```
4. 再起動後、スタートメニューから「Ubuntu」を開いてユーザー名とパスワードを設定します。

以降の操作はすべて **WSL2 のターミナル（Ubuntu）** で行ってください。

---

## 3. 初回セットアップ

### 3-1. リポジトリを WSL2 上に用意する

WSL2 のターミナルを開き、作業ディレクトリへ移動します。

```bash
cd ~/work/Anemometer   # クローン済みの場合
```

クローンしていない場合は先にクローンしてください。

```bash
git clone <リポジトリURL>
cd Anemometer
```

### 3-2. 環境変数ファイル（.env）を作成する

以下のコマンドを一度だけ実行し、各コンテナが必要とする設定ファイルを作成します。

```bash
mkdir -p mysql grafana django

# MySQL 接続情報
cat << 'EOF' > mysql/.env
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=anemometer
MYSQL_USER=anemometer
MYSQL_PASSWORD=password
EOF

# Django 接続情報
cat << 'EOF' > django/.env
MYSQL_DATABASE=anemometer
MYSQL_USER=anemometer
MYSQL_PASSWORD=password
EOF

# Grafana 設定
cat << 'EOF' > grafana/.env
GF_SECURITY_ADMIN_PASSWORD=admin
GF_SERVER_DOMAIN=localhost
GF_SERVER_ROOT_URL=http://localhost:8000/grafana/
GF_SERVER_SERVE_FROM_SUB_PATH=true
GF_INSTALL_PLUGINS=yesoreyeram-infinity-datasource,briangann-gauge-panel
EOF
```

> **本番運用時の注意**: パスワードは必ず強力なものに変更してください。

### 3-3. サーバーを起動する（初回ビルド込み）

```bash
bash ./init.sh
```

内部で次の処理が自動実行されます。

1. Docker イメージのビルド
2. 全コンテナの起動
3. Django マイグレーション（DB テーブルの作成）
4. 静的ファイルの収集

初回はイメージのダウンロードがあるため数分かかります。

### 3-4. 追加マイグレーションを実行する（初回のみ）

`init.sh` 完了後、以下を続けて実行します。

```bash
docker compose exec django ./manage.py makemigrations data flightdata frontend
docker compose exec django ./manage.py migrate
```

### 3-5. シークレットキーを登録する（初回のみ）

データの送受信に使用する認証キーをデータベースへ登録します。

```bash
docker compose exec django ./manage.py shell -c \
  "from data.models import SecretKey; SecretKey.objects.get_or_create(Key='secret')"
```

登録されたことを確認します。

```bash
docker compose exec django ./manage.py shell -c \
  "from data.models import SecretKey; print(list(SecretKey.objects.all()))"
# → [<SecretKey: SecretKey object (1)>] と表示されれば成功
```

> **セキュリティ上の注意**: デフォルトキー `secret` は開発用です。本番環境では Django Admin 画面（`/admin/`）から任意の文字列に変更し、シミュレータ側の環境変数 `ANEMOMETER_SECRET_KEY` にも同じ値を設定してください。

### 3-6. 起動確認

```bash
docker compose ps
```

以下の 4 コンテナすべての `Status` が `Up` になっていれば成功です。

```
NAME                    STATUS
anemometer-django-1     Up
anemometer-mysql-1      Up
anemometer-nginx-1      Up
anemometer-grafana-1    Up
```

---

## 4. サーバーの起動・停止

### 2 回目以降の起動

```bash
docker compose up -d
```

### 停止（データは保持）

```bash
docker compose stop
```

### 停止＋コンテナ削除（データは保持）

```bash
docker compose down
```

### データベースも含めて完全削除（注意: データが消えます）

```bash
docker compose down -v
```

---

## 5. シミュレータの使い方

実機センサーがない環境でも、付属のシミュレータで風速・風向のダミーデータを自動送信できます。

### 別の WSL2 ターミナルを開いて実行

```bash
cd ~/work/Anemometer/cli

# 初回のみ: 必要ライブラリのインストール
pip3 install requests

# シミュレータ起動
python3 cli.py
```

起動すると、富士川滑空場の 3 地点（南端・中央・北端）を模した 3 台のセンサーが **1 秒おきに** データを送信し続けます。

```
ターミナル画面例:
AID1(南端) good AT:12:34:56
AID2(中央) good AT:12:34:56
AID3(北端) good AT:12:34:57
...
```

- `good` と表示されれば送信成功です。
- 停止するには `Ctrl + C` を押してください。

### シミュレータのシークレットキーについて

シミュレータは環境変数 `ANEMOMETER_SECRET_KEY` からキーを読み込みます（未設定の場合は `secret` がデフォルト値）。

```bash
# キーを変更して起動する場合
ANEMOMETER_SECRET_KEY=your_key python3 cli.py
```

---

## 6. 各種アクセス先一覧

| 名称 | URL | 備考 |
|---|---|---|
| **Grafana ダッシュボード** | http://localhost:8000/grafana/ | ID: `admin` / PW: `admin` |
| **Django 管理画面** | http://localhost:8000/admin/ | スーパーユーザー作成後に使用可能 |
| **最新データ API** | http://localhost:8000/data/LD/ | ブラウザで JSON を直接確認できる |
| **全センサー状態 API** | http://localhost:8000/data/Anemometer/ | 各センサーの Working / Unstable 状態 |

> Grafana には **必ず `http://localhost:8000/grafana/`** からアクセスしてください。`localhost:3000` への直接アクセスはリダイレクトエラーになります。

### Django 管理画面のスーパーユーザー作成（任意）

```bash
docker compose exec django ./manage.py createsuperuser
```

---

## 7. ディレクトリ構成

```
Anemometer/
├── anemometer_server/          # Django プロジェクト本体
│   ├── anemometer_server/      # プロジェクト設定
│   │   ├── settings.py         # Django 設定（DB・ミドルウェア等）
│   │   └── urls.py             # ルートルーティング定義
│   ├── data/                   # メインアプリ（風速データの受信・保存・配信）
│   │   ├── models.py           # DB テーブル定義（Data, SecretKey）
│   │   ├── views.py            # API ロジック（認証・キャッシュ・返却）
│   │   ├── serializers.py      # データ変換・バリデーション
│   │   └── urls.py             # /data/ 以下のルーティング
│   └── flightdata/             # フライトデータ取得・管理アプリ
│
├── cli/                        # 開発・テスト用シミュレータ
│   ├── cli.py                  # メインスクリプト（ターミナル UI + データ生成）
│   └── server.py               # HMAC 署名付き HTTP 送信モジュール
│
├── grafana/
│   ├── .env                    # Grafana 環境変数
│   └── provisioning/           # 起動時自動ロードのダッシュボード・データソース設定
│
├── nginx/
│   └── nginx.conf              # リバースプロキシ設定
│
├── django/
│   ├── Dockerfile              # Django コンテナビルド定義
│   └── requirements.txt        # Python パッケージ一覧
│
├── sql/
│   └── init.sql                # MySQL 初回起動時の初期化スクリプト
│
├── mysql/.env                  # MySQL 環境変数（git 管理外）
├── docker-compose.yaml         # 全コンテナの構成定義
├── init.sh                     # 一括セットアップスクリプト
└── handover.md                 # 引き継ぎ資料（詳細な技術解説）
```

---

## 8. API エンドポイント一覧

| メソッド | パス | 説明 |
|---|---|---|
| `POST` | `/data/create/` | センサーデータの受信（HMAC 認証必須） |
| `GET` | `/data/LD/` | 各センサーの最新データを返す |
| `GET` | `/data/LHWD/` | 直近 1 時間分のデータを返す |
| `GET` | `/data/Anemometer/` | 全センサーの状態（Working / Unstable）を返す |
| `GET` | `/data/filter/?datetime_range=開始,終了` | 期間指定でのデータ取得（最大 1000 件） |
| `GET` | `/data/DHCP/` | 未使用の AID を自動割り当て |

### データ受信 API のリクエスト形式

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

Authorization ヘッダーに HMAC-SHA256 署名（Base64 エンコード）を付与する必要があります。

---

## 9. モデル変更時のマイグレーション手順

`data/models.py` などを修正した後は、必ず以下の手順で DB へ反映してください。

```bash
# 1. マイグレーションファイルを生成
docker compose exec django ./manage.py makemigrations

# 2. DB へ適用
docker compose exec django ./manage.py migrate
```

生成されたマイグレーションファイル（`data/migrations/` 以下）は **Git にコミット** して共有してください。

---

## 10. トラブルシューティング

### コンテナのログを確認する

```bash
docker compose logs django     # Django のログ
docker compose logs mysql      # MySQL のログ
docker compose logs nginx      # Nginx のログ
docker compose logs grafana    # Grafana のログ

docker compose logs -f django  # リアルタイムで追いかける場合
```

### Django コンテナ内に入って直接操作する

```bash
docker compose exec django /bin/bash
```

### Django シェルで DB を直接確認する

```bash
docker compose exec django ./manage.py shell
```

```python
# 例: 保存済みデータを確認
from data.models import Data
Data.objects.all()

# 例: SecretKey を確認
from data.models import SecretKey
SecretKey.objects.all()
```

### よくある問題と対処法

| 症状 | 原因 | 対処 |
|---|---|---|
| `Connection Error` がシミュレータに出る | サーバーが起動していない | `docker compose ps` で確認し、`docker compose up -d` で起動 |
| `Authentication Error` が出る | SecretKey が未登録、またはキーが一致しない | 手順 3-5 でキーを登録し、シミュレータ側のキーと一致させる |
| Grafana が `localhost:3000` で開けない | Nginx 経由でのアクセスが必須 | `http://localhost:8000/grafana/` を使用する |
| マイグレーションエラーが出る | テーブル定義とファイルが不一致 | `makemigrations` → `migrate` を再実行する |
| MySQL が起動しない（権限エラー） | ローカルディレクトリのマウント問題 | `docker compose down -v` でボリューム削除後、再セットアップ |
