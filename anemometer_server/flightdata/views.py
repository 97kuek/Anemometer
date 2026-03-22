import datetime
import json
import os
import threading

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from rest_framework.response import Response
from rest_framework.views import APIView

# #13: Firebase URLを環境変数化
FIREBASE_URL = os.environ.get(
    "FIREBASE_URL",
    "https://optimalis-database-default-rtdb.asia-southeast1.firebasedatabase.app/.json"
)
GETDATA_FILEPATH = os.path.join(os.path.dirname(__file__), "getdata.json")

sess = requests.session()
# ファイルアクセスの競合を防ぐためのロック (#5)
_file_lock = threading.Lock()


class LatestData():
    # #2: クラス変数 → インスタンス変数
    def __init__(self):
        self.LHWD = []

    def updateLHWD(self):
        with _file_lock:
            try:
                with open(GETDATA_FILEPATH, mode='r') as f:
                    lines = f.readlines()
                # 読み取り後にファイルをクリア
                with open(GETDATA_FILEPATH, mode='w'):
                    pass
            except FileNotFoundError:
                return

        for item in lines:
            item = item.strip()
            if not item:
                continue
            try:
                data = json.loads(item)
                data['Time'] = datetime.datetime.strptime(data['Time'], '%Y-%m-%d %H:%M:%S.%f')
                self.LHWD.append(data)
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    def checkLHWD(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.LHWD = [data for data in self.LHWD if data['Time'] >= cutoff]


# #3: fetch_fd=False の二重代入を削除
fetch_fd = True
latestdata = LatestData()


# #4: 関数名 'get' が requests.session.get と衝突するため改名
def fetch_flight_data():
    if not fetch_fd:
        return
    try:
        response = sess.get(FIREBASE_URL)
        json_data = json.loads(response.text)
        json_data['Time'] = str(datetime.datetime.now())
        with _file_lock:
            with open(GETDATA_FILEPATH, mode='a') as f:
                f.write(json.dumps(json_data) + "\n")
    except Exception as e:
        print(f"ERROR: Failed to fetch flight data: {e}")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_flight_data, 'interval', seconds=2)
    scheduler.start()
    print("flight data get is scheduled")


class LHWD(APIView):
    def get(self, request):
        latestdata.updateLHWD()
        latestdata.checkLHWD()
        return Response(latestdata.LHWD)


class LD(APIView):
    def get(self, request):
        latestdata.updateLHWD()
        cutoff = datetime.datetime.now() - datetime.timedelta(seconds=120)
        # #10: flightdataにも同じis_there_dataバグが存在したため修正
        recent = [item for item in latestdata.LHWD if item['Time'] > cutoff]
        if not recent:
            return Response([])
        return Response(max(recent, key=lambda x: x['Time']))