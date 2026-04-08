from collections import deque
import datetime
import json
import os
import threading

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from rest_framework.response import Response
from rest_framework.views import APIView

FIREBASE_URL = os.environ.get(
    "FIREBASE_URL",
    "https://optimalis-database-default-rtdb.asia-southeast1.firebasedatabase.app/.json"
)
GETDATA_FILEPATH = os.path.join(os.path.dirname(__file__), "getdata.json")

sess = requests.session()
_file_lock = threading.Lock()


class LatestData():
    def __init__(self):
        self.LHWD = deque(maxlen=1000)
        self._lock = threading.Lock()

    def updateLHWD(self):
        with _file_lock:
            try:
                with open(GETDATA_FILEPATH, mode='r') as f:
                    lines = f.readlines()
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
                with self._lock:
                    self.LHWD.append(data)
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    def checkLHWD(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        with self._lock:
            self.LHWD = deque(
                (data for data in self.LHWD if data['Time'] >= cutoff),
                maxlen=1000
            )


latestdata = LatestData()


def fetch_flight_data():
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
        with latestdata._lock:
            return Response(list(latestdata.LHWD))


class LD(APIView):
    def get(self, request):
        latestdata.updateLHWD()
        cutoff = datetime.datetime.now() - datetime.timedelta(seconds=120)
        with latestdata._lock:
            recent = [item for item in latestdata.LHWD if item['Time'] > cutoff]
        if not recent:
            return Response([])
        return Response(max(recent, key=lambda x: x['Time']))
