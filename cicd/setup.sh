TRG_DIR="/var/www/"

sudo cp -f uwsgi.service /usr/lib/systemd/system/

sudo systemctl daemon-reload
sudo systemctl restart uwsgi
sudo systemctl restart nginx

python3 ../anemometer_server/manage.py collectstatic
