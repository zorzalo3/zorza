from django.conf import settings
from .models import *

days = settings.TIMETABLE_WEEKDAYS

def get_timetable_context(lessons):
    periods = Period.objects.all()
    # TODO: implement DayPlan
    table = {period: {day[0]: [] for day in days} for period in periods}
    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson.period][lesson.weekday].append(lesson)
    context = {
        'days': days,
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': Teacher.objects.all().values(),
        'room_list': Room.objects.all().values(),
    }
    return context
