import locale
from datetime import datetime, date, timedelta
from collections import OrderedDict

from django.conf import settings
from django.db.models import Min, Max
from django.http import Http404
from django.core.serializers import serialize
from django.utils import timezone

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

    default_periods = Period.objects.filter(schedule__is_default=True)
    if not default_periods:
        raise Http404('No default timetable or periods')

    periods = get_period_range()
    period_strs = get_period_strings(default_periods)

    # TODO: a cleaner way to pass period str to the template while using
    #       period number as key?
    table = OrderedDict()
    for period in periods:
        table[period] = (period_strs[period], OrderedDict())
        for day_number, day_string in days:
            table[period][1][day_number] = []

    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson['period']][1][lesson['weekday']].append(lesson)

    teachers = Teacher.objects.all().values()
    teachers = sorted(teachers, key=lambda t:
        locale.strxfrm(t['last_name']+t['first_name']))
        # Sort considering system locale

    context = {
        'days': days,
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': teachers,
        'room_list': Room.objects.all().values(),
        'todays_periods_json': serialize('json', get_todays_periods()),
        'utc_offset': get_utc_offset(),
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

def get_days_periods(date):
    try:
        dayplan = DayPlan.objects.get(date=date)
        # If lessons are cancelled that day, return an empty list
        if dayplan.schedule is None:
            return []
        else:
            schedule = dayplan.schedule
    except:
        weekday = date.weekday()
        # if no dayplan for that day and it's a working day
        if any(weekday == day_number for day_number, day_string in days):
            schedule = Schedule.objects.get(is_default=True)
        else:
            return []
    return schedule.period_set.all()

def get_todays_periods():
    return get_days_periods(date.today())

def get_schedules_table():
    all_periods = Period.objects.all().prefetch_related('schedule')
    min_max = all_periods.aggregate(Min('number'), Max('number'))
    period_range = range(min_max['number__min'], min_max['number__max']+1)
    schedules = {period.schedule for period in all_periods}

    table = OrderedDict()
    for period in period_range:
        table[period] = OrderedDict()
        for schedule in schedules:
            table[period][schedule] = ''

    for period in all_periods:
        table[period.number][period.schedule] = str(period)

    return {
        'schedules': schedules,
        'table': table,
    }

def get_utc_offset():
    """Returns difference from UTC in minutes.
    Compatible with JS Date.getTimezoneOffset"""
    tz = timezone.get_default_timezone()
    now = timezone.make_aware(datetime.now(), tz)
    return -int(now.utcoffset().seconds / 60)

def get_period_str(period, date):
    periods = get_days_periods(date)
    try:
        return periods.get(number=period)
    except:
        return ''
