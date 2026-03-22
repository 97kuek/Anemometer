from django.db import models
# Create your models here.
from django.utils import timezone


class SecretKey(models.Model):
    Key=models.CharField(max_length=30)

class Data(models.Model):
    Time=models.DateTimeField()
    AID=models.IntegerField()
    data=models.JSONField()