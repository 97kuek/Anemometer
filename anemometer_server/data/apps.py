from django.apps import AppConfig


class DataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data'

    def ready(self):
        from .views import latestdata
        latestdata.DataInit()
