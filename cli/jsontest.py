"""
シミュレータの動作確認用テストスクリプト。
サーバーが起動している状態で実行してください。

Usage:
    cd cli
    python3 jsontest.py
"""
import requests
import json
import math
import time
import datetime
import hashlib
import hmac
import base64
import os


def sinwind(minute):
    """分を入力として正弦波的な風速を返す（0〜10 m/s）"""
    return 5 * (math.sin(minute / 60 * 2 * math.pi) + 1)


URL = "http://localhost:8000/data/create/"
SECRET_KEY_STR = os.environ.get("ANEMOMETER_SECRET_KEY", "secret")

sess = requests.session()


def make_signature(payload: bytes) -> str:
    psk = hashlib.sha256(SECRET_KEY_STR.encode()).digest()
    signature = hmac.new(key=psk, msg=payload, digestmod=hashlib.sha256).digest()
    return base64.b64encode(signature).decode()


print(f"送信先: {URL}")
print(f"SecretKey: {SECRET_KEY_STR}")
print("Ctrl+C で停止")

while True:
    minute = int(datetime.datetime.now().strftime('%M'))
    wind_speed = sinwind(minute)

    body = {
        "AID": 1,
        "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "WindSpeed": wind_speed,
        "WindDirection": 0.0,
        "Latitude": 35.11972,
        "Longitude": 138.63194,
        "data": {
            "WindSpeed": wind_speed,
            "WindDirection": 0.0,
            "Latitude": 35.11972,
            "Longitude": 138.63194,
            "LHWD": True,
            "LD": True,
        }
    }

    payload = json.dumps(body, separators=(',', ':')).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_signature(payload),
    }

    try:
        res = sess.post(URL, data=payload, headers=headers)
        print(f"[{body['Time']}] status={res.status_code} body={res.text}")
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)
