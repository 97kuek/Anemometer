#!/bin/bash

source /home/tyamanaka/server/bin/activate
uwsgi --ini /var/www/anemometer/cicd/uwsgi.ini < /dev/null
#uwsgi --socket :8001 --wsgi-file /var/www/anemometer/anemometer_server/anemometer_server/wsgi.py --chdir /var/www/anemometer/anemometer_server/ --ini /var/www/anemometer/cicd/uwsgi.ini < /dev/null
