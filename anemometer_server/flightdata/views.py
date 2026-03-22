from django.shortcuts import render

# Create your views here.

import requests,json,datetime,time
from apscheduler.schedulers.background import BackgroundScheduler

from rest_framework.response import Response
from rest_framework.views import APIView

url="https://optimalis-database-default-rtdb.asia-southeast1.firebasedatabase.app/.json"
sess=requests.session()

getdata_filepath="./getdata.json"


class LatestData():
    LHWD=[]#WindSpeed:,Time:(datetime型),AID

    def updateLHWD(self): 
        f=open(getdata_filepath,mode='r')
        givendata=[]
        for item in f.readlines():
            givendata.append(json.loads(item))
        f.close()
        f=open(getdata_filepath,mode='w')
        f.close()
        for item in givendata:
            item['Time']=datetime.datetime.strptime(item['Time'],'%Y-%m-%d %H:%M:%S.%f')
            self.LHWD.append(item)
    
    def checkLHWD(self):
        rmlist=[]
        for data in self.LHWD:
            if data['Time']<(datetime.datetime.now()-datetime.timedelta(hours=1)):
                rmlist.append(data)
        for data in rmlist:
            self.LHWD.remove(data)
    

fetch_fd=False
fetch_fd=True
latestdata=LatestData()

def get():
    if not fetch_fd:
        return 0
    get=sess.get(url) 
    json_data=json.loads(get.text)
    json_data['Time']=str(datetime.datetime.now())
    f=open(getdata_filepath,mode='a')
    f.write(json.dumps(json_data)+"\n")
    f.close()
    

def start():
   scheduler=BackgroundScheduler()
   scheduler.add_job(get,'interval',seconds=2)
   scheduler.start()
   print("flight data get is scheduled")



class LHWD(APIView):
    def get(self,response):
        latestdata.updateLHWD()
        latestdata.checkLHWD()
        return Response(latestdata.LHWD)

class LD(APIView):
    def get(self,response):
        latestdata.updateLHWD()
        if len(latestdata.LHWD) == 0:
            return Response([])
        ld_last=latestdata.LHWD[0]
        is_there_data=False
        for item in latestdata.LHWD:
            if ld_last['Time']<item['Time'] and item['Time']>(datetime.datetime.now()-datetime.timedelta(seconds=120)):
                ld_last=item
                is_there_data=True
        if is_there_data:return Response(ld_last)
        else: return Response([])