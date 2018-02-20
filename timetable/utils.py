from datetime import date, timedelta
from django.conf import settings
from .models import *
import locale

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

    # TODO: a cleaner way to pass str(period) to the template while using period.number as key?
    table = {period.number: [str(period), {day[0]: [] for day in days}] for period in periods}

    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson['period__number']][1][lesson['weekday']].append(lesson)

    teachers = Teacher.objects.all().values()

    # Reverse last name and first name
    for teacher in teachers:
        teacher['name'] = ' '.join(teacher['name'].split(' ', 1)[::-1])
    teachers = sorted(teachers, key=lambda t: locale.strxfrm(t['name']))

    substitutions, absences, reservations = get_events()

    context = {
        'days': days,
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': teachers,
        'room_list': Room.objects.all().values(),
    }
    context.update(get_events())
    return context

EVENTS_SPAN = timedelta(days=3)

def get_events(begin_date = date.today(), end_date = date.today()+EVENTS_SPAN):
    filter_kwargs = {
        'date__gte': begin_date,
        'date__lt': end_date,
    }

    events = {
        'substitutions': Substitution.objects.filter(**filter_kwargs),
        'absences': Absence.objects.filter(**filter_kwargs),
        'reservations': Reservation.objects.filter(**filter_kwargs),
    }

    return events
