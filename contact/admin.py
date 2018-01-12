from django.contrib import admin
from .models import *

class MessageAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime',)

admin.site.register(Message, MessageAdmin)
