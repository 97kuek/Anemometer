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

### 3. システムの一括セットアップ・起動

リポジトリ直下にある `init.sh` スクリプトを実行することで、Docker コンテナのビルドから起動、データベースの初期設定（マイグレーション）、静的ファイルの収集までをすべて自動で行います。

```bash
# 初回起動時、または設定変更時
bash ./init.sh
```

**`init.sh` 実行時に内部で行われていること:**
1. `docker compose build` : 必要な Docker イメージのビルド
2. `docker compose up -d` : 全コンテナのバックグラウンド起動
3. `docker compose exec django ./manage.py makemigrations` および `migrate` : データベースのテーブル作成・マイグレーション
4. `docker compose exec django ./manage.py collectstatic --noinput` : 静的ファイル（CSSや画像など）の収集

### 4. 起動の確認

以下のコマンドを実行し、4つのコンテナ（`django`, `mysql`, `nginx`, `grafana`）の Status が `Up`（起動中）になっていることを確認します。

```bash
docker compose ps
```

### 5. 各種画面へのアクセス

起動が完了したら、ブラウザから以下の URL にアクセスして動作を確認できます。

- **ダッシュボード (Grafana)**: [http://localhost:8000/grafana/](http://localhost:8000/grafana/)
  - 初期ログイン ID: `admin` / パスワード: `admin`
- **バックエンド管理画面 (Django Admin)**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### 6. システムの停止・削除

開発を終了してコンテナを停止する場合は、プロジェクトディレクトリで以下のコマンドを実行します。

```bash
# コンテナの停止（ビルド済みのイメージやデータベースのデータは保持されます）
docker compose stop

# コンテナの停止と削除（必要に応じてネットワーク等も削除されます）
docker compose down
```

### 7. シミュレータの実行（テストデータの送信）

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
