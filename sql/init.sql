-- MySQL初回起動時の初期化スクリプト
-- MYSQL_USER / MYSQL_DATABASE 環境変数で作成されたユーザーに対して
-- 対象データベースへのアクセス権を付与する

GRANT ALL PRIVILEGES ON anemometer.* TO 'anemometer'@'%';
FLUSH PRIVILEGES;
