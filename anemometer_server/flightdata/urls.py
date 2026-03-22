from django.urls import path,include
from . import views

urlpatterns=[
    path("LHWD/",views.LHWD.as_view()),
    path("LD/",views.LD.as_view())
]