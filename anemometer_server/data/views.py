from http import HTTPStatus
import hashlib
import hmac
import base64
import datetime
import json
import os

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Data, SecretKey
from .serializers import UseData


class LatestData():
    # #10: クラス変数 → インスタンス変数 (全インスタンスで共有されるミュータブルなリストを修正)
    def __init__(self):
        self.LHWD = []       # {WindSpeed, WindDirection, Latitude, Longitude, Time(datetime), AID, ...}
        self.Anemometer = [] # {AID, Status, LastUpdate(datetime)}

    def syntax_check(self, givendata):
        data = json.loads(givendata)
        return 'AID' in data and 'Time' in data and 'data' in data

    def updateLHWD(self, givendata):
        data = json.loads(givendata)
        # 'data'の中身をトップレベルに展開してGrafanaから直接読めるようにする
        newdata = dict(data.get('data', {}))
        newdata["Time"] = datetime.datetime.strptime(data["Time"], "%Y-%m-%d %H:%M:%S.%f")
        newdata["AID"] = data["AID"]
        self.LHWD.append(newdata)

    def updateAnemometer(self, givendata):
        AID = json.loads(givendata)['AID']
        now = datetime.datetime.now()
        # #11: LastUpdateをdatetime型で保存(strptimeの都度呼び出しを不要にする)
        for data in self.Anemometer:
            if data['AID'] == AID:
                data['Status'] = 'Working'
                data['LastUpdate'] = now
                return
        self.Anemometer.append({"AID": AID, "Status": "Working", "LastUpdate": now})

    def checkLHWD(self):
        # リスト内包表記でシンプルに
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.LHWD = [data for data in self.LHWD if data['Time'] >= cutoff]

    def checkAnemometer(self):
        # #11: strptime不要 (LastUpdateがdatetime型になったため)
        now = datetime.datetime.now()
        unstable_cutoff = now - datetime.timedelta(seconds=15)
        remove_cutoff = now - datetime.timedelta(seconds=60)
        for data in self.Anemometer:
            if data['LastUpdate'] < unstable_cutoff:
                data['Status'] = 'Unstable'
        self.Anemometer = [data for data in self.Anemometer if data['LastUpdate'] >= remove_cutoff]

    def DHCP(self):
        # #10(DHCP): AIDをintで比較するよう修正 (元はstr比較でバグ)
        used_aids = {data['AID'] for data in self.Anemometer}
        for i in range(1, 101):
            if i not in used_aids:
                return {"AID": i}
        print('DHCP error: all AID slots used')
        return None

    # HMAC-SHA256（BASE64）で認証
    def auth(self, payload, hmac_header):
        # #1: DB取得失敗時にFalseを返す (元はUnboundLocalErrorが発生していた)
        try:
            secret = hashlib.sha256(str(SecretKey.objects.all()[0].Key).encode()).digest()
        except Exception as error:
            print("ERROR: fail to get secretKey from DataBase:", error)
            return False
        signature = hmac.new(key=secret, msg=payload, digestmod=hashlib.sha256).digest()
        signature_base64 = base64.b64encode(signature).decode()
        # #7: 署名値とHMACヘッダのprint削除 (セキュリティリスク)
        return signature_base64 == hmac_header


latestdata = LatestData()


class WinddataAPIView(APIView):

    def post(self, request):
        if not latestdata.syntax_check(request.body):
            return HttpResponse("Syntax Error", status=HTTPStatus.BAD_REQUEST)
        if not latestdata.auth(request.body, request.headers.get('Authorization')):
            return HttpResponse("Authentication Error", status=HTTPStatus.UNAUTHORIZED)

        js_body = json.loads(request.body)
        js_body["Time"] = str(datetime.datetime.now())
        modified_body = json.dumps(js_body, separators=(',', ':')).encode('utf-8')
        modified_data = dict(js_body)

        latestdata.updateLHWD(modified_body)
        latestdata.updateAnemometer(modified_body)
        DataSerializer = UseData(data=modified_data)
        DataSerializer.is_valid(raise_exception=True)
        DataSerializer.save()
        return HttpResponse('good', status=HTTPStatus.CREATED)


class FilterdWD(APIView):
    def get(self, request):
        qs = request.query_params
        try:
            dt_range = qs["datetime_range"].split(',')
            dt_form = "%Y-%m-%dT%H:%M:%S"
            start_date = datetime.datetime.strptime(dt_range[0], dt_form)
            end_date = datetime.datetime.strptime(dt_range[1], dt_form)
            row_objects = list(Data.objects.filter(Time__range=(start_date, end_date)).values())
            return Response(row_objects)
        except ValueError as e:
            return HttpResponse(f"ERROR: invalid datetime format: {e}", status=HTTPStatus.BAD_REQUEST)
        except KeyError:
            return HttpResponse("ERROR: datetime_range parameter required", status=HTTPStatus.BAD_REQUEST)


class LHWD(APIView):
    def get(self, request):
        latestdata.checkLHWD()
        return Response(latestdata.LHWD)


class LD(APIView):
    def get(self, request):
        cutoff = datetime.datetime.now() - datetime.timedelta(seconds=120)
        aids_in_anemometer = {item['AID'] for item in latestdata.Anemometer}
        LDlist = []
        for aid in aids_in_anemometer:
            recent = [item for item in latestdata.LHWD if item['AID'] == aid and item['Time'] > cutoff]
            if recent:
                LDlist.append(max(recent, key=lambda x: x['Time']))
        return Response(LDlist)


class anemometer(APIView):
    def get(self, request):
        latestdata.checkAnemometer()
        return Response(latestdata.Anemometer)


class DHCP(APIView):
    def get(self, request):
        latestdata.checkAnemometer()
        return Response(latestdata.DHCP())
