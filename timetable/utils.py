from django.conf import settings
from .models import *

days = settings.TIMETABLE_WEEKDAYS

# Not always all those values are needed. 
# Move to views.py with values for each view?
lesson_values = [
    'id', 'group_id', 'group__name', 'subject_id', 'subject__name', 
    'subject__short_name', 'teacher_id', 'teacher__name', 'teacher__initials',
    'period__number', 'weekday', 'room_id', 'room__name', 'room__short_name',
]

def get_timetable_context(lessons):
    lessons = lessons.values(*lesson_values)
    periods = Period.objects.all()
    # TODO: implement DayPlan
    
    table = {period.number: {day[0]: [] for day in days} for period in periods}
    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson['period__number']][lesson['weekday']].append(lesson)

    context = {
        'days': days,
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': Teacher.objects.all().values(),
        'room_list': Room.objects.all().values(),
    }
    return context
