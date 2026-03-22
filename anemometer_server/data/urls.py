from django.urls import path
from . import views

urlpatterns = [
    path("create/",     views.WinddataAPIView.as_view()),
    path("filter/",     views.FilterdWD.as_view()),
    path("LHWD/",       views.LHWD.as_view()),
    path("LD/",         views.LD.as_view()),
    path("Anemometer/", views.anemometer.as_view()),
    path("DHCP/",       views.DHCP.as_view()),
]