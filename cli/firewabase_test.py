import requests
import json
import numpy as np
import datetime
import time
from apscheduler.schedulers.background import BackgroundScheduler

url="https://optimalis-database-default-rtdb.asia-southeast1.firebasedatabase.app/.json"
sess=requests.session()

ld_file_path="./ld.json"

def get():
   get=sess.get(url) 
   print(get.text)
   json_data=json.loads(get.text)
   json_data['Time']=str(datetime.datetime.now())
   print(json_data)
   f=open(ld_file_path,mode='a')
   f.write(json.dumps(json_data)+"\n")
   f.close

def readMode():
   f=open(ld_file_path,mode='r')
   ld=[]
   for item in f.readlines():
     ld.append(json.loads(item))
   print(len(ld))
   f.close
   f=open(ld_file_path,mode='w')
   f.close
   for item in ld:
      print(item['Time'])

def start():
   scheduler=BackgroundScheduler()
   f=open(ld_file_path,mode='a')
   f.close()
   scheduler.add_job(get,'interval',seconds=5)
   scheduler.start()


is_readMode=False
readMode()
if not is_readMode :
   start()
   time.sleep(1000)

