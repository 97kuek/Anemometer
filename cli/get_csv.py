import requests
import json
import pandas

filepath='out.csv'

start="2024-04-13T05:15:00"
end="2024-04-13T07:10:00"

host='localhost:8000'
host='anemometer.staging.tyama.mydns.jp'

url='http://'+host+'/data/filter/?datetime_range='+start+','+end

sess=requests.session()
ress=sess.get(url)

print(url)
print(ress)

print(json.loads(ress.text))


df=pandas.json_normalize(json.loads(ress.text))
df.to_csv(filepath, index=False)
