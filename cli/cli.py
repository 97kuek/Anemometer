import datetime
import time
import curses
import json
import random
from collections import deque
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout

from server import ServerComm
from Graphic import Graphic

graphic = Graphic()
servercomm = ServerComm()

posts = deque([""] * 100, maxlen=100)
graphic.stdscr.keypad(True)

# 富士川滑空場 滑走路中心座標
# RWY 18/36: 真方位約353度（磁気偏角~7°西偏 + 実測補正）
# 100mステップごとに: 緯度+0.000900度, 経度-0.000250度
STEP_LAT = 0.000900
STEP_LON = -0.000250
BASE_LAT = 35.11972
BASE_LON = 138.63194
ANEMOMETERS = [
    {'AID': 1, 'lat': BASE_LAT,                'lon': BASE_LON,                'label': 'AID1(南端)'},
    {'AID': 2, 'lat': BASE_LAT + STEP_LAT,     'lon': BASE_LON + STEP_LON,     'label': 'AID2(中央)'},
    {'AID': 3, 'lat': BASE_LAT + STEP_LAT * 2, 'lon': BASE_LON + STEP_LON * 2, 'label': 'AID3(北端)'},
]


def post_mode():
    for sensor in ANEMOMETERS:
        wind_speed = max(0.0, random.gauss(1.5, 0.5))
        wind_direction = (180.0 + random.gauss(0.0, 10.0)) % 360.0

        data = {
            'AID': sensor['AID'],
            'Time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            'WindSpeed': wind_speed,
            'WindDirection': wind_direction,
            'Latitude': sensor['lat'],
            'Longitude': sensor['lon'],
            'data': {
                'WindSpeed': wind_speed,
                'WindDirection': wind_direction,
                'Latitude': sensor['lat'],
                'Longitude': sensor['lon'],
                'LHWD': True,
                'LD': True
            }
        }
        result = servercomm.post_data(body=data)
        posts.appendleft(f"{sensor['label']} {result} AT:{datetime.datetime.now().strftime('%H:%M:%S')}")

    height, width = graphic.stdscr.getmaxyx()
    for i in range(height - 7):
        graphic.stdscr.addstr(i, 0, posts[height - 7 - i][:50])


def get_mode():
    graphic.stdscr.addstr(1, 40, "GET DATA")
    try:
        response_text = servercomm.get_data(query_set='?LD=True')
        response_json = json.loads(response_text)
        if response_json and len(response_json) > 0:
            getdata = response_json[0]
            wind_speed = getdata.get('WindSpeed', 0.0)
            wind_dir = getdata.get('WindDirection', 0.0)
            graphic.stdscr.addstr(3, 40, f"{wind_speed:.1f} m/s", curses.color_pair(1))
            graphic.stdscr.addstr(4, 40, f"Dir: {wind_dir:.1f} deg", curses.color_pair(1))
    except (json.JSONDecodeError, KeyError, IndexError):
        graphic.stdscr.addstr(3, 40, "Error or No Data", curses.color_pair(2))


def get_status():
    # #12: /data/Anemometer/ APIから動的にステータスを取得
    graphic.stdscr.addstr(6, 40, 'ANEMOMETER STATUS')
    try:
        response_text = servercomm.get_data(query_set='').replace('data/LD/', 'data/Anemometer/')
        # get_dataのパスを動的に変えるため直接呼ぶ
        import requests as req
        resp = req.get(servercomm.Server_Url + 'data/Anemometer/')
        anemometers = json.loads(resp.text)
        for idx, sensor in enumerate(anemometers):
            aid = sensor.get('AID', '?')
            status = sensor.get('Status', 'Unknown').upper()
            color = curses.color_pair(1) if status == 'WORKING' else curses.color_pair(2)
            graphic.stdscr.addstr(8 + idx, 40, f"ID:{aid}  {status}", color)
    except Exception:
        graphic.stdscr.addstr(8, 40, 'Status unavailable', curses.color_pair(2))


def main():
    try:
        while True:
            graphic.stdscr.clear()
            post_mode()
            get_mode()
            get_status()
            graphic.refresh()
            time.sleep(1)
    except KeyboardInterrupt:
        curses.endwin()


if __name__ == "__main__":
    main()