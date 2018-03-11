import locale
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Min, Max
from django.http import Http404
from django.core.serializers import serialize

from .models import *

days = settings.TIMETABLE_WEEKDAYS

# Not always all those values are needed.
# Move to views.py with values for each view?
lesson_values = [
    'id', 'group_id', 'group__name', 'subject_id', 'subject__name',
    'subject__short_name', 'teacher_id', 'teacher__first_name',
    'teacher__last_name', 'teacher__initials', 'period', 'weekday',
    'room_id', 'room__name', 'room__short_name',
]

def add_full_name(lesson_values):
    d = lesson_values
    full_name = d['teacher__first_name'] + ' ' + d['teacher__last_name']
    d.update({'teacher__name': full_name})

def get_period_range():
    """Returns period numbers for iteration"""
    result = Period.objects.aggregate(Min('number'), Max('number'))
    return range(result['number__min'], result['number__max']+1)

def get_period_strings(periods):
    return {period.number: str(period) for period in periods}

def get_timetable_context(lessons):

    lessons = lessons.values(*lesson_values)
    for lesson in lessons:
        add_full_name(lesson)

    default_periods = Period.objects.filter(timetable__is_default=True)
    if not default_periods:
        raise Http404('No default timetable or periods')

    periods = get_period_range()
    period_strs = get_period_strings(default_periods)

    # TODO: a cleaner way to pass str(period) to the template while using period.number as key?
    table = {period: [period_strs[period], {day[0]: [] for day in days}] for period in periods}

    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson['period']][1][lesson['weekday']].append(lesson)

    context = {
        'days': days,
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': Teacher.objects.all().values(),
        'room_list': Room.objects.all().values(),
        'todays_periods_json': serialize('json', get_todays_periods())
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
        'dayplans': DayPlan.objects.filter(**filter_kwargs),
    }

    return events

def get_todays_periods():
    try:
        times = DayPlan.objects.get(date=date.today()).timetable
    except:
        times = Times.objects.get(is_default=True)
    return times.period_set.all()
