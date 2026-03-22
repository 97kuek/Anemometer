from django.apps import AppConfig


class DataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data'

    def ready(self):
        from .views import latestdata
        # 起動時にDBから過去1時間分のデータをLHWDに読み込む
        try:
            from .models import Data
            import datetime
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
            for record in Data.objects.filter(Time__gte=cutoff).values():
                item = dict(record.get('data', {}))
                item['Time'] = record['Time']
                item['AID'] = record['AID']
                latestdata.LHWD.append(item)
            print(f'INFO: Loaded {len(latestdata.LHWD)} records from DB')
        except Exception as e:
            print(f'ERROR: Failed to load past data from DB: {e}')
