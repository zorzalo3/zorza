from django.urls import path

from . import views

app_name = 'timetable'
urlpatterns = [
    path('', views.hello_world, name='hello'),
]
