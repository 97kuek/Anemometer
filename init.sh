#モジュールインストールなどのためのリビルド
docker compose build
docker compose up -d

#DB,staticファイルの再構築
docker compose exec django chmod +x ./manage.py
docker compose exec django ./manage.py makemigrations
docker compose exec django ./manage.py migrate
docker compose exec django ./manage.py collectstatic --noinput
