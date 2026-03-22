
from django.urls import path,include
from . import views

urlpatterns = [
    path(r'http_test/',views.http_test),
    path('frontend/',views.index),
]