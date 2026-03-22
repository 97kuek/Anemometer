import hmac
import hashlib
import base64
import os
import requests
import json
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout

class ServerComm():
    def __init__(
            self,
            su='http://localhost:8000/',
            pd='data/create/',
            gd='data/LD/',            
            ):
        self.Server_Url=su
        self.Post_Dir=pd
        self.Get_Dir=gd
        self.SecretKey = os.environ.get("ANEMOMETER_SECRET_KEY", "secret")  # #6: 環境変数化

    def post_data(self,body):
        try:
            # データの整形（サーバー側と一致させる）
            payload = json.dumps(body, separators=(',', ':')).encode('utf-8')
            
            # HMAC-SHA256 署名の生成
            psk = hashlib.sha256(self.SecretKey.encode()).digest()
            signature = hmac.new(key=psk, msg=payload, digestmod=hashlib.sha256).digest()
            auth_header = base64.b64encode(signature).decode()

            headers = {
                'Authorization': auth_header,
                'Content-Type': 'application/json'
            }

            response = requests.post(
                self.Server_Url+self.Post_Dir,
                data=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.text
        except ConnectionError as ce:
            return "Connection Error:"+str(ce)
        except HTTPError as he:
            return "HTTP Error:"+str(he)
        except Timeout as te:
            return "Timeout Error:"+str(te)
        except RequestException as re:
            return "Error:"+str(re)
    


    def get_data(self,query_set=''):
        try:
            response = requests.get(self.Server_Url+self.Get_Dir+query_set)
            return response.text
        except ConnectionError as ce:
            return "Connection Error:"+str(ce)
        except HTTPError as he:
            return "HTTP Error:"+str(he)
        except Timeout as te:
            return "Timeout Error:"+str(te)
        except RequestException as re:
            return "Error:"+str(re)