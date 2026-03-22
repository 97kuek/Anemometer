# Anemometer (風速計データ収集・可視化システム)

IoTセンサー（風速計）などから送信される環境データを収集し、保存および可視化するためのシステムです。

## 概要
本システムは、各種環境データを受け取りデータベースに蓄積し、Grafanaによってリアルタイムでダッシュボード上に可視化するための基盤を提供します。Docker環境上で各種コンテナが連携して動作します。

## 主な構成要素
- **Backend**: Django
- **Database**: MySQL
- **Visualization**: Grafana
- **Web Server**: Nginx
- **Infrastructure**: Docker / Docker Compose
