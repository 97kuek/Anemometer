from django.contrib import admin

# Register your models here.

from .models import Data,SecretKey

@admin.register(Data)
class Winddata(admin.ModelAdmin):
    pass

@admin.register(SecretKey)
class SecretKry(admin.ModelAdmin):
    pass