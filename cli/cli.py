import asyncio
import datetime
import time
import curses
import requests
import json
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout

from server import ServerComm
from Graphic import Graphic

graphic=Graphic()
servercomm=ServerComm()

posts=[""]
graphic.stdscr.keypad(True)

for i in range(100):
    posts.insert(0,"")

def post_mode(count):
    # サーバーの syntax_check に合わせる (AID, Time, data) と同時に
    # DataSerializer に合わせるためトップレベルにも要素を配置する
    data={
        'AID': 1,
        'Time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        'WindSpeed': float(count),
        'WindDirection': 0.0,
        'Latitude': 35.0,
        'Longitude': 135.0,
        'data': {
            'WindSpeed': count,
            'LHWD': True,
            'LD': True
        }
    }
    posts.insert(0,servercomm.post_data(body=data)+" RECEVE AT:"+datetime.datetime.now().strftime("%H:%M:%S")) 

    height,width = graphic.stdscr.getmaxyx()
    for i in range(height-7):
        graphic.stdscr.addstr(i,0,posts[height-7-i][:30])

def get_mode(count):
    graphic.stdscr.addstr(1,40,"GET DATA")
    try:
        response_text = servercomm.get_data(query_set='?LD=True')
        response_json = json.loads(response_text)
        if response_json and len(response_json) > 0:
            getdata = response_json[0]
            # サーバー側でトップレベルに展開するよう修正したため直接取得する
            wind_speed = getdata.get('WindSpeed', 0.0)
            graphic.stdscr.addstr(3,40,str(wind_speed)+"m/s",curses.color_pair(1))
    except (json.JSONDecodeError, KeyError, IndexError) as e:
         graphic.stdscr.addstr(3,40,"Error or No Data",curses.color_pair(2))

def get_status():
    graphic.stdscr.addstr(6,40,'ANEMOMETER STATUS')
    graphic.stdscr.addstr(8,40,'ID:1  WORKING',curses.color_pair(2))

async def task(count):
    await asyncio.gather(
    post_mode(count),
    get_mode(count),
    get_status(),
    )

def main():
    count=int(0)
    try:
        while True:
            graphic.stdscr.clear()
            #asyncio.run(task(count=count))
            post_mode(count)
            get_mode(count)
            get_status()
            graphic.refresh()
            time.sleep(1)
            count+=1
    
    except KeyboardInterrupt:
        curses.endwin()

if __name__ == "__main__":
    main()

"""
表示する項目
瞬間風速
瞬間風向
更新時刻

3分間平均風速推移
3分間平均風向推移

過去

オプション　p pg g


"""