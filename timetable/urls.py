from django.urls import path

from . import views

urlpatterns = [
    path('', views.show_default_timetable, name='timetable'),
    path('class/<int:class_id>/', views.show_class_timetable, name='class_timetable'),
    path('groups/<group_ids>/', views.show_groups_timetable, name='groups_timetable'),
    path('room/<int:room_id>/', views.show_room_timetable, name='room_timetable'),
    path('teacher/<int:teacher_id>/', views.show_teacher_timetable, name='teacher_timetable'),
    path('personalize/<int:class_id>/', views.personalize, name='personalize'),
    path('times/', views.show_times, name='times'),
]
