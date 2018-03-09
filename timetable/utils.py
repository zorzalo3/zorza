from datetime import date, timedelta
from django.conf import settings
from .models import *
import locale

days = settings.TIMETABLE_WEEKDAYS

# Not always all those values are needed.
# Move to views.py with values for each view?
lesson_values = [
    'id', 'group_id', 'group__name', 'subject_id', 'subject__name',
    'subject__short_name', 'teacher_id', 'teacher__first_name',
    'teacher__last_name', 'teacher__initials', 'period__number', 'weekday',
    'room_id', 'room__name', 'room__short_name',
]

def add_full_name(lesson_values):
    d = lesson_values
    full_name = d['teacher__first_name'] + ' ' + d['teacher__last_name']
    d.update({'teacher__name': full_name})

def get_timetable_context(lessons):
    lessons = lessons.values(*lesson_values)
    for lesson in lessons:
        add_full_name(lesson)
    periods = Period.objects.all()

    # TODO: implement DayPlan

    # TODO: a cleaner way to pass str(period) to the template while using period.number as key?
    table = {period.number: [str(period), {day[0]: [] for day in days}] for period in periods}

    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson['period__number']][1][lesson['weekday']].append(lesson)

    substitutions, absences, reservations = get_events()

    context = {
        'days': days,
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': Teacher.objects.all().values(),
        'room_list': Room.objects.all().values(),
    }
    context.update(get_events())
    return context

EVENTS_SPAN = timedelta(days=3)

def get_events(begin_date=None, end_date=None):
    if begin_date is None:
        begin_date = date.today()
    if end_date is None:
        end_date = begin_date+EVENTS_SPAN

    filter_kwargs = {
        'date__gte': begin_date,
        'date__lt': end_date,
    }

    events = {
        'substitutions': Substitution.objects.filter(**filter_kwargs) \
                            .order_by('date', 'teacher', 'period'),
        'absences': Absence.objects.filter(**filter_kwargs) \
                            .order_by('date', 'group', 'period'),
        'reservations': Reservation.objects.filter(**filter_kwargs) \
                            .order_by('date', 'period'),
    }

    return events
