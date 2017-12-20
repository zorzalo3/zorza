from django.urls import path

from . import views

app_name = 'timetable'
urlpatterns = [
    path('', views.hello_world, name='hello'),
    path('timetable/', views.show_default_timetable, name='timetable'),
    path('timetable/class/<int>,', views.show_class_timetable, name='class_timetable'),
    path('timetable/groups/<slug>,', views.show_groups_timetable, name='groups_timetable'),
    path('timetable/room/<int>,', views.show_room_timetable, name='room_timetable'),
    path('timetable/teacher/<int>,', views.show_teacher_timetable, name='teacher_timetable'),
]
