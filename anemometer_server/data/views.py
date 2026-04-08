from collections import deque
from http import HTTPStatus
import hashlib
import hmac
import base64
import datetime
import json
import threading

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Data, SecretKey
from .serializers import UseData


class LatestData():
    def __init__(self):
        self.LHWD = deque(maxlen=1000)        # {WindSpeed, WindDirection, Latitude, Longitude, Time(datetime), AID, ...}
        self.Anemometer = deque(maxlen=256)   # {AID, Status, LastUpdate(datetime)}
        self._lock = threading.Lock()

    def syntax_check(self, givendata):
        data = json.loads(givendata)
        return 'AID' in data and 'Time' in data and 'data' in data

    def updateLHWD(self, givendata):
        data = json.loads(givendata)
        newdata = dict(data.get('data', {}))
        newdata["Time"] = datetime.datetime.strptime(data["Time"], "%Y-%m-%d %H:%M:%S.%f")
        newdata["AID"] = data["AID"]
        with self._lock:
            self.LHWD.append(newdata)

    def updateAnemometer(self, givendata):
        AID = json.loads(givendata)['AID']
        now = datetime.datetime.now()
        with self._lock:
            for data in self.Anemometer:
                if data['AID'] == AID:
                    data['Status'] = 'Working'
                    data['LastUpdate'] = now
                    return
            self.Anemometer.append({"AID": AID, "Status": "Working", "LastUpdate": now})

    def checkLHWD(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        with self._lock:
            self.LHWD = deque(
                (data for data in self.LHWD if data['Time'] >= cutoff),
                maxlen=1000
            )

    def checkAnemometer(self):
        now = datetime.datetime.now()
        unstable_cutoff = now - datetime.timedelta(seconds=15)
        remove_cutoff = now - datetime.timedelta(seconds=60)
        with self._lock:
            for data in self.Anemometer:
                if data['LastUpdate'] < unstable_cutoff:
                    data['Status'] = 'Unstable'
            self.Anemometer = deque(
                (data for data in self.Anemometer if data['LastUpdate'] >= remove_cutoff),
                maxlen=256
            )

    def DHCP(self):
        with self._lock:
            used_aids = {data['AID'] for data in self.Anemometer}
        for i in range(1, 101):
            if i not in used_aids:
                return {"AID": i}
        print('DHCP error: all AID slots used')
        return None

    def auth(self, payload, hmac_header):
        try:
            key_obj = SecretKey.objects.first()
            if key_obj is None:
                print("ERROR: no SecretKey in database")
                return False
            secret = hashlib.sha256(str(key_obj.Key).encode()).digest()
        except Exception as error:
            print("ERROR: fail to get secretKey from DataBase:", error)
            return False
        signature = hmac.new(key=secret, msg=payload, digestmod=hashlib.sha256).digest()
        signature_base64 = base64.b64encode(signature).decode()
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
            row_objects = list(Data.objects.filter(Time__range=(start_date, end_date)).values()[:1000])
            return Response(row_objects)
        except ValueError as e:
            return HttpResponse(f"ERROR: invalid datetime format: {e}", status=HTTPStatus.BAD_REQUEST)
        except KeyError:
            return HttpResponse("ERROR: datetime_range parameter required", status=HTTPStatus.BAD_REQUEST)


class LHWD(APIView):
    def get(self, request):
        latestdata.checkLHWD()
        with latestdata._lock:
            return Response(list(latestdata.LHWD))


class LD(APIView):
    def get(self, request):
        cutoff = datetime.datetime.now() - datetime.timedelta(seconds=120)
        with latestdata._lock:
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
        with latestdata._lock:
            return Response(list(latestdata.Anemometer))


class DHCP(APIView):
    def get(self, request):
        latestdata.checkAnemometer()
        return Response(latestdata.DHCP())
