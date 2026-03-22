from django.apps import AppConfig


class FlightdataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flightdata'

    def ready(self):
        from .views import start
        start()