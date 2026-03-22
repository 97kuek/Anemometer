
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.


def http_test(request):
    return HttpResponse("test")

def index(request):
    return render(request,'index.html')