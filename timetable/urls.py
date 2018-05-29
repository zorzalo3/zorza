from django.urls import path
from django.views.decorators.cache import never_cache

from .views import *

urlpatterns = [
    path('', show_default_timetable, name='timetable'),
    path('class/<int:class_id>/', show_class_timetable, name='class_timetable'),
    path('groups/<group_ids>/', show_groups_timetable, name='groups_timetable'),
    path('room/<int:room_id>/', show_room_timetable, name='room_timetable'),
    path('teacher/<int:teacher_id>/', show_teacher_timetable, name='teacher_timetable'),
    path('personalize/<int:class_id>/', personalize, name='personalize'),
    path('schedules/', show_schedules, name='schedules'),
    path('substitutions/add/', never_cache(AddSubstitutionsView1.as_view()), name='add_substitutions1'),
    path('substitutions/add/<int:teacher_id>/<date>/', add_substitutions2, name='add_substitutions2'),
    path('manage/', manage, name='manage'),
    path('calendar/edit/', edit_calendar, name='edit_calendar'),
]
