# Anemometer (風速計データ収集・可視化システム)

IoTセンサー（風速計）などから送信される環境データを収集し、保存および可視化するためのシステムです。

システムの詳細なアーキテクチャや技術的な背景、運用・仕様については[引き継ぎ資料](handover.md)に記載されています。

## 主な構成要素
- **Backend**: Django
- **Database**: MySQL
- **Visualization**: Grafana
- **Web Server**: Nginx
- **Infrastructure**: Docker / Docker Compose

## 開発環境のセットアップと起動方法

本システムは Docker を利用して構築されています。Windows 環境の場合は、ファイルシステムや権限の問題を回避するため、**WSL (Windows Subsystem for Linux) の利用を強く推奨**します。

### 1. 前提条件
- Docker および Docker Compose（Docker Desktop等）がインストールされており、起動していること。
- Windows の場合は WSL 環境（Ubuntu 等）がインストールされ、Docker が WSL と連携していること。

### 2. リポジトリのクローン
WSL のターミナル（または Linux/macOS のターミナル）を開き、本リポジトリをクローンして移動します。

```bash
git clone <本リポジトリのURL>
cd Anemometer
```

### 3. 環境変数の設定 (初回のみ)

本システムを起動する前に、データベースやDjango、Grafanaで使用する環境変数ファイル(`.env`)を作成する必要があります。
ターミナルで以下のコマンドを実行し、必要なディレクトリとファイルを作成してください。

```bash
# 各ディレクトリの作成
mkdir -p mysql grafana django

# mysql/.env の作成
cat << 'EOF' > mysql/.env
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=anemometer
MYSQL_USER=anemometer
MYSQL_PASSWORD=password
EOF

# django/.env の作成
cat << 'EOF' > django/.env
MYSQL_DATABASE=anemometer
MYSQL_USER=anemometer
MYSQL_PASSWORD=password
EOF

# grafana/.env の作成
cat << 'EOF' > grafana/.env
GF_SECURITY_ADMIN_PASSWORD=admin
GF_SERVER_DOMAIN=localhost
GF_SERVER_ROOT_URL=http://localhost:8000/grafana/
GF_SERVER_SERVE_FROM_SUB_PATH=true
GF_INSTALL_PLUGINS=yesoreyeram-infinity-datasource,briangann-gauge-panel
EOF
```

### 4. システムの一括セットアップ・起動

環境変数が用意できたら、リポジトリ直下にある `init.sh` スクリプトを実行します。これにより、Docker コンテナのビルドから起動、データベースの初期設定（マイグレーション）、静的ファイルの収集などが行われます。
また、Django独自のアプリケーション用のテーブルが正常に作成されるよう、追加のマイグレーションコマンドも実行します。

```bash
# コンテナのビルドと起動
bash ./init.sh

# テーブル不足エラー(SecretKey等)を防ぐため、追加のマイグレーションを実行
docker compose exec django ./manage.py makemigrations data flightdata frontend
docker compose exec django ./manage.py migrate
```

### 5. 初期データの登録

認証用のシークレットキーをデータベースに登録します。このキーはシミュレータや実機センサーがデータを送信する際の認証に使用するまた、サーバー側で照合するための値です。

```bash
docker compose exec django ./manage.py shell -c \
  "from data.models import SecretKey; SecretKey.objects.get_or_create(Key='secret')"
```

> ⚠️ デフォルトのキー値は `secret` です。本番運用時はセキュリティのため任意の文字列に変更し、シミュレータ側の `cli/server.py` 内の `self.SecretKey` 値と一致させてください。

### 6. 起動の確認

以下のコマンドを実行し、4つのコンテナ（`django`, `mysql`, `nginx`, `grafana`）の Status が `Up`（起動中）になっていることを確認します。

```bash
docker compose ps
```

### 7. 各種画面へのアクセス

起動が完了したら、ブラウザから以下の URL にアクセスして動作を確認できます。

- **ダッシュボード (Grafana)**: [http://localhost:8000/grafana/](http://localhost:8000/grafana/)
  - 初期ログイン ID: `admin` / パスワード: `admin`
  - 初回ログイン時にパスワード変更を求められる場合は、「スキップ」またはそのまま設定して構いません。
- **バックエンド管理画面 (Django Admin)**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### 7. システムの停止・削除

開発を終了してコンテナを停止する場合は、プロジェクトディレクトリで以下のコマンドを実行します。

```bash
# コンテナの停止（ビルド済みのイメージやデータベースのデータは保持されます）
docker compose stop

# コンテナの停止と削除（必要に応じてネットワーク等も削除されます）
docker compose down
```

### 8. シミュレータの実行（テストデータの送信）

風速計の実機がない環境でも、付属のシミュレータを使ってテストデータを送信できます。WSL 環境の別ターミナルを開いて実行してください。

```bash
cd cli
# 初回のみ必要なライブラリをインストール
pip3 install requests  

# シミュレータの起動
python3 cli.py
```
※ シミュレータを停止するには `Ctrl + C` を入力します。

---

さらに詳しいコンテナごとの役割、APIエンドポイント、Grafana の設定方法、マイグレーションの手順などについては、必ず[引き継ぎ資料](handover.md)を参照してください。
